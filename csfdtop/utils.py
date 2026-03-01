import hashlib


def get_name_year_hash(name, year):
    return hashlib.sha256(f"{name}{year}".encode()).hexdigest()
