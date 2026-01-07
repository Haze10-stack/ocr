from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import pytesseract
from PIL import Image
import io
import re
import os
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\SMUTIKANT\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Users\SMUTIKANT\AppData\Local\Programs\Tesseract-OCR\tessdata'

app = FastAPI(title="KYC OCR Validation System")

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

class KYCData(BaseModel):
    document_type: str
    name: Optional[str] = None
    document_number: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None

class ValidationResult(BaseModel):
    success: bool
    document_type: str
    extracted_data: Dict[str, Any]
    validation_errors: list
    confidence: str

class DocumentValidator:
    
    @staticmethod
    def validate_aadhaar(text: str) -> Dict[str, Any]:
        """Validate and extract Aadhaar card details"""
        text = text.replace(" ", "").replace("\n", " ")
        
        # Aadhaar number pattern: 12 digits
        aadhaar_pattern = r'\b\d{12}\b'
        aadhaar_match = re.search(aadhaar_pattern, text)
        
        # DOB pattern
        dob_pattern = r'(\d{2}[/-]\d{2}[/-]\d{4})'
        dob_match = re.search(dob_pattern, text)
        
        # Gender pattern
        gender_pattern = r'\b(Male|Female|MALE|FEMALE)\b'
        gender_match = re.search(gender_pattern, text, re.IGNORECASE)
        
        errors = []
        if not aadhaar_match:
            errors.append("Aadhaar number not found or invalid format")
        if not dob_match:
            errors.append("Date of birth not found")
            
        return {
            "document_number": aadhaar_match.group() if aadhaar_match else None,
            "dob": dob_match.group() if dob_match else None,
            "gender": gender_match.group() if gender_match else None,
            "errors": errors
        }
    
    @staticmethod
    def validate_pan(text: str) -> Dict[str, Any]:
        """Validate and extract PAN card details"""
        text_upper = text.upper()
        original_text = text
        
        # PAN pattern: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)
        pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
        pan_match = re.search(pan_pattern, text_upper)
        
        # Improved name extraction - more flexible pattern
        # Try multiple patterns to catch different formats
        name = None
        
        # Pattern 1: "Name :" or "Name:" followed by text (case insensitive)
        name_pattern1 = r'(?:NAME|Name)\s*:?\s*([A-Z][A-Z\s]+?)(?=\s*(?:Gender|GENDER|DOB|D\.O\.B|Pan\s*Number|PAN\s*NUMBER|Father|$))'
        name_match1 = re.search(name_pattern1, original_text, re.IGNORECASE | re.DOTALL)
        
        if name_match1:
            name = name_match1.group(1).strip()
            # Clean up the name - remove extra whitespace
            name = ' '.join(name.split())
        else:
            # Pattern 2: Try to find name between "Name" and other fields
            name_pattern2 = r'(?:NAME|Name)\s*:?\s*(.+?)(?=Gender|DOB|Pan\s*Number|$)'
            name_match2 = re.search(name_pattern2, text_upper, re.IGNORECASE | re.DOTALL)
            if name_match2:
                name = name_match2.group(1).strip()
                name = ' '.join(name.split())
        
        # DOB pattern - more flexible
        dob_pattern = r'(?:DOB|D\.O\.B|Date\s*of\s*Birth)\s*:?\s*(\d{2}[-/]\d{2}[-/]\d{4})'
        dob_match = re.search(dob_pattern, text_upper, re.IGNORECASE)
        
        errors = []
        if not pan_match:
            errors.append("PAN number not found or invalid format")
        else:
            # Validate PAN structure
            pan = pan_match.group()
            if pan[3] != 'P':  # 4th character should be 'P' for individual
                errors.append("PAN card appears to be for non-individual entity")
        
        if not name:
            errors.append("Name not clearly visible")
            
        return {
            "document_number": pan_match.group() if pan_match else None,
            "name": name,
            "dob": dob_match.group(1) if dob_match else None,
            "errors": errors
        }
    
    @staticmethod
    def validate_driving_license(text: str) -> Dict[str, Any]:
        """Validate and extract Driving License details"""
        text = text.upper().replace("\n", " ")
        
        # DL pattern: 2 letters (state code) + 2 digits + 4 digits + 7 digits
        dl_pattern = r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?\d{11}\b'
        dl_match = re.search(dl_pattern, text)
        
        # DOB pattern
        dob_pattern = r'(?:DOB|D\.O\.B|DATE OF BIRTH)[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})'
        dob_match = re.search(dob_pattern, text, re.IGNORECASE)
        
        errors = []
        if not dl_match:
            errors.append("Driving License number not found or invalid format")
        if not dob_match:
            errors.append("Date of birth not found")
            
        return {
            "document_number": dl_match.group() if dl_match else None,
            "dob": dob_match.group(1) if dob_match else None,
            "errors": errors
        }

def perform_ocr(image: Image.Image) -> str:
    """Perform OCR on the image"""
    try:
        # Preprocess image for better OCR
        image = image.convert('L')  # Convert to grayscale
        
        # Enhance image for better OCR
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)
        
        text = pytesseract.image_to_string(image, lang='eng')
        
        # Debug: print extracted text
        print(f"Extracted text: {text}")
        
        if not text or text.strip() == "":
            return "NO_TEXT_EXTRACTED"
        
        return text
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

def detect_document_type(text: str) -> str:
    """Detect document type from extracted text"""
    text_upper = text.upper()
    
    if "AADHAAR" in text_upper or "UNIQUE IDENTIFICATION" in text_upper:
        return "aadhaar"
    elif "INCOME TAX" in text_upper or re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text_upper):
        return "pan"
    elif "DRIVING LICENCE" in text_upper or "DRIVING LICENSE" in text_upper:
        return "driving_license"
    else:
        return "unknown"

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the HTML interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KYC OCR Validation</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            .tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 30px;
                border-bottom: 2px solid #eee;
            }
            .tab {
                padding: 12px 24px;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 16px;
                color: #666;
                border-bottom: 3px solid transparent;
                transition: all 0.3s;
            }
            .tab.active {
                color: #667eea;
                border-bottom-color: #667eea;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 600;
            }
            input[type="file"], select, input[type="text"], textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input[type="file"]:focus, select:focus, input[type="text"]:focus, textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            textarea {
                resize: vertical;
                min-height: 120px;
            }
            button[type="submit"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 14px 32px;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                cursor: pointer;
                width: 100%;
                font-weight: 600;
                transition: transform 0.2s;
            }
            button[type="submit"]:hover {
                transform: translateY(-2px);
            }
            button[type="submit"]:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            .result {
                margin-top: 30px;
                padding: 25px;
                border-radius: 10px;
                background: #f8f9fa;
            }
            .result.success {
                background: #d4edda;
                border: 2px solid #28a745;
            }
            .result.error {
                background: #f8d7da;
                border: 2px solid #dc3545;
            }
            .result h3 {
                margin-bottom: 15px;
                color: #333;
            }
            .result-item {
                margin: 10px 0;
                padding: 10px;
                background: white;
                border-radius: 5px;
            }
            .result-item strong {
                color: #667eea;
            }
            .error-list {
                list-style: none;
                padding: 0;
            }
            .error-list li {
                padding: 8px;
                margin: 5px 0;
                background: white;
                border-left: 4px solid #dc3545;
                border-radius: 4px;
            }
            .loader {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            .loader.active {
                display: block;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 KYC OCR Validation</h1>
            <p class="subtitle">Upload government ID documents for validation</p>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('upload')">📤 Upload Document</button>
                <button class="tab" onclick="switchTab('manual')">✍️ Manual Entry</button>
            </div>
            
            <!-- Upload Tab -->
            <div id="upload-tab" class="tab-content active">
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>Document Type</label>
                        <select name="document_type" id="upload_doc_type" required>
                            <option value="">Select document type</option>
                            <option value="aadhaar">Aadhaar Card</option>
                            <option value="pan">PAN Card</option>
                            <option value="driving_license">Driving License</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Upload Document Image</label>
                        <input type="file" name="file" accept="image/*" required>
                    </div>
                    <button type="submit">🔍 Validate Document</button>
                </form>
            </div>
            
            <!-- Manual Tab -->
            <div id="manual-tab" class="tab-content">
                <form id="manualForm">
                    <div class="form-group">
                        <label>Document Type</label>
                        <select name="document_type" id="manual_doc_type" required>
                            <option value="">Select document type</option>
                            <option value="aadhaar">Aadhaar Card</option>
                            <option value="pan">PAN Card</option>
                            <option value="driving_license">Driving License</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" name="name" placeholder="Enter full name">
                    </div>
                    <div class="form-group">
                        <label>Document Number</label>
                        <input type="text" name="document_number" placeholder="Enter document number" required>
                    </div>
                    <div class="form-group">
                        <label>Date of Birth (DD/MM/YYYY)</label>
                        <input type="text" name="dob" placeholder="DD/MM/YYYY">
                    </div>
                    <div class="form-group">
                        <label>Address</label>
                        <textarea name="address" placeholder="Enter address"></textarea>
                    </div>
                    <button type="submit">✅ Validate Details</button>
                </form>
            </div>
            
            <div class="loader" id="loader">
                <div class="spinner"></div>
                <p>Processing document...</p>
            </div>
            
            <div id="result"></div>
        </div>
        
        <script>
            function switchTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                event.target.classList.add('active');
                document.getElementById(tab + '-tab').classList.add('active');
                document.getElementById('result').innerHTML = '';
            }
            
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                
                document.getElementById('loader').classList.add('active');
                document.getElementById('result').innerHTML = '';
                
                try {
                    const response = await fetch('/validate-document', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    displayResult(data);
                } catch (error) {
                    displayError('Failed to process document: ' + error.message);
                }
                
                document.getElementById('loader').classList.remove('active');
            });
            
            document.getElementById('manualForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                
                document.getElementById('loader').classList.add('active');
                document.getElementById('result').innerHTML = '';
                
                try {
                    const response = await fetch('/validate-manual', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    displayResult(result);
                } catch (error) {
                    displayError('Failed to validate: ' + error.message);
                }
                
                document.getElementById('loader').classList.remove('active');
            });
            
            function displayResult(data) {
                const resultDiv = document.getElementById('result');
                const isSuccess = data.success && data.validation_errors.length === 0;
                
                let html = `<div class="result ${isSuccess ? 'success' : 'error'}">`;
                html += `<h3>${isSuccess ? '✅ Validation Successful' : '⚠️ Validation Issues Found'}</h3>`;
                html += `<div class="result-item"><strong>Document Type:</strong> ${data.document_type.toUpperCase()}</div>`;
                html += `<div class="result-item"><strong>Confidence:</strong> ${data.confidence}</div>`;
                
                if (data.extracted_data.document_number) {
                    html += `<div class="result-item"><strong>Document Number:</strong> ${data.extracted_data.document_number}</div>`;
                }
                if (data.extracted_data.name) {
                    html += `<div class="result-item"><strong>Name:</strong> ${data.extracted_data.name}</div>`;
                }
                if (data.extracted_data.dob) {
                    html += `<div class="result-item"><strong>Date of Birth:</strong> ${data.extracted_data.dob}</div>`;
                }
                if (data.extracted_data.gender) {
                    html += `<div class="result-item"><strong>Gender:</strong> ${data.extracted_data.gender}</div>`;
                }
                
                if (data.validation_errors.length > 0) {
                    html += '<h4 style="margin-top: 20px; color: #dc3545;">Validation Errors:</h4>';
                    html += '<ul class="error-list">';
                    data.validation_errors.forEach(error => {
                        html += `<li>${error}</li>`;
                    });
                    html += '</ul>';
                }
                
                html += '</div>';
                resultDiv.innerHTML = html;
            }
            
            function displayError(message) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = `<div class="result error"><h3>❌ Error</h3><p>${message}</p></div>`;
            }
        </script>
    </body>
    </html>
    """

@app.post("/validate-document", response_model=ValidationResult)
async def validate_document(
    file: UploadFile = File(...),
    document_type: str = Form(...)
):
    """Validate document from uploaded image"""
    
    # Validate document type
    if document_type not in ["aadhaar", "pan", "driving_license"]:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    # Read and process image
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Save image
        file_path = UPLOAD_DIR / f"{file.filename}"
        image.save(file_path)
        
        print(f"Processing {document_type} document: {file.filename}")
        
        # Perform OCR
        extracted_text = perform_ocr(image)
        
        if extracted_text == "NO_TEXT_EXTRACTED":
            return ValidationResult(
                success=False,
                document_type=document_type,
                extracted_data={"error": "No text could be extracted from image"},
                validation_errors=["Unable to extract text from image. Please ensure the image is clear and readable."],
                confidence="Low"
            )
        
        # Validate based on document type
        validator = DocumentValidator()
        if document_type == "aadhaar":
            result = validator.validate_aadhaar(extracted_text)
        elif document_type == "pan":
            result = validator.validate_pan(extracted_text)
        else:  # driving_license
            result = validator.validate_driving_license(extracted_text)
        
        # Determine confidence
        error_count = len(result["errors"])
        if error_count == 0:
            confidence = "High"
        elif error_count <= 2:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        return ValidationResult(
            success=error_count == 0,
            document_type=document_type,
            extracted_data=result,
            validation_errors=result["errors"],
            confidence=confidence
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/validate-manual", response_model=ValidationResult)
async def validate_manual(data: KYCData):
    """Validate manually entered KYC data"""
    
    errors = []
    
    # Validate based on document type
    if data.document_type == "aadhaar":
        if not data.document_number or not re.match(r'^\d{12}$', data.document_number.replace(" ", "")):
            errors.append("Invalid Aadhaar number format (should be 12 digits)")
    
    elif data.document_type == "pan":
        if not data.document_number or not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', data.document_number.upper()):
            errors.append("Invalid PAN number format (e.g., ABCDE1234F)")
    
    elif data.document_type == "driving_license":
        if not data.document_number or not re.match(r'^[A-Z]{2}[-\s]?\d{2}[-\s]?\d{11}$', data.document_number.upper()):
            errors.append("Invalid Driving License format")
    
    else:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    # Validate DOB format if provided
    if data.dob and not re.match(r'^\d{2}[/-]\d{2}[/-]\d{4}$', data.dob):
        errors.append("Invalid date of birth format (use DD/MM/YYYY or DD-MM-YYYY)")
    
    confidence = "High" if len(errors) == 0 else "Low"
    
    return ValidationResult(
        success=len(errors) == 0,
        document_type=data.document_type,
        extracted_data={
            "document_number": data.document_number,
            "name": data.name,
            "dob": data.dob,
            "address": data.address
        },
        validation_errors=errors,
        confidence=confidence
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)