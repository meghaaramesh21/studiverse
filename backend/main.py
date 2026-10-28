
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pymupdf
import re

app = FastAPI(title="Studiverse Learning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://meghaaramesh21.github.io"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Studiverse Learning API is running!"}


@app.post("/extract")
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")

    data = await file.read()

    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "PDF must be smaller than 10 MB.")

    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            pages = [page.get_text() for page in pdf]
    except Exception:
        raise HTTPException(400, "Could not read this PDF.")

    text = "\n".join(pages).strip()

    if not text:
        raise HTTPException(
            422,
            "No selectable text found. This PDF may need OCR."
        )

    # Basic heading-based topic detection.
    topics = []
    current_title = "Introduction"
    current_text = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        is_heading = (
            len(line) < 90
            and (
                re.match(r"^(unit|chapter|topic|module)\s+[\w.-]+", line, re.I)
                or re.match(r"^\d+(\.\d+)*\s+[A-Z]", line)
            )
        )

        if is_heading:
            if current_text:
                topics.append({
                    "title": current_title,
                    "content": "\n".join(current_text)
                })
            current_title = line
            current_text = []
        else:
            current_text.append(line)

    if current_text:
        topics.append({
            "title": current_title,
            "content": "\n".join(current_text)
        })

    return {
        "filename": file.filename,
        "page_count": len(pages),
        "topics": topics
    }
