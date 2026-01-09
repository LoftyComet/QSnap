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

def test_upload_paper():
    # Helper to clean up uploaded file
    test_filename = "test_upload_image.jpg"
    
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
    
    # Clean up file if created
    # Note: app/main.py uses "static/uploads" relative to working dir
    # Tests usually run from root or backend dir.
    # To be safe we could mock `open` or cleanup.
    expected_path = f"static/uploads/{test_filename}"
    if os.path.exists(expected_path):
        os.remove(expected_path)
