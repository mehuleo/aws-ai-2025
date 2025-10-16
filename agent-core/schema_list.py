"""
Schema definitions for the multi-agent system.
Contains all the data structures used in the planning and execution workflow.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# ============================================================================
# EMAIL PAYLOAD SCHEMA
# ============================================================================

@dataclass
class EmailPayload:
    """Schema for the incoming email payload."""
    from_email: str
    to: List[str]
    cc: List[str]
    agent_email: str
    subject: str
    body: str
    today: Optional[str] = None # current date and time in ISO 8601 format

# ============================================================================
# PLANNING AGENT SCHEMAS
# ============================================================================

@dataclass
class PlanStep:
    """Schema for individual steps in the execution plan."""
    executionOrder: int
    intent: str  # 'tool_execution', 'communicate', 'replan'
    stepOutcome: str
    context: str
    toolName: Optional[str] = None  # Only if intent='tool_execution'

@dataclass
class ExecutionPlan:
    """Schema for the complete execution plan from planning agent."""
    goal: str
    deliverable: str
    steps: List[PlanStep]

# ============================================================================
# REQUEST BUILDER SCHEMAS
# ============================================================================

@dataclass
class CurrentStep:
    """Schema for current step being processed by request builder."""
    executionOrder: int
    stepOutcome: str
    context: str
    toolName: str

@dataclass
class StepExecutionResult:
    """Schema for results from executed steps."""
    status: str  # 'success', 'error'
    executionOrder: int
    stepOutcome: str
    context: str
    toolName: str
    toolCalled: bool
    toolResponse: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class RequestBuilderInput:
    """Schema for input to request builder agent."""
    currentStep: CurrentStep
    previousExecutionResults: List[StepExecutionResult]
    originalEmail: EmailPayload

@dataclass
class RequestBuilderResponse:
    """Schema for response from request builder agent."""
    toolName: str
    status: str  # 'success', 'error', 'needs_clarification'
    apiPayload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class CommunicationInput:
    """Schema for input to communication agent."""
    currentStep: CurrentStep
    previousExecutionResults: List[StepExecutionResult]
    originalEmail: EmailPayload

@dataclass
class CommunicationResponse:
    """Schema for response from communication agent."""
    toolName: str
    status: str  # 'success', 'error', 'needs_clarification'
    apiPayload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_email_payload(payload: Dict[str, Any]) -> EmailPayload:
    """Validate and convert email payload to EmailPayload object."""
    required_fields = ['from', 'to', 'cc', 'agent_email', 'subject', 'body']
    
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
    
    return EmailPayload(
        from_email=payload['from'],
        to=payload['to'] if isinstance(payload['to'], list) else [payload['to']],
        cc=payload['cc'] if isinstance(payload['cc'], list) else [payload['cc']],
        agent_email=payload['agent_email'],
        subject=payload['subject'],
        body=payload['body']
    )

def validate_execution_plan(plan_data: Dict[str, Any]) -> ExecutionPlan:
    """Validate and convert plan data to ExecutionPlan object."""
    if 'goal' not in plan_data:
        raise ValueError("Missing required field: goal")
    if 'deliverable' not in plan_data:
        raise ValueError("Missing required field: deliverable")
    if 'steps' not in plan_data or not isinstance(plan_data['steps'], list):
        raise ValueError("Missing or invalid field: steps")
    
    steps = []
    for i, step_data in enumerate(plan_data['steps']):
        required_step_fields = ['executionOrder', 'intent', 'stepOutcome', 'context']
        for field in required_step_fields:
            if field not in step_data:
                raise ValueError(f"Missing required field in step {i}: {field}")
        
        if step_data['intent'] == 'tool_execution' and 'toolName' not in step_data:
            raise ValueError(f"Missing toolName for tool_execution step {i}")
        
        steps.append(PlanStep(
            executionOrder=step_data['executionOrder'],
            intent=step_data['intent'],
            stepOutcome=step_data['stepOutcome'],
            context=step_data['context'],
            toolName=step_data.get('toolName')
        ))
    
    return ExecutionPlan(
        goal=plan_data['goal'],
        deliverable=plan_data['deliverable'],
        steps=steps
    )

def validate_request_builder_response(response_data: Dict[str, Any]) -> RequestBuilderResponse:
    """Validate and convert request builder response to RequestBuilderResponse object."""
    required_fields = ['toolName', 'status']
    for field in required_fields:
        if field not in response_data:
            raise ValueError(f"Missing required field: {field}")
    
    if response_data['status'] == 'error' and 'error' not in response_data:
        raise ValueError("Error status requires error message")
    
    return RequestBuilderResponse(
        toolName=response_data['toolName'],
        status=response_data['status'],
        apiPayload=response_data.get('apiPayload'),
        error=response_data.get('error')
    )

def validate_communication_response(response_data: Dict[str, Any]) -> CommunicationResponse:
    """Validate and convert communication response to CommunicationResponse object."""
    required_fields = ['toolName', 'status']
    for field in required_fields:
        if field not in response_data:
            raise ValueError(f"Missing required field: {field}")
    
    if response_data['status'] == 'error' and 'error' not in response_data:
        raise ValueError("Error status requires error message")
    
    return CommunicationResponse(
        toolName=response_data['toolName'],
        status=response_data['status'],
        apiPayload=response_data.get('apiPayload'),
        error=response_data.get('error')
    )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_step_execution_result(
    step: PlanStep,
    status: str,
    tool_response: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> StepExecutionResult:
    """Create a StepExecutionResult from a PlanStep and execution outcome."""
    return StepExecutionResult(
        status=status,
        executionOrder=step.executionOrder,
        stepOutcome=step.stepOutcome,
        context=step.context,
        toolName=step.toolName or "",
        toolCalled=status == 'success' and step.intent == 'tool_execution',
        toolResponse=tool_response,
        error=error
    )

def create_current_step(step: PlanStep) -> CurrentStep:
    """Create a CurrentStep from a PlanStep."""
    if step.intent not in ['tool_execution', 'communicate'] or not step.toolName:
        raise ValueError("CurrentStep can only be created from tool_execution or communicate steps with toolName")
    
    return CurrentStep(
        executionOrder=step.executionOrder,
        stepOutcome=step.stepOutcome,
        context=step.context,
        toolName=step.toolName
    )
