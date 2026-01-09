from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..services import llm

router = APIRouter()

@router.post("/solve/{question_id}")
def solve_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Call LLM
    start_text = q.ocr_text if q.ocr_text else "Identify this question from image."
    # If we wanted to send image to LLM, we'd do it here. For now, text only.
    
    sol_result = llm.solve_question(start_text)
    
    q.answer = sol_result.get("answer", "")
    q.analysis = sol_result.get("analysis", "")
    q.solution_text = q.analysis # Keep populated
    
    db.commit()
    
    return {"solution": q.analysis, "answer": q.answer}
