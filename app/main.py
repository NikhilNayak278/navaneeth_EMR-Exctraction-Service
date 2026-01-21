from fastapi import FastAPI, UploadFile, File, HTTPException, Form
import uvicorn
import io
import json

from fastapi.responses import StreamingResponse
from typing import List
from . import ocr_engine
from . import ie_engine

app = FastAPI(title="Extraction Service", description="Extracts text and entities from medical images and PDFs.")

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    ocr_engine.init_ocr()
    # ie_engine.init_model()
    ie_engine.init_gemini()

@app.get("/")
def read_root():
    return {"status": "Extraction Service Running"}

@app.post("/extract")
async def extract_endpoint(
    file: UploadFile = File(...), 
    use_gemini: bool = Form(...), 
    use_ollama: bool = Form(...),
    is_handwritten: bool = Form(False)
):
    """
    Endpoint to accept an image or PDF file, extract text, and identify entities.
    Optional 'use_gemini' flag to use Google's Gemini API for extraction.
    Optional 'use_ollama' flag to use local Ollama model (default: llama3.2).
    Optional 'is_handwritten' flag to use Gemini Vision directly (skips OCR).
    """
    if not (file.content_type.startswith("image/") or file.content_type == "application/pdf"):
        raise HTTPException(status_code=400, detail="File must be an image or PDF.")
    
    try:
        # Read file content
        contents = await file.read()
        print(f"Use Gemini: {use_gemini}, Use Ollama: {use_ollama}, Handwriting Mode: {is_handwritten}")
        
        # Branch 1: Handwritten Mode (Pure Vision)
        if is_handwritten and use_gemini:
             print("Processing as Handwritten Document (Gemini Vision)...")
             entities = ie_engine.extract_image_with_gemini(contents)
             return entities

        # Branch 2: Digital/Hybrid Mode (OCR + LLM)
        # Step 1: OCR
        raw_text = ocr_engine.extract_text(contents)
        
        # Step 2: IE
        if use_gemini:
             entities = ie_engine.extract_with_gemini(raw_text)
        elif use_ollama:
             entities = ie_engine.extract_with_ollama(raw_text)
        else:
             entities = ie_engine.extract_entities(raw_text)
        
        # with open("discharge.json", "w") as f:
        # #     json.dump(entities, f, indent=4)
        # with open("lab.json", "r") as f:
        #     entities = json.load(f)
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract_batch")
async def extract_batch_endpoint(
    files: List[UploadFile] = File(...),
    use_gemini: bool = Form(...),
    use_ollama: bool = Form(...)
):
    """
    Accepts multiple files and streams extraction results one by one (SSE).
    """
    async def process_files():
        for file in files:
            result = {}
            try:
                if not (file.content_type.startswith("image/") or file.content_type == "application/pdf"):
                    result = {"error": f"File {file.filename} is not an image or PDF."}
                else:
                    contents = await file.read()
                    
                    # Step 1: OCR
                    raw_text = ocr_engine.extract_text(contents)
                    
                    # Step 2: IE
                    if use_gemini:
                        entities = ie_engine.extract_with_gemini(raw_text)
                    elif use_ollama:
                        entities = ie_engine.extract_with_ollama(raw_text)
                    else:
                        entities = ie_engine.extract_entities(raw_text)
                    
                    result = entities
            except Exception as e:
                result = {"error": f"Error processing {file.filename}: {str(e)}"}
            
            # Attach filename to result
            if isinstance(result, dict):
                result["_filename"] = file.filename
                
            yield f"data: {json.dumps(result)}\n\n"

    return StreamingResponse(process_files(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
