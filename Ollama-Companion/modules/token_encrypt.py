import streamlit as st
from cryptography.fernet import Fernet
from pathlib import Path
import subprocess

# Function to load the existing key
def load_key():
    key_dir = Path('.') / '.key'
    key_file_path = key_dir / 'encryption.key'
    return key_file_path.read_bytes()

# Encrypt the token
def encrypt_token(token):
    key = load_key()
    f = Fernet(key)
    encrypted_token = f.encrypt(token.encode())
    return encrypted_token.decode()

def generate_new_key():
    key_dir = Path('.') / '.key'
    key_file_path = key_dir / 'encryption.key'
    
    # Check if the key file exists and delete it
    if key_file_path.exists():
        try:
            key_file_path.unlink()  # Deletes the file
            print("Existing key file deleted.")
        except Exception as e:
            return f"Error deleting existing key: {e}"

    # Generate new key
    root_dir = Path(__file__).parent.parent
    script_path = root_dir / 'key_generation.py'
    try:
        subprocess.run(['python3', str(script_path)], check=True)
        return "New private key generated successfully."
    except subprocess.CalledProcessError as e:
        return f"Error generating new key: {e}"
    
    
def show_token_encrypt_page():
    st.title("Token Encryption")

    token = st.text_input("Enter your Hugging Face Token", type="password")

    if st.button("Encrypt Token"):
        if token:
            encrypted_token = encrypt_token(token)
            st.text_area("Encrypted Token", encrypted_token, height=100)
        else:
            st.error("Please enter a token to encrypt.")

    if st.button("Generate New Private Key"):
        message = generate_new_key()
        st.text(message)

# Uncomment this line to run this script directly for testing
# show_token_encrypt_page()
    with st.expander("Token Encryption Guide", expanded=False):
        st.markdown("""
        **Token Encryption Guide**

        This page assists you in encrypting your Hugging Face token for enhanced security.

        **Why Encrypt Your Token?**
        
        Encrypting your Hugging Face token adds an extra layer of security, protecting it from unauthorized access. It is particularly useful when you deploy scripts in shared environments.

        **How to Encrypt Your Token:**

        1. **Enter Your Token:** Type your Hugging Face token into the input field.
        2. **Encrypt:** Click the 'Encrypt Token' button to encrypt your token.
        3. **Use Your Encrypted Token:** The encrypted token will be displayed. You can now use this encrypted token within this app for secure uploading to Hugging Face.
        4. **Secure Usage:** Store your encrypted token securely. It will be your secure key for uploads in this application.

        Encrypting your token ensures its security and enables you to upload to Hugging Face safely within this app.
        """)
