from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False)
    
    questions = relationship("Question", back_populates="paper")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    
    image_path = Column(String) # Path to the cropped image
    bbox_json = Column(String) # JSON string of [x, y, w, h]
    
    ocr_text = Column(Text, default="")
    solution_text = Column(Text, default="")
    
    order_index = Column(Integer, default=0)
    
    paper = relationship("Paper", back_populates="questions")
