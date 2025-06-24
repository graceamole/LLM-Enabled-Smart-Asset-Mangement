import os
from  groq import Groq
client = Groq(api_key="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")
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "you are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Explain the importance of large language models",
        }
    ],
    model="llama-3.1-8b-instant",
)

print(chat_completion.choices[0].message.content)
