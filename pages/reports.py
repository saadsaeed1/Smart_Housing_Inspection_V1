def image_to_base64(img_path_str: str) -> str:
    """Converts a local image path to a base64 data URI for reliable HTML document embedding."""
    if not img_path_str or str(img_path_str).strip() in ["", "nan", "None"]:
        return ""
    
    raw_str = str(img_path_str).strip()
    candidate_paths = [
        Path(raw_str),
        PROJECT_ROOT / raw_str,
        Path.cwd() / raw_str,
    ]
    
    target_path = None
    for p in candidate_paths:
        if p.exists() and p.is_file():
            target_path = p
            break

    if not target_path:
        return ""

    try:
        suffix = target_path.suffix.lower().replace(".", "")
        mime = "image/jpeg" if suffix in ["jpg", "jpeg"] else f"image/{suffix}"
        with open(target_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""