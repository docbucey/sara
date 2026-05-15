"""
Basic tests for SARA Mama protocols and dispatcher
"""
import os
from sara_mamagen1 import MamaDispatcher

def test_word():
    dispatcher = MamaDispatcher()
    # Dummy test: file does not exist
    result = dispatcher.dispatch("word", {"docx_path": "nofile.docx", "required_sections": ["Intro"]})
    assert result["status"] == "ERROR" or result["status"] == "FAIL"

def test_excel():
    dispatcher = MamaDispatcher()
    result = dispatcher.dispatch("excel", {"excel_path": "nofile.xlsx", "required_sheets": ["Sheet1"], "required_columns": ["A"]})
    assert result["status"] == "ERROR" or result["status"] == "FAIL"

def test_email():
    dispatcher = MamaDispatcher()
    result = dispatcher.dispatch("email", {"email_data": {"to": "bademail", "from": "me@x", "subject": "Test", "body": "Hi"}})
    assert result["status"] == "FAIL"

def test_call():
    dispatcher = MamaDispatcher()
    result = dispatcher.dispatch("call", {"call_data": {"from": "123", "to": "456", "type": "voip"}})
    assert result["status"] == "FAIL"

def test_contacts():
    dispatcher = MamaDispatcher()
    dispatcher.mailroom.add_contact("Test User", "test@example.com")
    contacts = dispatcher.mailroom.list_contacts()
    assert any(c["email"] == "test@example.com" for c in contacts)
    dispatcher.mailroom.remove_contact("Test User", "test@example.com")
    contacts = dispatcher.mailroom.list_contacts()
    assert not any(c["email"] == "test@example.com" for c in contacts)

if __name__ == "__main__":
    test_word()
    test_excel()
    test_email()
    test_call()
    test_contacts()
    print("All basic tests passed.")
