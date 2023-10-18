import openai
import os
from time import sleep,time


def chatbot(conversation, model="gpt-4-0613", temperature=0):
    max_retry = 3
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=conversation, temperature=temperature)
            text = response['choices'][0]['message']['content']
            return text, response['usage']['total_tokens']
        except Exception as oops:
            print(f'\n\nError communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                a = conversation.pop(0)
                print('\n\n DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                print(f"\n\nExiting due to excessive errors in API: {oops}")
                exit(1)
            print(f'\n\nRetrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)


def stream_chunks(conversation):
    # record the time before the request is sent
    start_time = time()

    # send a ChatCompletion request with the conversation history
    response = openai.ChatCompletion.create(
        model='gpt-4-0613',
        messages=conversation,
        temperature=0.5,
        stream=True  # we set stream=True
    )

    for chunk in response:
        chunk_time = time() - start_time  # calculate the time delay of the chunk
        # Check if the chunk contains a 'role' field and if it's 'assistant'
        if chunk['choices'][0]['delta']:#and chunk['choices'][0]['delta']['role'] == 'assistant':
            chunk_message = chunk['choices'][0]['delta']  # extract the message
            yield chunk_message