from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import pytest

from app.main import app
from app.database import Base, get_db

# Setup In-Memory DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

@pytest.fixture
def cleanup_upload():
    uploaded_files = []
    yield uploaded_files
    for path in uploaded_files:
        if os.path.exists(path):
            os.remove(path)

def test_upload_paper(cleanup_upload):
    # Helper to clean up uploaded file
    test_filename = "test_upload_image.jpg"
    expected_path = f"static/uploads/{test_filename}"
    cleanup_upload.append(expected_path)
    
    # Create a dummy image file content
    file_content = b"fake image content"
    
    # Needs to be a valid file-like object
    response = client.post(
        "/upload",
        files={"file": (test_filename, file_content, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["filename"] == test_filename
