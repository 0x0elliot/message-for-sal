#!/usr/bin/env python3
"""
Message Encrypter for ESP32 Birthday Player
Use this to encrypt messages before uploading to GitHub
"""

import binascii

class MessageEncrypter:
    def __init__(self, encryption_key="SaloniKey2025"):
        self.encryption_key = encryption_key
    
    def encrypt_message(self, message):
        """Encrypt a message using XOR cipher"""
        encrypted_bytes = []
        key_len = len(self.encryption_key)
        
        for i, char in enumerate(message):
            key_char = self.encryption_key[i % key_len]
            encrypted_byte = ord(char) ^ ord(key_char)
            encrypted_bytes.append(encrypted_byte)
        
        # Convert to hex string
        hex_string = binascii.hexlify(bytes(encrypted_bytes)).decode('utf-8')
        return hex_string

    def decrypt_message(self, hex_string):
        """Decrypt a hex string back to readable text (for testing)"""
        try:
            # Convert hex to bytes
            encrypted_bytes = binascii.unhexlify(hex_string)
            
            # XOR decrypt
            decrypted = ""
            key_len = len(self.encryption_key)
            
            for i, byte in enumerate(encrypted_bytes):
                key_char = self.encryption_key[i % key_len]
                decrypted_char = chr(byte ^ ord(key_char))
                decrypted += decrypted_char
            
            return decrypted
        except Exception as e:
            return f"Error decrypting: {e}"
    
    def set_key(self, new_key):
        """Change the encryption key"""
        self.encryption_key = new_key
    
    def get_key(self):
        """Get the current encryption key"""
        return self.encryption_key

def main():
    # Create encrypter with default key
    encrypter = MessageEncrypter()
    
    print("🎂 ESP32 Birthday Player - Message Encrypter 🎂")
    print("=" * 50)
    print(f"Current encryption key: {encrypter.get_key()}")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Encrypt a new message")
        print("2. Test decrypt a message")
        print("3. Change encryption key")
        print("4. Exit")
        
        choice = input("\nChoose an option (1-4): ").strip()
        
        if choice == "1":
            print("\n📝 ENCRYPT MESSAGE")
            print("-" * 20)
            message = input("Enter your message: ")
            
            if message:
                encrypted = encrypter.encrypt_message(message)
                print(f"\n✅ ENCRYPTED MESSAGE (copy this to GitHub):")
                print(f"{'='*60}")
                print(encrypted)
                print(f"{'='*60}")
                print(f"\n📋 Instructions:")
                print(f"1. Copy the encrypted text above")
                print(f"2. Paste it into your GitHub file: message.txt")
                print(f"3. Commit and push the changes")
                print(f"4. Your ESP32 will show the decrypted message!")
            else:
                print("❌ No message entered!")
        
        elif choice == "2":
            print("\n🔍 TEST DECRYPT")
            print("-" * 20)
            hex_input = input("Enter encrypted hex string: ").strip()
            
            if hex_input:
                decrypted = encrypter.decrypt_message(hex_input)
                print(f"\n📖 Decrypted message: {decrypted}")
            else:
                print("❌ No hex string entered!")
        
        elif choice == "3":
            print("\n🔑 CHANGE ENCRYPTION KEY")
            print("-" * 25)
            print(f"Current key: {encrypter.get_key()}")
            new_key = input("Enter new encryption key: ").strip()
            
            if new_key:
                encrypter.set_key(new_key)
                print(f"✅ Key changed to: {encrypter.get_key()}")
                print("⚠️  Remember to update the key in your ESP32 code too!")
            else:
                print("❌ No key entered!")
        
        elif choice == "4":
            print("\n👋 Goodbye! Happy Birthday Saloni! 🎂❤️")
            break
        
        else:
            print("❌ Invalid choice! Please enter 1, 2, 3, or 4.")

# Example messages for quick testing
EXAMPLE_MESSAGES = [
    "I love you chotu" 
]

if __name__ == "__main__":
    # Show examples with default encrypter
    demo_encrypter = MessageEncrypter()
    
    print("\n🎁 Quick Examples:")
    print("-" * 20)
    for i, msg in enumerate(EXAMPLE_MESSAGES[:3], 1):
        encrypted = demo_encrypter.encrypt_message(msg)
        print(f"{i}. '{msg}'")
        print(f"   → {encrypted[:50]}...")
    
    print("\n" + "="*60)
    main()
