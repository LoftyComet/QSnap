import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from ..prompts import (
    SOLVER_SYSTEM_PROMPT, SOLVER_USER_PROMPT,
    SPLITTER_SYSTEM_PROMPT, SPLITTER_USER_PROMPT,
    FORMATTER_SYSTEM_PROMPT, FORMATTER_USER_PROMPT
)

# Ensure environment variables are loaded
# Using override=True to ensure .env values are used even if local env vars exist
load_dotenv(override=True)

def _get_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found")
        
    return ChatOpenAI(
        model=model_name, 
        base_url=base_url,
        api_key=api_key,
        temperature=0.3
    )

def split_text_into_questions(text: str):
    """
    Splits the full text into a list of questions using LLM.
    """
    if not text:
        return []
        
    try:
        llm = _get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", SPLITTER_SYSTEM_PROMPT),
            ("user", SPLITTER_USER_PROMPT)
        ])
        # Use JsonOutputParser? Or just parse string. 
        # DeepSeek might not output perfect JSON in strict mode, but let's try.
        # StrOutputParser is safer, then we parse.
        
        chain = prompt | llm | StrOutputParser()
        result_str = chain.invoke({"text": text})
        
        # Clean up markdown formatting if present
        import json
        import re
        
        # Remove ```json and ```
        clean_str = re.sub(r'```json\s*', '', result_str)
        clean_str = re.sub(r'```\s*', '', clean_str)
        
        data = json.loads(clean_str)
        return data.get("questions", [])
        
    except Exception as e:
        print(f"Error splitting questions: {e}")
        return [text] # Fallback: return whole text as one question

def format_and_check_question(text: str):
    """
    Formats the question text and checks if it is complete.
    Returns: {"formatted_text": str, "is_complete": bool}
    """
    if not text:
        return {"formatted_text": "", "is_complete": False}

    try:
        llm = _get_llm() # Use higher temperature or default
        prompt = ChatPromptTemplate.from_messages([
            ("system", FORMATTER_SYSTEM_PROMPT),
            ("user", FORMATTER_USER_PROMPT)
        ])
        
        # Enforce JSON output mode if model supports it, otherwise rely on prompt and parser
        # DeepSeek V3 is good at following instruction
        chain = prompt | llm | JsonOutputParser()
        
        # Invoke
        result = chain.invoke({"text": text})
        return result
    except Exception as e:
        print(f"Error formatting question: {e}")
        # Fallback: assume valid but raw
        return {"formatted_text": text, "is_complete": True}

def solve_question(question_text: str):
    """
    Generates a solution for the given question text.
    Returns JSON: {"answer": str, "analysis": str}
    """
    if not question_text:
        return {"answer": "", "analysis": "No question text provided."}

    try:
        llm = _get_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SOLVER_SYSTEM_PROMPT),
            ("user", SOLVER_USER_PROMPT)
        ])
        
        # Use JsonOutputParser to ensure we get structured data
        chain = prompt | llm | JsonOutputParser()
        
        return chain.invoke({"question": question_text})
    except Exception as e:
        print(f"Error solving question: {e}")
        # Fallback return format
        return {"answer": "Error", "analysis": f"Error generating solution: {str(e)}"}
