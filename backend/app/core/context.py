"""Request-scoped context propagated through the ASGI call stack.

``RequestIdMiddleware`` sets the current request id at the edge of every HTTP
request; domain code (``app.core.events.build_event``) reads it to fill
``correlationId`` without threading the value through every call signature.
"""

import contextvars

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "devos_request_id",
    default=None,
)


def set_current_request_id(request_id: str) -> contextvars.Token[str | None]:
    return _request_id_var.set(request_id)


def reset_current_request_id(token: contextvars.Token[str | None]) -> None:
    _request_id_var.reset(token)


def get_current_request_id() -> str | None:
    return _request_id_var.get()
