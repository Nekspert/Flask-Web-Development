import re
import unittest

from app import db, create_app
from app.models import Role, User


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Stranger' in response.get_data(as_text=True))

    def test_register_and_login(self):
        email = 'tim1234@gmail.com'
        password = 'cat1234'
        response = self.client.post('/auth/register', data={
            'email': email,
            'username': 'timurka',
            'password': password,
            'password2': password
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.post('/auth/login', data={
            'email': email,
            'password': password,
            'remember_me': True}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('Hello,\s+timurka!', response.get_data(as_text=True)))
        self.assertTrue('You have not confirmed your account yet' in response.get_data(as_text=True))

        user = User.query.filter_by(email=email).first()
        token: str = user.generate_confirmation_token()
        response = self.client.get(f'/auth/confirm/{token}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have confirmed your account. Thanks!' in response.get_data(as_text=True))

        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have been logged out.' in response.get_data(as_text=True))
