"""
Simple backup and restore for SARA Mama contacts
"""
import shutil
import os

CONTACT_FILES = [
    "mailroom_contacts.json",
    "switchboard_contacts.json"
]

BACKUP_DIR = "backup_contacts"

def backup_contacts():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for fname in CONTACT_FILES:
        src = os.path.join(os.path.dirname(__file__), fname)
        dst = os.path.join(BACKUP_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Backed up {fname} to {BACKUP_DIR}/")
        else:
            print(f"No file to backup: {fname}")

def restore_contacts():
    for fname in CONTACT_FILES:
        src = os.path.join(BACKUP_DIR, fname)
        dst = os.path.join(os.path.dirname(__file__), fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Restored {fname} from {BACKUP_DIR}/")
        else:
            print(f"No backup found for: {fname}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_contacts()
    else:
        backup_contacts()
