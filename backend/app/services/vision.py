import cv2
import numpy as np
import os
import easyocr
import uuid
import json
import subprocess

# Global reader instance (initialize once to avoid reloading model)
_reader = None

def get_reader():
    global _reader
    if _reader is None:
        # gpu=False assumes no CUDA; change to True if user has NVIDIA GPU
        _reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    return _reader

def process_image(image_path: str, output_dir: str):
    """
    Segments the image into questions and performs OCR.
    
    Args:
        image_path: Absolute path to the source image.
        output_dir: Directory to save cropped question images.
        
    Returns:
        List of dictionaries containing question data.
    """
    # 1. Read Image
    # Robust reading for Windows paths with special chars
    # img = cv2.imread(image_path)
    try:
        # Read file as byte stream first, then decode
        # This bypasses filepath encoding issues in cv2.imread
        stream = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(stream, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error reading image via imdecode: {e}")
        img = None

    if img is None:
        # Fallback to standard read (sometimes useful)
        img = cv2.imread(image_path)
        
    if img is None:
        # Detailed error for debugging
        abs_path = os.path.abspath(image_path)
        exists = os.path.exists(abs_path)
        raise ValueError(f"Could not read image at {image_path} (Abs: {abs_path}, Exists: {exists})")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Preprocess: Thresholding
    # Otsu's thresholding
    ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 3. Dilation to connect text lines into blocks
    # We want to merge horizontal text lines.
    # Kernel: wider than tall. Adjust (50, 5) based on resolution. 
    # High resolution images might need larger kernels.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 10)) 
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    
    # 4. Find Contours
    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 5. Filter and Process Contours
    question_blocks = []
    
    # Sort contours top-to-bottom
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    
    # Sort by Y coordinate
    # (x, y, w, h)
    bounding_boxes.sort(key=lambda b: b[1])
    
    os.makedirs(output_dir, exist_ok=True)
    
    for i, bbox in enumerate(bounding_boxes):
        x, y, w, h = bbox
        
        # Filter small noise (adjust thresholds as needed)
        if w < 100 or h < 50:
            continue
            
        # Crop
        crop = img[y:y+h, x:x+w]
        
        # Save Crop
        crop_filename = f"crop_{uuid.uuid4()}.jpg"
        crop_path_abs = os.path.join(output_dir, crop_filename)
        cv2.imwrite(crop_path_abs, crop)
        
        # Relative path for frontend serving
        # Assuming output_dir ends in "static/uploads"
        # We want "static/uploads/crop_..." usually, but let's return just filename and let caller handle
        
        # OCR (Using EasyOCR for better Chinese support)
        try:
            reader = get_reader()
            # EasyOCR can take the crop directly as a numpy array
            result = reader.readtext(crop, detail=0)
            text = " ".join(result)
        except Exception as e:
            # Fallback if OCR failed
            print(f"Warning: OCR failed: {e}")
            text = ""
            
        question_blocks.append({
            "bbox": [x, y, w, h],
            "image_filename": crop_filename,
            "ocr_text": text.strip()
        })
        
    if not question_blocks:
        # Fallback: If no contours found (e.g. blank page or bad threshold), return full image as one question
        # This ensures the user at least sees something
        print("Warning: No distinct questions found. Returning full image.")
        full_filename = f"full_{uuid.uuid4()}.jpg"
        cv2.imwrite(os.path.join(output_dir, full_filename), img)
        try:
            reader = get_reader()
            result = reader.readtext(img, detail=0)
            text = " ".join(result)
        except Exception:
            text = ""
        
        question_blocks.append({
            "bbox": [0, 0, img.shape[1], img.shape[0]],
            "image_filename": full_filename,
            "ocr_text": text.strip()
        })
    
    return question_blocks

def extract_text_full_page(image_path: str) -> str:
    """
    Performs OCR on the full image without segmentation.
    """
    try:
        if not os.path.exists(image_path):
             return ""
        
        # Robust reading
        stream = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(stream, cv2.IMREAD_COLOR)
        if img is None:
             img = cv2.imread(image_path)
        
        if img is None:
             return ""

        reader = get_reader()
        # detail=0 returns just the list of strings
        result = reader.readtext(img, detail=0)
        return "\n".join(result)
    except Exception as e:
        print(f"Error in extract_text_full_page: {e}")
        return ""

