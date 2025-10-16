"""
Google Calendar Authentication Module

This module provides authentication and token management for Google Calendar API access.
All calendar functions should use get_access_token() to authenticate users.
"""

import os
import boto3
import logging
import urllib.request
import urllib.parse
import json
import traceback
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Configuration
SUBSCRIBERS_TABLE_NAME = os.environ.get('SUBSCRIBERS_TABLE_NAME')
AGENTS_ALLOCATION_TABLE_NAME = os.environ.get('AGENTS_ALLOCATION_TABLE_NAME')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message, status_code=403):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def refresh_access_token(refresh_token):
    """
    Refresh Google access token using refresh token
    
    Args:
        refresh_token: The refresh token
        
    Returns:
        tuple: (new_token_data, error)
    """
    try:
        url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_encoded, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            
            if response.status != 200:
                error_msg = f"Failed to refresh access token: {response.status} - {response_data}"
                logger.error(error_msg)
                return None, error_msg
            
            token_data = json.loads(response_data)
            logger.info("Access token refresh successful")
            return token_data, None
        
    except Exception as e:
        error_msg = f"Error refreshing access token: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg


def lookup_email_from_agents_table(auth_email):
    """
    Lookup the email field from AGENTS_ALLOCATION_TABLE_NAME using auth_email as agent_email
    
    Args:
        auth_email (str): The agent_email to search for
        
    Returns:
        tuple: (email, error)
               - email: The email field from the record if found
               - error: Error message if not found or error occurred
    """
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        agents_table = dynamodb.Table(AGENTS_ALLOCATION_TABLE_NAME)
        
        # Query the agents table using agent_email as primary key
        response = agents_table.get_item(
            Key={'agent_email': auth_email}
        )
        
        # Check if item exists
        if 'Item' not in response:
            logger.error(f"Agent email not found in agents allocation table: {auth_email}")
            return None, f"Agent email {auth_email} not found in agents allocation table"
        
        # Extract the email field
        email = response['Item'].get('email')
        if not email:
            logger.error(f"No email field found for agent_email: {auth_email}")
            return None, f"No email field found for agent_email: {auth_email}"
        
        logger.info(f"Found email {email} for agent_email {auth_email}")
        return email, None
        
    except Exception as e:
        error_msg = f"Error looking up email from agents table: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg


def update_token_in_dynamodb(dynamodb_table, email, new_access_token, refresh_token, expires_in):
    """
    Update access token in DynamoDB
    
    Args:
        dynamodb_table: DynamoDB table object
        email: User's email (primary key)
        new_access_token: New access token
        refresh_token: Refresh token
        expires_in: Token expiration time in seconds
    """
    try:
        token_expires_at = (
            datetime.utcnow() + timedelta(seconds=expires_in)
        ).isoformat()
        
        dynamodb_table.update_item(
            Key={'email': email},
            UpdateExpression='SET google_access_token = :token, token_expires_at = :expires, refresh_token = :refresh',
            ExpressionAttributeValues={
                ':token': new_access_token,
                ':expires': token_expires_at,
                ':refresh': refresh_token
            }
        )
        logger.info(f"Token updated in database for user: {email}")
        return True, None
        
    except Exception as e:
        error_msg = f"Error updating token in DynamoDB: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return False, error_msg


def get_access_token(auth_email):
    """
    Get valid access token for a user, refreshing if necessary.
    
    This function acts as an authentication layer for all Google Calendar operations.
    It first looks up the auth_email in AGENTS_ALLOCATION_TABLE_NAME to get the corresponding
    email, then retrieves the user's access token from DynamoDB and refreshes it if expired.
    
    Args:
        auth_email (str): Agent email address (primary key in AGENTS_ALLOCATION_TABLE_NAME)
        
    Returns:
        tuple: (access_token, user_data, error)
               - access_token: Valid Google access token
               - user_data: User data from DynamoDB
               - error: Error dictionary if authentication fails
               
    Raises:
        AuthenticationError: If user is not authorized (no token in database)
    """
    try:
        # First, lookup the email from AGENTS_ALLOCATION_TABLE_NAME using auth_email
        email, lookup_error = lookup_email_from_agents_table(auth_email)
        if lookup_error:
            logger.error(f"Failed to lookup email for auth_email {auth_email}: {lookup_error}")
            raise AuthenticationError(f"Agent email not found: {lookup_error}", 404)
        
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        dynamodb_table = dynamodb.Table(SUBSCRIBERS_TABLE_NAME)
        
        # Query user from DynamoDB using email as primary key
        response = dynamodb_table.query(
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={
                ':email': email
            }
        )
        
        # Check if user exists
        if not response.get('Items'):
            logger.error(f"User not found in database: {email}")
            raise AuthenticationError("User not found", 404)
        
        user_data = response['Items'][0]
        
        # Check if user has calendar access
        access_token = user_data.get('google_access_token')
        refresh_token = user_data.get('refresh_token')
        
        if not access_token or not refresh_token:
            logger.error(f"User {email} does not have calendar access (no tokens)")
            raise AuthenticationError(
                "User is not authorized for calendar access. Please grant calendar permissions.",
                403
            )
        
        # Check token expiration
        token_expires_at = user_data.get('token_expires_at')
        if token_expires_at:
            try:
                expires_datetime = datetime.fromisoformat(token_expires_at.replace('Z', '+00:00'))
                current_time = datetime.utcnow()
                buffer_time = timedelta(seconds=30)  # 30 second buffer
                
                # If token is expired or will expire soon, refresh it
                if current_time + buffer_time >= expires_datetime:
                    logger.info(f"Access token expired for {email}, refreshing...")
                    
                    new_token_data, refresh_error = refresh_access_token(refresh_token)
                    
                    if refresh_error:
                        logger.error(f"Failed to refresh token for {email}: {refresh_error}")
                        raise AuthenticationError(
                            "Failed to refresh access token. Please re-authorize.",
                            401
                        )
                    
                    # Update access token
                    access_token = new_token_data.get('access_token')
                    expires_in = new_token_data.get('expires_in', 3600)
                    
                    # Update token in database
                    update_success, update_error = update_token_in_dynamodb(
                        dynamodb_table, 
                        email, 
                        access_token, 
                        refresh_token, 
                        expires_in
                    )
                    
                    if not update_success:
                        logger.warning(f"Failed to update token in database: {update_error}")
                    
                    # Update user_data with new token info
                    user_data['google_access_token'] = access_token
                    user_data['token_expires_at'] = (
                        datetime.utcnow() + timedelta(seconds=expires_in)
                    ).isoformat()
                    
                    logger.info(f"Token refreshed successfully for {email}")
                else:
                    logger.info(f"Token is still valid for {email}")
                    
            except Exception as e:
                logger.warning(f"Error checking token expiry for {email}: {str(e)}")
                # Continue with existing token if expiry check fails
        
        logger.info(f"Access token retrieved successfully for {email}")
        return access_token, user_data, None
        
    except AuthenticationError:
        # Re-raise authentication errors
        raise
    except Exception as e:
        error_msg = f"Error getting access token: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        raise AuthenticationError(f"Authentication error: {str(e)}", 500)


def get_calendar_service(email):
    """
    Get authenticated Google Calendar API service object.
    
    Args:
        email (str): User's email address
        
    Returns:
        tuple: (calendar_service, user_data, error)
    """
    try:
        access_token, user_data, error = get_access_token(email)
        if error:
            return None, None, error
        
        # Create credentials object
        credentials = Credentials(token=access_token)
        
        # Build Calendar API service
        service = build('calendar', 'v3', credentials=credentials)
        
        return service, user_data, None
        
    except AuthenticationError as e:
        return None, None, {
            'error': e.message,
            'status_code': e.status_code
        }
    except Exception as e:
        error_msg = f"Error creating calendar service: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, None, {
            'error': error_msg,
            'status_code': 500
        }

