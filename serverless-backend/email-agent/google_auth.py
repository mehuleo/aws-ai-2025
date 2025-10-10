import json
import boto3
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
import os
import traceback
import logging
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Configuration - Read from environment variables
SUBSCRIBERS_TABLE_NAME = os.environ.get('SUBSCRIBERS_TABLE_NAME')

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# Validate environment variables
def validate_environment():
    """Validate that all required environment variables are set"""
    missing_vars = []
    
    if not SUBSCRIBERS_TABLE_NAME:
        missing_vars.append('SUBSCRIBERS_TABLE_NAME')
    if not GOOGLE_CLIENT_ID:
        missing_vars.append('GOOGLE_CLIENT_ID')
    if not GOOGLE_CLIENT_SECRET:
        missing_vars.append('GOOGLE_CLIENT_SECRET')
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        return False, error_msg
    
    logger.info("All required environment variables are set")
    return True, None

def create_response(status_code, body_data, success=True):
    """Create a standardized HTTP response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body_data)
    }

def verify_google_token(token):
    """Verify Google ID token and return user info"""
    try:
        # Verify the token with Google
        url = f'https://oauth2.googleapis.com/tokeninfo?id_token={token}'
        
        with urllib.request.urlopen(url) as response:
            response_data = response.read().decode('utf-8')
            
            if response.status != 200:
                error_msg = f"Token verification failed: {response.status}"
                logger.error(f"{error_msg} - Response: {response_data}")
                return None, error_msg
            
            token_info = json.loads(response_data)
            
            # Verify the audience (client ID)
            if token_info.get('aud') != GOOGLE_CLIENT_ID:
                error_msg = f"Invalid audience in token. Expected: {GOOGLE_CLIENT_ID}, Got: {token_info.get('aud')}"
                logger.error(error_msg)
                return None, "Invalid audience in token"
            
            # Check token expiration
            exp = token_info.get('exp')
            if exp and datetime.utcnow().timestamp() > float(exp):
                error_msg = f"Token has expired. Exp: {exp}, Current: {datetime.utcnow().timestamp()}"
                logger.error(error_msg)
                return None, "Token has expired"
            
            logger.info(f"Token verified for user: {token_info.get('email', 'unknown')}")
            return token_info, None
        
    except urllib.error.URLError as e:
        error_msg = f"Error making request to Google: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Error verifying token: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg

def get_google_access_token(authorization_code, redirect_uri):
    """Exchange authorization code for access token"""
    try:
        token_url = 'https://oauth2.googleapis.com/token'
        
        data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        # Encode the data for POST request
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        
        # Create the request
        req = urllib.request.Request(token_url, data=data_encoded, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            
            if response.status != 200:
                error_msg = f"Failed to get access token: {response.status} - {response_data}"
                logger.error(error_msg)
                return None, error_msg
            
            token_data = json.loads(response_data)
            logger.info("Access token exchange successful")
            return token_data, None
        
    except urllib.error.URLError as e:
        error_msg = f"Error making request to Google: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Error getting access token: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg

def store_user_in_dynamodb(dynamodb_table, user_info, access_token=None):
    """Store or update user information and access token in DynamoDB"""
    try:
        user_id = user_info.get('sub')
        email = user_info.get('email')
        
        if not user_id or not email:
            error_msg = f"Missing required user information. user_id: {user_id}, email: {email}"
            logger.error(error_msg)
            return False, "Missing required user information"
        
        # Check if user already exists
        existing_user, error = get_user_from_dynamodb(dynamodb_table, email)
        
        if existing_user:
            # User exists, update the record
            logger.info(f"Updating existing user: {email}")
            
            # Generate new SID for update
            new_sid = str(uuid.uuid4())
            
            # Prepare update data
            update_data = {
                'email': email,  # Primary key
                'sid': new_sid,  # Sort key (refresh with new SID)
                'userId': user_id,
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'email_verified': user_info.get('email_verified', False),
                'last_login': datetime.utcnow().isoformat()
            }
            
            # Add access token if provided
            if access_token:
                update_data['google_access_token'] = access_token.get('access_token', '')
                update_data['refresh_token'] = access_token.get('refresh_token', '')
                update_data['token_expires_at'] = (
                    datetime.utcnow() + timedelta(seconds=access_token.get('expires_in', 3600))
                ).isoformat()
                update_data['calendar_access'] = True
            else:
                update_data['calendar_access'] = False
            
            # Update the item using email as primary key and sid as sort key
            dynamodb_table.put_item(Item=update_data)
            logger.info(f"User data updated for: {email} with new SID: {new_sid}")
            
        else:
            # User doesn't exist, create new record
            logger.info(f"Creating new user: {email}")
            
            # Generate new SID for new user
            new_sid = str(uuid.uuid4())
            
            # Prepare user data
            user_data = {
                'email': email,  # Primary key
                'sid': new_sid,  # Sort key
                'userId': user_id,
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'email_verified': user_info.get('email_verified', False),
                'last_login': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Add access token if provided
            if access_token:
                user_data['google_access_token'] = access_token.get('access_token', '')
                user_data['refresh_token'] = access_token.get('refresh_token', '')
                user_data['token_expires_at'] = (
                    datetime.utcnow() + timedelta(seconds=access_token.get('expires_in', 3600))
                ).isoformat()
                user_data['calendar_access'] = True
            else:
                user_data['calendar_access'] = False
            
            # Store in DynamoDB
            dynamodb_table.put_item(Item=user_data)
            logger.info(f"New user data stored for: {email} with SID: {new_sid}")
        
        return True, None
        
    except Exception as e:
        error_msg = f"Error storing user data: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return False, error_msg

def get_user_from_dynamodb(dynamodb_table, email):
    """Retrieve user information from DynamoDB using query with email as primary key"""
    try:
        # Use query since email is now the primary key
        response = dynamodb_table.query(
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={
                ':email': email
            }
        )
        
        if response['Items']:
            # Return the first matching item (there should only be one per email)
            user_item = response['Items'][0]
            logger.info(f"User found: {email}")
            return user_item, None
        else:
            logger.info(f"User not found: {email}")
            return None, "User not found"
            
    except Exception as e:
        error_msg = f"Error retrieving user data: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg

def validateGoogleAuth(event, context):
    """Main Lambda handler for Google authentication validation"""
    try:
        # Validate environment variables first
        env_valid, env_error = validate_environment()
        if not env_valid:
            logger.error(f"Environment validation failed: {env_error}")
            return create_response(500, {
                'success': False,
                'error': 'Server configuration error'
            })
        
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        dynamodb_table = dynamodb.Table(SUBSCRIBERS_TABLE_NAME)
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Get the action type
        action = body.get('action', 'validate_token')
        logger.info(f"Processing action: {action}")
        
        if action == 'validate_token':
            # Validate Google ID token
            token = body.get('token')
            if not token:
                logger.error("Token is missing from request body")
                return create_response(400, {
                    'success': False,
                    'error': 'Token is required'
                })
            
            # Verify token with Google
            user_info, error = verify_google_token(token)
            if error:
                logger.error(f"Token verification failed: {error}")
                return create_response(401, {
                    'success': False,
                    'error': error
                })
            
            # Store/update user in DynamoDB
            success, store_error = store_user_in_dynamodb(dynamodb_table, user_info)
            if not success:
                logger.warning(f"Failed to store user data: {store_error}")
            
            # Get the stored user data to include UUID
            stored_user_data, _ = get_user_from_dynamodb(dynamodb_table, user_info.get('email'))
            
            # Return user information
            response_data = {
                'success': True,
                'user': {
                    'sid': stored_user_data.get('sid') if stored_user_data else None,
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'email_verified': user_info.get('email_verified', False)
                }
            }
            logger.info(f"Authentication successful for user: {user_info.get('email')}")
            return create_response(200, response_data)
        
        elif action == 'get_calendar_access':
            # Handle Google Calendar access request
            email = body.get('email')
            if not email:
                logger.error("Email is missing from request body for calendar access")
                return create_response(400, {
                    'success': False,
                    'error': 'Email is required'
                })
            
            # Get user from DynamoDB
            user_data, error = get_user_from_dynamodb(dynamodb_table, email)
            if error:
                logger.error(f"Failed to get user data for calendar access: {error}")
                return create_response(404, {
                    'success': False,
                    'error': error
                })
            
            # Check if user already has calendar access
            calendar_access = user_data.get('calendar_access', False)
            if calendar_access:
                return create_response(200, {
                    'success': True,
                    'has_calendar_access': True,
                    'message': 'User already has calendar access'
                })
            
            # Generate OAuth URL for calendar access
            oauth_params = {
                'client_id': GOOGLE_CLIENT_ID,
                'redirect_uri': body.get('redirect_uri', 'http://localhost:3000/dashboard'),
                'scope': 'https://www.googleapis.com/auth/calendar',
                'response_type': 'code',
                'access_type': 'offline',
                'prompt': 'consent',
                'state': email  # Use email as state to identify user
            }
            
            oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(oauth_params)}"
            
            return create_response(200, {
                'success': True,
                'has_calendar_access': False,
                'oauth_url': oauth_url
            })
        
        elif action == 'get_user':
            # Get user information from DynamoDB with SID authentication
            email = body.get('email')
            sid = body.get('sid')
            
            if not email:
                logger.error("Email is missing from request body for get_user")
                return create_response(400, {
                    'success': False,
                    'error': 'Email is required'
                })
            
            if not sid:
                logger.error("SID is missing from request body for get_user")
                return create_response(400, {
                    'success': False,
                    'error': 'SID is required'
                })
            
            # Get user from DynamoDB
            user_data, error = get_user_from_dynamodb(dynamodb_table, email)
            if error:
                return create_response(404, {
                    'success': False,
                    'error': error
                })
            
            # Verify SID matches (authentication check)
            stored_sid = user_data.get('sid')
            if stored_sid != sid:
                logger.warning(f"SID mismatch for user {email}. Expected: {stored_sid}, Received: {sid}")
                return create_response(403, {
                    'success': False,
                    'error': 'Invalid SID - authentication failed'
                })
            
            # Return user information
            return create_response(200, {
                'success': True,
                'user': {
                    'id': user_data.get('userId'),
                    'sid': user_data.get('sid'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'picture': user_data.get('picture'),
                    'email_verified': user_data.get('email_verified', False),
                    'calendar_access': user_data.get('calendar_access', False)
                }
            })
        
        elif action == 'exchange_code':
            # Exchange authorization code for access token
            authorization_code = body.get('code')
            redirect_uri = body.get('redirect_uri')
            email = body.get('email')
            
            if not authorization_code or not redirect_uri or not email:
                logger.error("Missing required parameters for code exchange")
                return create_response(400, {
                    'success': False,
                    'error': 'Authorization code, redirect URI, and email are required'
                })
            
            # Exchange code for access token
            access_token_data, error = get_google_access_token(authorization_code, redirect_uri)
            if error:
                return create_response(400, {
                    'success': False,
                    'error': error
                })
            
            # Get user from DynamoDB
            user_data, error = get_user_from_dynamodb(dynamodb_table, email)
            if error:
                return create_response(404, {
                    'success': False,
                    'error': error
                })
            
            # Update user with access token
            success, store_error = store_user_in_dynamodb(dynamodb_table, user_data, access_token_data)
            if not success:
                return create_response(500, {
                    'success': False,
                    'error': store_error
                })
            
            logger.info(f"Calendar access granted for user: {email}")
            return create_response(200, {
                'success': True,
                'message': 'Calendar access granted successfully'
            })
        
        else:
            logger.error(f"Invalid action received: {action}")
            return create_response(400, {
                'success': False,
                'error': 'Invalid action. Supported actions: validate_token, get_calendar_access, get_user, exchange_code'
            })
    
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in request body: {str(e)}"
        logger.error(f"{error_msg} - Body: {event.get('body', 'None')}")
        return create_response(400, {
            'success': False,
            'error': 'Invalid JSON in request body'
        })
    except Exception as e:
        error_msg = f"Error in Google auth validation: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        
        # Return more specific error information in development
        error_detail = str(e) if os.environ.get('ENVIRONMENT') == 'development' else 'Internal server error'
        
        return create_response(500, {
            'success': False,
            'error': error_detail
        })

def handle_options(event, context):
    """Handle CORS preflight requests"""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': ''
    }
