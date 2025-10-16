import boto3
import json
import uuid
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_response(status_code, body_data, error_details=None):
    """
    Create a standardized HTTP response with CORS headers
    
    Args:
        status_code (int): HTTP status code
        body_data (dict): Response body data
        error_details (dict, optional): Additional error details for debugging
    
    Returns:
        dict: Standardized response object
    """
    response_body = body_data.copy()
    
    # Add error details if provided
    if error_details:
        response_body.update(error_details)
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(response_body)
    }

def test_invoke(event, context):
    """
    Test function to invoke Bedrock Agentcore with a given prompt
    """
    try:
        # Parse the request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Get the agent runtime ARN from environment variables
        agent_runtime_arn = os.environ.get('AGENT_RUNTIME_ARN')
        
        if not agent_runtime_arn:
            logger.error("Agent runtime ARN not configured in environment variables")
            return create_response(500, {'error': 'Agent runtime ARN not configured'})
        
        # Initialize Bedrock Agentcore client
        try:
            client = boto3.client('bedrock-agentcore', region_name='us-east-1')
        except Exception as client_error:
            logger.error(f"Failed to initialize Bedrock Agentcore client: {str(client_error)}")
            raise
        
        # Create payload for the agent
        payload = json.dumps(body)
        
        # Generate a unique session ID (must be 33+ characters)
        session_id = f"test-session-{uuid.uuid4().hex}-{int(datetime.now().timestamp())}"
        
        # Invoke the agent
        try:
            print(f"Invoking agent runtime with payload: {payload}, session_id: {session_id}")
            response = client.invoke_agent_runtime(
                agentRuntimeArn=agent_runtime_arn,
                runtimeSessionId=session_id,
                payload=payload,
                qualifier="DEFAULT"
            )
        except Exception as invoke_error:
            logger.error(f"Failed to invoke agent runtime: {str(invoke_error)}")
            raise
        
        # Process the response
        try:
            response_body = response['response'].read()
            response_data = json.loads(response_body)
        except Exception as response_error:
            logger.error(f"Failed to process response: {str(response_error)}")
            raise
        
        result = {
            'sessionId': session_id,
            'prompt': prompt,
            'agentResponse': response_data
        }
        
        return create_response(200, result)
        
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}")
        # Log additional context for debugging
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        return create_response(500, {
            'error': f'Failed to invoke agent: {str(e)}'
        }, {
            'errorType': str(type(e)),
            'traceback': traceback.format_exc()
        })
