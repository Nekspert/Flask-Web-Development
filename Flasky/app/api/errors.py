from flask import jsonify

from . import bp
from ..exceptions import ValidationError


def bad_request(message: str):
    response = jsonify({'error': 'Bad Request', 'message': message})
    response.status_code = 400
    return response


def forbidden(message: str):
    response = jsonify({'error': 'Forbidden', 'message': message})
    response.status_code = 403
    return response


def unauthorized(message):
    response = jsonify({'error': 'Unauthorized', 'message': message})
    response.status_code = 401
    return response


@bp.errorhandler(ValidationError)
def validation_error(e: ValidationError):
    return bad_request(e.args[0])
