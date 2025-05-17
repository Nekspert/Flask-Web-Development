from flask import Blueprint

bp = Blueprint('main', __name__)

from . import routes, errors
from ..models import Permissions


@bp.app_context_processor
def inject_permissions():
    return dict(Permissions=Permissions)
