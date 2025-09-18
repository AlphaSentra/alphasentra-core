"""
Description:
Utility functions for encrypting and decrypting strings using a secret key from environment variables.
"""
import base64
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Load environment variables from .env file
load_dotenv()

#To encrypt strng, paste the content below into CONTENT_TO_ENCRYPT and run this script. The encrypted result will be printed out.
CONTENT_TO_ENCRYPT = """ """

#To decrypt string, paste the encrypted content below into ENCRYPTED_CONTENT and run this script. The decrypted result will be printed out.
ENCRYPTED_CONTENT = ''

def encrypt_string(plaintext, secret_key=None):
    """
    Encrypt a string using a secret key from environment variables.
    
    Parameters:
    plaintext (str): The string to encrypt
    secret_key (str, optional): The secret key to use for encryption. 
    If None, uses ENCRYPTION_SECRET from .env
    
    Returns:
    str: Base64 encoded encrypted string, or None if encryption fails
    """
    try:
        # Get secret key from environment if not provided
        if secret_key is None:
            secret_key = os.getenv("ENCRYPTION_SECRET")
            if not secret_key:
                raise ValueError("ENCRYPTION_SECRET not found in environment variables")
        
        # Derive a 32-byte key from the secret using PBKDF2
        salt = b'AlphagoraSalt_'  # Fixed salt for simplicity (in production, use random salt)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        
        # Create Fernet instance with the derived key
        fernet = Fernet(key)
        
        # Encrypt the plaintext
        encrypted = fernet.encrypt(plaintext.encode())
        
        return encrypted.decode()
        
    except ImportError:
        # Fallback to simple encryption if cryptography is not available
        print("Warning: cryptography library not installed. Using simple base64 encoding.")
        return base64.urlsafe_b64encode(plaintext.encode()).decode()
        
    except Exception as e:
        print(f"Error encrypting string: {e}")
        return None


def decrypt_string(encrypted_text, secret_key=None):
    """
    Decrypt a string that was encrypted with encrypt_string.
    
    Parameters:
    encrypted_text (str): The encrypted string to decrypt
    secret_key (str, optional): The secret key to use for decryption.
    If None, uses ENCRYPTION_SECRET from .env
    
    Returns:
    str: Decrypted plaintext string, or None if decryption fails
    """
    try:
        # Get secret key from environment if not provided
        if secret_key is None:
            secret_key = os.getenv("ENCRYPTION_SECRET")
            if not secret_key:
                raise ValueError("ENCRYPTION_SECRET not found in environment variables")

        # Derive a 32-byte key from the secret using PBKDF2
        salt = b'AlphagoraSalt_'  # Fixed salt for simplicity (in production, use random salt)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))

        # Create Fernet instance with the derived key
        fernet = Fernet(key)

        # Decrypt the encrypted text
        decrypted = fernet.decrypt(encrypted_text.encode())

        return decrypted.decode()

    except ImportError:
        # Fallback to simple decryption if cryptography is not available
        print("Warning: cryptography library not installed. Using simple base64 decoding.")
        return base64.urlsafe_b64decode(encrypted_text.encode()).decode()
    
    except Exception as e:
        print("=" * 100)
        print("Invalid decryption: ENCRYPTION_SECRET is incorrect or the encrypted text is corrupted.")
        print("=" * 100)
        print(f"{e}")
        return None


def main_menu():
    """
    Main menu for encryption/decryption operations.
    Provides interactive terminal interface for users.
    """
    print("=" * 50)
    print("Alphagora Encryption/Decryption Tool")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Encrypt a string")
        print("2. Decrypt a string")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            encrypt_menu()
        elif choice == "2":
            decrypt_menu()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def encrypt_menu():
    """Menu for encrypting a string"""
    print("\n--- Encrypt String ---")
    plaintext = CONTENT_TO_ENCRYPT
    
    if not plaintext:
        print("No content to encrypt. Returning to main menu.")
        return
    
    # Check if ENCRYPTION_SECRET is set
    secret_key = os.getenv("ENCRYPTION_SECRET")
    if not secret_key:
        print("Warning: ENCRYPTION_SECRET environment variable not found.")
        use_custom = input("Use custom secret key? (y/n): ").strip().lower()
        if use_custom == 'y':
            secret_key = input("Enter custom secret key: ").strip()
        else:
            print("Using default encryption (may be less secure).")
            secret_key = None
    
    encrypted = encrypt_string(plaintext, secret_key)
    if encrypted:
        print(f"\nEncrypted result:")
        print(f"{encrypted}")
        print(f"\nYou can copy this encrypted text for storage or transmission.")
    else:
        print("Encryption failed.")


def decrypt_menu():
    """Menu for decrypting the encrypted content constant"""
    print("\n--- Decrypt Content ---")
    encrypted_text = ENCRYPTED_CONTENT
    
    if not encrypted_text:
        print("No encrypted content found. Returning to main menu.")
        return
    
    # Check if ENCRYPTION_SECRET is set
    secret_key = os.getenv("ENCRYPTION_SECRET")
    if not secret_key:
        print("Warning: ENCRYPTION_SECRET environment variable not found.")
        use_custom = input("Use custom secret key? (y/n): ").strip().lower()
        if use_custom == 'y':
            secret_key = input("Enter custom secret key: ").strip()
        else:
            print("Using default decryption (may not work if encrypted with custom key).")
            secret_key = None
    
    decrypted = decrypt_string(encrypted_text, secret_key)
    if decrypted:
        print(f"\nDecrypted result:")
        print(f"{decrypted}")
    else:
        print("Decryption failed. Check your secret key")


if __name__ == "__main__":
    main_menu()