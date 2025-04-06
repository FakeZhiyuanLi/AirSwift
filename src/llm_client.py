from utils import get_openai_key
from openai import OpenAI
import base64
from pathlib import Path
import io

class LLMClient:
    def __init__(self):
        self.openai_client = OpenAI(api_key=get_openai_key())
        self.base_dir = Path("src")
        self.file_desc_path = self.base_dir / "file_desc_prompts"

    
    def trascribe_desc(self, data: bytes):
        '''
        Calls Whisper API to transcribe audio bytes
        Returns a string with transcriptions
        '''
        wav_data = io.BytesIO(data)
        wav_data.name = "input.wav"
        transcription = self.openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_data
        )
        return transcription.text

    def encode_image(self, abs_image_path):
        with open(abs_image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def caption_image(self, image_data):
        caption_image_system_path = self.file_desc_path / "image_prompt" / "image_system_prompt"
        caption_image_user_path = self.file_desc_path / "image_prompt" / "image_user_prompt"
        with caption_image_system_path.open() as system_file_reader, caption_image_user_path.open() as user_file_reader:
            system_prompt = system_file_reader.read()
            user_prompt = user_file_reader.read()
        image_desc = self.openai_client.responses.create(
                model="gpt-4o",
                input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    { 
                        "type": "input_text", 
                        "text": user_prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_data}",
                    },
                ],
            }
        ],
            )
        return image_desc.output_text
    
    def caption_text(self, text):
        text_user_path = self.file_desc_path / "txt_prompt" / "txt_system_prompt"
        text_system_path = self.file_desc_path / "txt_prompt" / "txt_user_prompt"
        with text_system_path.open() as system_file_reader, text_user_path.open() as user_file_reader:
            system_prompt = system_file_reader.read()
            user_prompt = user_file_reader.read()
        text_desc = self.openai_client.responses.create(
                model="gpt-4o",
                input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    { 
                        "type": "input_text", 
                        "text": user_prompt
                    },
                    {
                        "type": "input_text",
                        "text": f"This is the text you will analyze: {text}",
                    },
                ],
            }
        ],
            )
        return text_desc.output_text

    def caption_csv(self, text):
        text_user_path = self.file_desc_path / "csv_prompt" / "csv_system_prompt"
        text_system_path = self.file_desc_path / "csv_prompt" / "csv_user_prompt"
        with text_system_path.open() as system_file_reader, text_user_path.open() as user_file_reader:
            system_prompt = system_file_reader.read()
            user_prompt = user_file_reader.read()
        text_desc = self.openai_client.responses.create(
                model="gpt-4o",
                input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    { 
                        "type": "input_text", 
                        "text": user_prompt
                    },
                    {
                        "type": "input_text",
                        "text": f"This is the text you will analyze: {text}",
                    },
                ],
            }
        ],
            )
        return text_desc.output_text