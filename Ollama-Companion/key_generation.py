## Key_generation.py
from cryptography.fernet import Fernet
from pathlib import Path

def generate_key():
    key_dir = Path('.') / '.key'
    key_file_path = key_dir / 'encryption.key'

    if not key_file_path.exists():
        key = Fernet.generate_key()
        if not key_dir.exists():
            key_dir.mkdir(parents=True, exist_ok=True)
        with open(key_file_path, 'wb') as key_file:
            key_file.write(key)

# Call the function to ensure the key is generated when the module is imported
generate_key()
