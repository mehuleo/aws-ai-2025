"""
Google Calendar Utility Functions

Common utility functions for calendar operations including
date handling, event formatting, and overlap detection.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from .auth import lookup_email_from_agents_table

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_date_range(days=14):
    """
    Get ISO format date range for today + specified days
    
    Args:
        days (int): Number of days ahead (default: 14)
        
    Returns:
        tuple: (time_min, time_max) in ISO format with Z suffix
    """
    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=days)).isoformat() + 'Z'
    return time_min, time_max


def parse_datetime(dt_string):
    """
    Parse datetime string to datetime object
    
    Args:
        dt_string: ISO format datetime string
        
    Returns:
        datetime object
    """
    if dt_string.endswith('Z'):
        dt_string = dt_string[:-1] + '+00:00'
    return datetime.fromisoformat(dt_string)


def check_time_overlap(event1_start, event1_end, event2_start, event2_end):
    """
    Check if two time ranges overlap
    
    Args:
        event1_start: Start time of first event (datetime or dict with 'dateTime' or 'date')
        event1_end: End time of first event
        event2_start: Start time of second event
        event2_end: End time of second event
        
    Returns:
        bool: True if events overlap
    """
    try:
        # Extract datetime strings from dict if needed
        if isinstance(event1_start, dict):
            event1_start = event1_start.get('dateTime') or event1_start.get('date')
        if isinstance(event1_end, dict):
            event1_end = event1_end.get('dateTime') or event1_end.get('date')
        if isinstance(event2_start, dict):
            event2_start = event2_start.get('dateTime') or event2_start.get('date')
        if isinstance(event2_end, dict):
            event2_end = event2_end.get('dateTime') or event2_end.get('date')
        
        # Parse to datetime objects
        start1 = parse_datetime(event1_start)
        end1 = parse_datetime(event1_end)
        start2 = parse_datetime(event2_start)
        end2 = parse_datetime(event2_end)
        
        # Check overlap: events overlap if one starts before the other ends
        return start1 < end2 and start2 < end1
        
    except Exception as e:
        logger.error(f"Error checking time overlap: {str(e)}")
        return False


def format_event_response(event):
    """
    Format Google Calendar event to standardized response schema
    
    Args:
        event: Raw event from Google Calendar API
        
    Returns:
        dict: Formatted event data
    """
    return {
        'id': event.get('id'),
        'summary': event.get('summary', 'No Title'),
        'description': event.get('description', ''),
        'start': event.get('start', {}),
        'end': event.get('end', {}),
        'status': event.get('status'),
        'creator': event.get('creator', {}),
        'organizer': event.get('organizer', {}),
        'attendees': event.get('attendees', []),
        'recurrence': event.get('recurrence', []),
        'recurring_event_id': event.get('recurringEventId'),
        'html_link': event.get('htmlLink'),
        'created': event.get('created'),
        'updated': event.get('updated'),
        'location': event.get('location', ''),
        'hangout_link': event.get('hangoutLink'),
        'conference_data': event.get('conferenceData', {}),
    }


def create_lambda_response(status_code, success, data=None, error=None):
    """
    Create standardized lambda response
    
    Args:
        status_code (int): HTTP status code
        success (bool): Success flag
        data: Response data (for successful responses)
        error: Error message (for error responses)
        
    Returns:
        dict: Lambda response object
    """
    response_body = {
        'success': success,
        'status_code': status_code
    }
    
    if success and data is not None:
        response_body['data'] = data
    elif not success and error:
        response_body['error'] = error
    
    return {
        'statusCode': status_code,
        'body': response_body
    }


def validate_input(event, required_fields=None):
    """
    Validate lambda event input and extract auth token bearer
    
    Args:
        event: Lambda event object
        required_fields: List of additional required field names
        
    Returns:
        tuple: (auth_email, body_data, error_response)
    """
    try:
        # Get auth email from headers
        auth_email = event.get('auth_email', '')
        
        if not auth_email:
            return None, None, create_lambda_response(
                401, False, error="X-Auth-Bearer header is required"
            )
        
        # Validate additional required fields
        if required_fields:
            missing_fields = []
            for field in required_fields:
                if field not in event or event.get(field) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return None, None, create_lambda_response(
                    400, False, 
                    error=f"Missing required fields: {', '.join(missing_fields)}"
                )
        
        return auth_email, event, None
        
    except Exception as e:
        logger.error(f"Error validating input: {str(e)}")
        return None, None, create_lambda_response(
            400, False, error=f"Invalid input: {str(e)}"
        )


def build_event_body(event_name, start_datetime, end_datetime, 
                     guest_emails=None, description=None, auth_email=None):
    """
    Build event body for Google Calendar API
    
    Args:
        event_name (str): Event summary/title
        start_datetime (str): Start datetime in ISO format
        end_datetime (str): End datetime in ISO format
        guest_emails (list): List of guest email addresses
        description (str): Event description (optional)
        auth_email (str): Authenticated user's email for Creator/Organizer
        
    Returns:
        dict: Event body for API request
    """
    event_body = {
        'summary': event_name,
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'UTC',
        }
    }
    
    if description:
        event_body['description'] = description
    
    # Add Creator and Organizer data if auth_email is provided
    if auth_email:
        # Creator: always auth_email with self=False
        event_body['organizer'] = {
            'email': auth_email,
            'self': False
        }
        
        # Organizer: lookup email from agents table with self=True
        try:
            organizer_email, error = lookup_email_from_agents_table(auth_email)
            if organizer_email and not error:
                event_body['creator'] = {
                    'email': organizer_email,
                    'self': True
                }
            else:
                logger.warning(f"Could not lookup organizer email for {auth_email}: {error}")
                # Fallback to auth_email if lookup fails
                event_body['creator'] = {
                    'email': auth_email,
                    'self': True
                }
        except Exception as e:
            logger.error(f"Error looking up organizer email: {str(e)}")
            # Fallback to auth_email if lookup fails
            event_body['creator'] = {
                'email': auth_email,
                'self': True
            }
    
    if guest_emails:
        event_body['attendees'] = [
            {'email': email, 'self': False} for email in guest_emails
        ]
    
    return event_body


def convert_datetime_to_timezone(dt_string, target_timezone):
    """
    Convert a datetime string to a specific timezone
    
    Args:
        dt_string: ISO format datetime string
        target_timezone: Target timezone string (e.g., 'America/New_York')
        
    Returns:
        str: ISO format datetime string in target timezone
    """
    try:
        from datetime import timezone as dt_timezone
        import pytz
        
        # Parse the datetime string
        if dt_string.endswith('Z'):
            dt_string = dt_string[:-1] + '+00:00'
        
        dt = datetime.fromisoformat(dt_string)
        
        # If datetime is naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_timezone.utc)
        
        # Convert to target timezone
        target_tz = pytz.timezone(target_timezone)
        dt_converted = dt.astimezone(target_tz)
        
        return dt_converted.isoformat()
        
    except Exception as e:
        logger.error(f"Error converting datetime to timezone: {str(e)}")
        return dt_string  # Return original if conversion fails


def convert_event_to_timezone(event, timezone):
    """
    Convert event datetime fields to a specific timezone
    
    Args:
        event: Event dict with start/end datetime fields
        timezone: Target timezone string
        
    Returns:
        dict: Event with converted datetime fields
    """
    try:
        # Convert start time
        if 'start' in event:
            if 'dateTime' in event['start']:
                event['start']['dateTime'] = convert_datetime_to_timezone(
                    event['start']['dateTime'], 
                    timezone
                )
                event['start']['timeZone'] = timezone
        
        # Convert end time
        if 'end' in event:
            if 'dateTime' in event['end']:
                event['end']['dateTime'] = convert_datetime_to_timezone(
                    event['end']['dateTime'], 
                    timezone
                )
                event['end']['timeZone'] = timezone
        
        return event
        
    except Exception as e:
        logger.error(f"Error converting event to timezone: {str(e)}")
        return event  # Return original if conversion fails

