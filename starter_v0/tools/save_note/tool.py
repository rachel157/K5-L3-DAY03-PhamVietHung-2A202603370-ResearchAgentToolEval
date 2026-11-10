import os
from tools._shared import ROOT

NOTES_DIR = ROOT / "artifacts" / "notes"

def save_note(filename: str, content: str, confirmed: bool = False) -> dict:
    if confirmed is not True:
        question = f"Do you confirm saving the note to '{filename}'?"
        return {
            "awaiting_user": True,
            "question": question,
            "response_type": "yes_no",
            "message": question,
        }
    if not filename or not isinstance(filename, str):
        return {"error": "Invalid filename provided."}
    if not isinstance(content, str):
        return {"error": "Content must be a string."}
    try:
        safe_name = os.path.basename(filename.strip())
        if safe_name in {"", ".", ".."}:
            return {"error": "Invalid filename provided."}
        if not safe_name.endswith(".md"):
            safe_name += ".md"
        os.makedirs(NOTES_DIR, exist_ok=True)
        filepath = os.path.join(NOTES_DIR, safe_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content or "")
        return {
            "success": True,
            "filename": safe_name,
            "path": filepath,
            "message": f"Successfully saved note to {filepath}"
        }
    except Exception as e:
        return {"error": f"Failed to save note: {str(e)}"}
