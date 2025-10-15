# Executive Assistant Multi-Agent System

A sophisticated multi-agent system built on Amazon Bedrock for intelligent executive assistant capabilities, featuring a three-agent architecture with planning, request building, and communication agents.

## Overview

This project implements an intelligent executive assistant system using Amazon Bedrock's capabilities. The system consists of three specialized agents that work together to process email-based instructions and execute calendar-related tasks through a structured planning and execution workflow with comprehensive schema validation.

## Architecture

The system uses a **three-agent architecture**:

- **Planning Agent (Intent Planner)**: Analyzes email requests and creates structured execution plans
- **Request Builder Agent**: Constructs API payloads for specific tool executions
- **Communication Agent**: Handles email communications and user interactions

## Features

- **Multi-Agent System**: Three specialized agents working in coordination
- **Bedrock Integration**: Built on Amazon Bedrock Agent Core App with Nova Lite model
- **MCP Tool Integration**: Connects to external tools via Model Context Protocol (MCP)
- **OAuth Authentication**: Secure token-based authentication for tool access
- **Structured Planning**: Converts email instructions into structured JSON execution plans
- **Schema Validation**: Comprehensive data validation using Pydantic-style schemas
- **Email Processing**: Handles email-based input with structured payload validation
- **Communication Tools**: Built-in email communication capabilities
- **Calendar Management**: Specialized for calendar and scheduling operations
- **Multi-Step Execution**: Sequential step execution with result tracking
- **Error Handling**: Robust error handling and recovery mechanisms
- **Docker Support**: Containerized deployment with OpenTelemetry instrumentation

## Project Structure

```
agent-core/
├── ea_multiagent.py              # Main multi-agent system implementation
├── agentcore_gateway_setup.py    # Gateway setup utilities (commented)
├── utils.py                      # Utility functions for authentication and prompts
├── schema_list.py                # Schema definitions and validation functions
├── prompts/
│   ├── planning_agent_prompt.txt     # Planning agent system prompt
│   └── requestbuilder_agent_prompt.txt # Request builder agent system prompt
├── tools/
│   └── communication_tool.json   # Local communication tool definition
├── Dockerfile                    # Container configuration
├── .env.example                  # Environment configuration template
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Prerequisites

- Python 3.13 or higher
- AWS credentials configured with Bedrock access
- Access to Amazon Bedrock services (Nova Lite model)
- OAuth credentials for MCP gateway access
- Docker (for containerized deployment)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-core
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your actual values:
# GATEWAY_URL=your_gateway_url_here
# CLIENT_ID=your_client_id_here
# CLIENT_SECRET=your_client_secret_here
# TOKEN_URL=your_token_url_here
```

4. Configure AWS credentials:
```bash
aws configure
```

## Usage

### Running the Multi-Agent System

To run the executive assistant system locally:

```bash
python ea_multiagent.py
```

The system will:
1. Fetch OAuth access token using provided credentials
2. Retrieve available tools from the MCP gateway
3. Load the planning agent system prompt
4. Start the Bedrock Agent Core App on port 8088

### Agent Invocation

The system can be invoked with an email payload containing structured email data:

```python
payload = {
    "from": "user@company.com",
    "to": ["assistant@company.com"],
    "cc": [],
    "agent_email": "assistant@company.com",
    "subject": "Schedule a 30-minute meeting with the marketing team this week",
    "body": "Please schedule a 30-minute meeting with the marketing team this week to discuss the Q4 campaign."
}

result = invoke(payload)
print(result)
```

### API Endpoint

The system exposes an entrypoint function that processes executive assistant requests:

```python
@app.entrypoint
def invoke(payload):
    """Executive Assistant Multi-Agent System entry point"""
    # Validates email payload using schema validation
    # Creates planning agent with system prompt
    # Executes three-phase workflow: Planning → Request Building → Communication
    # Returns comprehensive execution results with step-by-step tracking
```

## Configuration

### Environment Variables

The system requires the following environment variables (configured in `.env`):

```bash
# MCP Gateway Configuration
GATEWAY_URL=your_gateway_url_here
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
TOKEN_URL=your_token_url_here

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Bedrock Agent Core Configuration
BEDROCK_AGENTCORE_MEMORY_ID=test_agent_mem-wmWVwL400H
BEDROCK_AGENTCORE_MEMORY_NAME=planning_agent_memory
```

### Model Configuration

The system uses Amazon Nova Lite model by default:
```python
MODEL_ID = "us.amazon.nova-lite-v1:0"
```

Alternative models available:
- `us.amazon.nova-pro-v1:0` (Nova Pro)
- `us.anthropic.claude-3-7-sonnet-20250219-v1:0` (Claude 3.7 Sonnet)

### Bedrock Configuration

Ensure your AWS account has access to Amazon Bedrock services and the appropriate permissions are configured for the Nova models.

## Development

### Multi-Agent Workflow

The system implements a sophisticated three-phase workflow:

1. **Planning Phase**: Planning agent analyzes email requests and creates structured execution plans
2. **Request Building Phase**: Request builder agent constructs API payloads for specific tool executions
3. **Communication Phase**: Communication agent handles email communications and user interactions
4. **Tool Execution**: Executes calendar and scheduling operations via MCP tools
5. **Result Tracking**: Comprehensive tracking of step execution results and error handling

### Adding New Features

1. **New Agent Types**: Add new agent prompts in the `prompts/` directory
2. **Tool Integration**: Extend the MCP tool set via gateway configuration or add local tools in `tools/` directory
3. **Schema Extensions**: Add new data structures and validation functions in `schema_list.py`
4. **System Prompts**: Modify agent behavior by updating prompt files
5. **Dependencies**: Add new packages to `requirements.txt`

### Testing

Test the system with executive assistant email scenarios:

```python
# Test with email-based calendar management requests
test_emails = [
    {
        "from": "user@company.com",
        "to": ["assistant@company.com"],
        "cc": [],
        "agent_email": "assistant@company.com",
        "subject": "Schedule marketing team meeting",
        "body": "Please schedule a 30-minute meeting with the marketing team this week to discuss Q4 campaign."
    },
    {
        "from": "user@company.com",
        "to": ["assistant@company.com"],
        "cc": [],
        "agent_email": "assistant@company.com",
        "subject": "Check availability",
        "body": "What's my availability for tomorrow afternoon? I need to schedule a client call."
    },
    {
        "from": "user@company.com",
        "to": ["assistant@company.com"],
        "cc": [],
        "agent_email": "assistant@company.com",
        "subject": "Cancel meeting",
        "body": "Please cancel my 3 PM meeting today with the development team."
    }
]

for email in test_emails:
    result = invoke(email)
    print(f"Email Subject: {email['subject']}")
    print(f"Response: {result}\n")
```

## Dependencies

- `boto3`: AWS SDK for Python
- `strands-agents`: Core agent framework
- `strands-agents-tools`: Agent tool integrations
- `bedrock-agentcore`: Amazon Bedrock Agent Core framework
- `bedrock-agentcore-starter-toolkit`: Starter toolkit for Bedrock agents
- `requests`: HTTP library for API calls and OAuth
- `python-dotenv`: Environment variable management
- `mcp`: Model Context Protocol support
- `dataclasses`: Data structure definitions (Python 3.7+ built-in)
- `typing`: Type hints and annotations (Python 3.5+ built-in)
- `json`: JSON processing (Python built-in)
- `logging`: Application logging (Python built-in)

## AWS Services Used

- **Amazon Bedrock**: Core AI/ML service with Nova Lite model
- **AWS IAM**: Identity and access management
- **AWS Lambda**: Serverless compute (if deployed)
- **OpenTelemetry**: Observability and monitoring

## Deployment

### Local Development
```bash
python ea_multiagent.py
```

### Docker Deployment
Build and run the containerized version:

```bash
# Build the Docker image
docker build -t executive-assistant-agent .

# Run the container
docker run -p 8088:8088 \
  -e GATEWAY_URL=your_gateway_url \
  -e CLIENT_ID=your_client_id \
  -e CLIENT_SECRET=your_client_secret \
  -e TOKEN_URL=your_token_url \
  executive-assistant-agent
```

### AWS Lambda Deployment
The system can be packaged and deployed to AWS Lambda for serverless execution with OpenTelemetry instrumentation.

### Container Features
- **Multi-stage build** with UV package manager
- **OpenTelemetry instrumentation** for observability
- **Non-root user** for security
- **Python 3.13** runtime
- **Memory management** with Bedrock Agent Core

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the GNU AFFERO GENERAL PUBLIC LICENSE - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check AWS Bedrock documentation
- Review the Strands framework documentation

## Roadmap

### Completed Features ✅
- [x] Multi-agent system architecture (three-agent system)
- [x] Planning agent with structured intent generation
- [x] Request builder agent for API payload construction
- [x] Communication agent for email interactions
- [x] MCP tool integration
- [x] OAuth authentication
- [x] Docker containerization
- [x] OpenTelemetry instrumentation
- [x] Schema validation and data structures
- [x] Email-based input processing
- [x] Multi-step execution workflow
- [x] Comprehensive error handling and result tracking
- [x] Local tool integration (communication tools)

### In Progress 🚧
- [ ] Enhanced communication agent implementation
- [ ] Full tool execution integration
- [ ] Advanced error recovery mechanisms

### Planned Features 📋
- [ ] Conversation memory and context management
- [ ] Comprehensive testing suite
- [ ] Performance monitoring and optimization
- [ ] Additional calendar and scheduling tools
- [ ] Advanced email parsing and processing
- [ ] Multi-language support
- [ ] Integration with additional calendar providers
- [ ] Real-time notification system
- [ ] User preference learning and adaptation
