from mealpilot.graph.graph import Recommendation


class SessionStore:
    def __init__(self) -> None:
        self._data: dict[str, list[Recommendation]] = {}

    def append(self, session_id: str, rec: Recommendation) -> None:
        self._data.setdefault(session_id, []).append(rec)

    def history(self, session_id: str) -> list[Recommendation]:
        return self._data.get(session_id, [])


_store = SessionStore()


def get_session_store() -> SessionStore:
    return _store
