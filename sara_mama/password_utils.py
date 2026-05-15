"""
Optional password protection for SARA Mama contacts (simple, not cryptographically strong)
"""
import getpass
import hashlib
import os

PASSWORD_FILE = os.path.join(os.path.dirname(__file__), "mama_password.txt")

def set_password():
    pw = getpass.getpass("Set new password: ")
    pw2 = getpass.getpass("Confirm password: ")
    if pw != pw2:
        print("Passwords do not match.")
        return
    h = hashlib.sha256(pw.encode()).hexdigest()
    with open(PASSWORD_FILE, "w") as f:
        f.write(h)
    print("Password set.")

def check_password():
    if not os.path.exists(PASSWORD_FILE):
        print("No password set.")
        return True
    pw = getpass.getpass("Enter password: ")
    h = hashlib.sha256(pw.encode()).hexdigest()
    with open(PASSWORD_FILE) as f:
        stored = f.read().strip()
    if h == stored:
        print("Access granted.")
        return True
    else:
        print("Access denied.")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "set":
        set_password()
    else:
        check_password()
