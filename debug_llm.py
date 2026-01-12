
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load env
load_dotenv("/root/QSnap/backend/.env")

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")
model_name = os.getenv("LLM_MODEL")

print(f"Testing LLM Text Generation...")
print(f"API Base: {base_url}")
print(f"Model: {model_name}")

if not api_key:
    print("Error: No API Key")
    exit(1)

llm = ChatOpenAI(
    model=model_name,
    base_url=base_url,
    api_key=api_key,
    temperature=0.3
)

prompt = ChatPromptTemplate.from_messages([
    ("user", "Hello, do you work? Reply with 'Yes, I am working'.")
])

chain = prompt | llm | StrOutputParser()

try:
    start = time.time()
    print("Sending request...")
    res = chain.invoke({})
    print(f"Response ({time.time() - start:.2f}s): {res}")
except Exception as e:
    print(f"Error: {e}")
