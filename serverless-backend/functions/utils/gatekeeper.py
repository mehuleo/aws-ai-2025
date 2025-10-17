import json
import boto3
import os
import re
from typing import List, Dict, Any, Optional


# AWS Configuration - Read from environment variables
AGENTS_ALLOCATION_TABLE_NAME = os.environ.get('AGENTS_ALLOCATION_TABLE_NAME')
GATEKEEPER_MAX_EMAIL_SIZE_KB = int(os.environ.get('GATEKEEPER_MAX_EMAIL_SIZE_KB', '100'))
GATEKEEPER_EXCEPTION_EMAILS = os.environ.get('GATEKEEPER_EXCEPTION_EMAILS', '')
GATEKEEPER_REBOUND_FROM_EMAIL = os.environ.get('GATEKEEPER_REBOUND_FROM_EMAIL', 'mailer-daemon@superagent.diy')
GATEKEEPER_SEND_REBOUND_EMAILS = os.environ.get('GATEKEEPER_SEND_REBOUND_EMAILS', 'true').lower() == 'true'


def extract_email_address(email_string: str) -> Optional[str]:
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


def normalize_list_field(value: Any, default: List = None) -> List:
    """Normalize a field to a list"""
    if default is None:
        default = []
    
    if isinstance(value, list):
        return value
    elif value:
        return [value]
    else:
        return default


def get_exception_emails() -> List[str]:
    """Parse exception emails from environment variable"""
    if not GATEKEEPER_EXCEPTION_EMAILS:
        return []
    
    # Split by comma and clean up whitespace
    emails = [email.strip() for email in GATEKEEPER_EXCEPTION_EMAILS.split(',')]
    return [email for email in emails if email]


def is_superagent_diy_domain(email: str) -> bool:
    """Check if email belongs to @superagent.diy domain"""
    if not email:
        return False
    
    extracted_email = extract_email_address(email)
    if not extracted_email:
        return False
    
    return extracted_email.lower().endswith('@superagent.diy')


def check_email_size(event: Dict[str, Any]) -> bool:
    """Check if email size is within limits"""
    try:
        # Get email size from SES event
        ses_record = event.get('Records', [{}])[0].get('ses', {})
        mail = ses_record.get('mail', {})
        
        # Get size from mail headers or estimate from content
        size_bytes = mail.get('size', 0)
        
        # Convert to KB
        size_kb = size_bytes / 1024
        
        print(f"Email size: {size_kb:.2f} KB (limit: {GATEKEEPER_MAX_EMAIL_SIZE_KB} KB)")
        
        return size_kb <= GATEKEEPER_MAX_EMAIL_SIZE_KB
        
    except Exception as e:
        print(f"Error checking email size: {str(e)}")
        # If we can't determine size, allow it through (fail open)
        return True


def check_agent_allocation(dynamodb, email_addresses: List[str]) -> bool:
    """Check if any email address exists in AGENTS_ALLOCATION_TABLE_NAME"""
    if not email_addresses:
        return False
    
    try:
        agents_table = dynamodb.Table(AGENTS_ALLOCATION_TABLE_NAME)
        
        # Check each email address
        for email in email_addresses:
            if not email:
                continue
                
            try:
                response = agents_table.scan(
                    FilterExpression='agent_email = :user_email',
                    ExpressionAttributeValues={
                        ':user_email': email
                    }
                )
                
                if response['Items']:
                    print(f"Found agent allocation for email: {email}")
                    return True
                    
            except Exception as e:
                print(f"Error scanning for email {email}: {str(e)}")
                continue
        
        print("No agent allocation found for any email addresses")
        return False
        
    except Exception as e:
        print(f"Error checking agent allocation: {str(e)}")
        # If we can't check, allow it through (fail open)
        return True


def check_exception_emails(email_addresses: List[str]) -> bool:
    """Check if any email address is in the exception list"""
    exception_emails = get_exception_emails()
    
    if not exception_emails:
        return False
    
    for email in email_addresses:
        if not email:
            continue
            
        extracted_email = extract_email_address(email)
        if extracted_email and extracted_email.lower() in [e.lower() for e in exception_emails]:
            print(f"Email {extracted_email} found in exception list")
            return True
    
    return False


def extract_email_addresses_from_event(event: Dict[str, Any]) -> List[str]:
    """Extract all email addresses from SES event"""
    email_addresses = []
    
    try:
        ses_record = event.get('Records', [{}])[0].get('ses', {})
        mail = ses_record.get('mail', {})
        common_headers = mail.get('commonHeaders', {})
        
        # Extract from address
        from_address = mail.get('source', '')
        if from_address:
            email_addresses.append(from_address)
        
        # Extract to addresses
        to_addresses = normalize_list_field(common_headers.get('to', mail.get('destination', [])))
        email_addresses.extend(to_addresses)
        
        # Extract cc addresses
        cc_addresses = normalize_list_field(common_headers.get('cc', []))
        email_addresses.extend(cc_addresses)
        
        # Clean and deduplicate
        cleaned_addresses = []
        for email in email_addresses:
            extracted = extract_email_address(email)
            if extracted and extracted not in cleaned_addresses:
                cleaned_addresses.append(extracted)
        
        print(f"Extracted email addresses: {cleaned_addresses}")
        return cleaned_addresses
        
    except Exception as e:
        print(f"Error extracting email addresses: {str(e)}")
        return []


def get_original_sender_email(event: Dict[str, Any]) -> Optional[str]:
    """Get the original sender's email address from the SES event"""
    try:
        ses_record = event.get('Records', [{}])[0].get('ses', {})
        mail = ses_record.get('mail', {})
        from_address = mail.get('source', '')
        
        if from_address:
            return extract_email_address(from_address)
        
        return None
        
    except Exception as e:
        print(f"Error getting original sender email: {str(e)}")
        return None


def get_original_subject(event: Dict[str, Any]) -> str:
    """Get the original email subject from the SES event"""
    try:
        ses_record = event.get('Records', [{}])[0].get('ses', {})
        mail = ses_record.get('mail', {})
        common_headers = mail.get('commonHeaders', {})
        
        return common_headers.get('subject', 'No Subject')
        
    except Exception as e:
        print(f"Error getting original subject: {str(e)}")
        return 'No Subject'


def get_message_id(event: Dict[str, Any]) -> Optional[str]:
    """Get the SES message ID from the event"""
    try:
        ses_record = event.get('Records', [{}])[0].get('ses', {})
        mail = ses_record.get('mail', {})
        return mail.get('messageId')
        
    except Exception as e:
        print(f"Error getting message ID: {str(e)}")
        return None


def send_ses_bounce(ses_client, message_id: str, original_sender: str, rejection_reason: str) -> bool:
    """Send an SES bounce message to reject the email"""
    if not GATEKEEPER_SEND_REBOUND_EMAILS:
        print("Bounce emails are disabled")
        return True
    
    if not original_sender:
        print("No original sender email found, cannot send bounce")
        return False
    
    try:
        # Send SES bounce
        response = ses_client.send_bounce(
            OriginalMessageId=message_id,
            BounceSenderArn=f"arn:aws:ses:us-east-1:*:identity/{GATEKEEPER_REBOUND_FROM_EMAIL}",
            BouncedRecipientInfoList=[
                {
                    'Recipient': original_sender,
                    'BounceType': 'ContentRejected',
                    'RecipientDsnFields': {
                        'FinalRecipient': original_sender,
                        'Action': 'failed',
                        'Status': '5.7.1',
                        'DiagnosticCode': rejection_reason
                    }
                }
            ],
            BounceMessageTemplate={
                'Subject': 'Email Rejected - SuperAgent System',
                'HtmlPart': f"""
                <html>
                <body>
                    <h2>Email Delivery Failed</h2>
                    <p>Your email could not be delivered to the SuperAgent system.</p>
                    <p><strong>Reason:</strong> {rejection_reason}</p>
                    
                    <h3>What you can do:</h3>
                    <ul>
                        <li>Visit <a href="https://superagent.diy">https://superagent.diy</a> to create an account</li>
                        <li>Make sure you're using a valid @superagent.diy email address</li>
                        <li>Ensure your email is under {GATEKEEPER_MAX_EMAIL_SIZE_KB}KB in size</li>
                        <li>If you believe this is an error, please contact our support team</li>
                    </ul>
                    
                    <p><strong>Note:</strong> This is an automated message. Please do not reply to this email.</p>
                    
                    <hr>
                    <p><small>SuperAgent Email System</small></p>
                </body>
                </html>
                """,
                'TextPart': f"""
Email Delivery Failed

Your email could not be delivered to the SuperAgent system.

Reason: {rejection_reason}

What you can do:
- Visit https://superagent.diy to create an account
- Make sure you're using a valid @superagent.diy email address
- Ensure your email is under {GATEKEEPER_MAX_EMAIL_SIZE_KB}KB in size
- If you believe this is an error, please contact our support team

Note: This is an automated message. Please do not reply to this email.

---
SuperAgent Email System
                """
            }
        )
        
        print(f"SES bounce sent successfully. MessageId: {response['MessageId']}")
        return True
        
    except Exception as e:
        print(f"Error sending SES bounce: {str(e)}")
        return False


def send_rebound_email(ses_client, original_sender: str, original_subject: str, rejection_reason: str) -> bool:
    """Send a rebound email to the original sender explaining why their email was rejected"""
    if not GATEKEEPER_SEND_REBOUND_EMAILS:
        print("Rebound emails are disabled")
        return True
    
    if not original_sender:
        print("No original sender email found, cannot send rebound")
        return False
    
    try:
        # Create rebound email content
        subject = f"Re: {original_subject} - Email Rejected"
        
        html_body = f"""
        <html>
        <body>
            <h2>Email Delivery Failed</h2>
            <p>Your email with subject "<strong>{original_subject}</strong>" could not be delivered to the SuperAgent system.</p>
            
            <h3>Reason for Rejection:</h3>
            <p>{rejection_reason}</p>
            
            <h3>What you can do:</h3>
            <ul>
                <li>Visit <a href="https://superagent.diy">https://superagent.diy</a> to create an account</li>
                <li>Make sure you're using a valid @superagent.diy email address</li>
                <li>Ensure your email is under {GATEKEEPER_MAX_EMAIL_SIZE_KB}KB in size</li>
                <li>If you believe this is an error, please contact our support team</li>
            </ul>
            
            <p><strong>Note:</strong> This is an automated message. Please do not reply to this email.</p>
            
            <hr>
            <p><small>SuperAgent Email System</small></p>
        </body>
        </html>
        """
        
        text_body = f"""
Email Delivery Failed

Your email with subject "{original_subject}" could not be delivered to the SuperAgent system.

Reason for Rejection:
{rejection_reason}

What you can do:
- Visit https://superagent.diy to create an account
- Make sure you're using a valid @superagent.diy email address
- Ensure your email is under {GATEKEEPER_MAX_EMAIL_SIZE_KB}KB in size
- If you believe this is an error, please contact our support team

Note: This is an automated message. Please do not reply to this email.

---
SuperAgent Email System
        """
        
        # Send the rebound email
        response = ses_client.send_email(
            Source=GATEKEEPER_REBOUND_FROM_EMAIL,
            Destination={
                'ToAddresses': [original_sender]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': text_body,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f"Rebound email sent successfully to {original_sender}. MessageId: {response['MessageId']}")
        return True
        
    except Exception as e:
        print(f"Error sending rebound email to {original_sender}: {str(e)}")
        return False


def gatekeeper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    SES Inbound Email Gatekeeper Lambda Function
    
    This function validates incoming emails and decides whether to allow or reject them.
    
    Validation rules:
    1. Check if any email address (to/from) with @superagent.diy domain exists in AGENTS_ALLOCATION_TABLE_NAME
    2. Check if email size is within limits (configurable via GATEKEEPER_MAX_EMAIL_SIZE_KB)
    3. Check exception email list (configurable via GATEKEEPER_EXCEPTION_EMAILS)
    
    Returns:
        - {"disposition": "continue"} to continue SES processing
        - {"disposition": "stop_rule_set"} to reject the email
    """
    
    print(f"Gatekeeper received event: {json.dumps(event, default=str)}")
    print(f"Configuration - Max size: {GATEKEEPER_MAX_EMAIL_SIZE_KB}KB, Send rebounds: {GATEKEEPER_SEND_REBOUND_EMAILS}, From: {GATEKEEPER_REBOUND_FROM_EMAIL}")
    
    # Initialize clients
    dynamodb = boto3.resource('dynamodb')
    ses_client = boto3.client('ses')
    
    # Get original sender info for bounce emails
    original_sender = get_original_sender_email(event)
    original_subject = get_original_subject(event)
    message_id = get_message_id(event)
    print(f"Original sender: {original_sender}, Subject: {original_subject}, MessageId: {message_id}")
    
    try:
        # Extract email addresses from the event
        email_addresses = extract_email_addresses_from_event(event)
        
        if not email_addresses:
            print("No email addresses found in event, rejecting")
            rejection_reason = "No valid email addresses could be extracted from the message headers. Please ensure your email has proper To/From/CC headers."
            send_rebound_email(ses_client, original_sender, original_subject, rejection_reason)
            print("RETURNING: {'disposition': 'stop_rule_set'}")
            return {"disposition": "stop_rule_set"}
        
        # Check email size
        if not check_email_size(event):
            print(f"Email size exceeds limit of {GATEKEEPER_MAX_EMAIL_SIZE_KB} KB, rejecting")
            # Get actual size for the message
            try:
                ses_record = event.get('Records', [{}])[0].get('ses', {})
                mail = ses_record.get('mail', {})
                actual_size_bytes = mail.get('size', 0)
                actual_size_kb = actual_size_bytes / 1024
                rejection_reason = f"Email size ({actual_size_kb:.1f} KB) exceeds the maximum allowed size of {GATEKEEPER_MAX_EMAIL_SIZE_KB} KB. Please reduce the email size by removing attachments or content."
            except:
                rejection_reason = f"Email size exceeds the maximum allowed size of {GATEKEEPER_MAX_EMAIL_SIZE_KB} KB. Please reduce the email size by removing attachments or content."
            send_rebound_email(ses_client, original_sender, original_subject, rejection_reason)
            print("RETURNING: {'disposition': 'stop_rule_set'}")
            return {"disposition": "stop_rule_set"}
        
        # Check exception emails first (these always pass)
        if check_exception_emails(email_addresses):
            print("Email found in exception list, allowing")
            print("RETURNING: {'disposition': 'continue'}")
            return {"disposition": "continue"}
        
        # Check for @superagent.diy domain emails
        superagent_emails = [email for email in email_addresses if is_superagent_diy_domain(email)]
        
        if not superagent_emails:
            print("No @superagent.diy domain emails found, rejecting")
            email_list = ", ".join(email_addresses) if email_addresses else "none found"
            rejection_reason = f"No @superagent.diy domain email addresses found in the message. Found email addresses: {email_list}"
            send_rebound_email(ses_client, original_sender, original_subject, rejection_reason)
            print("RETURNING: {'disposition': 'stop_rule_set'}")
            return {"disposition": "stop_rule_set"}
        
        # Check if any @superagent.diy email exists in agent allocation table
        if check_agent_allocation(dynamodb, superagent_emails):
            print("Valid agent allocation found, allowing")
            print("RETURNING: {'disposition': 'continue'}")
            return {"disposition": "continue"}
        else:
            print("No valid agent allocation found for @superagent.diy emails, rejecting")
            superagent_list = ", ".join(superagent_emails) if superagent_emails else "none found"
            rejection_reason = f"You don't have access to SuperAgent. Please visit https://superagent.diy and create an account. Email addresses checked: {superagent_list}"
            send_rebound_email(ses_client, original_sender, original_subject, rejection_reason)
            print("RETURNING: {'disposition': 'stop_rule_set'}")
            return {"disposition": "stop_rule_set"}
            
    except Exception as e:
        print(f"Error in gatekeeper function: {str(e)}")
        # In case of error, reject the email (fail closed for security)
        rejection_reason = f"System error occurred while processing your email: {str(e)}"
        send_ses_bounce(ses_client, message_id, original_sender, rejection_reason)
        print("RETURNING: {'disposition': 'stop_rule_set'}")
        return {"disposition": "stop_rule_set"}


# For testing purposes
if __name__ == "__main__":
    # Test event structure
    test_event = {
        "Records": [
            {
                "ses": {
                    "mail": {
                        "messageId": "test-message-id",
                        "source": "test@superagent.diy",
                        "destination": ["agent@superagent.diy"],
                        "size": 51200,  # 50KB
                        "commonHeaders": {
                            "from": ["test@superagent.diy"],
                            "to": ["agent@superagent.diy"],
                            "subject": "Test Email"
                        }
                    }
                }
            }
        ]
    }
    
    result = gatekeeper(test_event, None)
    print(f"Test result: {result}")
    print(f"Expected: {{'disposition': 'continue'}} or {{'disposition': 'stop_rule_set'}}")
