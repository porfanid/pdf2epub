Anthropic

LiteLLM supports all anthropic models.

    claude-3.5 (claude-3-5-sonnet-20240620)
    claude-3 (claude-3-haiku-20240307, claude-3-opus-20240229, claude-3-sonnet-20240229)
    claude-2
    claude-2.1
    claude-instant-1.2

info

Anthropic API fails requests when max_tokens are not passed. Due to this litellm passes max_tokens=4096 when no max_tokens are passed.
API Keys

import os

os.environ["ANTHROPIC_API_KEY"] = "your-api-key"
# os.environ["ANTHROPIC_API_BASE"] = "" # [OPTIONAL] or 'ANTHROPIC_BASE_URL'

Usage

import os
from litellm import completion

# set env - [OPTIONAL] replace with your anthropic key
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

messages = [{"role": "user", "content": "Hey! how's it going?"}]
response = completion(model="claude-3-opus-20240229", messages=messages)
print(response)

Usage - Streaming

Just set stream=True when calling completion.

import os
from litellm import completion

# set env
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

messages = [{"role": "user", "content": "Hey! how's it going?"}]
response = completion(model="claude-3-opus-20240229", messages=messages, stream=True)
for chunk in response:
    print(chunk["choices"][0]["delta"]["content"])  # same as openai format

Usage with LiteLLM Proxy

Here's how to call Anthropic with the LiteLLM Proxy Server
1. Save key in your environment

export ANTHROPIC_API_KEY="your-api-key"

2. Start the proxy

    config.yaml
    config - default all Anthropic Model
    cli

model_list:
  - model_name: claude-3 ### RECEIVED MODEL NAME ###
    litellm_params: # all params accepted by litellm.completion() - https://docs.litellm.ai/docs/completion/input
      model: claude-3-opus-20240229 ### MODEL NAME sent to `litellm.completion()` ###
      api_key: "os.environ/ANTHROPIC_API_KEY" # does os.getenv("AZURE_API_KEY_EU")

litellm --config /path/to/config.yaml

3. Test it

    Curl Request
    OpenAI v1.0.0+
    Langchain

curl --location 'http://0.0.0.0:4000/chat/completions' \
--header 'Content-Type: application/json' \
--data ' {
      "model": "claude-3",
      "messages": [
        {
          "role": "user",
          "content": "what llm are you"
        }
      ]
    }
'

Supported Models

Model Name 👉 Human-friendly name.
Function Call 👉 How to call the model in LiteLLM.
Model Name	Function Call
claude-3-5-sonnet	completion('claude-3-5-sonnet-20240620', messages)
claude-3-haiku	completion('claude-3-haiku-20240307', messages)
claude-3-opus	completion('claude-3-opus-20240229', messages)
claude-3-5-sonnet-20240620	completion('claude-3-5-sonnet-20240620', messages)
claude-3-sonnet	completion('claude-3-sonnet-20240229', messages)
claude-2.1	completion('claude-2.1', messages)
claude-2	completion('claude-2', messages)
claude-instant-1.2	completion('claude-instant-1.2', messages)
claude-instant-1	completion('claude-instant-1', messages)
Prompt Caching

Use Anthropic Prompt Caching

Relevant Anthropic API Docs
note

Here's what a sample Raw Request from LiteLLM for Anthropic Context Caching looks like:

POST Request Sent from LiteLLM:
curl -X POST \
https://api.anthropic.com/v1/messages \
-H 'accept: application/json' -H 'anthropic-version: 2023-06-01' -H 'content-type: application/json' -H 'x-api-key: sk-...' -H 'anthropic-beta: prompt-caching-2024-07-31' \
-d '{'model': 'claude-3-5-sonnet-20240620', [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What are the key terms and conditions in this agreement?",
          "cache_control": {
            "type": "ephemeral"
          }
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "Certainly! The key terms and conditions are the following: the contract is 1 year long for $10/mo"
        }
      ]
    }
  ],
  "temperature": 0.2,
  "max_tokens": 10
}'

Caching - Large Context Caching

This example demonstrates basic Prompt Caching usage, caching the full text of the legal agreement as a prefix while keeping the user instruction uncached.

    LiteLLM SDK
    LiteLLM Proxy

response = await litellm.acompletion(
    model="anthropic/claude-3-5-sonnet-20240620",
    messages=[
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an AI assistant tasked with analyzing legal documents.",
                },
                {
                    "type": "text",
                    "text": "Here is the full text of a complex legal agreement",
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        },
        {
            "role": "user",
            "content": "what are the key terms and conditions in this agreement?",
        },
    ]
)

Caching - Tools definitions

In this example, we demonstrate caching tool definitions.

The cache_control parameter is placed on the final tool

    LiteLLM SDK
    LiteLLM Proxy

import litellm

response = await litellm.acompletion(
    model="anthropic/claude-3-5-sonnet-20240620",
    messages = [{"role": "user", "content": "What's the weather like in Boston today?"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
                "cache_control": {"type": "ephemeral"}
            },
        }
    ]
)

Caching - Continuing Multi-Turn Convo

In this example, we demonstrate how to use Prompt Caching in a multi-turn conversation.

The cache_control parameter is placed on the system message to designate it as part of the static prefix.

The conversation history (previous messages) is included in the messages array. The final turn is marked with cache-control, for continuing in followups. The second-to-last user message is marked for caching with the cache_control parameter, so that this checkpoint can read from the previous cache.

    LiteLLM SDK
    LiteLLM Proxy

import litellm

response = await litellm.acompletion(
    model="anthropic/claude-3-5-sonnet-20240620",
    messages=[
        # System Message
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "Here is the full text of a complex legal agreement"
                    * 400,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        },
        # marked for caching with the cache_control parameter, so that this checkpoint can read from the previous cache.
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What are the key terms and conditions in this agreement?",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Certainly! the key terms and conditions are the following: the contract is 1 year long for $10/mo",
        },
        # The final turn is marked with cache-control, for continuing in followups.
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What are the key terms and conditions in this agreement?",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        },
    ]
)

Function/Tool Calling
info

LiteLLM now uses Anthropic's 'tool' param 🎉 (v1.34.29+)

from litellm import completion

# set env
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]
messages = [{"role": "user", "content": "What's the weather like in Boston today?"}]

response = completion(
    model="anthropic/claude-3-opus-20240229",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)
# Add any assertions, here to check response args
print(response)
assert isinstance(response.choices[0].message.tool_calls[0].function.name, str)
assert isinstance(
    response.choices[0].message.tool_calls[0].function.arguments, str
)

Forcing Anthropic Tool Use

If you want Claude to use a specific tool to answer the user’s question

You can do this by specifying the tool in the tool_choice field like so:

response = completion(
    model="anthropic/claude-3-opus-20240229",
    messages=messages,
    tools=tools,
    tool_choice={"type": "tool", "name": "get_weather"},
)

Parallel Function Calling

Here's how to pass the result of a function call back to an anthropic model:

from litellm import completion
import os 

os.environ["ANTHROPIC_API_KEY"] = "sk-ant.."


litellm.set_verbose = True

### 1ST FUNCTION CALL ###
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]
messages = [
    {
        "role": "user",
        "content": "What's the weather like in Boston today in Fahrenheit?",
    }
]
try:
    # test without max tokens
    response = completion(
        model="anthropic/claude-3-opus-20240229",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    # Add any assertions, here to check response args
    print(response)
    assert isinstance(response.choices[0].message.tool_calls[0].function.name, str)
    assert isinstance(
        response.choices[0].message.tool_calls[0].function.arguments, str
    )

    messages.append(
        response.choices[0].message.model_dump()
    )  # Add assistant tool invokes
    tool_result = (
        '{"location": "Boston", "temperature": "72", "unit": "fahrenheit"}'
    )
    # Add user submitted tool results in the OpenAI format
    messages.append(
        {
            "tool_call_id": response.choices[0].message.tool_calls[0].id,
            "role": "tool",
            "name": response.choices[0].message.tool_calls[0].function.name,
            "content": tool_result,
        }
    )
    ### 2ND FUNCTION CALL ###
    # In the second response, Claude should deduce answer from tool results
    second_response = completion(
        model="anthropic/claude-3-opus-20240229",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    print(second_response)
except Exception as e:
    print(f"An error occurred - {str(e)}")

s/o @Shekhar Patnaik for requesting this!
Computer Tools

from litellm import completion

tools = [
    {
        "type": "computer_20241022",
        "function": {
            "name": "computer",
            "parameters": {
                "display_height_px": 100,
                "display_width_px": 100,
                "display_number": 1,
            },
        },
    }
]
model = "claude-3-5-sonnet-20241022"
messages = [{"role": "user", "content": "Save a picture of a cat to my desktop."}]

resp = completion(
    model=model,
    messages=messages,
    tools=tools,
    # headers={"anthropic-beta": "computer-use-2024-10-22"},
)

print(resp)

Usage - Vision

from litellm import completion

# set env
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

def encode_image(image_path):
    import base64

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


image_path = "../proxy/cached_logo.jpg"
# Getting the base64 string
base64_image = encode_image(image_path)
resp = litellm.completion(
    model="anthropic/claude-3-opus-20240229",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Whats in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64," + base64_image
                    },
                },
            ],
        }
    ],
)
print(f"\nResponse: {resp}")

Passing Extra Headers to Anthropic API

Pass extra_headers: dict to litellm.completion

from litellm import completion
messages = [{"role": "user", "content": "What is Anthropic?"}]
response = completion(
    model="claude-3-5-sonnet-20240620", 
    messages=messages, 
    extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"}
)

Usage - "Assistant Pre-fill"

You can "put words in Claude's mouth" by including an assistant role message as the last item in the messages array.

    [!IMPORTANT] The returned completion will not include your "pre-fill" text, since it is part of the prompt itself. Make sure to prefix Claude's completion with your pre-fill.

import os
from litellm import completion

# set env - [OPTIONAL] replace with your anthropic key
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

messages = [
    {"role": "user", "content": "How do you say 'Hello' in German? Return your answer as a JSON object, like this:\n\n{ \"Hello\": \"Hallo\" }"},
    {"role": "assistant", "content": "{"},
]
response = completion(model="claude-2.1", messages=messages)
print(response)

Example prompt sent to Claude


Human: How do you say 'Hello' in German? Return your answer as a JSON object, like this:

{ "Hello": "Hallo" }

Assistant: {

Usage - "System" messages

If you're using Anthropic's Claude 2.1, system role messages are properly formatted for you.

import os
from litellm import completion

# set env - [OPTIONAL] replace with your anthropic key
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

messages = [
    {"role": "system", "content": "You are a snarky assistant."},
    {"role": "user", "content": "How do I boil water?"},
]
response = completion(model="claude-2.1", messages=messages)

Example prompt sent to Claude

You are a snarky assistant.

Human: How do I boil water?

Assistant: