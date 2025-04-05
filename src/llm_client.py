from utils import get_openai_key
from openai import OpenAI
import base64

class LLMClient:
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=get_openai_key())

    def encode_image(self, abs_image_path):
        with open(abs_image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def caption_image(self, image_data):
        image_desc = self.openai_client.responses.create(
                model="gpt-4o",
                input=[
                    {
                        "role": "user",
                        "content": [
                            { "type": "input_text", 
                                "text": "what's in this image?" },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{image_data}",
                            },
                        ],
                    }
                ],
            )
        return image_desc.output_text