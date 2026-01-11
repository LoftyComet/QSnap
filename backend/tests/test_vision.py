import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import app.services.vision as vision_module

# Reset singleton before tests
@pytest.fixture(autouse=True)
def reset_reader():
    vision_module._reader = None
    yield
    vision_module._reader = None

@patch("app.services.vision.easyocr.Reader")
def test_get_reader(mock_reader_cls):
    # Test singleton behavior
    r1 = vision_module.get_reader()
    r2 = vision_module.get_reader()
    assert r1 is r2
    mock_reader_cls.assert_called_once()

@patch("app.services.vision.cv2")
@patch("app.services.vision.np")
@patch("app.services.vision.os")
@patch("app.services.vision.get_reader") # Mock get_reader to return our mock reader
def test_process_image_success(mock_get_reader, mock_os, mock_np, mock_cv2):
    # Setup basic mocks
    output_dir = "test_output"
    
    # 1. Image loading
    # Mock fromfile and imdecode
    mock_cv2.imdecode.return_value = MagicMock(name='image')
    # Because process_image does img[y:y+h, x:x+w], the mock image needs to return a crop when sliced
    mock_crop = MagicMock(name='crop')
    mock_cv2.imdecode.return_value.__getitem__.return_value = mock_crop
    
    # 2. CV2 processing chain
    mock_cv2.cvtColor.return_value = MagicMock(name='gray')
    mock_cv2.threshold.return_value = (0, MagicMock(name='thresh'))
    mock_cv2.dilate.return_value = MagicMock(name='dilated')
    
    # 3. Contours
    # Create valid contours that will produce valid bounding boxes
    c1 = MagicMock()
    c2 = MagicMock()
    mock_cv2.findContours.return_value = ([c1, c2], None)
    
    # 4. Bounding Rects
    # Return (x, y, w, h). Make them large enough to pass (w>100, h>50)
    mock_cv2.boundingRect.side_effect = [(0, 0, 150, 100), (0, 200, 200, 100)]
    
    # 5. OCR Reader Mock
    mock_reader_instance = MagicMock()
    mock_get_reader.return_value = mock_reader_instance
    # readtext returns list of strings when detail=0
    mock_reader_instance.readtext.return_value = ["Question 1"]
        
    # Run
    results = vision_module.process_image("dummy_path.jpg", output_dir)
    
    # Assertions
    assert len(results) == 2
    assert results[0]['ocr_text'] == "Question 1"
    
    # Check if imwrite was called 2 times (once per crop)
    assert mock_cv2.imwrite.call_count == 2
    
    # Check if directory was made
    mock_os.makedirs.assert_called_with(output_dir, exist_ok=True)

@patch("app.services.vision.cv2")
@patch("app.services.vision.np")
def test_process_image_read_fail(mock_np, mock_cv2):
    # Simulate read failure
    mock_cv2.imdecode.return_value = None
    mock_cv2.imread.return_value = None
    
    with pytest.raises(ValueError):
        vision_module.process_image("baduserpath.jpg", "out")

