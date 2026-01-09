from unittest.mock import patch, MagicMock
import os
from app.services.llm import solve_question

def test_solve_question_empty_input():
    result = solve_question("")
    assert result == "No question text provided."

def test_solve_question_no_api_key():
    # Save original env
    old_env = dict(os.environ)
    try:
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        result = solve_question("Question?")
        assert "Error: OPENAI_API_KEY not found" in result
    finally:
        os.environ.clear()
        os.environ.update(old_env)

@patch("app.services.llm.ChatOpenAI")
@patch("app.services.llm.ChatPromptTemplate")
@patch("app.services.llm.StrOutputParser")
def test_solve_question_success(mock_parser_cls, mock_prompt_cls, mock_openai_cls):
    # Setup mocks
    mock_prompt_instance = MagicMock()
    mock_prompt_cls.from_messages.return_value = mock_prompt_instance
    
    mock_llm_instance = MagicMock()
    mock_openai_cls.return_value = mock_llm_instance
    
    mock_parser_instance = MagicMock()
    mock_parser_cls.return_value = mock_parser_instance
    
    # Mock the chaining: prompt | llm | parser
    # Step 1: prompt | llm -> intermediate_chain
    mock_intermediate = MagicMock()
    mock_prompt_instance.__or__.return_value = mock_intermediate
    
    # Step 2: intermediate_chain | parser -> final_chain
    mock_final_chain = MagicMock()
    mock_intermediate.__or__.return_value = mock_final_chain
    
    # Setup return value
    mock_final_chain.invoke.return_value = "The answer is 42."
    
    # Ensure environment has API key
    # Also unset OPENAI_API_BASE if present to match the expected call with base_url=None
    # Or just don't check base_url strictly if not knowing the env
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "LLM_MODEL": "gpt-3.5-turbo"}):
        if "OPENAI_API_BASE" in os.environ:
             del os.environ["OPENAI_API_BASE"]
             
        result = solve_question("What is the meaning of life?")
        
        assert result == "The answer is 42."
        mock_openai_cls.assert_called_with(
            model="gpt-3.5-turbo",
            base_url=None,
            api_key="test-key",
            temperature=0.3
        )
        mock_final_chain.invoke.assert_called_once()

@patch("app.services.llm.ChatOpenAI")
def test_solve_question_exception(mock_openai):
    mock_openai.side_effect = Exception("API Error")
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        result = solve_question("Question")
        assert "Error generating solution" in result
