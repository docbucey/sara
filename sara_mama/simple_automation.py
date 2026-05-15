"""
Simple automation example for SARA Mama: batch add contacts
"""
from sara_mamagen1 import MamaDispatcher

def batch_add_mailroom_contacts(contact_list):
    dispatcher = MamaDispatcher()
    for name, email in contact_list:
        result = dispatcher.mailroom.add_contact(name, email)
        print(f"Added: {name} <{email}> — {result['status']}")

def batch_add_switchboard_contacts(contact_list):
    dispatcher = MamaDispatcher()
    for name, number in contact_list:
        result = dispatcher.switchboard.add_contact(name, number)
        print(f"Added: {name} [{number}] — {result['status']}")

if __name__ == "__main__":
    # Example usage
    mail_contacts = [("Alice", "alice@example.com"), ("Bob", "bob@example.com")]
    phone_contacts = [("Alice", "+1234567890"), ("Bob", "+1987654321")]
    batch_add_mailroom_contacts(mail_contacts)
    batch_add_switchboard_contacts(phone_contacts)
