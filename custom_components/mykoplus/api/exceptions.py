from __future__ import annotations

class MykoPlusError(Exception):
    pass

class MykoPlusConnectionError(MykoPlusError):
    pass

class MykoPlusAuthError(MykoPlusError):
    pass

class MykoPlusApiError(MykoPlusError):

    def __init__(self, code: int | None, err_id: str | None, message: str) -> None:
        self.code = code
        self.err_id = err_id
        self.message = message
        super().__init__(f'[{code}/{err_id}] {message}')
