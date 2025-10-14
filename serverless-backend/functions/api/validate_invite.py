import json
import boto3
import os
import traceback
import logging
import random
import string
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Configuration - Read from environment variables
SUBSCRIBERS_TABLE_NAME = os.environ.get('SUBSCRIBERS_TABLE_NAME')
AGENTS_ALLOCATION_TABLE_NAME = os.environ.get('AGENTS_ALLOCATION_TABLE_NAME')
INVITE_CODE = os.environ.get('INVITE_CODE', '9339c102-5cd1-4686-958e-fe8ab27ba1e0')  # Default fallback
SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL')

def create_response(status_code, body_data):
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

def generate_agent_email(dynamodb_table, max_attempts=5):
    """Generate a unique random agent email address in format: word-word-number@superagent.diy"""
    try:
        # List of adjectives and nouns for generating random combinations
        adjectives = [
            'absent', 'active', 'agile', 'bold', 'bright', 'calm', 'clever', 'cool', 'daring', 'eager',
            'fierce', 'gentle', 'happy', 'keen', 'lively', 'mighty', 'noble', 'proud', 'quick', 'radiant',
            'sharp', 'swift', 'tough', 'vivid', 'wise', 'zealous', 'brave', 'calm', 'daring', 'eager',
            'fierce', 'gentle', 'happy', 'keen', 'lively', 'mighty', 'noble', 'proud', 'quick', 'radiant'
        ]
        
        nouns = [
            'siege', 'storm', 'blade', 'flame', 'wave', 'star', 'moon', 'sun', 'wind', 'fire',
            'ice', 'rock', 'tree', 'bird', 'wolf', 'lion', 'eagle', 'bear', 'fox', 'deer',
            'river', 'mountain', 'ocean', 'forest', 'desert', 'valley', 'peak', 'cave', 'lake', 'meadow',
            'thunder', 'lightning', 'shadow', 'spirit', 'soul', 'heart', 'mind', 'dream', 'hope', 'faith'
        ]
        
        for attempt in range(max_attempts):
            # Generate random combination
            adjective = random.choice(adjectives)
            noun = random.choice(nouns)
            number = random.randint(10, 99)
            
            agent_email = f"{adjective}-{noun}-{number}@superagent.diy"
            
            # Check if this email already exists
            response = dynamodb_table.get_item(
                Key={
                    'agent_email': agent_email
                }
            )
            
            if 'Item' not in response:
                # Email is unique, return it
                logger.info(f"Generated unique agent email: {agent_email}")
                return agent_email
            else:
                logger.warning(f"Agent email {agent_email} already exists, trying again... (attempt {attempt + 1}/{max_attempts})")
        
        # If we get here, we couldn't generate a unique email after max_attempts
        error_msg = f"Failed to generate unique agent email after {max_attempts} attempts"
        logger.error(error_msg)
        return None
        
    except Exception as e:
        error_msg = f"Error generating agent email: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None

def store_agent_email(dynamodb_table, agent_email, user_email):
    """Store agent email and user email mapping in AGENTS_ALLOCATION_TABLE_NAME"""
    try:
        # Store the mapping (uniqueness is already guaranteed by generate_agent_email)
        item = {
            'agent_email': agent_email,  # Primary key
            'email': user_email,
            'created_at': datetime.utcnow().isoformat()
        }
        
        dynamodb_table.put_item(Item=item)
        logger.info(f"Agent email {agent_email} stored for user {user_email}")
        return True, None
        
    except Exception as e:
        error_msg = f"Error storing agent email: {str(e)}"
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

def send_welcome_email(ses_client, user_email, user_name, agent_email=None):
    """Send welcome email to the user using SES"""
    try:
        # Create the email content
        subject = "Welcome to SuperAgent! 🎉"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to SuperAgent</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb;">Welcome to SuperAgent! 🎉</h1>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #1e40af; margin-top: 0;">Hello {user_name or 'there'}!</h2>
                <p>Your invite has been successfully validated and you now have access to SuperAgent.</p>
                {f'<p><strong>Your Agent Email:</strong> {agent_email}</p>' if agent_email else ''}
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3 style="color: #1e40af;">What's Next?</h3>
                <ul>
                    <li>Access your dashboard to get started</li>
                    <li>Connect your Google Calendar for seamless scheduling</li>
                    <li>Start creating your AI-powered executive assistant</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="https://superagent.diy/dashboard" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    Go to Dashboard
                </a>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #6b7280;">
                <p>If you have any questions, feel free to reach out to our support team.</p>
                <p>Best regards,<br>The SuperAgent Team</p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to SuperAgent! 🎉
        
        Hello {user_name or 'there'}!
        
        Your invite has been successfully validated and you now have access to SuperAgent.
        {f'Your Agent Email: {agent_email}' if agent_email else ''}
        
        What's Next?
        - Access your dashboard to get started
        - Connect your Google Calendar for seamless scheduling
        - Start creating your AI-powered executive assistant
        
        Go to Dashboard: https://superagent.diy/dashboard
        
        If you have any questions, feel free to reach out to our support team.
        
        Best regards,
        The SuperAgent Team
        """
        
        # Send the email
        response = ses_client.send_email(
            Source=SES_FROM_EMAIL,
            Destination={
                'ToAddresses': [user_email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    },
                    'Text': {
                        'Data': text_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        logger.info(f"Welcome email sent successfully to {user_email}. MessageId: {response['MessageId']}")
        return True, None
        
    except Exception as e:
        error_msg = f"Error sending welcome email: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return False, error_msg

def validate_invite(event, context):
    """Main Lambda handler for invite validation"""
    try:
        # Initialize AWS services
        dynamodb = boto3.resource('dynamodb')
        subscribers_table = dynamodb.Table(SUBSCRIBERS_TABLE_NAME)
        agents_table = dynamodb.Table(AGENTS_ALLOCATION_TABLE_NAME)
        ses_client = boto3.client('ses')
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract required parameters
        email = body.get('email')
        sid = body.get('sid')
        invite_code = body.get('invite_code')
        
        # Validate required parameters
        if not email:
            logger.error("Email is missing from request body")
            return create_response(400, {
                'success': False,
                'error': 'Email is required'
            })
        
        if not sid:
            logger.error("SID is missing from request body")
            return create_response(400, {
                'success': False,
                'error': 'SID is required'
            })
        
        if not invite_code:
            logger.error("Invite code is missing from request body")
            return create_response(400, {
                'success': False,
                'error': 'Invite code is required'
            })
        
        # Get user from DynamoDB
        user_data, error = get_user_from_dynamodb(subscribers_table, email)
        if error:
            logger.error(f"Failed to get user data: {error}")
            return create_response(404, {
                'success': False,
                'error': 'User not found'
            })
        
        # Verify SID matches (authentication check)
        stored_sid = user_data.get('sid')
        if stored_sid != sid:
            logger.warning(f"SID mismatch for user {email}. Expected: {stored_sid}, Received: {sid}")
            return create_response(403, {
                'success': False,
                'error': 'Invalid SID - authentication failed'
            })
        
        # Validate invite code
        if invite_code != INVITE_CODE:
            logger.warning(f"Invalid invite code for user {email}. Expected: {INVITE_CODE}, Received: {invite_code}")
            return create_response(400, {
                'success': False,
                'error': 'Invalid invite code'
            })
        
        # Generate and store agent email
        agent_email = generate_agent_email(agents_table)
        if not agent_email:
            logger.error("Failed to generate unique agent email")
            return create_response(500, {
                'success': False,
                'error': 'Failed to generate unique agent email'
            })
        
        # Store the agent email mapping
        stored, store_error = store_agent_email(agents_table, agent_email, email)
        if not stored:
            logger.error(f"Failed to store agent email: {store_error}")
            return create_response(500, {
                'success': False,
                'error': 'Failed to store agent email'
            })
        
        logger.info(f"Successfully generated and stored agent email: {agent_email}")
        
        # Send welcome email
        user_name = user_data.get('user_name', '')
        email_sent, email_error = send_welcome_email(ses_client, email, user_name, agent_email)
        
        if not email_sent:
            logger.warning(f"Failed to send welcome email: {email_error}")
            # Don't fail the entire request if email fails, but log it
        
        # Return success response
        logger.info(f"Invite validation successful for user: {email}")
        return create_response(200, {
            'success': True,
            'message': 'Invite validated successfully',
            'user': {
                'email': email,
                'user_name': user_name,
                'agent_email': agent_email,
                'email_sent': email_sent
            }
        })
    
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in request body: {str(e)}"
        logger.error(f"{error_msg} - Body: {event.get('body', 'None')}")
        return create_response(400, {
            'success': False,
            'error': 'Invalid JSON in request body'
        })
    except Exception as e:
        error_msg = f"Error in invite validation: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        
        # Return more specific error information in development
        error_detail = str(e) if os.environ.get('ENVIRONMENT') == 'development' else 'Internal server error'
        
        return create_response(500, {
            'success': False,
            'error': error_detail
        })

def get_agent_email_from_dynamodb(dynamodb_table, user_email):
    """Retrieve agent email from AGENTS_ALLOCATION_TABLE_NAME using user email"""
    try:
        # Scan the table to find the agent email for the given user email
        response = dynamodb_table.scan(
            FilterExpression='email = :user_email',
            ExpressionAttributeValues={
                ':user_email': user_email
            }
        )
        
        if response['Items']:
            # Return the first matching item (there should only be one per user)
            agent_item = response['Items'][0]
            logger.info(f"Agent email found for user: {user_email}")
            return agent_item, None
        else:
            logger.info(f"No agent email found for user: {user_email}")
            return None, "No agent email found for this user"
            
    except Exception as e:
        error_msg = f"Error retrieving agent email: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return None, error_msg

def get_agent_email(event, context):
    """Main Lambda handler for getting agent email"""
    try:
        # Initialize AWS services
        dynamodb = boto3.resource('dynamodb')
        subscribers_table = dynamodb.Table(SUBSCRIBERS_TABLE_NAME)
        agents_table = dynamodb.Table(AGENTS_ALLOCATION_TABLE_NAME)
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract required parameters
        email = body.get('email')
        sid = body.get('sid')
        
        # Validate required parameters
        if not email:
            logger.error("Email is missing from request body")
            return create_response(400, {
                'success': False,
                'error': 'Email is required'
            })
        
        if not sid:
            logger.error("SID is missing from request body")
            return create_response(400, {
                'success': False,
                'error': 'SID is required'
            })
        
        # Get user from DynamoDB to validate authentication
        user_data, error = get_user_from_dynamodb(subscribers_table, email)
        if error:
            logger.error(f"Failed to get user data: {error}")
            return create_response(404, {
                'success': False,
                'error': 'User not found'
            })
        
        # Verify SID matches (authentication check)
        stored_sid = user_data.get('sid')
        if stored_sid != sid:
            logger.warning(f"SID mismatch for user {email}. Expected: {stored_sid}, Received: {sid}")
            return create_response(403, {
                'success': False,
                'error': 'Invalid SID - authentication failed'
            })
        
        # Get agent email from AGENTS_ALLOCATION_TABLE_NAME
        agent_data, error = get_agent_email_from_dynamodb(agents_table, email)
        if error:
            logger.error(f"Failed to get agent email: {error}")
            return create_response(404, {
                'success': False,
                'error': error
            })
        
        # Return success response with agent email
        logger.info(f"Agent email retrieved successfully for user: {email}")
        return create_response(200, {
            'success': True,
            'agent_email': agent_data.get('agent_email'),
            'user_email': agent_data.get('email'),
            'created_at': agent_data.get('created_at')
        })
    
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in request body: {str(e)}"
        logger.error(f"{error_msg} - Body: {event.get('body', 'None')}")
        return create_response(400, {
            'success': False,
            'error': 'Invalid JSON in request body'
        })
    except Exception as e:
        error_msg = f"Error in get agent email: {str(e)}"
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
