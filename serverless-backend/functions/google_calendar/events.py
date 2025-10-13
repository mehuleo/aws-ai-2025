"""
Google Calendar Events Lambda Functions

This module contains all lambda functions for managing Google Calendar events.
Each function authenticates using get_access_token() and interacts with
the Google Calendar API.
"""

import logging
import traceback
from .auth import get_calendar_service, AuthenticationError
from .utils import (
    get_date_range, 
    format_event_response, 
    create_lambda_response,
    validate_email_input,
    check_time_overlap,
    build_event_body,
    parse_datetime,
    convert_event_to_timezone
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Primary calendar ID constant
PRIMARY_CALENDAR = 'primary'


def get_all_events(event, context):
    """
    Lambda function: Fetch all events from user's primary calendar
    for today + next 14 days. Converts all event times to user's timezone.
    
    Args:
        event: Lambda event containing 'email'
        context: Lambda context
        
    Returns:
        dict: Response with events list or error
    """
    try:
        # Validate input
        email, body, error_response = validate_email_input(event)
        if error_response:
            return error_response
        
        logger.info(f"Fetching events for user: {email}")
        
        # Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # Get user's timezone from calendar settings
        try:
            calendar = service.calendars().get(calendarId=PRIMARY_CALENDAR).execute()
            user_timezone = calendar.get('timeZone', 'UTC')
            logger.info(f"User timezone: {user_timezone}")
        except Exception as e:
            logger.warning(f"Could not fetch timezone, defaulting to UTC: {str(e)}")
            user_timezone = 'UTC'
        
        # Get date range (today + 14 days)
        time_min, time_max = get_date_range(14)
        
        # Fetch events from primary calendar
        events_result = service.events().list(
            calendarId=PRIMARY_CALENDAR,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Convert events to user's timezone and format
        formatted_events = []
        for evt in events:
            # Convert to user's timezone
            evt_with_timezone = convert_event_to_timezone(evt, user_timezone)
            # Format event
            formatted_evt = format_event_response(evt_with_timezone)
            formatted_events.append(formatted_evt)
        
        logger.info(f"Successfully fetched {len(formatted_events)} events for {email}")
        
        return create_lambda_response(
            200, 
            True, 
            data={
                'events': formatted_events,
                'count': len(formatted_events),
                'timezone': user_timezone,
                'time_range': {
                    'start': time_min,
                    'end': time_max
                }
            }
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e.message}")
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error fetching events: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)


def get_event_instances(event, context):
    """
    Lambda function: Fetch instances of a recurring event
    for today + next 14 days.
    
    Args:
        event: Lambda event containing 'email' and 'event_id'
        context: Lambda context
        
    Returns:
        dict: Response with event instances or error
    """
    try:
        # Validate input
        email, body, error_response = validate_email_input(event, ['event_id'])
        if error_response:
            return error_response
        
        event_id = body.get('event_id')
        logger.info(f"Fetching instances for event {event_id}, user: {email}")
        
        # Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # Get date range (today + 14 days)
        time_min, time_max = get_date_range(14)
        
        # Fetch event instances
        instances_result = service.events().instances(
            calendarId=PRIMARY_CALENDAR,
            eventId=event_id,
            timeMin=time_min,
            timeMax=time_max
        ).execute()
        
        instances = instances_result.get('items', [])
        
        # Format instances
        formatted_instances = [format_event_response(inst) for inst in instances]
        
        logger.info(f"Successfully fetched {len(formatted_instances)} instances for event {event_id}")
        
        return create_lambda_response(
            200, 
            True, 
            data={
                'instances': formatted_instances,
                'count': len(formatted_instances),
                'parent_event_id': event_id,
                'time_range': {
                    'start': time_min,
                    'end': time_max
                }
            }
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e.message}")
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error fetching event instances: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)


def create_event(event, context):
    """
    Lambda function: Create a new event in user's primary calendar.
    Checks for time overlap before creating.
    
    Args:
        event: Lambda event containing:
            - email: User's email
            - event_name: Event title
            - start_datetime: Start datetime (ISO format)
            - end_datetime: End datetime (ISO format)
            - guest_emails: List of guest emails (optional)
            - description: Event description (optional)
        context: Lambda context
        
    Returns:
        dict: Response with created event or error
    """
    try:
        # Validate input
        required_fields = ['event_name', 'start_datetime', 'end_datetime']
        email, body, error_response = validate_email_input(event, required_fields)
        if error_response:
            return error_response
        
        event_name = body.get('event_name')
        start_datetime = body.get('start_datetime')
        end_datetime = body.get('end_datetime')
        guest_emails = body.get('guest_emails', [])
        description = body.get('description')
        
        logger.info(f"Creating event '{event_name}' for user: {email}")
        
        # Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # Check for time overlap with existing events
        # First, get all events in the relevant time range
        time_min, time_max = get_date_range(14)
        
        events_result = service.events().list(
            calendarId=PRIMARY_CALENDAR,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True
        ).execute()
        
        existing_events = events_result.get('items', [])
        
        # Check each event for overlap
        for existing_event in existing_events:
            if check_time_overlap(
                start_datetime, 
                end_datetime,
                existing_event.get('start'),
                existing_event.get('end')
            ):
                logger.warning(f"Time overlap detected with event: {existing_event.get('id')}")
                return create_lambda_response(
                    409, 
                    False, 
                    error=f"Time overlap detected with existing event: '{existing_event.get('summary', 'Untitled')}'. Please choose a different time slot."
                )
        
        # No overlap, create the event
        event_body = build_event_body(
            event_name, 
            start_datetime, 
            end_datetime,
            guest_emails,
            description
        )
        
        created_event = service.events().insert(
            calendarId=PRIMARY_CALENDAR,
            body=event_body,
            sendUpdates='all'  # Send notifications to guests
        ).execute()
        
        formatted_event = format_event_response(created_event)
        
        logger.info(f"Successfully created event {created_event.get('id')} for {email}")
        
        return create_lambda_response(
            201, 
            True, 
            data={
                'event': formatted_event,
                'message': 'Event created successfully'
            }
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e.message}")
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error creating event: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)


def update_event(event, context):
    """
    Lambda function: Update an existing event.
    
    Args:
        event: Lambda event containing:
            - email: User's email
            - event_id: Event ID or instance ID
            - recurrence: Recurrence rule (optional)
            - event_name: New event title (optional)
            - start_datetime: New start datetime (optional)
            - end_datetime: New end datetime (optional)
            - guest_emails: New guest list (optional)
            - description: New description (optional)
        context: Lambda context
        
    Returns:
        dict: Response with updated event or error
    """
    try:
        # Validate input
        email, body, error_response = validate_email_input(event, ['event_id'])
        if error_response:
            return error_response
        
        event_id = body.get('event_id')
        logger.info(f"Updating event {event_id} for user: {email}")
        
        # Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # Get the existing event
        try:
            existing_event = service.events().get(
                calendarId=PRIMARY_CALENDAR,
                eventId=event_id
            ).execute()
        except Exception as e:
            logger.error(f"Event not found: {event_id}")
            return create_lambda_response(404, False, error="Event not found")
        
        # Build update body with provided fields
        update_body = {}
        
        if body.get('event_name'):
            update_body['summary'] = body.get('event_name')
        
        if body.get('description') is not None:
            update_body['description'] = body.get('description')
        
        if body.get('start_datetime'):
            update_body['start'] = {
                'dateTime': body.get('start_datetime'),
                'timeZone': 'UTC'
            }
        
        if body.get('end_datetime'):
            update_body['end'] = {
                'dateTime': body.get('end_datetime'),
                'timeZone': 'UTC'
            }
        
        if body.get('guest_emails') is not None:
            update_body['attendees'] = [
                {'email': email} for email in body.get('guest_emails')
            ]
        
        if body.get('recurrence') is not None:
            update_body['recurrence'] = body.get('recurrence')
        
        # Merge with existing event
        for key, value in update_body.items():
            existing_event[key] = value
        
        # Update the event
        updated_event = service.events().update(
            calendarId=PRIMARY_CALENDAR,
            eventId=event_id,
            body=existing_event,
            sendUpdates='all'
        ).execute()
        
        formatted_event = format_event_response(updated_event)
        
        logger.info(f"Successfully updated event {event_id} for {email}")
        
        return create_lambda_response(
            200, 
            True, 
            data={
                'event': formatted_event,
                'message': 'Event updated successfully'
            }
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e.message}")
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error updating event: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)


def delete_event(event, context):
    """
    Lambda function: Delete an event or event instance.
    
    Args:
        event: Lambda event containing:
            - email: User's email
            - event_id: Event ID or instance ID
        context: Lambda context
        
    Returns:
        dict: Response with success message or error
    """
    try:
        # Validate input
        email, body, error_response = validate_email_input(event, ['event_id'])
        if error_response:
            return error_response
        
        event_id = body.get('event_id')
        logger.info(f"Deleting event {event_id} for user: {email}")
        
        # Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # Delete the event
        try:
            service.events().delete(
                calendarId=PRIMARY_CALENDAR,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return create_lambda_response(
                404, 
                False, 
                error="Event not found or already deleted"
            )
        
        logger.info(f"Successfully deleted event {event_id} for {email}")
        
        return create_lambda_response(
            200, 
            True, 
            data={
                'message': 'Event deleted successfully',
                'event_id': event_id
            }
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e.message}")
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error deleting event: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)


def rsvp_event(event, context):
    """
    Lambda function: Mark RSVP status on an event.
    
    Args:
        event: Lambda event containing:
            - email: User's email
            - event_id: Event ID or instance ID
            - rsvp_status: 'accepted', 'tentative', or 'declined'
            - note: Optional note (optional)
        context: Lambda context
        
    Returns:
        dict: Response with success message or error
    """
    try:
        # Validate input
        required_fields = ['event_id', 'rsvp_status']
        email, body, error_response = validate_email_input(event, required_fields)
        if error_response:
            return error_response
        
        event_id = body.get('event_id')
        rsvp_status = body.get('rsvp_status').lower()
        note = body.get('note', '')
        
        # Validate RSVP status
        valid_statuses = ['accepted', 'tentative', 'declined']
        if rsvp_status not in valid_statuses:
            return create_lambda_response(
                400, 
                False, 
                error=f"Invalid RSVP status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Map user-friendly names to API values
        status_map = {
            'accepted': 'accepted',
            'tentative': 'tentative',
            'declined': 'declined'
        }
        response_status = status_map[rsvp_status]
        
        logger.info(f"Setting RSVP status '{rsvp_status}' for event {event_id}, user: {email}")
        
        # Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # Get the event
        try:
            existing_event = service.events().get(
                calendarId=PRIMARY_CALENDAR,
                eventId=event_id
            ).execute()
        except Exception as e:
            logger.error(f"Event not found: {event_id}")
            return create_lambda_response(404, False, error="Event not found")
        
        # Update attendee response status
        attendees = existing_event.get('attendees', [])
        user_found = False
        
        for attendee in attendees:
            if attendee.get('email') == email:
                attendee['responseStatus'] = response_status
                if note:
                    attendee['comment'] = note
                user_found = True
                break
        
        if not user_found:
            # User is not in attendee list, add them
            attendees.append({
                'email': email,
                'responseStatus': response_status,
                'comment': note if note else ''
            })
        
        existing_event['attendees'] = attendees
        
        # Update the event
        updated_event = service.events().update(
            calendarId=PRIMARY_CALENDAR,
            eventId=event_id,
            body=existing_event,
            sendUpdates='all'
        ).execute()
        
        logger.info(f"Successfully updated RSVP status for event {event_id}, user: {email}")
        
        return create_lambda_response(
            200, 
            True, 
            data={
                'message': f'RSVP status set to {rsvp_status}',
                'event_id': event_id,
                'rsvp_status': rsvp_status
            }
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e.message}")
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error setting RSVP status: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)


def get_availability(event, context):
    """
    Lambda function: Find free time slots using FreeBusy API.
    
    Args:
        event: Lambda event containing:
            - email: User's email
            - start_time: Start time for lookup (optional, defaults to now + 1 hour)
            - end_time: End time for lookup (optional, defaults to now + 14 days)
        context: Lambda context
        
    Returns:
        dict: Response with free/busy information or error
    """
    try:
        # Validate input
        email, body, error_response = validate_email_input(event)
        if error_response:
            return error_response
        
        logger.info(f"Fetching availability for user: {email}")
        
        # Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # Get time range
        if body.get('start_time') and body.get('end_time'):
            time_min = body.get('start_time')
            time_max = body.get('end_time')
        else:
            # Default: now + 1 hour to next 14 days
            from datetime import datetime, timedelta
            start = datetime.utcnow() + timedelta(hours=1)
            end = datetime.utcnow() + timedelta(days=14)
            time_min = start.isoformat() + 'Z'
            time_max = end.isoformat() + 'Z'
        
        # Query FreeBusy
        freebusy_query = {
            'timeMin': time_min,
            'timeMax': time_max,
            'items': [{'id': PRIMARY_CALENDAR}]
        }
        
        freebusy_result = service.freebusy().query(body=freebusy_query).execute()
        
        calendar_freebusy = freebusy_result.get('calendars', {}).get(PRIMARY_CALENDAR, {})
        busy_slots = calendar_freebusy.get('busy', [])
        
        logger.info(f"Successfully fetched availability for {email}")
        
        return create_lambda_response(
            200, 
            True, 
            data={
                'time_range': {
                    'start': time_min,
                    'end': time_max
                },
                'busy_slots': busy_slots,
                'busy_count': len(busy_slots)
            }
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e.message}")
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error fetching availability: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)


def get_timezone(event, context):
    """
    Lambda function: Get primary calendar's timezone.
    
    Args:
        event: Lambda event containing:
            - email: User's email
        context: Lambda context
        
    Returns:
        dict: Response with timezone information or error
    """
    try:
        # Validate input
        email, body, error_response = validate_email_input(event)
        if error_response:
            return error_response
        
        logger.info(f"Fetching timezone for user: {email}")
        
        # Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # Get calendar settings
        calendar = service.calendars().get(calendarId=PRIMARY_CALENDAR).execute()
        
        timezone = calendar.get('timeZone', 'UTC')
        
        logger.info(f"Successfully fetched timezone '{timezone}' for {email}")
        
        return create_lambda_response(
            200, 
            True, 
            data={
                'timezone': timezone,
                'calendar_id': calendar.get('id'),
                'calendar_summary': calendar.get('summary')
            }
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e.message}")
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error fetching timezone: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)

