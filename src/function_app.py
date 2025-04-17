import json
import logging
import os
import azure.functions as func
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

_SNIPPET_NAME_PROPERTY_NAME = "snippetname"
_SNIPPET_PROPERTY_NAME = "snippet"
_BLOB_PATH = "snippets/{mcptoolargs." + _SNIPPET_NAME_PROPERTY_NAME + "}.json"
_FLAG_NUMBER_PROPERTY_NAME="flagnumber"
_FLAG_NAME_PROPERTY="flag"

# Key Vault configuration
_key_vault_name = os.getenv("KEY_VAULT_NAME")
_key_vault_uri = f"https://{_key_vault_name}.vault.azure.net/"
_secret_client = None

def get_secret_client():
    """Lazy initialization of the Key Vault secret client."""
    global _secret_client
    if _secret_client is None:
        try:
            credential = DefaultAzureCredential()
            _secret_client = SecretClient(vault_url=_key_vault_uri, credential=credential)
            logging.info("Key Vault secret client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Key Vault client: {str(e)}")
            raise
    return _secret_client

class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description

    def to_dict(self):
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }

def verify_flag_with_keyvault_value(challenge_number: int, submitted_flag: str):
    try:
        secret_name = f"flag-{challenge_number}"
        client = get_secret_client()
        stored_flag = client.get_secret(secret_name).value
        return submitted_flag == stored_flag
    except Exception as e:
        logging.error(f'Error verifying flag: {str(e)}')
        return False
    
# Define the tool properties using the ToolProperty class
tool_properties_save_snippets_object = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet."),
    ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The content of the snippet."),
]

tool_properties_get_snippets_object = [ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet.")]

tool_properties_verify_flag_object = [
    ToolProperty(_FLAG_NUMBER_PROPERTY_NAME, "int", "The number of the challenge"),
    ToolProperty(_FLAG_NAME_PROPERTY, "string", "The content of the flag")
]

# Convert the tool properties to JSON
tool_properties_save_snippets_json = json.dumps([prop.to_dict() for prop in tool_properties_save_snippets_object])
tool_properties_get_snippets_json = json.dumps([prop.to_dict() for prop in tool_properties_get_snippets_object])
tool_properties_verify_flag_json = json.dumps([prop.to_dict() for prop in tool_properties_verify_flag_object])


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="hello_mcp",
    description="Hello world.",
    toolProperties="[]",
)
def hello_mcp(context) -> None:
    """
    A simple function that returns a greeting message.

    Args:
        context: The trigger context (not used in this function).

    Returns:
        str: A greeting message.
    """
    return "Hello I am MCPTool!"

@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="hello_ctf_user",
    description="Success message when lab connect to server",
    toolProperties="[]"
)
def hello_ctfuser(context) -> None:
    return "Your lab has succesfully connected to our server"


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_snippet",
    description="Retrieve a snippet by name.",
    toolProperties=tool_properties_get_snippets_json,
)
@app.generic_input_binding(arg_name="file", type="blob", connection="AzureWebJobsStorage", path=_BLOB_PATH)
def get_snippet(file: func.InputStream, context) -> str:
    """
    Retrieves a snippet by name from Azure Blob Storage.

    Args:
        file (func.InputStream): The input binding to read the snippet from Azure Blob Storage.
        context: The trigger context containing the input arguments.

    Returns:
        str: The content of the snippet or an error message.
    """
    snippet_content = file.read().decode("utf-8")
    logging.info(f"Retrieved snippet: {snippet_content}")
    return snippet_content


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="save_snippet",
    description="Save a snippet with a name.",
    toolProperties=tool_properties_save_snippets_json,
)
@app.generic_output_binding(arg_name="file", type="blob", connection="AzureWebJobsStorage", path=_BLOB_PATH)
def save_snippet(file: func.Out[str], context) -> str:
    content = json.loads(context)
    snippet_name_from_args = content["arguments"][_SNIPPET_NAME_PROPERTY_NAME]
    snippet_content_from_args = content["arguments"][_SNIPPET_PROPERTY_NAME]

    if not snippet_name_from_args:
        return "No snippet name provided"

    if not snippet_content_from_args:
        return "No snippet content provided"

    file.set(snippet_content_from_args)
    logging.info(f"Saved snippet: {snippet_content_from_args}")
    return f"Snippet '{snippet_content_from_args}' saved successfully"

@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="verify_flag",
    description="Verify your found flag",
    toolProperties=tool_properties_verify_flag_json,
)
def verify_flag(context) -> str:
    content = json.loads(context)
    flag_number_from_args = content["arguments"][_FLAG_NUMBER_PROPERTY_NAME]
    flag_content_from_args = content["arguments"][_FLAG_NAME_PROPERTY]
    
    
    if not flag_content_from_args:
        return "No flag content provided"
    
    if not flag_number_from_args:
        return "No flag number provided"
    
    try: 
        
        if verify_flag_with_keyvault_value(flag_number_from_args, flag_content_from_args):
            return "Correct!"
        else:
            return "No bueno, incorrect"
    except ValueError:
        return "Invalid challenge number format"
    except Exception as e:
        logging.error(f"Error verifying flag {str(e)}")
        return "An error occured."
    