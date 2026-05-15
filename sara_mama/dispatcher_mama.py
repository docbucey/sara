"""Central FSM/dispatcher for protocol routing in MAMA."""

from typing import Any, Dict

from .secretary_protocol import SecretaryProtocol
from .accountant_protocol import AccountantProtocol
from .mailroom_protocol import MailroomProtocol
from .marketing_protocol import MarketingProtocol
from .switchboard_protocol import SwitchboardProtocol
from .settings_protocol import SettingsProtocol
from .geek_protocol import (
    add_contact as geek_add_contact,
    list_contacts as geek_list_contacts,
    remove_contact as geek_remove_contact,
)

SARA_MAMA_HEADER_BYTE0 = 0x01
SARA_MAMA_HEADER_BYTE1 = 0x3A
SARA_MAMA_HEADER_BYTE2 = 0x01
SARA_MAMA_HEADER_BYTE3 = 0xD2
SARA_MAMA_HEADER_BYTE4 = 0xB0
SARA_MAMA_HEADER_BYTE5 = 0x51

SARA_MAMA_BINARY_SPECIAL_HEADER_BYTES = bytes([
    SARA_MAMA_HEADER_BYTE0,
    SARA_MAMA_HEADER_BYTE1,
    SARA_MAMA_HEADER_BYTE2,
    SARA_MAMA_HEADER_BYTE3,
    SARA_MAMA_HEADER_BYTE4,
    SARA_MAMA_HEADER_BYTE5,
])


class MamaDispatcher:
    def __init__(self):
        self.secretary = SecretaryProtocol()
        self.accountant = AccountantProtocol()
        self.mailroom = MailroomProtocol()
        self.marketing = MarketingProtocol()
        self.switchboard = SwitchboardProtocol()
        self.settings = SettingsProtocol()

    def dispatch(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route the request to the correct protocol handler based on task_type.
        All orchestration and security checks flow through control FSM/shunt header logic.
        This ensures Mama is always slaved to control for backend actions.
        """
        payload = dict(payload)
        payload['mama_shunt_header'] = SARA_MAMA_BINARY_SPECIAL_HEADER_BYTES
        if task_type == "word":
            return self.secretary.handle(payload)
        elif task_type == "excel":
            return self.accountant.handle(payload)
        elif task_type == "email":
            return self.mailroom.handle(payload)
        elif task_type == "call":
            return self.switchboard.handle(payload)
        elif task_type == "marketing":
            return self.marketing.handle(payload)
        elif task_type == "settings":
            return self.settings.handle(payload)
        elif task_type == "list_contacts_geek":
            return geek_list_contacts()
        elif task_type == "add_contact_geek":
            return geek_add_contact(payload.get("name"), payload.get("url"), payload.get("roles"))
        elif task_type == "remove_contact_geek":
            return geek_remove_contact(payload.get("name"), payload.get("url"))
        else:
            return {"error": f"Unknown task_type: {task_type}"}
