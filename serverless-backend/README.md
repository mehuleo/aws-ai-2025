# Email Agent Services - Serverless Backend

A serverless application built with AWS Lambda that provides email processing, Google OAuth authentication, calendar integration, and AI agent capabilities using AWS Bedrock.

## Overview

This serverless backend provides:
- **Email Processing**: Automatically processes incoming emails via Amazon SES
- **Google OAuth**: Handles Google authentication and authorization
- **Calendar Integration**: Manages Google Calendar access and operations
- **AI Agent**: AWS Bedrock agent integration for intelligent processing
- **Health Monitoring**: Health check endpoints

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Email Flow                               │
│  Email → SES → S3 → Lambda (parseEmail) → DynamoDB              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Authentication Flow                         │
│  Client → API Gateway → Lambda (validateGoogleAuth) → DynamoDB  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         AI Agent Flow                            │
│  Client → API Gateway → Lambda (testInvoke) → AWS Bedrock       │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
serverless-backend/
├── serverless.yml                    # Serverless Framework configuration
├── serverless-config.yml             # Environment-specific config (gitignored)
├── serverless-config.example.yml     # Example configuration template
├── requirements.txt                  # Main Python dependencies
├── README.md                         # This file
├── functions/                        # Lambda function code
│   ├── auth/
│   │   └── google_auth.py           # Google OAuth authentication
│   ├── utils/
│   │   └── email_utils.py           # Email parsing and processing
│   ├── health/
│   │   └── health.py                # Health check endpoint
│   └── intelligence/
│       └── agent_test.py            # AWS Bedrock agent integration
└── layers/
    └── google_deps/
        └── requirements.txt          # Google Calendar API dependencies
```

## Prerequisites

- Node.js (for Serverless Framework)
- Python 3.12
- AWS Account with appropriate permissions
- Serverless Framework CLI
- AWS credentials configured

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Before deploying, you need to set up your configuration file:

1. Copy the example configuration file:
   ```bash
   cp serverless-config.example.yml serverless-config.yml
   ```

2. Edit `serverless-config.yml` with your AWS resource names and API credentials:
   ```yaml
   S3_BUCKET_NAME: your-s3-bucket-name
   EMAILS_TABLE_NAME: your-emails-table-name
   SUBSCRIBERS_TABLE_NAME: your-subscribers-table-name
   GOOGLE_CLIENT_ID: your-google-oauth-client-id
   GOOGLE_CLIENT_SECRET: your-google-oauth-client-secret
   GOOGLE_AUTH_REDIRECT_URI: your-redirect-uri
   AGENT_RUNTIME_ARN: your-bedrock-agent-runtime-arn
   ```

**Important**: The `serverless-config.yml` file is excluded from git (via `.gitignore`) to keep your configuration private. Only commit `serverless-config.example.yml` to the repository.

## AWS Resources Required

### S3 Bucket
- **Purpose**: Stores raw email files from SES
- **Configuration**: Must be configured in `serverless-config.yml`

### DynamoDB Tables

#### 1. Emails Table
- **Purpose**: Stores parsed email data
- **Primary Key**: `uuid` (String)
- **Attributes**: message_id, timestamp, from, to, cc, subject, body, s3_bucket, s3_key, session_id, subscribers

#### 2. Subscribers Table
- **Purpose**: Stores user authentication and profile data
- **Primary Key**: `email` (String)
- **Attributes**: sid, userId, user_name, picture, email_verified, google_access_token, refresh_token, token_expires_at, calendar_access

### SES Configuration
- Domain or email address verified in SES
- SES receipt rule configured to:
  - Save emails to S3 bucket (with `inbox/` prefix)
  - Trigger `parseEmail` Lambda function

### Google OAuth Configuration
- Google Cloud Project with OAuth 2.0 credentials
- Authorized redirect URIs configured
- Scopes: email, profile, calendar (optional)

### AWS Bedrock
- Bedrock agent runtime configured
- Agent ARN added to configuration

## Installation

1. **Navigate to the serverless-backend directory**
   ```bash
   cd serverless-backend
   ```

2. **Install Serverless Framework** (if not already installed)
   ```bash
   npm install -g serverless
   ```

3. **Install Serverless plugins**
   ```bash
   npm install serverless-python-requirements
   ```

4. **Configure AWS credentials**
   ```bash
   aws configure
   ```

5. **Set up configuration file** (see Configuration section above)
   ```bash
   cp serverless-config.example.yml serverless-config.yml
   # Edit serverless-config.yml with your values
   ```

## Serverless Framework Configuration

### Service Details
- **Organization**: condor
- **Service Name**: email-agent-services
- **Runtime**: Python 3.12
- **Deployment Bucket**: serverless-email-agent
- **Stage**: prod
- **Memory Size**: 256 MB

### Plugins
- `serverless-python-requirements`: Handles Python dependencies and layers

### Custom Configuration
- **dockerizePip**: true (builds dependencies in Docker for Lambda compatibility)
- **slim**: true (removes unnecessary files to reduce package size)
- **layer**: enabled (creates Lambda layers for dependencies)

### Layers
- **googleDeps**: Google Calendar API client dependencies
  - google-api-python-client==2.126.0
  - google-auth==2.25.2
  - google-auth-oauthlib==1.2.0
  - google-auth-httplib2==0.2.0

## Deployment

Deploy to AWS:

```bash
serverless deploy
```

Deploy specific function:

```bash
serverless deploy function -f parseEmail
```

## Lambda Functions

### 1. ping (Health Check)

**Purpose**: Health check endpoint to verify service is running

**Handler**: `functions/health/health.ping`

**Endpoint**: `GET /v1/health`

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Go Serverless v4.0! Your function executed successfully!"
  }
}
```

**IAM Permissions**: None required

---

### 2. parseEmail (Email Processing)

**Purpose**: Parse incoming emails from SES and store in DynamoDB

**Handler**: `functions/utils/email_utils.parseEmail`

**Trigger**: SES email receipt (via S3 action)

**Process**:
1. Extract metadata from SES event (message ID, source, timestamp, destination)
2. Retrieve raw email content from S3
3. Parse email body (supports both plain text and HTML)
4. Extract email headers (to, cc, from, subject)
5. Lookup subscribers in DynamoDB
6. Generate unique UUID and session_id (based on subject hash)
7. Store structured data in DynamoDB

**DynamoDB Schema** (Emails Table):
```json
{
  "uuid": "string (UUID)",
  "message_id": "string",
  "timestamp": "string (ISO 8601)",
  "received_at": "string (ISO 8601)",
  "from": "string",
  "to": ["array of strings"],
  "cc": ["array of strings"],
  "subject": "string",
  "session_id": "string (MD5 hash of cleaned subject)",
  "body": "string",
  "s3_bucket": "string",
  "s3_key": "string",
  "subscribers": ["array of email strings"]
}
```

**IAM Permissions**:
- S3: GetObject, ListBucket
- SES: Full access
- DynamoDB: PutItem, GetItem, UpdateItem, Query, Scan (on both tables)

---

### 3. validateGoogleAuth (Google OAuth)

**Purpose**: Handle Google OAuth authentication and authorization flows

**Handler**: `functions/auth/google_auth.validateGoogleAuth`

**Endpoint**: `POST /v1/validateGoogleAuth`

**Actions Supported**:

#### a) validate_token
Validates Google ID token and stores/updates user in DynamoDB

**Request**:
```json
{
  "action": "validate_token",
  "token": "google_id_token"
}
```

**Response**:
```json
{
  "success": true,
  "user": {
    "sid": "session_id",
    "email": "user@example.com",
    "user_name": "User Name",
    "picture": "profile_picture_url",
    "email_verified": true
  }
}
```

#### b) get_user
Retrieves user information with SID authentication

**Request**:
```json
{
  "action": "get_user",
  "email": "user@example.com",
  "sid": "session_id"
}
```

#### c) get_calendar_access
Generates OAuth URL for Google Calendar access

**Request**:
```json
{
  "action": "get_calendar_access",
  "email": "user@example.com",
  "redirect_uri": "https://yourapp.com/callback"
}
```

#### d) exchange_code
Exchanges authorization code for access token

**Request**:
```json
{
  "action": "exchange_code",
  "code": "authorization_code",
  "redirect_uri": "https://yourapp.com/callback",
  "email": "user@example.com"
}
```

#### e) get_calendars
Retrieves user's Google calendars

**Request**:
```json
{
  "action": "get_calendars",
  "email": "user@example.com",
  "sid": "session_id"
}
```

**IAM Permissions**:
- DynamoDB: PutItem, GetItem, UpdateItem, Query, Scan (on Subscribers table)

---

### 4. testInvoke (AWS Bedrock Agent)

**Purpose**: Test endpoint for AWS Bedrock agent runtime invocation

**Handler**: `functions/intelligence/agent_test.test_invoke`

**Endpoint**: `POST /v1/test-invoke`

**Request**:
```json
{
  "prompt": "Your prompt text here"
}
```

**Response**:
```json
{
  "sessionId": "generated_session_id",
  "prompt": "Your prompt text here",
  "agentResponse": {
    // Bedrock agent response data
  }
}
```

**IAM Permissions**:
- Bedrock: InvokeAgentRuntime

## AWS Resources Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://your-bucket-name
```

Configure bucket policy to allow SES to write:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ses.amazonaws.com"
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

### 2. Create DynamoDB Tables

**Emails Table**:
```bash
aws dynamodb create-table \
  --table-name your-emails-table-name \
  --attribute-definitions AttributeName=uuid,AttributeType=S \
  --key-schema AttributeName=uuid,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

**Subscribers Table**:
```bash
aws dynamodb create-table \
  --table-name your-subscribers-table-name \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 3. Configure Amazon SES

1. **Verify domain or email address** in Amazon SES console

2. **Create SES Receipt Rule Set** (if not exists):
   ```bash
   aws ses create-receipt-rule-set --rule-set-name default-rule-set
   aws ses set-active-receipt-rule-set --rule-set-name default-rule-set
   ```

3. **Configure SES Receipt Rule**:
   - Action 1: Save to S3 bucket with prefix `inbox/`
   - Action 2: Invoke Lambda function `parseEmail`

### 4. Google OAuth Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Google+ API and Google Calendar API
3. Create OAuth 2.0 credentials (Web application)
4. Add authorized redirect URIs
5. Copy Client ID and Client Secret to `serverless-config.yml`

### 5. AWS Bedrock Setup

1. Enable AWS Bedrock in your AWS account
2. Create or configure an agent runtime
3. Note the Agent Runtime ARN and add to `serverless-config.yml`

## Testing

### Local Testing

Test the health check function:
```bash
serverless invoke local -f ping
```

### Remote Testing

**Test health endpoint**:
```bash
serverless invoke -f ping
```

**Test validateGoogleAuth function**:
```bash
serverless invoke -f validateGoogleAuth --data '{"body": "{\"action\": \"validate_token\", \"token\": \"your_google_token\"}"}'
```

**Test email processing**:
Send a test email to your SES-configured email address and monitor CloudWatch logs:
```bash
serverless logs -f parseEmail --tail
```

**Test Bedrock agent**:
```bash
curl -X POST https://your-api-gateway-url/v1/test-invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
```

## Monitoring

View function logs:
```bash
# View parseEmail logs
serverless logs -f parseEmail

# View validateGoogleAuth logs
serverless logs -f validateGoogleAuth

# View testInvoke logs
serverless logs -f testInvoke
```

View logs in real-time:
```bash
serverless logs -f parseEmail --tail
```

Monitor all functions via AWS CloudWatch Logs console.

## API Endpoints

After deployment, you'll have the following API endpoints:

- `GET /v1/health` - Health check endpoint
- `POST /v1/validateGoogleAuth` - Google OAuth authentication
- `POST /v1/test-invoke` - Bedrock agent test invocation

The `parseEmail` function is triggered automatically by SES and doesn't have an HTTP endpoint.

## Error Handling

All functions include comprehensive error handling:
- Catches all exceptions during processing
- Logs full stack traces for debugging
- Returns appropriate HTTP status codes (200 for success, 400/401/403/404/500 for errors)
- Provides detailed error messages in response body
- CORS headers enabled for browser access

## Development

### Function Organization

Functions are organized by domain:
- **auth/**: Authentication and authorization (Google OAuth)
- **utils/**: Utility functions (email parsing, processing)
- **health/**: Health check and monitoring
- **intelligence/**: AI/ML integrations (Bedrock agent)

### Email Processing Features

The `email_utils.py` module provides:
- **Email parsing**: Supports plain text, HTML, and multipart emails
- **Subscriber lookup**: Automatically checks if email participants are registered subscribers
- **Session grouping**: Groups related emails by subject (hash-based session_id)
- **Metadata extraction**: Comprehensive extraction of email headers and content

### Google OAuth Features

The `google_auth.py` module provides:
- **Token verification**: Validates Google ID tokens without external dependencies
- **Session management**: SID-based session tracking for security
- **Calendar integration**: OAuth flow for Google Calendar access
- **Token refresh**: Automatic access token refresh when expired
- **Multi-action API**: Single endpoint handles multiple auth operations

## Troubleshooting

### Email not being processed

1. Check SES receipt rules are configured correctly
2. Verify S3 bucket name matches `serverless-config.yml`
3. Check Lambda function has necessary IAM permissions
4. Verify SES has permission to write to S3 bucket
5. Review CloudWatch logs for parseEmail function
6. Ensure email is sent to verified SES domain/email

### Google OAuth errors

1. Verify Google Client ID and Secret in `serverless-config.yml`
2. Check redirect URI matches Google OAuth configuration
3. Ensure OAuth consent screen is configured in Google Cloud Console
4. Verify API scopes are correctly requested
5. Check token hasn't expired (tokens expire after ~1 hour)
6. Review CloudWatch logs for validateGoogleAuth function

### DynamoDB errors

1. Verify table names match `serverless-config.yml`
2. Check tables exist in correct AWS region
3. Verify Lambda has DynamoDB permissions (PutItem, GetItem, Query, etc.)
4. Check primary key schema matches code expectations
5. Review CloudWatch logs for specific error messages

### S3 access errors

1. Verify bucket exists and is in correct region
2. Check bucket policy allows Lambda access
3. Verify SES has permission to write to bucket
4. Ensure bucket name in config matches actual bucket name

### Bedrock agent errors

1. Verify AGENT_RUNTIME_ARN is correctly configured
2. Check Lambda has bedrock-agentcore:InvokeAgentRuntime permission
3. Ensure Bedrock agent is deployed and active
4. Verify region matches agent location
5. Check session ID format (must be 33+ characters)

### Deployment issues

1. Ensure Serverless Framework is installed: `npm install -g serverless`
2. Install required plugin: `npm install serverless-python-requirements`
3. Verify AWS credentials are configured: `aws configure`
4. Check `serverless-config.yml` exists and has all required values
5. Ensure Docker is running (required for `dockerizePip`)
6. Try deploying with `--verbose` flag for detailed logs

### CORS issues

1. All HTTP endpoints have CORS enabled by default
2. Check `Access-Control-Allow-Origin: *` in response headers
3. Verify preflight OPTIONS requests are handled
4. Review browser console for specific CORS errors

## Security Considerations

1. **Configuration Security**: 
   - Never commit `serverless-config.yml` to version control
   - Rotate Google OAuth credentials regularly
   - Use AWS Secrets Manager for sensitive data in production

2. **Authentication**:
   - SID-based session management provides stateless authentication
   - Google tokens are verified server-side
   - Access tokens automatically refresh when expired

3. **IAM Permissions**:
   - Functions use least-privilege IAM roles
   - Each function only has access to resources it needs
   - Review IAM policies regularly

4. **CORS**:
   - Currently set to `*` for development
   - Restrict to specific origins in production

## Performance Optimization

- **Individual Packaging**: Each function is packaged separately to reduce cold start times
- **Lambda Layers**: Google dependencies in a shared layer reduce deployment size
- **Memory Size**: 256 MB configured - adjust based on actual usage
- **DynamoDB**: On-demand billing mode scales automatically
- **Docker Pip**: Ensures native dependencies are compiled for Lambda environment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Related Documentation

- [Serverless Framework Documentation](https://www.serverless.com/framework/docs)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [Amazon SES Documentation](https://docs.aws.amazon.com/ses/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

## License

GNU AFFERO GENERAL PUBLIC LICENSE

## Support

For issues, questions, or contributions, please refer to the project repository.

---

Built with ❤️ using Serverless Framework
