# Amazon Bedrock Agent Core

A Python-based agent core framework built on Amazon Bedrock for creating intelligent AI agents.

## Overview

This project provides a foundation for building AI agents using Amazon Bedrock's capabilities. The agent core handles the basic infrastructure for agent invocation, message processing, and response generation.

## Features

- **Bedrock Integration**: Built on Amazon Bedrock Agent Core App
- **Agent Framework**: Utilizes the Strands agent framework
- **Simple API**: Easy-to-use entrypoint for agent invocation
- **Message Processing**: Handles user prompts and generates intelligent responses

## Project Structure

```
agent-core/
├── test-agent.py          # Main agent implementation
├── README.md              # This file
└── .gitignore            # Git ignore rules
```

## Prerequisites

- Python 3.8 or higher
- AWS credentials configured
- Access to Amazon Bedrock services
- Required Python packages (see requirements below)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-core
```

2. Install dependencies:
```bash
pip install bedrock-agentcore strands
```

3. Configure AWS credentials:
```bash
aws configure
```

## Usage

### Running the Agent

To run the agent locally:

```bash
python test-agent.py
```

### Agent Invocation

The agent can be invoked with a payload containing a user prompt:

```python
payload = {
    "prompt": "Hello! How can I help you today?"
}

result = invoke(payload)
print(result["result"])
```

### API Endpoint

The agent exposes an entrypoint function that can be used as an API endpoint:

```python
@app.entrypoint
def invoke(payload):
    """Your AI agent function"""
    user_message = payload.get("prompt", "Hello! How can I help you today?")
    result = agent(user_message)
    return {"result": result.message}
```

## Configuration

### Environment Variables

Set the following environment variables for proper configuration:

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Bedrock Configuration

Ensure your AWS account has access to Amazon Bedrock services and the appropriate permissions are configured.

## Development

### Adding New Features

1. Extend the `Agent` class with additional capabilities
2. Modify the `invoke` function to handle new payload structures
3. Add new dependencies to requirements.txt

### Testing

Run the agent with different prompts to test functionality:

```python
# Test with different prompts
test_prompts = [
    "What is the weather like?",
    "Help me write an email",
    "Explain quantum computing"
]

for prompt in test_prompts:
    result = invoke({"prompt": prompt})
    print(f"Prompt: {prompt}")
    print(f"Response: {result['result']}\n")
```

## Dependencies

- `bedrock-agentcore`: Amazon Bedrock Agent Core framework
- `strands`: Agent framework for building intelligent agents

## AWS Services Used

- **Amazon Bedrock**: Core AI/ML service for agent capabilities
- **AWS IAM**: Identity and access management
- **AWS Lambda**: Serverless compute (if deployed)

## Deployment

### Local Development
```bash
python test-agent.py
```

### AWS Lambda Deployment
The agent can be packaged and deployed to AWS Lambda for serverless execution.

### Container Deployment
Build a Docker container for containerized deployment:

```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "test-agent.py"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check AWS Bedrock documentation
- Review the Strands framework documentation

## Roadmap

- [ ] Add more sophisticated agent capabilities
- [ ] Implement conversation memory
- [ ] Add support for multiple agent types
- [ ] Create deployment automation
- [ ] Add comprehensive testing suite
- [ ] Implement monitoring and logging
