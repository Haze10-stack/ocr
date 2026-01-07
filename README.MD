# KYC OCR Validation System

A FastAPI-based web application for validating Indian government ID documents (Aadhaar, PAN Card, and Driving License) using OCR technology.

## Features

- 📄 **Document Upload & Validation**: Upload images of government IDs for automatic validation
- ✍️ **Manual Entry**: Manually enter document details for validation
- 🔍 **OCR Processing**: Extracts text from document images using Tesseract OCR
- ✅ **Format Validation**: Validates document numbers, dates, and other fields
- 🎨 **Modern UI**: Clean, responsive web interface

## Supported Documents

- **Aadhaar Card**: 12-digit unique identification number
- **PAN Card**: 10-character alphanumeric code (e.g., ABCDE1234F)
- **Driving License**: State code + 13-digit number (e.g., MH-01-20230001234)

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR

## Installation

### Step 1: Install Tesseract OCR

#### Windows

1. Download the Tesseract installer from the official repository:
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest version (e.g., `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)

2. Run the installer:
   - During installation, note the installation path (default: `C:\Program Files\Tesseract-OCR`)
   - Make sure to install the **English language data** (tessdata)

3. Verify installation:
   ```bash
   tesseract --version
   ```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```

#### macOS

```bash
brew install tesseract
```

### Step 2: Clone or Download the Project

```bash
git clone <your-repository-url>
cd kyc-ocr-validation
```

Or simply download and extract the project files.

### Step 3: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, install packages manually:

```bash
pip install fastapi uvicorn python-multipart pillow pytesseract
```

### Step 5: Configure Tesseract Path

Open `main.py` and update the Tesseract path according to your installation:

#### Windows
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
```

#### Linux/macOS
```python
# Usually no configuration needed, but if required:
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
os.environ['TESSDATA_PREFIX'] = r'/usr/share/tesseract-ocr/5/tessdata'
```

To find your Tesseract location:

**Windows:**
```bash
where tesseract
```

**Linux/macOS:**
```bash
which tesseract
```

## Running the Application

1. Start the FastAPI server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

3. You should see the KYC OCR Validation interface

## Usage

### Upload Document Method

1. Select the **Upload Document** tab
2. Choose the document type (Aadhaar, PAN, or Driving License)
3. Click "Choose File" and select a clear image of your document
4. Click "🔍 Validate Document"
5. View the extraction results and validation status

### Manual Entry Method

1. Select the **Manual Entry** tab
2. Choose the document type
3. Fill in the document details
4. Click "✅ Validate Details"
5. View the validation results

## Project Structure

```
kyc-ocr-validation/
│
├── main.py                 # Main FastAPI application
├── uploads/               # Directory for uploaded images
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## API Endpoints

### `GET /`
Returns the HTML interface

### `POST /validate-document`
Validates a document from an uploaded image
- **Parameters:**
  - `file`: Image file (multipart/form-data)
  - `document_type`: Type of document (aadhaar/pan/driving_license)
- **Returns:** ValidationResult JSON

### `POST /validate-manual`
Validates manually entered document data
- **Body:** JSON with document details
- **Returns:** ValidationResult JSON

## Validation Rules

### Aadhaar Card
- Must be exactly 12 digits
- Date of birth should be in DD-MM-YYYY or DD/MM/YYYY format
- Gender should be present

### PAN Card
- Format: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)
- 4th character should be 'P' for individual
- Name should be clearly visible

### Driving License
- Format: 2 letters (state code) + 2 digits + 11 digits
- Date of birth should be present

## Troubleshooting

### Common Issues

**1. "Tesseract not found" error**
- Make sure Tesseract is installed correctly
- Verify the path in `main.py` matches your installation
- Check if Tesseract is in your system PATH

**2. Poor OCR accuracy**
- Use high-quality, well-lit images
- Ensure the document is flat and not tilted
- Avoid shadows and reflections
- Use images with at least 300 DPI resolution

**3. "No text could be extracted" error**
- Check image quality and clarity
- Ensure the document is fully visible in the image
- Try preprocessing the image (increase contrast, convert to grayscale)

**4. Port already in use**
```bash
# Change the port in main.py or run with:
uvicorn main:app --port 8001
```

## Image Requirements

For best results, uploaded images should:
- Be in JPEG, PNG, or similar common formats
- Have good lighting and contrast
- Be at least 300 DPI resolution
- Show the entire document clearly
- Be free from glare, shadows, or obstructions
- Have the document oriented correctly (not rotated)

## Security Considerations

⚠️ **Important**: This is a demonstration application. For production use:

1. Add user authentication and authorization
2. Implement rate limiting
3. Add input sanitization and validation
4. Use HTTPS for secure transmission
5. Store sensitive data securely (encrypted)
6. Add audit logging
7. Implement CORS policies
8. Validate file types and sizes strictly
9. Add virus scanning for uploaded files
10. Comply with data protection regulations (GDPR, etc.)

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI
- **Pytesseract**: Python wrapper for Tesseract OCR
- **Pillow (PIL)**: Image processing library
- **Pydantic**: Data validation using Python type annotations

## Future Enhancements

- [ ] Add support for more document types (Voter ID, Passport)
- [ ] Implement document verification with government databases
- [ ] Add face matching for ID verification
- [ ] Support multiple languages
- [ ] Add batch processing capability
- [ ] Implement machine learning for better accuracy
- [ ] Add document quality assessment
- [ ] Create mobile app version

## License

This project is for educational purposes. Ensure compliance with local regulations when handling personal identification documents.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please create an issue in the repository or contact the development team.

## Acknowledgments

- Tesseract OCR by Google
- FastAPI framework
- Python community

---

**Version:** 1.0.0  
**Last Updated:** January 2026