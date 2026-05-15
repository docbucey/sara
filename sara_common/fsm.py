"""
Canonical ShuntFSM — the ONE shared finite state machine for shunt/evolution
routing across all five SARA pillars.

All pillar modules should import from here instead of defining their own copy.
"""

from typing import Any, Dict, List, Optional, Tuple


class ShuntFSM:
    """
    Minimal finite state machine for shunt/evolution routing.
    Accepts commands, manages state, and walks transitions.

    Parameters
    ----------
    states : Dict[str, int]
        Mapping of state names to numeric identifiers.
    transitions : Dict[str, Any]
        Mapping of ``(state, command)`` keys to ``(next_state, action_fn)``
        tuples.  ``action_fn`` may be ``None``.
    initial_state : str, optional
        Starting state name.  Defaults to the first state whose numeric id
        is ``0``, or the first key in *states* if no zero-id exists.
    """

    def __init__(
        self,
        states: Dict[str, int],
        transitions: Dict[str, Any],
        initial_state: Optional[str] = None,
    ):
        self.states = states
        self.transitions = transitions
        self._state: str = initial_state or self._default_initial(states)
        self._initial_state: str = self._state
        self.history: List[Tuple[str, str, str, Any]] = []
        self.improvements: List[Tuple[str, str, str, Any]] = []
        self.max_improvements = 10

    @staticmethod
    def _default_initial(states: Dict[str, int]) -> str:
        for name, sid in states.items():
            if sid == 0:
                return name
        return next(iter(states))

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        self._state = value

    def handle(self, command: str, payload: Any = None) -> dict:
        """Look up the transition for (current_state, command).

        If a handler function is registered it is called with *payload* (when
        provided).  Returns a result dict with ``success``, ``state``, and
        ``result`` keys.
        """
        key = (self._state, command)
        if key not in self.transitions:
            return {"success": False, "error": f"No transition for ({self._state}, {command})"}

        next_state, action_fn = self.transitions[key]
        if action_fn and payload is not None:
            result = action_fn(payload)
        elif action_fn:
            result = action_fn()
        else:
            result = None

        record = (self._state, command, next_state, result)
        self.history.append(record)
        self._state = next_state

        if len(self.improvements) < self.max_improvements:
            self.improvements.append(record)

        return {"success": True, "state": self._state, "result": result}

    def get_state(self) -> str:
        """Return current state name."""
        return self._state

    def reset(self, state: Optional[str] = None) -> None:
        """Reset FSM to *state* (or its original initial state)."""
        self._state = state or self._initial_state
        self.history.clear()
        self.improvements.clear()

    def get_history(self) -> List[Tuple[str, str, str, Any]]:
        return list(self.history)

    def get_first_ten_improvements(self) -> List[Tuple[str, str, str, Any]]:
        return list(self.improvements)
