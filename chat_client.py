import asyncio
import websockets
import sys

import ssl

cert_file = './cert/my-ca.crt'
ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cert_file)

conversation = "You are a helpful assistant.\n"

prompt_instruction = """
Welcome to FalconChat!
Instructions: 
1. Type a message then 'END' on a newline to submit a message
2. To quit, type 'exit' then 'END' on a newline
"""

extraneous_string = '\nUser'

def definitely_no_extraneous_token(resp, extraneous):
    return extraneous not in resp and not any(resp.endswith(extraneous[:i]) for i in range(1, len(extraneous) + 1))

def definitely_has_extraneous_token(resp, extraneous):
    return extraneous in resp

def remove_all_traces_extraneous_token(resp, extraneous):
    resp = resp.split(extraneous)[0] # Remove everything after extraneous
    for i in range(len(extraneous), 0, -1):
        if resp.endswith(extraneous[:i]):
            return resp[0:-i]
    return resp

async def tok_gen(websocket, extraneous):
    buffer = ''

    while True:
        response = await websocket.recv()
        if response:
            buffer += response
            if definitely_no_extraneous_token(buffer, extraneous):
                yield buffer
                buffer = ''
            elif definitely_has_extraneous_token(buffer, extraneous):
                # Exit early to prevent assistant playing the part of the user
                clipped = remove_all_traces_extraneous_token(buffer, extraneous)
                if clipped:
                    yield clipped
                break
        else:
            # Received end token
            clipped = remove_all_traces_extraneous_token(buffer, extraneous)
            if clipped:
                yield clipped
            break


def get_user_input():
    prompt = ''
    while True:
        try:
            line = input()
            if line.lower() != 'end':
                prompt += line + '\n'
            else:
                break
        except EOFError:
            break

    prompt = prompt.strip()
    return prompt


async def text_requester():
    global conversation

    ip = input("Enter the server ip address: ")
    print(prompt_instruction.lstrip('\n'))

    waive_next_prompt = False

    while True:
        async with websockets.connect(f"wss://{ip}:8765/chat", ssl=ssl_context) as websocket:
        #async with websockets.connect(f"ws://{ip}:8765/chat") as websocket:
            if waive_next_prompt:
                    waive_next_prompt = False
            else:
                print('User: ', end = '')
                
                prompt = get_user_input()
                if prompt.lower() == 'exit':
                    return
                
                conversation += f'\nUser: {prompt}\nAssistant: '

            try:
                await websocket.send(conversation)

                print('Assistant: ', end = '')

                async for token in tok_gen(websocket, extraneous_string):
                    print(token, end = '')
                    sys.stdout.flush()
                    conversation += token
                
                print('')
                conversation += '\n'

                await websocket.close()
                
            except websockets.exceptions.ConnectionClosed:
                print("Connection with server closed. Trying to reconnect...")
                waive_next_prompt = True

asyncio.get_event_loop().run_until_complete(text_requester())
