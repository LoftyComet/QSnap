from unittest.mock import patch, MagicMock
from app.services.export import generate_word_doc
from types import SimpleNamespace

@patch("app.services.export.Document")
@patch("os.path.exists")
@patch("app.services.export.Inches")
def test_generate_word_doc(mock_inches, mock_exists, mock_document_cls):
    # Setup mocks
    mock_document = MagicMock()
    mock_document_cls.return_value = mock_document
    mock_exists.return_value = True # Assume logic finds images

    # Create dummy data
    paper = SimpleNamespace(filename="test_paper.pdf", file_path="static/uploads/test_paper.pdf")
    q1 = SimpleNamespace(ocr_text="What is 2+2?", image_path="static/uploads/img1.jpg", solution_text="4", is_incomplete=False)
    q2 = SimpleNamespace(ocr_text="Describe AI.", image_path="static/uploads/img2.jpg", solution_text="AI is artificial intelligence.", is_incomplete=False)
    questions = [q1, q2]
    
    output_path = "output.docx"
    
    # Run function
    result = generate_word_doc(paper, questions, output_path)
    
    # Assertions
    assert result == output_path
    mock_document_cls.assert_called_once()
    mock_document.add_heading.assert_any_call('Solutions: test_paper.pdf', 0)
    
    # Verify Structure based on new export.py
    # 1. Problem Statement
    mock_document.add_heading.assert_any_call('Problem Statement', level=2)
    
    # 2. Check if pictures were added (since mock_exists is True)
    assert mock_document.add_picture.call_count == 2
    
    # 3. Analysis/Solution
    # Since we only provided solution_text and no answer/analysis, it falls back to Analysis heading
    mock_document.add_heading.assert_any_call('Analysis', level=2)
    
    # Check if document was saved
    mock_document.save.assert_called_with(output_path)

@patch("app.services.export.Document")
@patch("os.path.exists")
def test_generate_word_doc_missing_image(mock_exists, mock_document_cls):
    # Setup mocks
    mock_document = MagicMock()
    mock_document_cls.return_value = mock_document
    mock_exists.return_value = False # Images not found

    paper = SimpleNamespace(filename="test.pdf", file_path="static/uploads/test.pdf")
    q1 = SimpleNamespace(ocr_text="Q1", image_path="img1.jpg", solution_text="S1", is_incomplete=False)
    questions = [q1]
    
    generate_word_doc(paper, questions, "out.docx")
    
    # Picture should NOT be added
    mock_document.add_picture.assert_not_called()
    
    # Headers should still be there
    mock_document.add_heading.assert_any_call('Problem Statement', level=2)
    mock_document.add_heading.assert_any_call('Analysis', level=2)
