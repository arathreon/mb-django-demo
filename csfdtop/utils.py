import unicodedata


def normalize_text(text: str) -> str:
    """Removes diacritics and converts to lowercase"""
    if not text:
        return ""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()
