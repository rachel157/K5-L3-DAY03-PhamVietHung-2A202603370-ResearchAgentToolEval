import os

def save_note(filename: str, content: str, confirmed: bool = False) -> dict:
    if not confirmed:
        return {
            "awaiting_user": True,
            "message": f"Do you confirm saving the note to '{filename}'?"
        }
    if not filename or not isinstance(filename, str):
        return {"error": "Invalid filename provided."}
    try:
        safe_name = os.path.basename(filename.strip())
        if not safe_name.endswith(".md"):
            safe_name += ".md"
        os.makedirs("artifacts/notes", exist_ok=True)
        filepath = os.path.join("artifacts/notes", safe_name)
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