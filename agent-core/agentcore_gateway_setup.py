# # Import SDK and set up client
# import json
# from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
# client = GatewayClient(region_name='us-east-1')

# # Retrieve the authorization configuration from the create response. When you create the gateway, specify it in the authorizer_config field
# cognito_result = client.create_oauth_authorizer_with_cognito("emailagent-gateway-1-cognito")
# authorizer_configuration = cognito_result["authorizer_config"]
# print(str(authorizer_configuration))


# # create the gateway.
# gateway = client.create_mcp_gateway(
#   name="emailagent-gateway-1", # the name of the Gateway - if you don't set one, one will be generated.
#   role_arn=None, # the role arn that the Gateway will use - if you don't set one, one will be created.
#   authorizer_config=authorizer_configuration, # Variable from inbound authorization setup steps. Contains the OAuth authorizer details for authorizing callers to your Gateway (MCP only supports OAuth).
#   enable_semantic_search=True # enable semantic search.
# )

# try:
#     print(str(gateway))
# except Exception as e:
#     print(str(e))
