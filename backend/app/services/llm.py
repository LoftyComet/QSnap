import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ..prompts import SOLVER_SYSTEM_PROMPT, SOLVER_USER_PROMPT

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
    
    try:
        return chain.invoke({"question": question_text})
    except Exception as e:
        return f"Error generating solution: {str(e)}"
