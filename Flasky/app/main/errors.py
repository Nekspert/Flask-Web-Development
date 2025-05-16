from flask import render_template

from . import bp


@bp.app_errorhandler(404)
def page_bot_found(e):
    return render_template('404.html'), 404


@bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500