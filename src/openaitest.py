from utils import get_openai_key
from openai import OpenAI

client = OpenAI(api_key=get_openai_key())

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "Write a one-sentence bedtime story about a unicorn."
        }
    ]
)

print(completion.choices[0].message.content)