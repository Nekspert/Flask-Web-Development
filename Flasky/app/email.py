from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from . import mail


def send_async_mail(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs) -> Thread:
    msg = Message(current_app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=current_app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    app = current_app._get_current_object()
    thr = Thread(target=send_async_mail, args=(app, msg))
    thr.start()
    return thr
