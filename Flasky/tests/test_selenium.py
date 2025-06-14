import threading
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By

from app import create_app, db, fake
from app.models import Role, User


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # start chrome
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        try:
            cls.client = webdriver.Chrome(options=options)
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.client:
            # create the application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # suppress logging to keep unittest output clean
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel('ERROR')

            # create the database and populate with some fake data
            db.create_all()
            Role.insert_roles()
            fake.users(10)
            fake.posts(10)

            # add an administrator user
            admin_role = Role.query.filter_by(permissions='Administrator').first()
            admin = User(email='john@example.com',
                         username='john', password='cat',
                         role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # start the Flask server in a thread
            cls.server_thread = threading.Thread(
                target=cls.app.run, kwargs={'debug': False,
                                            'use_reloader': False,
                                            'use_debugger': False})
            cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the Flask server and the browser
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            # destroy database
            db.drop_all()
            db.session.remove()

            # remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        self.client.get('http://localhost:5000/')
        self.assertTrue('Hello, Stranger!', self.client.page_source)

        self.client.find_element(by=By.LINK_TEXT, value='Log In').click()
        self.assertIn('<h1>Login</h1>', self.client.page_source)
        # log in
        self.client.find_element(by=By.NAME, value='email'). \
            send_keys('john@example.com')
        self.client.find_element(by=By.NAME, value='password').send_keys('cat')
        self.client.find_element(by=By.NAME, value='submit').click()
        self.assertTrue('Hello, john!', self.client.page_source)
        # navigate to the user's profile page
        self.client.find_element(by=By.LINK_TEXT, value='Profile').click()
        self.assertIn('<h1>john</h1>', self.client.page_source)
