import os
import yaml
import json
from numpy import dot
from numpy.linalg import norm

def get_api_key(api_key_path):
    with open(api_key_path, 'r') as f:
        config = yaml.safe_load(f)
    os.environ['OPENAI_API_KEY'] = config['openai']['key']

def load_prompt(args):
	with open(args, "r", encoding="UTF-8") as f:
		prompt = yaml.load(f, Loader=yaml.FullLoader)["prompt"]
	return prompt

def load_data(arg):
    with open(arg, 'r',encoding='utf-8') as json_file:
        data = json.load(json_file)

    return data

def cos_sim(a, b):
    return dot(a, b) / (norm(a) * norm(b))

def load_prefix(args):
	with open(args, "r", encoding="UTF-8") as f:
		prefix = yaml.load(f, Loader=yaml.FullLoader)["prefix"]
	return prefix

def load_message(args):
	with open(args, "r", encoding="UTF-8") as f:
		prefix = yaml.load(f, Loader=yaml.FullLoader)["message"]
	return prefix