import os
from dotenv import load_dotenv
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from utils import fetch_access_token, update_tool_set_in_sync, load_system_prompt, get_json_keyval, AgentName

# Load environment variables
load_dotenv()

# Configuration
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
TOKEN_URL = os.getenv("TOKEN_URL", "")
GATEWAY_URL = os.getenv("GATEWAY_URL", "")
MODEL_ID = "us.amazon.nova-lite-v1:0"
# MODEL_ID = "us.amazon.nova-pro-v1:0"
# MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

# Global state
ACCESS_TOKEN = None
TOOL_SET = []
SYSTEM_PROMPT = ""
app = BedrockAgentCoreApp()

# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

@app.entrypoint
def invoke(payload):
    """Main entry point for processing user questions."""
    try:
        # Validate input
        if not isinstance(payload, dict):
            return {"error": "Invalid payload format. Expected a dictionary."}
        
        # Validate prompt
        question = payload.get("prompt", "")
        if not isinstance(question, str) or not question.strip():
            return {"error": "Invalid or empty prompt provided."}
        
        # Validate tool set auth token
        tool_set_auth_token = get_json_keyval(payload, "headers.X-Auth-Bearer")
        if not tool_set_auth_token:
            return {"error": "Tool set auth token not available. Please restart the service."}
        else:
            print(f"Tool set auth token: {tool_set_auth_token}")
        
        # Create and run agent
        agent = Agent(
            model=MODEL_ID,
            system_prompt=SYSTEM_PROMPT,
            callback_handler=None
        )
        result = agent(question)
        return result
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {e}"}

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    try:
        print("Starting Planning Agent...")
        ACCESS_TOKEN = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
        TOOL_SET = update_tool_set_in_sync(GATEWAY_URL, ACCESS_TOKEN)
        SYSTEM_PROMPT = load_system_prompt(AgentName.PLANNER, TOOL_SET)
        print("Access token fetched successfully")
        print("Starting Bedrock Agent Core App...")
        app.run(port=8088)
        
    except KeyboardInterrupt:
        print("\nPlanning Agent stopped gracefully")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}. Check GATEWAY_URL, CLIENT_ID, CLIENT_SECRET, TOKEN_URL")
        exit(1)