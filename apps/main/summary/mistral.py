# bnb_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_quant_type='nf4',
#     bnb_4bit_use_double_quant=True,
# )
#
# model = AutoModelForCausalLM.from_pretrained(
#     'mistralai/Mistral-7B-Instruct-v0.2',
#     quantization_config=bnb_config
# )
#
# tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
# messages = [
#     {"role": "user", "content": TEMPLATE.format(text=text)},
# ]
#
# encodeds = tokenizer.apply_chat_template(messages, return_tensors="pt")
#
# model_inputs = encodeds.to('cpu')
#
# generated_ids = model.generate(model_inputs, max_new_tokens=1000, do_sample=True)
# decoded = tokenizer.batch_decode(generated_ids)
# print(decoded[0])
