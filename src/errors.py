class CashboxClientError(Exception):
    msg: str | None = None

    def __init__(self, msg: str | None = None):
        super().__init__(msg)


class CashboxConnectionError(CashboxClientError):
    pass


class CashboxDisconnectionError(CashboxClientError):
    pass


class CashboxAlreadyInUse(CashboxClientError):
    pass


class CashboxTaskError(CashboxClientError):
    pass


class NotConnectedToServer(CashboxClientError):
    pass
