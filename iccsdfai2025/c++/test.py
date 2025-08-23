from cryptography.fernet import Fernet

# Replace this with the ENCRYPTION_KEY from app.py
ENCRYPTION_KEY = b'-ghyUIji5aoY_kYQbRgGZyZyvYoSrp4tY4Gn4VRo1wI='  # Replace with your actual key
cipher_suite = Fernet(ENCRYPTION_KEY)

def decrypt_output(encrypted_output):
    try:
        # Decrypt the output
        decrypted_output = cipher_suite.decrypt(encrypted_output.encode()).decode()
        return decrypted_output
    except Exception as e:
        return f"Error during decryption: {str(e)}"

if __name__ == "__main__":
    print("=== Decryption Tool ===")
    encrypted_output = input("Enter the encrypted output: ").strip()
    decrypted_output = decrypt_output(encrypted_output)
    print("\nDecrypted Output:")
    print(decrypted_output)