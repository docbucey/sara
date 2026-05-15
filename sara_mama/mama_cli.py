"""
Mama CLI: Simple command-line interface for personal protocol actions
"""
import sys
import json
import os
from sara_mamagen1 import MamaDispatcher

def main():
    dispatcher = MamaDispatcher()
    print("SARA Mama CLI — Personal Work Environment")
    print("Type 'help' for commands. Type 'exit' to quit.")
    while True:
        cmd = input("mama> ").strip()
        if cmd in ("exit", "quit"):
            print("Goodbye!")
            break
        if cmd == "help":
                        print("""
Commands:
    word <docx_path> <section1,section2,...>         — Validate Word doc for sections
    excel <xlsx_path> <sheet1,sheet2> <col1,col2>    — Validate Excel for sheets/columns
    email <to> <from> <subject> <body>               — Validate email
    call <from> <to> <type>                          — Validate call/VoIP
    contacts <protocol>                              — List contacts (mailroom, switchboard, geek)
    add_contact <protocol> <name> <address> [roles]  — Add contact (mailroom: email, switchboard: number, geek: url [roles])
    remove_contact <protocol> <name> <address>       — Remove contact
    bridge_to_web_ai <name> <url> <task> [data]      — Bridge to web AI (geek)
    learn_from_interaction <name> <url> <json_data>  — Learn/scrape from web AI (geek)
    settings get <key> [default]                     — Get a setting
    settings set <key> <value>                       — Set a setting
    settings remove <key>                            — Remove a setting
    settings all                                     — Show all settings
    settings enable_night_shift [json_config]         — Enable night shift (optionally with config)
    settings disable_night_shift                     — Disable night shift
    settings night_shift_status                      — Show night shift enabled status
    settings set_bridge_roles <ai_name> <roles_csv>  — Set bridge AI roles (comma-separated)
    settings get_bridge_roles <ai_name>              — Get bridge AI roles for AI
    settings enable_training_mode [targets_csv]      — Enable training mode (optional targets)
    settings disable_training_mode                   — Disable training mode
    settings training_mode_status                    — Show training mode status
    ide diagnostics [ide] [research]                 — Launch IDE diagnostics/improvement mode (optionally specify IDE, research mode)
    ide research_window <url>                        — Launch research web window
    ide list_files [directory]                       — List files in directory
    ide open_file <file_path>                        — Show file content
    ide run_code_action <action> <file_path>         — Run code action (format, lint, etc.)
    help                                            — Show this help
    exit                                            — Quit
""")
                        continue
        try:
            parts = cmd.split()
            if not parts:
                continue
            action = parts[0]
            result = None
            if action == "word" and len(parts) >= 3:
                docx_path = parts[1]
                if not os.path.exists(docx_path):
                    print(f"File not found: {docx_path}")
                    continue
                sections = parts[2].split(",")
                result = dispatcher.dispatch("word", {"docx_path": docx_path, "required_sections": sections})
            elif action == "excel" and len(parts) >= 4:
                xlsx_path = parts[1]
                if not os.path.exists(xlsx_path):
                    print(f"File not found: {xlsx_path}")
                    continue
                sheets = parts[2].split(",")
                cols = parts[3].split(",")
                result = dispatcher.dispatch("excel", {"excel_path": xlsx_path, "required_sheets": sheets, "required_columns": cols})
            elif action == "email" and len(parts) >= 5:
                result = dispatcher.dispatch("email", {"email_data": {"to": parts[1], "from": parts[2], "subject": parts[3], "body": " ".join(parts[4:])}})
            elif action == "call" and len(parts) >= 4:
                result = dispatcher.dispatch("call", {"call_data": {"from": parts[1], "to": parts[2], "type": parts[3]}})
            elif action == "contacts" and len(parts) == 2:
                proto = parts[1]
                if proto == "mailroom":
                    result = dispatcher.mailroom.list_contacts()
                elif proto == "switchboard":
                    result = dispatcher.switchboard.list_contacts()
                elif proto == "geek":
                    result = dispatcher.dispatch("list_contacts_geek", {})
                else:
                    print("Unknown protocol for contacts. Use 'mailroom', 'switchboard', or 'geek'.")
                    continue
            elif action == "add_contact" and (len(parts) == 4 or len(parts) == 5):
                proto, name, addr = parts[1:4]
                if proto == "mailroom":
                    result = dispatcher.mailroom.add_contact(name, addr)
                elif proto == "switchboard":
                    result = dispatcher.switchboard.add_contact(name, addr)
                elif proto == "geek":
                    roles = parts[4].split(",") if len(parts) == 5 else None
                    result = dispatcher.dispatch("add_contact_geek", {"name": name, "url": addr, "roles": roles})
                else:
                    print("Unknown protocol for add_contact. Use 'mailroom', 'switchboard', or 'geek'.")
                    continue
            elif action == "remove_contact" and len(parts) == 4:
                proto, name, addr = parts[1:4]
                if proto == "mailroom":
                    result = dispatcher.mailroom.remove_contact(name, addr)
                elif proto == "switchboard":
                    result = dispatcher.switchboard.remove_contact(name, addr)
                elif proto == "geek":
                    result = dispatcher.dispatch("remove_contact_geek", {"identifier": name if name else addr})
                else:
                    print("Unknown protocol for remove_contact. Use 'mailroom', 'switchboard', or 'geek'.")
                    continue
            elif action == "bridge_to_web_ai" and len(parts) >= 4:
                name, url, task = parts[1:4]
                data = json.loads(parts[4]) if len(parts) > 4 else None
                result = dispatcher.dispatch("bridge_to_web_ai", {"name": name, "url": url, "task": task, "data": data})
            elif action == "learn_from_interaction" and len(parts) >= 4:
                name, url = parts[1:3]
                interaction_data = json.loads(parts[3]) if len(parts) > 3 else {}
                result = dispatcher.dispatch("learn_from_interaction", {"name": name, "url": url, "interaction_data": interaction_data})
            elif action == "settings" and len(parts) >= 2:
                sub = parts[1]
                if sub == "get" and len(parts) >= 3:
                    key = parts[2]
                    default = parts[3] if len(parts) > 3 else None
                    result = dispatcher.dispatch("settings_get", {"key": key, "default": default})
                elif sub == "set" and len(parts) >= 4:
                    key, value = parts[2], parts[3]
                    result = dispatcher.dispatch("settings_set", {"key": key, "value": value})
                elif sub == "remove" and len(parts) == 3:
                    key = parts[2]
                    result = dispatcher.dispatch("settings_remove", {"key": key})
                elif sub == "all":
                    result = dispatcher.dispatch("settings_all", {})
                elif sub == "enable_night_shift":
                    config = json.loads(parts[2]) if len(parts) > 2 else None
                    result = dispatcher.dispatch("settings_enable_night_shift", {"config": config})
                elif sub == "disable_night_shift":
                    result = dispatcher.dispatch("settings_disable_night_shift", {})
                elif sub == "night_shift_status":
                    result = dispatcher.dispatch("settings_night_shift_status", {})
                elif sub == "set_bridge_roles" and len(parts) == 4:
                    ai_name, roles_csv = parts[2], parts[3]
                    roles = [r.strip() for r in roles_csv.split(",") if r.strip()]
                    result = dispatcher.dispatch("settings_set_bridge_roles", {"ai_name": ai_name, "roles": roles})
                elif sub == "get_bridge_roles" and len(parts) == 3:
                    ai_name = parts[2]
                    result = dispatcher.dispatch("settings_get_bridge_roles", {"ai_name": ai_name})
                elif sub == "enable_training_mode":
                    targets = [t.strip() for t in parts[2].split(",")] if len(parts) > 2 else None
                    result = dispatcher.dispatch("settings_enable_training_mode", {"targets": targets})
                elif sub == "disable_training_mode":
                    result = dispatcher.dispatch("settings_disable_training_mode", {})
                elif sub == "training_mode_status":
                    result = dispatcher.dispatch("settings_training_mode_status", {})
                else:
                    print("Unknown settings command. Type 'help' for usage.")
                    continue
            elif action == "ide" and len(parts) >= 2:
                sub = parts[1]
                if sub == "diagnostics":
                    ide = parts[2] if len(parts) > 2 else "code"
                    research = (len(parts) > 3 and parts[3].lower() == "research")
                    result = dispatcher.dispatch("ide", {"command": "diagnostics_mode", "args": {"ide": ide, "research": research}})
                elif sub == "research_window" and len(parts) == 3:
                    url = parts[2]
                    result = dispatcher.dispatch("ide", {"command": "launch_research_window", "args": {"url": url}})
                elif sub == "list_files":
                    directory = parts[2] if len(parts) > 2 else "."
                    result = dispatcher.dispatch("ide", {"command": "list_files", "args": {"directory": directory}})
                elif sub == "open_file" and len(parts) == 3:
                    file_path = parts[2]
                    result = dispatcher.dispatch("ide", {"command": "open_file", "args": {"file_path": file_path}})
                elif sub == "run_code_action" and len(parts) == 4:
                    action_name, file_path = parts[2], parts[3]
                    result = dispatcher.dispatch("ide", {"command": "run_code_action", "args": {"action": action_name, "file_path": file_path}})
                else:
                    print("Unknown ide command. Type 'help' for usage.")
                    continue
            else:
                print("Unknown or malformed command. Type 'help' for usage.")
                continue
            if result is not None:
                if result.get("status") in ("ERROR", "error"):
                    print(f"Error: {result.get('reason', result.get('error', result))}")
                elif result.get("status") == "FAIL":
                    print(f"Validation failed: {json.dumps(result, indent=2, ensure_ascii=False)}")
                else:
                    print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
