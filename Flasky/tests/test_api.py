import json
import re
import unittest
from base64 import b64encode

from flask import url_for

from app import db, create_app
from app.models import Role, User, Post, Comment


class APITestCase(unittest.TestCase):
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

    @staticmethod
    def get_api_headers(email, password) -> dict[str, str]:
        return {
            'Authorization': 'Basic ' + b64encode((email + ':' + password).encode('utf-8')).decode(),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_no_auth(self):
        response = self.client.get(url_for('api.get_posts'),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_not_found(self):
        response = self.client.get('wrong/url', headers=self.get_api_headers('name', 'passw'))
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['error'], 'Not Found')

    def test_bad_auth(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(username='tima', email='tim@gramil.com', password='cat123', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        response = self.client.get(url_for('api.get_posts'),
                                   headers=self.get_api_headers('tim@gramil.com', 'dog'))
        self.assertEqual(response.status_code, 401)

    def test_good_auth(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(username='tima', email='tim@gramil.com', password='cat123', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        response = self.client.get(url_for('api.get_user_followed_posts', id=u.id),
                                   headers=self.get_api_headers('tim@gramil.com', 'cat123'))
        self.assertEqual(response.status_code, 200)

    def test_token_auth(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(username='tima', email='tim@gramil.com', password='cat123', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        response = self.client.get(url_for('api.get_posts'),
                                   headers=self.get_api_headers('bad-token', ''))
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url_for('api.get_token'),
                                    headers=self.get_api_headers('tim@gramil.com', 'cat123'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']
        response = self.client.get(
            '/api/v1/posts/',
            headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

    def test_anonymous(self):
        response = self.client.get(
            '/api/v1/posts/',
            headers=self.get_api_headers('', ''))
        self.assertEqual(response.status_code, 401)

    def test_unconfirmed_account(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(username='tima', email='tim@gramil.com', password='cat123', role=r)
        db.session.add(u)
        db.session.commit()

        response = self.client.get(
            '/api/v1/posts/',
            headers=self.get_api_headers('tim@gramil.com', 'cat123'))
        self.assertEqual(response.status_code, 403)

    def test_posts(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(username='tima', email='tim@gramil.com', password='cat123', confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        response = self.client.get(url_for('api.get_posts'),
                                   headers=self.get_api_headers('tim@gramil.com', 'cat123'))
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIsNotNone(json_response.get('posts'))
        self.assertTrue(len(json_response['posts']) == 0)

        response = self.client.post(url_for('api.new_post'),
                                    headers=self.get_api_headers('tim@gramil.com', 'cat123'),
                                    data=json.dumps({'body': 'Hi everyone!'}))
        self.assertEqual(response.status_code, 201)

        response = self.client.get(url_for('api.get_post', id=1),
                                   headers=self.get_api_headers('tim@gramil.com', 'cat123'))
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertTrue(len(json_response) > 0)
        self.assertEqual('Hi everyone!', json_response['body'])

        response = self.client.put(url_for('api.edit_post', id=1),
                                   headers=self.get_api_headers('tim@gramil.com', 'cat123'),
                                   data=json.dumps({'body': 'Bye bye!'}))
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertTrue(len(json_response) > 0)
        self.assertFalse('Hi everyone!' == json_response['body'])
        self.assertEqual('Bye bye!', json_response['body'])

    def test_users(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='john@example.com', username='john',
                  password='cat', confirmed=True, role=r)
        u2 = User(email='susan@example.com', username='susan',
                  password='dog', confirmed=True, role=r)
        db.session.add_all([u1, u2])
        db.session.commit()

        response = self.client.get(
            f'/api/v1/users/{u1.id}',
            headers=self.get_api_headers('susan@example.com', 'dog'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'john')

        response = self.client.get(
            f'/api/v1/users/{u2.id}',
            headers=self.get_api_headers('susan@example.com', 'dog'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'susan')

    def test_comments(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='john@example.com', username='john',
                  password='cat', confirmed=True, role=r)
        u2 = User(email='susan@example.com', username='susan',
                  password='dog', confirmed=True, role=r)
        db.session.add_all([u1, u2])
        db.session.commit()

        post = Post(body='body of the post', author=u1)
        db.session.add(post)
        db.session.commit()

        response = self.client.post(
            f'/api/v1/posts/{post.id}/comments/',
            headers=self.get_api_headers('susan@example.com', 'dog'),
            data=json.dumps({'body': 'Good [post](http://example.com)!'}))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data(as_text=True))
        url = response.headers.get('Location')
        self.assertIsNotNone(url)
        self.assertEqual(json_response['body'], 'Good [post](http://example.com)!')
        self.assertEqual(re.sub('<.*?>', '', json_response['html_body']), 'Good post!')

        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['body'], 'Good [post](http://example.com)!')

        comment = Comment(body='Thank you!', author=u1, post=post)
        db.session.add(comment)
        db.session.commit()

        response = self.client.get(f'/api/v1/posts/{post.id}/comments/',
                                   headers=self.get_api_headers('susan@example.com', 'dog'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('comments'))
        self.assertEqual(json_response.get('count', 0), 2)
