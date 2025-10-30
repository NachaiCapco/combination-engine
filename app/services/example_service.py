import io
import pandas as pd
from app.services.note_data import get_note_data

def build_example_combination_excel() -> bytes:
    """
    Build example Excel file with combination-data and note sheets
    
    Returns:
        bytes: Excel file content
    """
    # Example data for combination-data sheet
    example_data = {
        "[API]endpoint": [
            "https://api.example.com/users/{id}",
            "https://api.example.com/products",
            "https://api.example.com/orders/{orderId}"
        ],
        "[API]Method": [
            "GET",
            "POST",
            "PUT"
        ],
        "[Request][Header]x-api-key": [
            "key123",
            "key456",
            ""
        ],
        "[Request][Header]authorization": [
            "",
            "Bearer token456",
            "Bearer token789"
        ],
        "[Request][Query]status": [
            "ACTIVE",
            "INACTIVE",
            "PENDING"
        ],
        "[Request][Query]page": [
            "1",
            "2",
            ""
        ],
        "[Request][Query]sort": [
            "",
            "-created_at",
            "name"
        ],
        "[Request][Body]username": [
            "",
            "john_doe",
            "jane_smith"
        ],
        "[Request][Body]profile.name": [
            "",
            "John Doe",
            "Jane Smith"
        ],
        "[Request][Body]profile.age[Type:int]": [
            "",
            "25",
            "30"
        ],
        "[Request][Body]settings.notifications[Type:bool]": [
            "",
            "true",
            "false"
        ],
        "[Request][Body]children[0].name": [
            "",
            "Alice",
            "Bob"
        ],
        "[Response][API]status": [
            "200",
            "201",
            "200"
        ],
        "[Response][Body]success[Type:bool]": [
            "true",
            "true",
            "true"
        ],
        "[Response][Body]data.id": [
            "123",
            "456",
            "789"
        ],
        "[Response][Body]data.total:gt[Type:int]": [
            "0",
            "10",
            "5"
        ],
        "[Response][Body]data.score:between[Type:float]": [
            "",
            "50.0,100.0",
            "0.0,50.0"
        ],
        "[Response][Body]data.message:contains": [
            "success",
            "",
            "completed"
        ],
        "[Response][Header]x-request-id": [
            "req-001",
            "req-002",
            "req-003"
        ],
    }
    
    example_df = pd.DataFrame(example_data)
    
    # Use centralized note data
    note_df = pd.DataFrame(get_note_data())
    
    # Create Excel file in memory
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        example_df.to_excel(writer, index=False, sheet_name="combination-data")
        note_df.to_excel(writer, index=False, sheet_name="note")
    
    buf.seek(0)
    return buf.getvalue()
