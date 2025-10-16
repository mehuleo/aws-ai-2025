from datetime import datetime, timezone
import json
from time import timezone
import requests
import re
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

def clean_agent_json_response(agent_result):
    """
    Clean agent response by removing markdown code block markers and handling various edge cases.
    
    Handles cases like:
    - ```json {...} ```
    - ```json  {...} ``` (with extra spaces)
    - ```json\n{...}\n``` (with newlines)
    - ```\n{...}\n``` (without json specifier)
    - Indented JSON output
    - AgentResult objects (extracts text content)
    
    Args:
        response_text (str or AgentResult): Raw response text from agent or AgentResult object
        
    Returns:
        str: Cleaned JSON string ready for parsing
    """
    response_text = str(agent_result)
    # Handle AgentResult objects
    if hasattr(response_text, 'content'):
        response_text = response_text.content
    elif hasattr(response_text, 'text'):
        response_text = response_text.text
    elif hasattr(response_text, 'message'):
        response_text = response_text.message
    elif not isinstance(response_text, str):
        # Try to convert to string as fallback
        response_text = str(response_text).strip()
    
    if not response_text or not isinstance(response_text, str):
        return response_text
    
    # Strip leading and trailing whitespace
    cleaned = response_text
    
    # Remove markdown code block markers using regex
    # Pattern matches: ```json, ```json with spaces/newlines, or just ``` with spaces/newlines
    # at the beginning and ``` with optional spaces/newlines at the end
    
    # Remove opening markers (```json or ``` with optional spaces/newlines)
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
    
    # Remove closing markers (``` with optional spaces/newlines)
    cleaned = re.sub(r'\n?\s*```$', '', cleaned)
    
    # Strip any remaining leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

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

def call_tool_set_in_sync(gateway_url, access_token, tool_name, api_payload, agent_email):
    """Call a specific tool from the tool set using MCP protocol."""
    if access_token is None:
        raise ValueError("Access token not available. Please fetch access token first.")
    
    if not tool_name:
        raise ValueError("Tool name is required for tool execution.")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    # Always replace the auth_email with the agent_email
    api_payload["auth_email"] = agent_email
    payload = {
        "jsonrpc": "2.0",
        "id": f"call-tool-{tool_name}",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": api_payload or {}
        }
    }
    
    try:
        response = requests.post(gateway_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        
        # Extract result from the JSON-RPC response structure
        if "result" in response_data:
            # Use the new utility function to extract JSON from MCP response
            return extract_json_from_mcp_response(response_data["result"])
        elif "error" in response_data:
            error_msg = response_data["error"].get("message", "Unknown error")
            raise Exception(f"Tool call failed: {error_msg}")
        else:
            raise Exception(f"Unexpected response structure: {response_data}")
            
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Failed to call tool {tool_name}: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error while calling tool {tool_name}: {e}")

def extract_json_from_mcp_response(mcp_response):
    """
    Extract and parse JSON from MCP tool call response.
    
    Handles MCP response format like:
    {
        "isError": false,
        "content": [
            {
                "type": "text",
                "text": "{\"statusCode\":404,\"body\":{\"success\":false,\"status_code\":404,\"error\":\"User not found\"}}"
            }
        ]
    }
    
    Args:
        mcp_response (dict): The MCP tool call response
        
    Returns:
        dict: Parsed JSON data from the response, or None if extraction fails
        
    Raises:
        ValueError: If the response format is invalid or contains an error
        json.JSONDecodeError: If the extracted text is not valid JSON
    """
    if not isinstance(mcp_response, dict):
        raise ValueError("MCP response must be a dictionary")
    
    # Check if there's an error
    if mcp_response.get("isError", False):
        error_msg = "MCP response indicates an error"
        if "content" in mcp_response and mcp_response["content"]:
            # Try to extract error message from content
            for item in mcp_response["content"]:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        error_data = json.loads(item["text"])
                        if isinstance(error_data, dict) and "error" in error_data:
                            error_msg = error_data["error"]
                        break
                    except json.JSONDecodeError:
                        error_msg = item["text"]
        raise ValueError(f"MCP tool call failed: {error_msg}")
    
    # Extract content array
    content = mcp_response.get("content", [])
    if not content:
        raise ValueError("MCP response has no content")
    
    # Look for text content in the content array
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text_content = item.get("text", "")
            if text_content:
                try:
                    # Parse the JSON string
                    return json.loads(text_content)
                except json.JSONDecodeError as e:
                    raise json.JSONDecodeError(f"Failed to parse JSON from MCP response: {e}", text_content, 0)
    
    raise ValueError("No text content found in MCP response")

def load_local_tools(tool_name):
    """Load local tools from JSON file in tools/ directory."""
    try:
        with open(f"tools/{tool_name}.json", "r", encoding='utf-8') as f:
            # Load JSON content and return as list
            tools = json.load(f)
            return tools
    except FileNotFoundError:
        print(f"Warning: Tool file tools/{tool_name}.json not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in tools/{tool_name}.json: {e}")
        return []
    except Exception as e:
        print(f"Warning: Error reading tool file tools/{tool_name}.json: {e}")
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

            # Replace the {today} placeholder with the actual today's date
            # Get current UTC datetime
            utc_now = datetime.now(timezone.utc)
            # ISO 8601 format
            iso_utc = utc_now.isoformat()
            prompt = prompt.replace("{today}", iso_utc)
            
            # print("System prompt:")
            # print(prompt)
            return prompt
    except FileNotFoundError:
        return default_prompt
    except Exception as e:
        print(f"Warning: Error reading system prompt file: {e}")
        return default_prompt
