import os
from PIL import Image
from llm_client import LLMClient

llm_api = LLMClient()

def process_text_file(abs_file_path) -> str:
    with open(abs_file_path, 'r') as fp:
        text_content = fp.read()
    return text_content

def process_image_file(abs_file_path: str) -> str:
    image = llm_api.encode_image(abs_file_path)
    image_desc = llm_api.caption_image(image)
    return image_desc

def process_pdf_file(abs_file_path: str) -> str:
    