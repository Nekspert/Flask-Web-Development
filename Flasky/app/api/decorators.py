from typing import Callable
from functools import wraps

from flask import g

from .errors import forbidden


def permission_required(permission: int) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return func(*args, **kwargs)

        return wrapper

    return decorator
