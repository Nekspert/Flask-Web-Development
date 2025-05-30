import datetime
import time
import unittest

from app import db, create_app
from app.models import User, Permissions, AnonymousUser, Role, Follow


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_confirmed(self):
        u = User()
        self.assertFalse(u.confirmed)

    def test_confirm_verification_expired(self):
        u = User(email='tim@12.gmail.com', username='pass', password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertFalse(u.confirmed)
        token = u.generate_confirmation_token()
        time.sleep(3)
        self.assertFalse(u.confirm(token, expiration=0))

    def test_confirm_verification(self):
        u = User()
        self.assertFalse(u.confirmed)
        token2 = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token2, expiration=0))

    def test_valid_reset_token(self):
        u = User(email='tim@12.gmail.com', username='pass', password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_invalid_reset_token(self):
        u = User(email='tim@12.gmail.com', username='pass', password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertFalse(User.reset_password(token + 'a', 'horse'))
        self.assertTrue(u.verify_password('cat'))

    def test_valid_email_change_token(self):
        u = User(email='john@example.com', username='pass', password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('susan@example.org')
        self.assertTrue(u.change_email(token))
        self.assertTrue(u.email == 'susan@example.org')

    def test_invalid_email_change_token(self):
        u1 = User(email='john@example.com', username='pass1', password='cat')
        u2 = User(email='susan@example.org', username='pass2', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_email_change_token('david@example.net')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'susan@example.org')

    def test_duplicate_email_change_token(self):
        u1 = User(email='john@example.com', username='pass1', password='cat')
        u2 = User(email='susan@example.org', username='pass2', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u2.generate_email_change_token('john@example.com')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'susan@example.org')

    def test_user_role(self):
        u = User(email='sad', username='asd', password='12')

        self.assertTrue(u.can(Permissions.FOLLOW.value))
        self.assertTrue(u.can(Permissions.WRITE.value))
        self.assertTrue(u.can(Permissions.COMMENT.value))
        self.assertFalse(u.can(Permissions.MODERATE.value))
        self.assertFalse(u.can(Permissions.ADMIN.value))

    def test_moderator_role(self):
        r = Role.query.filter_by(name='Moderator').first()
        u = User(email='john@example.com', password='cat', role=r)
        self.assertTrue(u.can(Permissions.FOLLOW.value))
        self.assertTrue(u.can(Permissions.COMMENT.value))
        self.assertTrue(u.can(Permissions.WRITE.value))
        self.assertTrue(u.can(Permissions.MODERATE.value))
        self.assertFalse(u.can(Permissions.ADMIN.value))

    def test_administrator_role(self):
        r = Role.query.filter_by(name='Administrator').first()
        u = User(email='john@example.com', password='cat', role=r)
        self.assertTrue(u.can(Permissions.FOLLOW.value))
        self.assertTrue(u.can(Permissions.COMMENT.value))
        self.assertTrue(u.can(Permissions.WRITE.value))
        self.assertTrue(u.can(Permissions.MODERATE.value))
        self.assertTrue(u.can(Permissions.ADMIN.value))

    def test_anonymous_user(self):
        u = AnonymousUser()

        self.assertFalse(u.can(Permissions.FOLLOW))
        self.assertFalse(u.can(Permissions.COMMENT))
        self.assertFalse(u.can(Permissions.WRITE))
        self.assertFalse(u.can(Permissions.MODERATE))
        self.assertFalse(u.can(Permissions.ADMIN))

    def test_timestamps(self):
        u = User(email='tim@12.gmail.com', username='pass', password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertTrue(
            (datetime.datetime.utcnow() - u.moment_since).total_seconds() < 3)
        self.assertTrue(
            (datetime.datetime.utcnow() - u.last_seen).total_seconds() < 3)

    def test_ping(self):
        u = User(email='tim@12.gmail.com', username='pass', password='cat')
        db.session.add(u)
        db.session.commit()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_follows(self):
        u1 = User(email='tim@1.gmail.com', username='pass1', password='cat')
        u2 = User(email='tim@2.gmail.com', username='pass2', password='cat')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))

        timestamp_before = datetime.datetime.utcnow()
        f = Follow(follower_id=u1.id, followed_id=u2.id)
        db.session.add(f)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))
        timestamp_after = datetime.datetime.utcnow()
        self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
