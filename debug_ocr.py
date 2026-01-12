import os
import base64
import httpx
import json
from dotenv import load_dotenv
import mimetypes

load_dotenv("backend/.env")

api_key = os.getenv("OCR_API_KEY") or os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OCR_API_BASE") or os.getenv("OPENAI_API_BASE")
model = "Pro/Qwen/Qwen2.5-VL-7B-Instruct"

image_path = "backend/static/uploads/ls02.png"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_image_mime_type(image_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    return mime_type or "image/jpeg"

base64_image = encode_image(image_path)
mime_type = get_image_mime_type(image_path)

print(f"Testing Model: {model}")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "输出图片中的文字。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    "max_tokens": 1000
}

url = f"{base_url}/chat/completions"

try:
    response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
    print(f"Status Code: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
