import pandas as pd

keys = pd.read_csv('/Users/zhiyuan/Documents/keys.csv')

AWS_ACCESS_KEY = keys["Access key ID"][0]
AWS_SECRET_KEY = keys["Secret access key"][0]
OPENAI_KEY = keys[" OpenAI key"][0]

def get_aws_access_key():
    return AWS_ACCESS_KEY

def get_aws_secret_key():
    return AWS_SECRET_KEY

def get_openai_key():
    return OPENAI_KEY