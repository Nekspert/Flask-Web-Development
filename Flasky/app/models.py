from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager


@login_manager.user_loader
def user_load(user_id):
    return User.query.get(int(user_id))


class Role(db.Model):
    __tablename__ = 'roles'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)

    users: so.DynamicMapped[Optional['User']] = so.relationship('User', back_populates='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role "{self.name}">'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(128))
    confirmed: so.Mapped[bool] = so.mapped_column(default=False)

    role_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('roles.id'))
    role: so.Mapped[Optional[Role]] = so.relationship(Role, back_populates='users')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self) -> str:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id})

    def confirm(self, token: str | bytes, expiration: int = 3600) -> bool:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode(), max_age=expiration)
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        except Exception:
            return False

        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self) -> str:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        return s.dumps({'reset': self.id})

    @staticmethod
    def reset_password(token: str | bytes, new_password: str, expiration: int = 3600) -> bool:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode(), max_age=expiration)
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        except Exception:
            return False

        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email: str) -> str:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        return s.dumps({
            'change_email': self.id, 'new_email': new_email
        })

    def change_email(self, token: str | bytes, expiration: int = 3600) -> bool:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode(), max_age=expiration)
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        except Exception:
            return False

        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def __repr__(self):
        return f'<User "{self.username}">'
