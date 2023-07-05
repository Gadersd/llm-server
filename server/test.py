# Runs Falcon-40B Instruct in 8bit mode which should take ~45GB of RAM

from transformers import AutoTokenizer, AutoModelForCausalLM
import transformers
import torch

falcon_7b_instruct = "tiiuae/falcon-7b-instruct"
falcon_40b_instruct = "tiiuae/falcon-40b-instruct"
falcon_40b_uncensored = "ehartford/WizardLM-Uncensored-Falcon-40b"

model_id = falcon_7b_instruct

try:
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        load_in_8bit=True,
        device_map="auto",
    )
except Exception as e:
    print(f'Error Loading model {model_id}. Error: {e}')
    exit(1)

print(f'Loaded {model_id}')

try:
    pipeline = transformers.pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )
except Exception as e:
    print(f'Error creating pipeline. Error: {e}')
    exit(1)

prompt = "Write a poem about Valencia."
print(f'Prompt: {prompt}\n')

try:
    sequences = pipeline(
        prompt,
        max_length=500,
        do_sample=True,
        top_k=10,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
    )
except Exception as e:
    print(f'Error sampling model. Error: {e}')
    exit(1)

for seq in sequences:
    print(f"Result: {seq['generated_text']}")

print('\nsuccess')
