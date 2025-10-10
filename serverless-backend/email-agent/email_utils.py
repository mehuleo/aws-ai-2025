import json
import boto3
import email
from email import policy
import uuid
from datetime import datetime
import traceback
import os
import hashlib
import re


# AWS Configuration - Read from environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
EMAILS_TABLE_NAME = os.environ.get('EMAILS_TABLE_NAME')
SUBSCRIBERS_TABLE_NAME = os.environ.get('SUBSCRIBERS_TABLE_NAME')


def extract_ses_metadata(event):
    """Extract metadata from SES event"""
    ses_record = event['Records'][0]['ses']
    mail = ses_record['mail']
    
    return {
        'message_id': mail['messageId'],
        'source': mail['source'],
        'timestamp': mail['timestamp'],
        'destination': mail['destination'],
        'common_headers': mail.get('commonHeaders', {})
    }


def get_s3_object_key(message_id):
    """Construct S3 object key for email"""
    return f"inbox/{message_id}"


def retrieve_email_from_s3(s3_client, message_id):
    """Retrieve raw email content from S3"""
    object_key = get_s3_object_key(message_id)
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=object_key)
    return response['Body'].read(), object_key


def extract_email_body(msg):
    """Extract text and HTML body from email message"""
    body_text = ""
    body_html = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body_text = part.get_payload(decode=True).decode()
                except Exception:
                    body_text = str(part.get_payload())
            elif content_type == "text/html" and "attachment" not in content_disposition:
                try:
                    body_html = part.get_payload(decode=True).decode()
                except Exception:
                    body_html = str(part.get_payload())
    else:
        try:
            body_text = msg.get_payload(decode=True).decode()
        except Exception:
            body_text = str(msg.get_payload())
    
    return body_text if body_text else body_html


def parse_email_content(email_content):
    """Parse raw email content and extract body"""
    msg = email.message_from_bytes(email_content, policy=policy.default)
    return extract_email_body(msg)


def normalize_list_field(value, default=None):
    """Normalize a field to a list"""
    if default is None:
        default = []
    
    if isinstance(value, list):
        return value
    elif value:
        return [value]
    else:
        return default


def clean_subject(subject):
    """Clean email subject by removing reply/forward prefixes and trimming spaces"""
    if not subject:
        return ""
    
    # Remove common reply/forward prefixes (case insensitive)
    prefixes_to_remove = [
        r'^Re:\s*',
        r'^Fw:\s*', 
        r'^Fwd:\s*',
        r'^RE:\s*',
        r'^FW:\s*',
        r'^FWD:\s*',
        r'^Re\[\d+\]:\s*',  # Outlook numbered replies like Re[2]:, Re[3]:
        r'^RE\[\d+\]:\s*'   # Uppercase version
    ]
    
    cleaned_subject = subject
    for prefix in prefixes_to_remove:
        cleaned_subject = re.sub(prefix, '', cleaned_subject, flags=re.IGNORECASE)
    
    # Trim leading and trailing whitespace
    cleaned_subject = cleaned_subject.strip()
    
    return cleaned_subject


def build_parsed_email(metadata, email_body):
    """Build parsed email structure from metadata and body"""
    common_headers = metadata['common_headers']
    source = metadata['source']
    destination = metadata['destination']
    
    from_address = common_headers.get('from', [source])
    if isinstance(from_address, list):
        from_address = from_address[0]
    
    return {
        "to": normalize_list_field(common_headers.get('to', destination)),
        "cc": normalize_list_field(common_headers.get('cc')),
        "from": from_address,
        "subject": common_headers.get('subject', 'No Subject'),
        "body": email_body
    }


def lookup_subscribers(dynamodb, parsed_email):
    """Lookup subscribers from superagent-subscribers table based on email addresses"""
    # Collect all email addresses from from, to, and cc lists
    email_addresses = []
    
    # Add from address
    if parsed_email.get('from'):
        email_addresses.append(parsed_email['from'])
    
    # Add to addresses
    if parsed_email.get('to'):
        email_addresses.extend(parsed_email['to'])
    
    # Add cc addresses
    if parsed_email.get('cc'):
        email_addresses.extend(parsed_email['cc'])
    
    # Remove duplicates and empty values
    email_addresses = list(set([email for email in email_addresses if email]))
    
    if not email_addresses:
        return []
    
    # Bulk lookup using batch_get_item
    try:
        # Build the request items for batch_get_item
        keys = [{'emailId': email_id} for email_id in email_addresses]
        
        # DynamoDB batch_get_item requires the client, not resource
        dynamodb_client = boto3.client('dynamodb')
        
        # Use batch_get_item (max 100 items per request)
        subscribers = []
        # Process in chunks of 100 (DynamoDB limit)
        for i in range(0, len(keys), 100):
            batch_keys = keys[i:i+100]
            response = dynamodb_client.batch_get_item(
                RequestItems={
                    SUBSCRIBERS_TABLE_NAME: {
                        'Keys': [{'emailId': {'S': key['emailId']}} for key in batch_keys]
                    }
                }
            )
            
            # Extract email IDs from the response
            if SUBSCRIBERS_TABLE_NAME in response.get('Responses', {}):
                for item in response['Responses'][SUBSCRIBERS_TABLE_NAME]:
                    if 'emailId' in item:
                        subscribers.append(item['emailId']['S'])
        
        return subscribers
        
    except Exception as e:
        print(f"Error looking up subscribers in bulk: {str(e)}")
        return []


def create_dynamodb_item(metadata, parsed_email, s3_key, subscribers=None):
    """Create DynamoDB item from parsed email data"""
    record_uuid = str(uuid.uuid4())
    
    if subscribers is None:
        subscribers = []
    
    # Clean subject and generate session_id
    cleaned_subject = clean_subject(parsed_email['subject'])
    session_id = hashlib.md5(cleaned_subject.encode('utf-8')).hexdigest()
    
    return {
        'uuid': record_uuid,
        'message_id': metadata['message_id'],
        'timestamp': metadata['timestamp'],
        'received_at': datetime.utcnow().isoformat(),
        'from': parsed_email['from'],
        'to': parsed_email['to'],
        'cc': parsed_email['cc'],
        'subject': parsed_email['subject'],
        'session_id': session_id,
        'body': parsed_email['body'],
        's3_bucket': S3_BUCKET_NAME,
        's3_key': s3_key,
        'subscribers': subscribers
    }, record_uuid


def store_email_in_dynamodb(dynamodb_table, dynamodb_item):
    """Store email data in DynamoDB"""
    dynamodb_table.put_item(Item=dynamodb_item)


def parseEmail(event, context):
    """Main Lambda handler for parsing and storing emails from SES"""
    try:
        # Initialize AWS clients
        s3_client = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        dynamodb_table = dynamodb.Table(EMAILS_TABLE_NAME)
        
        # Extract metadata from SES event
        metadata = extract_ses_metadata(event)
        
        # Retrieve email from S3
        email_content, s3_key = retrieve_email_from_s3(s3_client, metadata['message_id'])
        
        # Parse email body
        email_body = parse_email_content(email_content)
        
        # Build parsed email structure
        parsed_email = build_parsed_email(metadata, email_body)
        
        # Lookup subscribers
        subscribers = lookup_subscribers(dynamodb, parsed_email)
        
        # Create DynamoDB item
        dynamodb_item, record_uuid = create_dynamodb_item(metadata, parsed_email, s3_key, subscribers)
        
        # Store in DynamoDB
        store_email_in_dynamodb(dynamodb_table, dynamodb_item)
        
        # Return success response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Email parsed and stored successfully",
                "uuid": record_uuid,
                "email": parsed_email
            })
        }
        
    except Exception as e:
        # Log error details for debugging
        error_msg = f"Error parsing email: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Error parsing email",
                "error": str(e)
            })
        }
