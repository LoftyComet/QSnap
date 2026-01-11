import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from ..prompts import SOLVER_SYSTEM_PROMPT, SOLVER_USER_PROMPT, SPLITTER_SYSTEM_PROMPT, SPLITTER_USER_PROMPT

# Ensure environment variables are loaded
# Using override=True to ensure .env values are used even if local env vars exist
load_dotenv(override=True)

def solve_question(question_text: str):
    """
    Generates a solution for the given question text.
    """
    if not question_text:
        return "No question text provided."

    # Force reloading environment to be absolutely sure
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")

    if not api_key:
        return "Error: OPENAI_API_KEY not found in environment."

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
        
        return chain.invoke({"question": question_text})
    except Exception as e:
        return f"Error generating solution: {str(e)}"

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
