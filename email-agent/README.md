# Email Agent - Serverless Email Processing System

A serverless application built with AWS Lambda that automatically processes incoming emails received via Amazon SES (Simple Email Service), parses their content, and stores them in DynamoDB for further processing.

## Overview

This email agent automatically:
- Receives emails through Amazon SES
- Stores raw email content in S3
- Parses email metadata and body content
- Stores structured email data in DynamoDB with unique identifiers

## Architecture

```
Email → SES → S3 (Raw Email) → Lambda (parseEmail) → DynamoDB (Parsed Data)
```

### Components

1. **Amazon SES**: Receives incoming emails
2. **S3 Bucket**: Stores raw email content (`inbound-superagent.diy`)
3. **Lambda Functions**:
   - `hello`: Health check endpoint
   - `parseEmail`: Main email processing function
4. **DynamoDB Table**: Stores parsed email data (`Superagent-raw-emails`)

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

2. Edit `serverless-config.yml` with your AWS resource names:
   ```yaml
   S3_BUCKET_NAME: your-s3-bucket-name
   DYNAMODB_TABLE_NAME: your-dynamodb-table-name
   ```

**Important**: The `serverless-config.yml` file is excluded from git (via `.gitignore`) to keep your configuration private. Only commit `serverless-config.example.yml` to the repository.

## AWS Resources Required

### S3 Bucket
- **Name**: `inbound-superagent.diy`
- **Purpose**: Stores raw email files

### DynamoDB Table
- **Name**: `Superagent-raw-emails`
- **Purpose**: Stores parsed email data
- **Primary Key**: `uuid` (String)

### SES Configuration
- Domain or email address verified in SES
- SES receipt rule configured to:
  - Save emails to S3 bucket
  - Trigger Lambda function

## Installation

1. **Clone the repository**
   ```bash
   cd serverless-project/email-agent
   ```

2. **Install Serverless Framework** (if not already installed)
   ```bash
   npm install -g serverless
   ```

3. **Configure AWS credentials**
   ```bash
   aws configure
   ```

4. **Update configuration** (if needed)
   - Edit `handler.py` to update S3 bucket name and DynamoDB table name
   - Edit `serverless.yml` to update organization and deployment settings

## Configuration

### Environment Variables (handler.py)

```python
S3_BUCKET_NAME = "inbound-superagent.diy"
DYNAMODB_TABLE_NAME = "Superagent-raw-emails"
```

### Serverless Configuration (serverless.yml)

- **Organization**: condor
- **Service Name**: email-agent
- **Runtime**: Python 3.12
- **Deployment Bucket**: serverless-email-agent

## Deployment

Deploy to AWS:

```bash
serverless deploy
```

Deploy specific function:

```bash
serverless deploy function -f parseEmail
```

## Functions

### hello

**Purpose**: Health check endpoint

**Handler**: `handler.hello`

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Go Serverless v4.0! Your function executed successfully!"
  }
}
```

### parseEmail

**Purpose**: Parse incoming emails from SES and store in DynamoDB

**Handler**: `handler.parseEmail`

**Trigger**: SES email receipt

**Process**:
1. Extract metadata from SES event (message ID, source, timestamp, destination)
2. Retrieve raw email content from S3
3. Parse email body (supports both plain text and HTML)
4. Extract email headers (to, cc, from, subject)
5. Generate unique UUID for the email
6. Store structured data in DynamoDB

**DynamoDB Schema**:
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
  "body": "string",
  "s3_bucket": "string",
  "s3_key": "string"
}
```

**IAM Permissions**:
- S3: GetObject, ListBucket
- SES: Full access
- DynamoDB: PutItem, GetItem, UpdateItem, Query, Scan

## SES Setup

1. **Verify domain or email address** in Amazon SES console

2. **Create S3 bucket** for storing emails:
   ```bash
   aws s3 mb s3://inbound-superagent.diy
   ```

3. **Create DynamoDB table**:
   ```bash
   aws dynamodb create-table \
     --table-name Superagent-raw-emails \
     --attribute-definitions AttributeName=uuid,AttributeType=S \
     --key-schema AttributeName=uuid,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

4. **Configure SES Receipt Rule**:
   - Action 1: Save to S3 bucket `inbound-superagent.diy` with prefix `inbox/`
   - Action 2: Invoke Lambda function `parseEmail`

## Testing

### Local Testing

Test the hello function:
```bash
serverless invoke local -f hello
```

### Remote Testing

Test deployed function:
```bash
serverless invoke -f hello
```

Send a test email to your SES-configured email address and monitor CloudWatch logs:
```bash
serverless logs -f parseEmail --tail
```

## Monitoring

View function logs:
```bash
serverless logs -f parseEmail
```

View logs in real-time:
```bash
serverless logs -f parseEmail --tail
```

## Error Handling

The `parseEmail` function includes comprehensive error handling:
- Catches all exceptions during email processing
- Logs full stack traces for debugging
- Returns appropriate HTTP status codes (200 for success, 500 for errors)
- Provides detailed error messages in response body

## Development

### Function Structure

The code is organized into modular functions for maintainability:
- `extract_ses_metadata()`: Extract SES event data
- `retrieve_email_from_s3()`: Fetch raw email from S3
- `parse_email_content()`: Parse raw email bytes
- `extract_email_body()`: Extract text/HTML body
- `build_parsed_email()`: Structure email data
- `create_dynamodb_item()`: Prepare DynamoDB record
- `store_email_in_dynamodb()`: Persist to database

### Email Body Parsing

Supports:
- Plain text emails
- HTML emails
- Multipart emails
- Attachments (ignored in body extraction)

## Troubleshooting

### Email not being processed

1. Check SES receipt rules are configured correctly
2. Verify S3 bucket name matches configuration
3. Check Lambda function has necessary IAM permissions
4. Review CloudWatch logs for errors

### DynamoDB errors

1. Verify table name matches configuration
2. Check table exists in correct region
3. Verify Lambda has DynamoDB permissions

### S3 access errors

1. Verify bucket exists and is in correct region
2. Check bucket policy allows Lambda access
3. Verify SES has permission to write to bucket

## License

MIT

## Author

Built with ❤️ using Serverless Framework

