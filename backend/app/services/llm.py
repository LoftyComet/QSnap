import os
import base64
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from ..prompts import (
    SOLVER_SYSTEM_PROMPT, SOLVER_USER_PROMPT, 
    SPLITTER_SYSTEM_PROMPT, SPLITTER_USER_PROMPT,
    OCR_SYSTEM_PROMPT, OCR_USER_PROMPT,
    FORMATTER_SYSTEM_PROMPT, FORMATTER_USER_PROMPT
)

# Ensure environment variables are loaded
# Using override=True to ensure .env values are used even if local env vars exist
load_dotenv(override=True)

import mimetypes

def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_image_mime_type(image_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    return mime_type or "image/jpeg"

def ocr_image(image_path: str) -> str:
    """
    Perform OCR on an image using a Multimodal LLM (like GPT-4o).
    """
    if not os.path.exists(image_path):
        return ""

    # Load OCR-specific configurations first, fall back to global settings
    ocr_api_key = os.getenv("OCR_API_KEY") or os.getenv("OPENAI_API_KEY")
    ocr_api_base = os.getenv("OCR_API_BASE") or os.getenv("OPENAI_API_BASE")
    # Default to LLM_MODEL if OCR_MODEL is not set, but user usually sets OCR_MODEL for visual tasks
    ocr_model_name = os.getenv("OCR_MODEL") or os.getenv("LLM_MODEL", "gpt-4o")

    if not ocr_api_key:
        print("Error: No API Key found for OCR (checked OCR_API_KEY and OPENAI_API_KEY).")
        return ""

    try:
        # Create a dedicated LLM instance for OCR
        llm = ChatOpenAI(
            model=ocr_model_name,
            base_url=ocr_api_base,
            api_key=ocr_api_key,
            temperature=0.0 # Lower temperature for OCR accuracy
        )

        base64_image = encode_image_to_base64(image_path)
        mime_type = get_image_mime_type(image_path)
        
        # Construct message with image
        messages = [
            SystemMessage(content=OCR_SYSTEM_PROMPT),
            HumanMessage(content=[
                {"type": "text", "text": OCR_USER_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                }
            ])
        ]
        
        print(f"Sending OCR request to {ocr_model_name} with mime type {mime_type}...")
        response = llm.invoke(messages)
        print(f"OCR Full Response Object: {response}")
        print(f"OCR Response content: {response.content}")
        
        # Guard against weird "value" responses or empty responses
        if response.content and str(response.content).strip().lower() == "value":
             print("Warning: Model returned only 'value'. This might be an API error or model hallucination.")
             return ""
             
        return response.content.strip()


    except Exception as e:
        print(f"Error calling LLM for OCR: {e}")
        return ""

def format_and_check_question(ocr_text: str) -> dict:
    """
    Formats the OCR text and checks if it's a complete question.
    Returns specific dict format with keys 'formatted_text' and 'is_complete'.
    """
    if not ocr_text:
         return {"formatted_text": "", "is_complete": False}

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")

    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        return {"formatted_text": ocr_text, "is_complete": True} # Fallback

    try:
        llm = ChatOpenAI(
            model=model_name, 
            base_url=base_url,
            api_key=api_key,
            temperature=0.1 # Lower temp for formatting
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", FORMATTER_SYSTEM_PROMPT),
            ("user", FORMATTER_USER_PROMPT)
        ])
        
        # We need JSON output.
        # StrOutputParser + manual parsing is safest against model chatter.
        chain = prompt | llm | StrOutputParser()
        
        raw_result = chain.invoke({"text": ocr_text})
        
        # Clean markdown
        cleaned_result = raw_result.strip()
        if "```" in cleaned_result:
            match = re.search(r'\{.*\}', cleaned_result, re.DOTALL)
            if match:
                cleaned_result = match.group(0)
        
        try:
            return json.loads(cleaned_result)
        except json.JSONDecodeError:
            print(f"JSON Decode Error in Format: {raw_result}")
            return {"formatted_text": ocr_text, "is_complete": True} # Fallback
            
    except Exception as e:
        print(f"Error calling LLM for Format: {e}")
        return {"formatted_text": ocr_text, "is_complete": True}

def solve_question(question_text: str):
    """
    Generates a solution for the given question text.
    Returns a dict with 'answer' and 'analysis'.
    """
    if not question_text:
        return {"answer": "", "analysis": "No question text provided."}

    # Force reloading environment to be absolutely sure
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")

    if not api_key:
        return {"answer": "Error", "analysis": "Error: OPENAI_API_KEY not found in environment."}

    try:
        # Using explicit parameters for better compatibility
        llm = ChatOpenAI(
            model=model_name, 
            base_url=base_url, # Modern parameter name
            api_key=api_key,   # Explicitly pass the key
            temperature=0.3
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SOLVER_SYSTEM_PROMPT),
            ("user", SOLVER_USER_PROMPT)
        ])
        
        chain = prompt | llm | StrOutputParser()
        
        raw_result = chain.invoke({"question": question_text})
        
        # Clean markdown
        cleaned_result = raw_result.strip()
        if "```" in cleaned_result:
             # Find first { and last }
            match = re.search(r'\{.*\}', cleaned_result, re.DOTALL)
            if match:
                cleaned_result = match.group(0)
        
        try:
            return json.loads(cleaned_result)
        except json.JSONDecodeError:
            return {
                "answer": "Parse Error", 
                "analysis": raw_result
            }

    except Exception as e:
        print(f"Error calling LLM for Solver: {e}")
        return {"answer": "Error", "analysis": f"Error generating solution: {str(e)}"}

def split_text_into_questions(full_text: str) -> list[str]:
    """
    Splits the full text of a paper into individual questions using LLM.
    """
    if not full_text:
        return []

    # Force reloading environment
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")

    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        return [full_text]

    try:
        llm = ChatOpenAI(
            model=model_name, 
            base_url=base_url,
            api_key=api_key,
            temperature=0.1
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SPLITTER_SYSTEM_PROMPT),
            ("user", SPLITTER_USER_PROMPT)
        ])
        
        chain = prompt | llm | JsonOutputParser()
        
        result = chain.invoke({"text": full_text})
        
        if isinstance(result, dict) and "questions" in result:
             # Ensure items are strings
             return [str(q) for q in result["questions"]]
        elif isinstance(result, list):
             return [str(q) for q in result]
        
        print(f"Unexpected split format: {type(result)}")
        return [full_text] 
        
    except Exception as e:
        print(f"Error splitting text: {str(e)}")
        # Simple heuristic fallback
        return [chunk.strip() for chunk in full_text.split('\n\n') if chunk.strip()]
