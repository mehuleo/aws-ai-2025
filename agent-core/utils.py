import json
import requests
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class AgentName(Enum):
    """Enum for agent names that maps to prompt file names."""
    PLANNER = "planning_agent_prompt"
    REQUEST_BUILDER = "requestbuilder_agent_prompt"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_json_keyval(data, path, default=None):
    """
    Generic function to get nested values from a dictionary using dot notation.
    
    Args:
        data (dict): The dictionary to search in
        path (str): Dot-separated path to the nested key (e.g., "headers.X-Auth-Bearer")
        default: Default value to return if key is not found
    
    Returns:
        The value at the specified path or default if not found
    
    Examples:
        get_json_keyval(payload, "headers.X-Auth-Bearer")
        get_json_keyval(payload, "user.profile.name", "Unknown")
        get_json_keyval(payload, "config.database.host")
    """
    keys = path.split(".")
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data

def fetch_access_token(client_id, client_secret, token_url):
    """Fetch OAuth access token from the token endpoint."""
    # Validate required parameters
    if not all([token_url, client_id, client_secret]):
        raise ValueError("Missing required OAuth credentials")
    
    if not token_url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid TOKEN_URL format: {token_url}")
    
    try:
        response = requests.post(
            token_url,
            data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        response.raise_for_status()
        
        response_data = response.json()
        if 'access_token' not in response_data:
            raise KeyError("Response does not contain 'access_token' field")
        
        return response_data['access_token']
        
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Failed to fetch access token: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error while fetching access token: {e}")

def update_tool_set_in_sync(gateway_url, access_token):
    """Fetch and return the list of available tools from the gateway."""
    if access_token is None:
        raise ValueError("Access token not available. Please fetch access token first.")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "jsonrpc": "2.0",
        "id": "list-tools-request",
        "method": "tools/list"
    }
    response = requests.post(gateway_url, headers=headers, json=payload)
    response_data = response.json()

    # Extract tools from the JSON-RPC response structure
    if "result" in response_data and "tools" in response_data["result"]:
        return response_data["result"]["tools"]
    else:
        print(f"Unexpected response structure: {response_data}")
        return []

def load_system_prompt(agent_name, tool_set):
    """Load system prompt from file or return default."""
    default_prompt = "Try to answer the user's question using the tools available."
    tool_set_json_str = json.dumps(tool_set, indent=2) if tool_set else "[]"
    
    # Get the filename from the enum
    if isinstance(agent_name, AgentName):
        filename = f"{agent_name.value}.txt"
    else:
        # Fallback for string values (backward compatibility)
        filename = f"{agent_name}.txt"
    
    try:
        with open(f"prompts/{filename}", "r", encoding='utf-8') as f:
            # Read the entire file content
            prompt = f.read().strip()
            # Replace the {tool_set} placeholder with the actual tool set JSON
            prompt = prompt.replace("{tool_set}", tool_set_json_str)
            # print("System prompt:")
            # print(prompt)
            return prompt
    except FileNotFoundError:
        return default_prompt
    except Exception as e:
        print(f"Warning: Error reading system prompt file: {e}")
        return default_prompt
