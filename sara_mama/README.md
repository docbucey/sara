# SARA Mama Personal Work Environment

## Overview
SARA Mama is a personal productivity and automation environment supporting:
- Word processing (Secretary)
- Spreadsheets (Accountant)
- Email (Mailroom)
- Slides/graphics (Marketing)
- Calls/VoIP (Switchboard)
- Persistent contacts for email and phone

## Getting Started
1. Run `mama_cli.py` for a simple command-line interface.
2. Use commands like `word`, `excel`, `email`, `call`, `contacts`, `add_contact`, `remove_contact`.
3. Contacts are saved automatically and persist across sessions.

## Protocol Actions
- **word**: Validate Word documents for required sections.
- **excel**: Validate Excel files for required sheets/columns.
- **email**: Validate email fields and addresses.
- **call**: Validate phone/VoIP call data.
- **contacts**: List contacts for mailroom or switchboard.
- **add_contact/remove_contact**: Manage contacts.

## Data & Storage
- Contacts are stored as JSON files in the same directory as the protocols.
- No cloud sync by default (local only).

## Security
- For personal use: no authentication by default.
- Optional: enable password or encryption (see below).

## Backup & Restore
- Copy the `*_contacts.json` files to back up your contacts.
- Restore by copying them back into the protocol directory.

## Automation
- You can script CLI commands or extend `mama_cli.py` for batch actions.

## Support
- For help, run `mama_cli.py` and type `help`.
- All code is local and modifiable for your needs.

---
