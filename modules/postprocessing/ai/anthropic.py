import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my_api_key",
)

message = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=4999,
    temperature=0,
    messages=[]
)
print(message.content)