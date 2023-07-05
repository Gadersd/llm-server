import asyncio
import websockets
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, StoppingCriteria, StoppingCriteriaList
import torch
import threading
from threading import Thread
import ssl

falcon_7b_instruct = "tiiuae/falcon-7b-instruct"
falcon_40b_instruct = "tiiuae/falcon-40b-instruct"
falcon_40b_uncensored = "ehartford/WizardLM-Uncensored-Falcon-40b"

model_id = falcon_7b_instruct

tok = AutoTokenizer.from_pretrained(model_id)
eos_string = tok.convert_ids_to_tokens(tok.eos_token_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    load_in_8bit=True,
)

async def iterate_blocking(iterator):
    loop = asyncio.get_running_loop()
    DONE = object()
    while True:
        obj = await loop.run_in_executor(None, next, iterator, DONE)
        if obj is DONE:
            break
        yield obj



# Allows for manually stopping token generation
class CustomStoppingCriteria(StoppingCriteria):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()
    
    def __call__(self, input_ids: torch.LongTensor, score: torch.FloatTensor, **kwargs) -> bool:
        return self._stop_event.is_set()


async def send_tokens(websocket, prompt):
    inputs = tok([prompt], return_token_type_ids=False, return_tensors="pt").to('cuda')
    streamer = TextIteratorStreamer(tok, skip_prompt=True)

    stop_generation = CustomStoppingCriteria()
    stopping_criteria = StoppingCriteriaList([stop_generation])

    generation_kwargs = dict(inputs, stopping_criteria=stopping_criteria, streamer=streamer, max_new_tokens=500)
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    
    try:
        async for next_token in iterate_blocking(streamer):
            next_token = next_token.replace(eos_string, '')
            if next_token:
                await websocket.send(next_token)
        await websocket.send('')
    except websockets.exceptions.ConnectionClosed:   # Handle websocket disconnect
        stop_generation.stop()
        thread.join()
        print('Client disconnected')

semaphore = asyncio.Semaphore(1)  # allows only a single instance

async def text_generator(websocket, path):
    if path == '/chat':
        async with semaphore:  # limit number of concurrent tasks
            async for message in websocket:
                prompt = message
                await send_tokens(websocket, prompt)
            

print(f'{model_id} loaded. Now starting server...')
#print(eos_string)

# Load certificate and key
#ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#ssl_context.load_cert_chain('cert/cert.pem', 'cert/key.pem')

# Load certificate and key
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile='cert/server.crt', keyfile='cert/server.key')

start_server = websockets.serve(text_generator, "0.0.0.0", 8765, ssl=ssl_context)
#start_server = websockets.serve(text_generator, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()