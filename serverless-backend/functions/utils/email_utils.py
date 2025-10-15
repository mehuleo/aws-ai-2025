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
AGENTS_ALLOCATION_TABLE_NAME = os.environ.get('AGENTS_ALLOCATION_TABLE_NAME')


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


def extract_email_address(email_string):
    """Extract email address from formatted string like 'John Doe <someone@gmail.com>' or 'someone@gmail.com'"""
    if not email_string:
        return None
    
    # Remove leading/trailing whitespace
    email_string = email_string.strip()
    
    # Pattern to match email addresses in angle brackets: "John Doe <email@domain.com>"
    angle_bracket_pattern = r'<([^>]+)>'
    match = re.search(angle_bracket_pattern, email_string)
    if match:
        return match.group(1).strip()
    
    # Pattern to match plain email addresses: "email@domain.com"
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, email_string)
    if match:
        return match.group(0).strip()
    
    # If no pattern matches, return the original string (might be a malformed email)
    return email_string


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
        # Note: Since we now have email as primary key and sid as sort key,
        # we need to query each email individually or use a different approach
        # For now, we'll use individual queries since batch_get_item requires both keys
        
        # DynamoDB resource for queries
        dynamodb_table = dynamodb.Table(SUBSCRIBERS_TABLE_NAME)
        
        subscribers = []
        # Query each email individually
        for email in email_addresses:
            try:
                response = dynamodb_table.query(
                    KeyConditionExpression='email = :email',
                    ExpressionAttributeValues={
                        ':email': email
                    }
                )
                
                if response['Items']:
                    # Add the email to subscribers list if found
                    subscribers.append(email)
                    
            except Exception as e:
                print(f"Error querying for email {email}: {str(e)}")
                continue
        
        return subscribers
        
    except Exception as e:
        print(f"Error looking up subscribers: {str(e)}")
        return []


def find_agent_email(dynamodb, parsed_email):
    """Find agent email by scanning AGENTS_ALLOCATION_TABLE_NAME for matching email addresses"""
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
    
    print(f"Email addresses: {str(email_addresses)}")
    
    # Extract email addresses and remove duplicates and empty values
    email_addresses = list(set([extract_email_address(email) for email in email_addresses if email and extract_email_address(email)]))

    print(f"Email addresses after extraction: {str(email_addresses)}")
    
    if not email_addresses:
        print("No email addresses found")
        return None
    
    try:
        # Get the agents allocation table
        agents_table = dynamodb.Table(AGENTS_ALLOCATION_TABLE_NAME)
        
        # Scan the table to find matching email addresses
        for email in email_addresses:
            try:
                response = agents_table.scan(
                    FilterExpression='email = :user_email',
                    ExpressionAttributeValues={
                        ':user_email': email
                    }
                )
                
                if response['Items']:
                    # Return the first matching agent_email
                    agent_item = response['Items'][0]
                    print(f"Found agent email {agent_item['agent_email']} for user email {email}")
                    return agent_item['agent_email']
                    
            except Exception as e:
                print(f"Error scanning for email {email}: {str(e)}")
                continue
        
        print("No agent email found for any of the email addresses")
        return None
        
    except Exception as e:
        print(f"Error looking up agent email: {str(e)}")
        return None


def create_dynamodb_item(metadata, parsed_email, s3_key, subscribers=None, agent_email=None):
    """Create DynamoDB item from parsed email data"""
    record_uuid = str(uuid.uuid4())
    
    if subscribers is None:
        subscribers = []
    
    # Clean subject and generate session_id
    cleaned_subject = clean_subject(parsed_email['subject'])
    session_id = hashlib.md5(cleaned_subject.encode('utf-8')).hexdigest()
    
    # Build the DynamoDB item
    dynamodb_item = {
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
    }
    
    # Add agent_email if provided
    if agent_email:
        dynamodb_item['agent_email'] = agent_email
    
    return dynamodb_item, record_uuid


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

        # Find agent email
        agent_email = find_agent_email(dynamodb, parsed_email)
        
        # Create DynamoDB item
        dynamodb_item, record_uuid = create_dynamodb_item(metadata, parsed_email, s3_key, subscribers, agent_email)
        
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
