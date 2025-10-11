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
GOOGLE_AUTH_REDIRECT_URI = os.environ.get('GOOGLE_AUTH_REDIRECT_URI')

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
    if not GOOGLE_AUTH_REDIRECT_URI:
        missing_vars.append('GOOGLE_AUTH_REDIRECT_URI')
    
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
            
            # Add user_name field for compatibility (same as name from Google)
            token_info['user_name'] = token_info.get('name', '')
            
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
            # logger.info(f"Response data: {str(response_data)}")
            logger.info("Access token exchange successful")
            """token_data sample response:
                {
                    "access_token": "string",
                    "expires_in": 1234,
                    "refresh_token": "string",
                    "scope": "string",
                    "token_type": "string",
                    "refresh_token_expires_in": 123,
                }
            """
            return token_data, None
        
    except urllib.error.URLError as e:
        error_msg = f"Error making request to Google: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Error getting access token: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg

def store_user_in_dynamodb(dynamodb_table, user_info, access_token=None, renew_sid=True):
    """Store or update user information and access token in DynamoDB
    Args:
        dynamodb_table: DynamoDB table object
        user_info: Dictionary containing user information
        access_token: Optional access token data
        renew_sid: If True, generate a new SID for the user; if False, use the existing SID
    """
    try:
        # Generate new SID for new user
        if renew_sid:
            new_sid = str(uuid.uuid4())
        else:
            new_sid = user_info.get('sid', None)
            
        if not new_sid:
            error_msg = f"Missing required user information. sid: {new_sid}"
            logger.error(error_msg)
            return False, "Missing required user information"
            
        user_id = user_info.get('sub') or user_info.get('userId')
        email = user_info.get('email')
        
        if not email:
            error_msg = f"Missing required user information. email: {email}"
            logger.error(error_msg)
            return False, "Missing required user information"
        
        # Check if user already exists
        existing_user, error = get_user_from_dynamodb(dynamodb_table, email)
        
        if existing_user:
            # User exists, update the record
            logger.info(f"Updating existing user: {email}")
            
            # Prepare update data
            update_data = {
                'userId': user_id,
                'user_name': user_info.get('user_name', ''),
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
                update_data['google_access_token'] = existing_user.get('google_access_token', None)
                update_data['refresh_token'] = existing_user.get('refresh_token', None)
                update_data['token_expires_at'] = existing_user.get('token_expires_at', None)
                update_data['calendar_access'] = existing_user.get('calendar_access', False)
            
            # Print debug information
            # print(f"update_data: {str(update_data)}")
            # print(f"existing_user: {str(existing_user)}")
            # print(f"user_info: {str(user_info)}")
            
            # Update the item using email as primary key
            dynamodb_table.update_item(
                Key={
                    'email': email
                },
                UpdateExpression='SET sid = :new_sid, userId = :userId, user_name = :user_name, picture = :picture, email_verified = :email_verified, last_login = :last_login, google_access_token = :google_access_token, refresh_token = :refresh_token, token_expires_at = :token_expires_at, calendar_access = :calendar_access',
                ExpressionAttributeValues={
                    ':new_sid': new_sid,
                    ':userId': update_data['userId'],
                    ':user_name': update_data['user_name'],
                    ':picture': update_data['picture'],
                    ':email_verified': update_data['email_verified'],
                    ':last_login': update_data['last_login'],
                    ':google_access_token': update_data.get('google_access_token', ''),
                    ':refresh_token': update_data.get('refresh_token', ''),
                    ':token_expires_at': update_data.get('token_expires_at', ''),
                    ':calendar_access': update_data.get('calendar_access', False)
                }
            )
            logger.info(f"User data updated for: {email} with new SID: {new_sid}")
            
        else:
            # User doesn't exist, create new record
            logger.info(f"Creating new user: {email}")
            
            # Prepare user data
            user_data = {
                'email': email,  # Primary key
                'sid': new_sid,
                'userId': user_id,
                'user_name': user_info.get('user_name', ''),
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
                user_data['google_access_token'] = None
                user_data['refresh_token'] = None
                user_data['token_expires_at'] = None
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

def refresh_access_token(client_id, client_secret, refresh_token):
    """Refresh Google access token using refresh token"""
    try:
        url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        # Encode the data for POST request
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        
        # Create the request
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
        
    except urllib.error.URLError as e:
        error_msg = f"Error making request to Google for token refresh: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Error refreshing access token: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg

def get_google_calendars(access_token, user_data, dynamodb_table=None):
    """Fetch user's Google calendars using the access token"""
    try:
        # Check if token is expired (with 30 second buffer)
        token_expires_at = user_data.get('token_expires_at')
        if token_expires_at:
            try:
                expires_datetime = datetime.fromisoformat(token_expires_at.replace('Z', '+00:00'))
                current_time = datetime.utcnow()
                buffer_time = timedelta(seconds=30)
                
                if current_time + buffer_time >= expires_datetime:
                    logger.info("Access token is expired or will expire soon, refreshing...")
                    
                    # Get refresh token
                    refresh_token = user_data.get('refresh_token')
                    if not refresh_token:
                        error_msg = "No refresh token available"
                        logger.error(error_msg)
                        return None, error_msg
                    
                    # Refresh the access token
                    new_token_data, refresh_error = refresh_access_token(
                        GOOGLE_CLIENT_ID, 
                        GOOGLE_CLIENT_SECRET, 
                        refresh_token
                    )
                    
                    if refresh_error:
                        logger.error(f"Failed to refresh access token: {refresh_error}")
                        return None, f"Token refresh failed: {refresh_error}"
                    
                    # Update the access token in the response
                    access_token = new_token_data.get('access_token')
                    
                    # Update database with new token if dynamodb_table is provided
                    if dynamodb_table:
                        # Prepare updated token data for database storage
                        updated_token_data = {
                            'access_token': access_token,
                            'refresh_token': refresh_token,  # Keep the same refresh token
                            'expires_in': new_token_data.get('expires_in', 3600)
                        }
                        
                        # Update user data in database
                        success, store_error = store_user_in_dynamodb(
                            dynamodb_table, 
                            user_data, 
                            updated_token_data, 
                            renew_sid=False
                        )
                        
                        if not success:
                            logger.warning(f"Failed to update database with new token: {store_error}")
                        else:
                            logger.info("Database updated with new access token")
                    
                    logger.info("Access token refreshed successfully")
            except Exception as e:
                logger.warning(f"Error checking token expiry: {str(e)}")
                # Continue with original token if expiry check fails
        
        url = 'https://www.googleapis.com/calendar/v3/users/me/calendarList'
        
        # Create the request with authorization header
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            
            if response.status != 200:
                error_msg = f"Failed to fetch calendars: {response.status} - {response_data}"
                logger.error(error_msg)
                return None, error_msg
            
            calendar_data = json.loads(response_data)
            calendars = []
            
            # Extract relevant calendar information
            for calendar in calendar_data.get('items', []):
                calendar_info = {
                    'id': calendar.get('id'),
                    'summary': calendar.get('summary'),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False),
                    'accessRole': calendar.get('accessRole'),
                    'backgroundColor': calendar.get('backgroundColor', '#1a73e8'),
                    'foregroundColor': calendar.get('foregroundColor', '#ffffff')
                }
                calendars.append(calendar_info)
            
            logger.info(f"Successfully fetched {len(calendars)} calendars")
            return calendars, None
        
    except urllib.error.URLError as e:
        error_msg = f"Error making request to Google Calendar API: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Error fetching calendars: {str(e)}"
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
                    'user_name': user_info.get('user_name'),
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
            
            # # Check if user already has calendar access
            # calendar_access = user_data.get('calendar_access', False)
            # if calendar_access:
            #     return create_response(200, {
            #         'success': True,
            #         'has_calendar_access': True,
            #         'message': 'User already has calendar access'
            #     })
            
            # Generate OAuth URL for calendar access
            oauth_params = {
                'client_id': GOOGLE_CLIENT_ID,
                'redirect_uri': body.get('redirect_uri', GOOGLE_AUTH_REDIRECT_URI),
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
                    'user_name': user_data.get('user_name'),
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
            
            # Update user with access token, and prevent renewing the SID
            success, store_error = store_user_in_dynamodb(dynamodb_table, user_data, access_token_data, False)
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
        
        elif action == 'get_calendars':
            # Get user's Google calendars
            email = body.get('email')
            sid = body.get('sid')
            
            if not email:
                logger.error("Email is missing from request body for get_calendars")
                return create_response(400, {
                    'success': False,
                    'error': 'Email is required'
                })
            
            if not sid:
                logger.error("SID is missing from request body for get_calendars")
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
            
            # Check if user has calendar access
            if not user_data.get('calendar_access', False):
                return create_response(403, {
                    'success': False,
                    'error': 'User does not have calendar access'
                })
            
            # Get access token
            access_token = user_data.get('google_access_token')
            if not access_token:
                return create_response(403, {
                    'success': False,
                    'error': 'No access token available'
                })
            
            # Fetch calendars from Google Calendar API
            calendars, error = get_google_calendars(access_token, user_data, dynamodb_table)
            if error:
                return create_response(500, {
                    'success': False,
                    'error': error
                })
            
            return create_response(200, {
                'success': True,
                'calendars': calendars
            })
        
        else:
            logger.error(f"Invalid action received: {action}")
            return create_response(400, {
                'success': False,
                'error': 'Invalid action. Supported actions: validate_token, get_calendar_access, get_user, exchange_code, get_calendars'
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
