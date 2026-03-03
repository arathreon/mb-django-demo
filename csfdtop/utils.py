import hashlib
import unicodedata


def get_name_year_hash(name, year):
    """Hashes the name and year to create a unique identifier"""
    return hashlib.sha256(f"{name}{year}".encode()).hexdigest()


def normalize_text(text):
    """Removes diacritics and converts to lowercase"""
    if not text:
        return ""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()
