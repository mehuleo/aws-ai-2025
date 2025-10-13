# Google Calendar Lambda Functions

This module provides Lambda functions for managing Google Calendar operations. All functions are designed to be invoked internally by other services (e.g., Bedrock Agent) and are **not exposed via API Gateway**.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Folder Structure](#folder-structure)
- [Authentication](#authentication)
- [Lambda Functions](#lambda-functions)
- [Code Standards](#code-standards)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Adding New Functions](#adding-new-functions)

---

## Architecture Overview

### Design Principles

1. **Modular Architecture**: Code is organized into separate modules for authentication, utilities, and event operations
2. **Authentication Layer**: All functions use a centralized authentication mechanism via `get_access_token()`
3. **Token Management**: Automatic token refresh with DynamoDB persistence
4. **Error Handling**: Standardized error responses with appropriate HTTP status codes
5. **Google API Integration**: Uses Google Calendar API v3 via `google-api-python-client`

### Dependencies

All functions use the `googleDeps` Lambda layer which includes:
- `google-api-python-client`
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`

Dependencies are defined in `layers/google_deps/requirements.txt`.

---

## Folder Structure

```
functions/google_calendar/
├── __init__.py              # Module initialization
├── auth.py                  # Authentication and token management
├── utils.py                 # Utility functions (date handling, formatting, validation)
├── events.py                # All calendar event Lambda functions
└── README.md               # This file
```

### Module Responsibilities

#### `auth.py`
- **Purpose**: Centralized authentication for all calendar operations
- **Key Functions**:
  - `get_access_token(email)`: Retrieve and refresh user's access token
  - `get_calendar_service(email)`: Get authenticated Google Calendar API service
  - `refresh_access_token(refresh_token)`: Refresh expired tokens
  - `update_token_in_dynamodb()`: Update tokens in DynamoDB

#### `utils.py`
- **Purpose**: Common utility functions used across Lambda functions
- **Key Functions**:
  - `get_date_range(days)`: Generate ISO format date ranges
  - `check_time_overlap()`: Detect event time conflicts
  - `format_event_response()`: Standardize event response format
  - `create_lambda_response()`: Create consistent Lambda responses
  - `validate_email_input()`: Input validation and sanitization
  - `build_event_body()`: Build event payloads for Google API

#### `events.py`
- **Purpose**: All Lambda function handlers for calendar operations
- **Contains**: 8 Lambda function handlers (see below)

---

## Authentication

### How Authentication Works

All calendar functions follow this authentication flow:

1. **Input**: Lambda receives user's email address
2. **Token Retrieval**: `get_access_token(email)` queries DynamoDB for user's tokens
3. **Authorization Check**: If no `google_access_token` exists, raises `403 Forbidden`
4. **Token Validation**: Checks if token is expired (with 30-second buffer)
5. **Token Refresh**: If expired, uses `refresh_token` to get new `access_token`
6. **Database Update**: Updates DynamoDB with new token and expiration time
7. **API Service**: Returns authenticated Google Calendar API service object

### DynamoDB Schema

**Table**: `SUBSCRIBERS_TABLE_NAME` (configured in serverless-config.yml)

**Primary Key**: `email` (string)

**Relevant Fields**:
- `google_access_token` (string): Current access token
- `refresh_token` (string): Refresh token for token renewal
- `token_expires_at` (string): ISO format timestamp of token expiration
- `calendar_access` (boolean): Flag indicating calendar permissions granted

### Error Responses

Authentication errors return standardized responses:

- **403 Forbidden**: User not authorized (no tokens in database)
- **401 Unauthorized**: Token refresh failed
- **404 Not Found**: User not found in database
- **500 Internal Server Error**: Unexpected authentication error

---

## Lambda Functions

### 1. `get_all_events`

**Handler**: `functions/google_calendar/events.get_all_events`

**Purpose**: Fetch all events from user's primary calendar for today + next 14 days

**Input**:
```json
{
  "email": "user@example.com"
}
```

**Output**:
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "status_code": 200,
    "data": {
      "events": [
        {
          "id": "event_id_123",
          "summary": "Meeting with Team",
          "description": "Discuss project updates",
          "start": { "dateTime": "2025-10-15T10:00:00Z" },
          "end": { "dateTime": "2025-10-15T11:00:00Z" },
          "status": "confirmed",
          "attendees": [...],
          ...
        }
      ],
      "count": 5,
      "time_range": {
        "start": "2025-10-13T00:00:00Z",
        "end": "2025-10-27T23:59:59Z"
      }
    }
  }
}
```

---

### 2. `get_event_instances`

**Handler**: `functions/google_calendar/events.get_event_instances`

**Purpose**: Fetch instances of a recurring event for today + next 14 days

**Input**:
```json
{
  "email": "user@example.com",
  "event_id": "recurring_event_parent_id"
}
```

**Output**:
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "status_code": 200,
    "data": {
      "instances": [
        {
          "id": "recurring_event_parent_id_20251015T100000Z",
          "summary": "Weekly Standup",
          "start": { "dateTime": "2025-10-15T10:00:00Z" },
          "end": { "dateTime": "2025-10-15T10:30:00Z" },
          "recurring_event_id": "recurring_event_parent_id",
          ...
        }
      ],
      "count": 2,
      "parent_event_id": "recurring_event_parent_id",
      "time_range": {
        "start": "2025-10-13T00:00:00Z",
        "end": "2025-10-27T23:59:59Z"
      }
    }
  }
}
```

---

### 3. `create_event`

**Handler**: `functions/google_calendar/events.create_event`

**Purpose**: Create a new event in user's primary calendar with overlap checking

**Input**:
```json
{
  "email": "user@example.com",
  "event_name": "Project Meeting",
  "start_datetime": "2025-10-15T14:00:00Z",
  "end_datetime": "2025-10-15T15:00:00Z",
  "guest_emails": ["guest1@example.com", "guest2@example.com"],
  "description": "Optional description"
}
```

**Output (Success)**:
```json
{
  "statusCode": 201,
  "body": {
    "success": true,
    "status_code": 201,
    "data": {
      "event": {
        "id": "new_event_id",
        "summary": "Project Meeting",
        ...
      },
      "message": "Event created successfully"
    }
  }
}
```

**Output (Overlap Detected)**:
```json
{
  "statusCode": 409,
  "body": {
    "success": false,
    "status_code": 409,
    "error": "Time overlap detected with existing event: 'Team Standup'. Please choose a different time slot."
  }
}
```

**Features**:
- Checks for time overlap with existing events before creating
- Returns `409 Conflict` if overlap detected
- Sends email notifications to all guests
- Uses UTC timezone by default

---

### 4. `update_event`

**Handler**: `functions/google_calendar/events.update_event`

**Purpose**: Update an existing event or event instance

**Input**:
```json
{
  "email": "user@example.com",
  "event_id": "event_id_or_instance_id",
  "event_name": "Updated Meeting Title",
  "start_datetime": "2025-10-15T15:00:00Z",
  "end_datetime": "2025-10-15T16:00:00Z",
  "guest_emails": ["newguest@example.com"],
  "description": "Updated description",
  "recurrence": ["RRULE:FREQ=WEEKLY;COUNT=10"]
}
```

**Notes**:
- All fields except `email` and `event_id` are optional
- Only provided fields will be updated
- For recurring events:
  - Use parent event ID (e.g., `1c1koptjesmb3dfrkdnc538t2d`) to update all instances
  - Use instance ID (e.g., `1c1koptjesmb3dfrkdnc538t2d_20251012T091500Z`) to update specific occurrence

**Output**:
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "status_code": 200,
    "data": {
      "event": { ... },
      "message": "Event updated successfully"
    }
  }
}
```

---

### 5. `delete_event`

**Handler**: `functions/google_calendar/events.delete_event`

**Purpose**: Delete an event or event instance

**Input**:
```json
{
  "email": "user@example.com",
  "event_id": "event_id_or_instance_id"
}
```

**Output**:
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "status_code": 200,
    "data": {
      "message": "Event deleted successfully",
      "event_id": "event_id_or_instance_id"
    }
  }
}
```

---

### 6. `rsvp_event`

**Handler**: `functions/google_calendar/events.rsvp_event`

**Purpose**: Mark RSVP status on an event

**Input**:
```json
{
  "email": "user@example.com",
  "event_id": "event_id_or_instance_id",
  "rsvp_status": "accepted",
  "note": "Looking forward to it!"
}
```

**RSVP Status Values**:
- `accepted`: Accept the invitation
- `tentative`: Maybe attending
- `declined`: Decline the invitation

**Output**:
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "status_code": 200,
    "data": {
      "message": "RSVP status set to accepted",
      "event_id": "event_id_or_instance_id",
      "rsvp_status": "accepted"
    }
  }
}
```

---

### 7. `get_availability`

**Handler**: `functions/google_calendar/events.get_availability`

**Purpose**: Find free/busy time slots using Google Calendar FreeBusy API

**Input**:
```json
{
  "email": "user@example.com",
  "start_time": "2025-10-13T10:00:00Z",
  "end_time": "2025-10-27T23:59:59Z"
}
```

**Notes**:
- `start_time` and `end_time` are optional
- If not provided, defaults to: now + 1 hour through now + 14 days

**Output**:
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "status_code": 200,
    "data": {
      "time_range": {
        "start": "2025-10-13T10:00:00Z",
        "end": "2025-10-27T23:59:59Z"
      },
      "busy_slots": [
        {
          "start": "2025-10-15T10:00:00Z",
          "end": "2025-10-15T11:00:00Z"
        },
        {
          "start": "2025-10-16T14:00:00Z",
          "end": "2025-10-16T15:00:00Z"
        }
      ],
      "busy_count": 2
    }
  }
}
```

---

### 8. `get_timezone`

**Handler**: `functions/google_calendar/events.get_timezone`

**Purpose**: Get primary calendar's timezone

**Input**:
```json
{
  "email": "user@example.com"
}
```

**Output**:
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "status_code": 200,
    "data": {
      "timezone": "America/Los_Angeles",
      "calendar_id": "primary",
      "calendar_summary": "user@example.com"
    }
  }
}
```

---

## Code Standards

### General Guidelines

1. **Modularity**: Keep functions focused on a single responsibility
2. **DRY Principle**: Use utility functions to avoid code duplication
3. **Error Handling**: Always use try-except blocks and log errors with traceback
4. **Logging**: Log all important operations (authentication, API calls, errors)
5. **Input Validation**: Validate all inputs before processing
6. **Response Format**: Use `create_lambda_response()` for consistent responses

### Naming Conventions

- **Functions**: Use snake_case (e.g., `get_all_events`)
- **Constants**: Use UPPER_CASE (e.g., `PRIMARY_CALENDAR`)
- **Variables**: Use descriptive snake_case (e.g., `event_id`, `access_token`)
- **Modules**: Use lowercase (e.g., `auth.py`, `events.py`)

### Response Format

All Lambda functions return this structure:

```python
{
    'statusCode': 200,  # HTTP status code
    'body': {
        'success': True/False,
        'status_code': 200,
        'data': { ... }  # For successful responses
        # OR
        'error': 'Error message'  # For error responses
    }
}
```

### HTTP Status Codes

- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Token refresh failed
- `403 Forbidden`: User not authorized
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., time overlap)
- `500 Internal Server Error`: Unexpected error

### Environment Variables

All functions require these environment variables:
- `SUBSCRIBERS_TABLE_NAME`: DynamoDB table name for user data
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret

These are configured in `serverless-config.yml`.

---

## Error Handling

### Error Response Structure

```python
{
    'statusCode': 400,  # Appropriate HTTP status code
    'body': {
        'success': False,
        'status_code': 400,
        'error': 'Human-readable error message suitable for AI agents'
    }
}
```

### Error Categories

1. **Authentication Errors** (`auth.py`)
   - User not found: 404
   - No calendar access: 403
   - Token refresh failure: 401

2. **Validation Errors** (`utils.py`)
   - Missing required fields: 400
   - Invalid input format: 400

3. **API Errors** (`events.py`)
   - Event not found: 404
   - Time overlap: 409
   - Google API errors: 500

### Custom Exceptions

```python
class AuthenticationError(Exception):
    """Raised when authentication fails"""
    def __init__(self, message, status_code=403):
        self.message = message
        self.status_code = status_code
```

---

## Testing

### Manual Testing

To test a Lambda function locally or via AWS Console:

```json
{
  "email": "test@example.com",
  "event_name": "Test Event",
  "start_datetime": "2025-10-20T10:00:00Z",
  "end_datetime": "2025-10-20T11:00:00Z"
}
```

### Prerequisites for Testing

1. User must exist in DynamoDB `SUBSCRIBERS_TABLE_NAME`
2. User must have `google_access_token` and `refresh_token` set
3. User must have `calendar_access` set to `true`

### Testing Authentication

```python
# Test get_access_token
from functions.google_calendar.auth import get_access_token

email = "test@example.com"
try:
    access_token, user_data, error = get_access_token(email)
    print(f"Access token: {access_token[:20]}...")
except AuthenticationError as e:
    print(f"Auth failed: {e.message} (Status: {e.status_code})")
```

---

## Adding New Functions

### Step 1: Implement the Function

Add your new Lambda function to `events.py`:

```python
def your_new_function(event, context):
    """
    Lambda function: Brief description
    
    Args:
        event: Lambda event containing required fields
        context: Lambda context
        
    Returns:
        dict: Response with data or error
    """
    try:
        # 1. Validate input
        email, body, error_response = validate_email_input(
            event, 
            ['required_field1', 'required_field2']
        )
        if error_response:
            return error_response
        
        # 2. Get authenticated calendar service
        service, user_data, error = get_calendar_service(email)
        if error:
            return create_lambda_response(
                error.get('status_code', 500), 
                False, 
                error=error.get('error')
            )
        
        # 3. Your business logic here
        result = service.events().someMethod(...).execute()
        
        # 4. Format and return response
        return create_lambda_response(
            200, 
            True, 
            data={'result': result}
        )
        
    except AuthenticationError as e:
        return create_lambda_response(e.status_code, False, error=e.message)
    except Exception as e:
        error_msg = f"Error in your_new_function: {str(e)}"
        logger.error(f"{error_msg} - Traceback: {traceback.format_exc()}")
        return create_lambda_response(500, False, error=error_msg)
```

### Step 2: Add to serverless.yml

Add the function definition to `serverless.yml`:

```yaml
yourNewFunction:
  handler: functions/google_calendar/events.your_new_function
  layers:
    - {Ref: GoogleDepsLambdaLayer}
  iamRoleStatements:
    - Effect: Allow
      Action:
        - dynamodb:Query
        - dynamodb:GetItem
        - dynamodb:UpdateItem
      Resource: 
        - "arn:aws:dynamodb:*:*:table/${file(./serverless-config.yml):SUBSCRIBERS_TABLE_NAME}"
  package:
    include:
      - functions/google_calendar/**
```

**Important**: Do NOT add API Gateway events. These functions are internal only.

### Step 3: Update Documentation

Add your function's documentation to this README under [Lambda Functions](#lambda-functions).

### Step 4: Deploy

```bash
cd serverless-backend
serverless deploy
```

---

## Best Practices

### 1. Always Use Authentication Layer

```python
# ✅ Correct
service, user_data, error = get_calendar_service(email)
if error:
    return create_lambda_response(...)

# ❌ Incorrect - Don't bypass authentication
service = build('calendar', 'v3', credentials=some_creds)
```

### 2. Use Primary Calendar

```python
# ✅ Correct
service.events().list(calendarId=PRIMARY_CALENDAR)

# ❌ Incorrect - Don't hardcode calendar IDs
service.events().list(calendarId='user@example.com')
```

### 3. Handle Time Zones Properly

```python
# ✅ Correct - Use UTC and ISO format
start_datetime = "2025-10-15T10:00:00Z"

# ❌ Incorrect - Don't use naive datetimes
start_datetime = "2025-10-15 10:00:00"
```

### 4. Validate All Inputs

```python
# ✅ Correct
email, body, error_response = validate_email_input(event, ['required_field'])
if error_response:
    return error_response

# ❌ Incorrect - Don't assume inputs exist
email = event['email']  # May raise KeyError
```

### 5. Log Appropriately

```python
# ✅ Correct
logger.info(f"Creating event for user: {email}")
logger.error(f"Error: {str(e)} - Traceback: {traceback.format_exc()}")

# ❌ Incorrect - Don't expose sensitive data
logger.info(f"Access token: {access_token}")
```

---

## Troubleshooting

### Common Issues

1. **403 Forbidden Error**
   - **Cause**: User doesn't have calendar access or tokens not in database
   - **Solution**: User needs to grant calendar permissions via OAuth flow

2. **401 Unauthorized Error**
   - **Cause**: Token refresh failed
   - **Solution**: User needs to re-authorize the application

3. **404 Not Found Error**
   - **Cause**: Event ID doesn't exist or user not in database
   - **Solution**: Verify event ID and user email

4. **409 Conflict Error**
   - **Cause**: Time overlap when creating event
   - **Solution**: Choose a different time slot

5. **500 Internal Server Error**
   - **Cause**: Unexpected error in code or Google API
   - **Solution**: Check CloudWatch logs for detailed error trace

### Debugging

Enable detailed logging:

```python
import logging
logger.setLevel(logging.DEBUG)
```

Check AWS CloudWatch logs for the Lambda function.

---

## Support

For questions or issues:

1. Check this README
2. Review code comments in `auth.py`, `utils.py`, and `events.py`
3. Check AWS CloudWatch logs for error details
4. Review Google Calendar API documentation: https://developers.google.com/calendar/api/v3/reference

---

## Version History

- **v1.0** (2025-10-13): Initial implementation
  - 8 Lambda functions for calendar management
  - Centralized authentication with token refresh
  - DynamoDB integration for user data
  - Comprehensive error handling and logging

