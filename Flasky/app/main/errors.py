from flask import render_template, request, jsonify

from . import bp


@bp.app_errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:  # checks the "Accept" request header
        response = jsonify({'error': 'Forbidden'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403


@bp.app_errorhandler(404)
def page_bot_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:  # checks the "Accept" request header
        response = jsonify({'error': 'Not Found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@bp.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:  # checks the "Accept" request header
        response = jsonify({'error': 'Internal Server Error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500
