"""Generate an editable project draft from an uploaded project abstract."""
import hashlib
import json
import re
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

from fastapi import HTTPException, UploadFile, status

from app.services.ai_service import _call_gemini

MAX_ABSTRACT_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def _extract_docx(data: bytes) -> str:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    paragraphs = []
    for paragraph in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        text = "".join(node.text or "" for node in paragraph.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
        if text.strip():
            paragraphs.append(text.strip())
    return "\n".join(paragraphs)


def _extract_text(filename: str, data: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension in {".txt", ".md"}:
        return data.decode("utf-8", errors="replace")
    if extension == ".docx":
        try:
            return _extract_docx(data)
        except (KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "The Word document could not be read") from exc
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
        except ImportError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "PDF analysis is unavailable until the backend dependencies are installed") from exc
        except Exception as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "The PDF could not be read") from exc
    raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a .txt, .md, .pdf, or .docx abstract")


def _fallback_draft(text: str) -> dict:
    lines = [re.sub(r"^#+\s*", "", line).strip() for line in text.splitlines() if line.strip()]
    title = next((line for line in lines if line.lower() not in {"abstract", "project abstract"}), "New project")
    title = re.sub(r"^(project|title)\s*:\s*", "", title, flags=re.IGNORECASE).strip()[:200] or "New project"
    words = re.findall(r"[A-Za-z0-9]+", title.upper())
    prefix = "".join(words[:3])[:10] or "PROJECT"
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:4].upper()
    description = " ".join(lines[1:] if len(lines) > 1 else lines)[:2000]
    return {"code": f"{prefix}-{digest}", "name": title, "description": description or "Project generated from uploaded abstract."}


def analyze_abstract(file: UploadFile) -> dict:
    filename = file.filename or "abstract.txt"
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a .txt, .md, .pdf, or .docx abstract")
    data = file.file.read(MAX_ABSTRACT_BYTES + 1)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The uploaded abstract is empty")
    if len(data) > MAX_ABSTRACT_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "The abstract must be 5 MB or smaller")

    text = _extract_text(filename, data).strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No readable text was found in the abstract")

    fallback = _fallback_draft(text)
    prompt = (
        "Create a concise project draft from this abstract. Return JSON only with exactly these string fields: "
        "code, name, description. The code must be short uppercase letters/numbers with hyphens, the name a clear "
        "project title, and the description a faithful 1-3 sentence summary. Do not invent dates, people, or clients.\n\n"
        f"Abstract:\n{text[:12000]}"
    )
    ai_text = _call_gemini(prompt)
    if ai_text:
        match = re.search(r"\{[\s\S]*\}", ai_text)
        if match:
            try:
                draft = json.loads(match.group())
                if all(isinstance(draft.get(field), str) and draft[field].strip() for field in ("code", "name", "description")):
                    return {**draft, "ai_generated": True}
            except json.JSONDecodeError:
                pass
    return {**fallback, "ai_generated": False}