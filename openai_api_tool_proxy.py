import re
import string
import random
import json
import pprint
import datetime
import logging
import httpx
from ast import literal_eval
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


UPSTREAM = "http://127.0.0.1:11434"


log = logging.getLogger(__name__)
app = FastAPI()


def add_tool_calls_to_request(data):
    """ Performs prompt patching on requests.
    """
    # need to remove tool call messages as vllm validates tool_calls is a str
    for message in data.get('messages', []):
        if 'tool_calls' in message:
            del message['tool_calls']

    # if there are no tools in the request, we don't need to patch up the prompt
    if 'tools' not in data:
        return data
    # if we already patched up the prompt, we don't need to patch it again
    if any('You are a function calling AI model' in message['content'] for message in data.get('messages', []) if message.get('content')):
        return data

    # create the tool system prompt
    today = datetime.datetime.now().strftime("%A %Y-%m-%d")
    system_prompt = (
        f"The date today is {today}\n"
        + """
You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Here are the available tools:
<tools>
"""
        + str(data['tools'])
        + """

</tools> Use the following pydantic model json schema for each tool call you will make: {'title': 'FunctionCall', 'type': 'object', 'properties': {'arguments': {'title': 'Arguments', 'type': 'object'}, 'name': {'title': 'Name', 'type': 'string'}}, 'required': ['arguments', 'name']} For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:
<tool_call>
{'arguments': <args-dict>, 'name': <function-name>}
</tool_call>
"""
    )

    if 'messages' not in data:
        data['messages'] = []

    # patch up the system prompt
    for message in data.get('messages'):
        if message['role'] == 'system':
            message['content'] = message['content'] + '\n' + system_prompt
            break
    else:
        # or add it if no system prompt was present
        data['messages'].append({'role': 'system', 'content': system_prompt})

    return data


def add_tool_calls_to_response(data):
    """ Extract tool calls and add them to the response JSON.
    """
    # depending on the tool template, extract the tool calls and format them openai-compliant in the response JSON
    tool_calls = []
    tool_re = re.compile(r'<tool_call>(.*?)</tool_call>', flags=re.DOTALL)
    for choice in data.get('choices', []):
        message = choice['message']
        tools = tool_re.findall(message['content'])

        if tools:
            message['content'] = ''

        message['tool_calls'] = []
        for tool in tools:
            tool_call_json = literal_eval(tool)
            tool_call_json['arguments'] = json.dumps(tool_call_json['arguments'])
            log.debug(f'TOOL:\n{pprint.pformat(tool_call_json)}')
            message['tool_calls'].append(
                {
                    'id': f'call_{"".join(random.choice(string.digits + string.ascii_letters) for _ in range(24))}',
                    'type': 'function',
                    'function': tool_call_json,
                }
            )

    return data


@app.post("/{path:path}")
async def reverse_proxy(path: str, request: Request):
    """ Reverse proxy for OpenAI API calls.
    """
    # currently only tested against
    assert path in ('v1/chat/completions',), 'This proxy is currently only tested against the chat completions API'
    async with httpx.AsyncClient() as client:
        request_data = await request.json()
        request_data = add_tool_calls_to_request(request_data)
        log.debug(f'REQUEST:\n{pprint.pformat(request_data)}')
        proxy = await client.post(UPSTREAM + f"/{path}", json=request_data)

    response_data = proxy.json()
    response_data = add_tool_calls_to_response(response_data)
    log.debug(f'RESPONSE:\n{pprint.pformat(response_data)}')
    return JSONResponse(status_code=proxy.status_code, content=response_data)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001)
