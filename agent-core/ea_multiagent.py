import os
import json
import boto3
from dotenv import load_dotenv
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from utils import (
    fetch_access_token, 
    update_tool_set_in_sync, 
    call_tool_set_in_sync,
    load_system_prompt, 
    load_local_tools,
    clean_agent_json_response,
    AgentName
)
from schema_list import (
    validate_email_payload,
    validate_execution_plan,
    validate_request_builder_response,
    validate_communication_response,
    create_step_execution_result,
    create_current_step,
    EmailPayload,
    ExecutionPlan,
    PlanStep,
    StepExecutionResult,
    CurrentStep,
    RequestBuilderInput,
    RequestBuilderResponse,
    CommunicationInput,
    CommunicationResponse
)

# Load environment variables
load_dotenv()

# Configuration
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
TOKEN_URL = os.getenv("TOKEN_URL", "")
GATEWAY_URL = os.getenv("GATEWAY_URL", "")
MODEL_ID = "us.amazon.nova-lite-v1:0"
# MODEL_ID = "us.amazon.nova-pro-v1:0"

# Global state
ACCESS_TOKEN = None
TOOL_SET = []
app = BedrockAgentCoreApp()

# Logging configuration removed - using print statements instead

# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

def create_planning_agent() -> Agent:
    """Create and return a planning agent with system prompt."""
    print("Creating planning agent...")
    system_prompt = load_system_prompt(AgentName.PLANNER, TOOL_SET)
    return Agent(
        model=MODEL_ID,
        system_prompt=system_prompt,
        callback_handler=None
    )

def create_request_builder_agent() -> Agent:
    """Create and return a request builder agent with system prompt."""
    print("Creating request builder agent...")
    system_prompt = load_system_prompt(AgentName.REQUEST_BUILDER, TOOL_SET)
    return Agent(
        model=MODEL_ID,
        system_prompt=system_prompt,
        callback_handler=None
    )

def create_communication_agent() -> Agent:
    """Create and return a communication agent with system prompt."""
    print("Creating communication agent...")
    communication_tools = load_local_tools("communication_tools")
    system_prompt = load_system_prompt(AgentName.REQUEST_BUILDER, communication_tools)
    return Agent(
        model=MODEL_ID,
        system_prompt=system_prompt,
        callback_handler=None
    )

# ============================================================================
# MULTI-AGENT WORKFLOW FUNCTIONS
# ============================================================================

def execute_planning_phase(email_data: EmailPayload) -> ExecutionPlan:
    """Execute Step 1: Planning agent to create execution plan."""
    print("Starting planning phase...")
    
    try:
        # Create planning agent
        planning_agent = create_planning_agent()
        
        # Prepare email data for planning (remove sensitive info)
        planning_input = {
            "from": email_data.from_email,
            "to": email_data.to,
            "cc": email_data.cc,
            "agent_email": email_data.agent_email,
            "subject": email_data.subject,
            "body": email_data.body
        }
        
        print(f"Planning agent input: {json.dumps(planning_input, indent=2)}")
        
        # Run planning agent
        planning_response = planning_agent(json.dumps(planning_input))
        print(f"Planning agent response: {planning_response}")
        
        # Parse JSON response
        try:
            # Clean response using utility function (handles AgentResult objects)
            cleaned_response = clean_agent_json_response(planning_response)
            if isinstance(cleaned_response, str):
                plan_data = json.loads(cleaned_response)
            else:
                plan_data = cleaned_response
            print(f"Parsed plan data: {json.dumps(plan_data, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse planning agent response as JSON: {e}")
            print(f"Raw response: {planning_response}")
            print(f"Cleaned response: {cleaned_response}")
            raise ValueError(f"Planning agent returned invalid JSON: {e}")
        
        # Validate and convert to ExecutionPlan
        execution_plan = validate_execution_plan(plan_data)
        print(f"Validated execution plan with {len(execution_plan.steps)} steps")
        
        return execution_plan
        
    except Exception as e:
        print(f"Planning phase failed: {e}")
        raise

def execute_request_builder_phase(
    current_step: CurrentStep,
    previous_results: list[StepExecutionResult],
    original_email: EmailPayload
) -> RequestBuilderResponse:
    """Execute Step 2: Request builder agent to create API payload."""
    print(f"Starting request builder phase for step {current_step.executionOrder}...")
    
    try:
        # Create request builder agent
        request_builder_agent = create_request_builder_agent()
        
        # Prepare input for request builder
        request_builder_input = RequestBuilderInput(
            currentStep=current_step,
            previousExecutionResults=previous_results,
            originalEmail=original_email
        )
        
        # Convert to JSON for agent
        input_data = {
            "currentStep": {
                "executionOrder": current_step.executionOrder,
                "stepOutcome": current_step.stepOutcome,
                "context": current_step.context,
                "toolName": current_step.toolName
            },
            "previousExecutionResults": [
                {
                    "status": result.status,
                    "executionOrder": result.executionOrder,
                    "stepOutcome": result.stepOutcome,
                    "context": result.context,
                    "toolName": result.toolName,
                    "toolCalled": result.toolCalled,
                    "toolResponse": result.toolResponse,
                    "error": result.error
                }
                for result in previous_results
            ],
            "originalEmail": {
                "from": original_email.from_email,
                "to": original_email.to,
                "cc": original_email.cc,
                "agent_email": original_email.agent_email,
                "subject": original_email.subject,
                "body": original_email.body
            }
        }
        
        print(f"Request builder input: {json.dumps(input_data, indent=2)}")
        
        # Run request builder agent
        request_builder_response = request_builder_agent(json.dumps(input_data))
        print(f"Request builder response: {request_builder_response}")
        
        # Parse JSON response
        try:
            # Clean response using utility function (handles AgentResult objects)
            cleaned_response = clean_agent_json_response(request_builder_response)
            
            response_data = json.loads(cleaned_response)
            print(f"Parsed request builder data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse request builder response as JSON: {e}")
            print(f"Raw response: {request_builder_response}")
            print(f"Cleaned response: {cleaned_response}")
            raise ValueError(f"Request builder agent returned invalid JSON: {e}")
        
        # Validate and convert to RequestBuilderResponse
        builder_response = validate_request_builder_response(response_data)
        print(f"Validated request builder response: {builder_response.status}")
        
        return builder_response
        
    except Exception as e:
        print(f"Request builder phase failed: {e}")
        raise

def execute_communication_phase(
    current_step: CurrentStep,
    previous_results: list[StepExecutionResult],
    original_email: EmailPayload
) -> CommunicationResponse:
    """Execute communication phase: Communication agent to create API payload."""
    print(f"Starting communication phase for step {current_step.executionOrder}...")
    
    try:
        # Create communication agent
        communication_agent = create_communication_agent()
        
        # Prepare input for communication agent
        communication_input = CommunicationInput(
            currentStep=current_step,
            previousExecutionResults=previous_results,
            originalEmail=original_email
        )
        
        # Convert to JSON for agent
        input_data = {
            "currentStep": {
                "executionOrder": current_step.executionOrder,
                "stepOutcome": current_step.stepOutcome,
                "context": current_step.context,
                "toolName": current_step.toolName
            },
            "previousExecutionResults": [
                {
                    "status": result.status,
                    "executionOrder": result.executionOrder,
                    "stepOutcome": result.stepOutcome,
                    "context": result.context,
                    "toolName": result.toolName,
                    "toolCalled": result.toolCalled,
                    "toolResponse": result.toolResponse,
                    "error": result.error
                }
                for result in previous_results
            ],
            "originalEmail": {
                "from": original_email.from_email,
                "to": original_email.to,
                "cc": original_email.cc,
                "agent_email": original_email.agent_email,
                "subject": original_email.subject,
                "body": original_email.body
            }
        }
        
        print(f"Communication agent input: {json.dumps(input_data, indent=2)}")
        
        # Run communication agent
        communication_response = communication_agent(json.dumps(input_data))
        print(f"Communication agent response: {communication_response}")
        
        # Parse JSON response
        try:
            # Clean response using utility function (handles AgentResult objects)
            cleaned_response = clean_agent_json_response(communication_response)
            
            response_data = json.loads(cleaned_response)
            print(f"Parsed communication data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse communication response as JSON: {e}")
            print(f"Raw response: {communication_response}")
            print(f"Cleaned response: {cleaned_response}")
            raise ValueError(f"Communication agent returned invalid JSON: {e}")
        
        # Validate and convert to CommunicationResponse
        comm_response = validate_communication_response(response_data)
        print(f"Validated communication response: {comm_response.status}")
        
        return comm_response
        
    except Exception as e:
        print(f"Communication phase failed: {e}")
        raise

def execute_tool_call(tool_name: str, api_payload: dict, agent_email: str) -> dict:
    """Execute a tool call using the MCP protocol."""
    print(f"Executing tool call: {tool_name}")
    print(f"Tool payload: {json.dumps(api_payload, indent=2)}")
    
    try:
        result = call_tool_set_in_sync(GATEWAY_URL, ACCESS_TOKEN, tool_name, api_payload, agent_email)
        print(f"Tool call successful: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        print(f"Tool call failed: {e}")
        raise

def send_ses_email(api_payload: dict) -> dict:
    """Send an email using AWS SES based on the API payload."""
    print("Sending email via SES...")
    
    try:
        # Initialize SES client
        ses_client = boto3.client('ses', region_name='us-east-1')
        
        # Validate API payload
        if not api_payload:
            raise ValueError("No API payload provided")
        
        # Validate required fields
        required_fields = ['to', 'body', 'from', 'subject']
        for field in required_fields:
            if field not in api_payload:
                raise ValueError(f"Missing required field in email payload: {field}")
        
        # Extract email components
        to_addresses = api_payload.get('to', [])
        cc_addresses = api_payload.get('cc', [])
        from_addresses = api_payload.get('from', '')
        subject = api_payload.get('subject', '')
        body = api_payload.get('body', '')
        
        # Prepare destination
        destination = {
            'ToAddresses': to_addresses
        }
        if cc_addresses:
            destination['CcAddresses'] = cc_addresses
        
        # Create email message
        message = {
            'Subject': {
                'Data': subject,  # Default subject, could be enhanced
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body,
                    'Charset': 'UTF-8'
                }
            }
        }
        
        # Send email
        response = ses_client.send_email(
            Source=from_addresses,
            Destination=destination,
            Message=message
        )
        
        print(f"Email sent successfully. MessageId: {response['MessageId']}")
        
        return {
            'status': 'success',
            'messageId': response['MessageId'],
            'message': 'Email sent successfully'
        }
        
    except Exception as e:
        error_msg = f"Failed to send email via SES: {str(e)}"
        print(error_msg)
        return {
            'status': 'error',
            'error': error_msg
        }

def execute_step(
    step: PlanStep,
    previous_results: list[StepExecutionResult],
    original_email: EmailPayload
) -> StepExecutionResult:
    """Execute a single step from the execution plan."""
    print(f"Executing step {step.executionOrder}: {step.intent}")
    
    try:
        if step.intent == 'tool_execution':
            print("Tool execution step encountered")
            # Create current step for request builder
            current_step = create_current_step(step)
            
            # Get API payload from request builder
            builder_response = execute_request_builder_phase(
                current_step, previous_results, original_email
            )
            
            if builder_response.status == 'error':
                return create_step_execution_result(
                    step, 'error', error=builder_response.error
                )
            
            if builder_response.status == 'needs_clarification':
                return create_step_execution_result(
                    step, 'error', error="Request builder needs clarification"
                )
            
            # Execute tool call
            tool_response = execute_tool_call(step.toolName, builder_response.apiPayload, original_email.agent_email)
            
            return create_step_execution_result(
                step, 'success', tool_response=tool_response
            )
            
        elif step.intent == 'communicate':
            print("Communicating step encountered")
            # Create current step for communication agent
            step.toolName = "communicate"
            current_step = create_current_step(step)
            
            # Get API payload from communication agent
            comm_response = execute_communication_phase(
                current_step, previous_results, original_email
            )
            
            if comm_response.status == 'error':
                return create_step_execution_result(
                    step, 'error', error=comm_response.error
                )
            
            if comm_response.status == 'needs_clarification':
                return create_step_execution_result(
                    step, 'error', error="Communication agent needs clarification"
                )
            
            # Execute communication tool call - send SES email
            ses_payload = {
                "from": original_email.agent_email,
                "to": [original_email.from_email],
                "cc": comm_response.apiPayload.get('cc', []),
                "subject": f"Re: {original_email.subject}" if not original_email.subject.lower().startswith("re: ") else original_email.subject,
                "body": comm_response.apiPayload.get('body', '')
            }
            print(f"SES payload: {json.dumps(ses_payload, indent=2)}")
            tool_response = send_ses_email(ses_payload)
            
            # Check if email sending was successful
            if tool_response.get('status') == 'error':
                return create_step_execution_result(
                    step, 'error', error=tool_response.get('error', 'Failed to send email')
                )
            
            return create_step_execution_result(
                step, 'success', tool_response=tool_response
            )
            
        elif step.intent == 'replan':
            # Handle replanning if needed
            print("Replanning step encountered")
            return create_step_execution_result(
                step, 'success', tool_response={"message": "Replanning step processed"}
            )
            
        else:
            raise ValueError(f"Unknown step intent: {step.intent}")
            
    except Exception as e:
        print(f"Step execution failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return create_step_execution_result(step, 'error', error=str(e))

def execute_plan(execution_plan: ExecutionPlan, original_email: EmailPayload) -> list[StepExecutionResult]:
    """Execute the complete execution plan."""
    print(f"Starting plan execution with {len(execution_plan.steps)} steps")
    
    execution_results = []
    
    for step in execution_plan.steps:
        print(f"Processing step {step.executionOrder}: {step.stepOutcome}")
        
        # Execute the step
        result = execute_step(step, execution_results, original_email)
        execution_results.append(result)
        
        # Log step result
        print(f"Step {step.executionOrder} completed with status: {result.status}")
        if result.error:
            print(f"Step {step.executionOrder} error: {result.error}")
    
    print(f"Plan execution completed. {len(execution_results)} steps processed.")
    return execution_results

# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

@app.entrypoint
def invoke(payload):
    """Main entry point for processing email requests."""
    try:
        print("=== Multi-Agent System Started ===")
        print(f"Received payload: {json.dumps(payload, indent=2)}")
        
        # Validate input
        if not isinstance(payload, dict):
            print("Invalid payload format. Expected a dictionary.")
            return {"error": "Invalid payload format. Expected a dictionary."}
        
        # Validate and parse email payload
        try:
            email_data = validate_email_payload(payload)
            print(f"Validated email payload from: {email_data.from_email}")
        except ValueError as e:
            print(f"Email payload validation failed: {e}")
            return {"error": f"Email payload validation failed: {e}"}
        
        # Step 1: Execute planning phase
        try:
            execution_plan = execute_planning_phase(email_data)
            print(f"Planning phase completed. Goal: {execution_plan.goal}")
        except Exception as e:
            import traceback
            print(f"Planning phase failed: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return {"error": f"Planning phase failed: {e}"}
        
        # Step 2 & 3: Execute the plan
        try:
            execution_results = execute_plan(execution_plan, email_data)
            
            # Count successful vs failed steps
            successful_steps = sum(1 for result in execution_results if result.status == 'success')
            failed_steps = len(execution_results) - successful_steps
            
            print(f"Execution completed. {successful_steps} successful, {failed_steps} failed steps.")
            
            # Return comprehensive results
            return {
                "status": "completed",
                "goal": execution_plan.goal,
                "deliverable": execution_plan.deliverable,
                "total_steps": len(execution_results),
                "successful_steps": successful_steps,
                "failed_steps": failed_steps,
                "execution_results": [
                    {
                        "executionOrder": result.executionOrder,
                        "status": result.status,
                        "stepOutcome": result.stepOutcome,
                        "toolName": result.toolName,
                        "error": result.error,
                        "toolResponse": result.toolResponse
                    }
                    for result in execution_results
                ]
            }
            
        except Exception as e:
            print(f"Plan execution failed: {e}")
            return {"error": f"Plan execution failed: {e}"}
            
    except Exception as e:
        print(f"Unexpected error in multi-agent system: {e}")
        return {"error": f"Unexpected error: {e}"}

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    try:
        print("Starting Multi-Agent Executive Assistant...")
        
        # Initialize access token and tool set
        print("Fetching access token...")
        ACCESS_TOKEN = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
        
        print("Updating tool set...")
        TOOL_SET = update_tool_set_in_sync(GATEWAY_URL, ACCESS_TOKEN)
        print(f"Loaded {len(TOOL_SET)} tools")
        
        print("Multi-Agent system initialized successfully")
        print("Starting Bedrock Agent Core App...")
        app.run()
        
    except KeyboardInterrupt:
        print("Multi-Agent system stopped gracefully")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}. Check GATEWAY_URL, CLIENT_ID, CLIENT_SECRET, TOKEN_URL")
        exit(1)