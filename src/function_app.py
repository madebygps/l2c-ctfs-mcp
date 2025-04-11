import json
import logging

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

_FLAG_NUMBER_PROPERTY_NAME="flagnumber"
_FLAG_NAME_PROPERTY="flag"


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

tool_properties_verify_flag_object = [
    ToolProperty(_FLAG_NUMBER_PROPERTY_NAME, "string", "The number of the challenge"),
    ToolProperty(_FLAG_NAME_PROPERTY, "string", "The content of the flag")
]

tool_properties_verify_flag_json = json.dumps([prop.to_dict() for prop in tool_properties_verify_flag_object])

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
    toolName="verify_flag",
    description="Verify your found flag",
    toolProperties=tool_properties_verify_flag_json,
)
def verify_flag(context) -> str:
    content = json.loads(context)
    flag_number_from_args = content["arguments"][_FLAG_NUMBER_PROPERTY_NAME]
    flag_content_from_args = content["arguments"][_FLAG_NAME_PROPERTY]
    
    print(f"the content: {flag_content_from_args}")
    print(f"the number: {flag_number_from_args}")
    
    if not flag_content_from_args:
        return "No flag content provided"
    
    if not flag_number_from_args:
        return "No flag content provided"
    
    if int(flag_number_from_args) == 1 and flag_content_from_args == "hello":
        return "You got it"
    else:
        return "failed"