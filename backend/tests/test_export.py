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
    paper = SimpleNamespace(filename="test_paper.pdf")
    q1 = SimpleNamespace(ocr_text="What is 2+2?", image_path="static/uploads/img1.jpg", solution_text="4")
    q2 = SimpleNamespace(ocr_text="Describe AI.", image_path="static/uploads/img2.jpg", solution_text="AI is artificial intelligence.")
    questions = [q1, q2]
    
    output_path = "output.docx"
    
    # Run function
    result = generate_word_doc(paper, questions, output_path)
    
    # Assertions
    assert result == output_path
    mock_document_cls.assert_called_once()
    mock_document.add_heading.assert_any_call('Solutions: test_paper.pdf', 0)
    
    # Check if pictures were added (since mock_exists is True)
    assert mock_document.add_picture.call_count == 2
    
    # Check if document was saved
    mock_document.save.assert_called_with(output_path)

@patch("app.services.export.Document")
@patch("os.path.exists")
def test_generate_word_doc_missing_image(mock_exists, mock_document_cls):
    # Setup mocks
    mock_document = MagicMock()
    mock_document_cls.return_value = mock_document
    mock_exists.return_value = False # Images not found

    paper = SimpleNamespace(filename="test.pdf")
    q1 = SimpleNamespace(ocr_text="Q1", image_path="img1.jpg", solution_text="S1")
    questions = [q1]
    
    generate_word_doc(paper, questions, "out.docx")
    
    # Picture should NOT be added
    mock_document.add_picture.assert_not_called()
    # Check that fallback text is NOT added because logic skips the image entirely if not found
    # (Checking expected behavior of current implementation)
    mock_document.add_paragraph.assert_any_call("Question Text:", style='Intense Quote') # Check other calls still happen
