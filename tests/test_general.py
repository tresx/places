import os
import unittest
import warnings

from flask import current_app
import psycopg2
from psycopg2.extras import DictCursor

from places import create_app
from places.auth import generate_csrf_token
from places.db import init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf-8')


class TestPlaces(unittest.TestCase):

    def setUp(self):
        # Ignore ResourceWarning on add places test
        warnings.filterwarnings("ignore",
                                category=ResourceWarning,
                                message="unclosed.*<ssl.SSLSocket.*>")

        # App fixture
        app = create_app({
            'TESTING': True,
            'DATABASE': 'postgres://postgres:password@localhost:5432/places_test',
            'API_KEY': os.getenv('API_KEY'),
        })
        with app.app_context():
            # Initialise test database with testing data
            init_db()
            with psycopg2.connect(dsn=current_app.config['DATABASE'],
                                  cursor_factory=DictCursor) as conn:
                conn.cursor().execute(_data_sql)
            conn.close()
        self.app = app

        # Client fixture
        self.client = app.test_client()

        # Runner fixture
        self.runner = app.test_cli_runner()

    ## Helper methods
    def register(self, email, password):
        return self.client.post('/auth/register',
                                data={
                                    'email': email,
                                    'password': password
                                },
                                follow_redirects=True)

    def login(self, email, password):
        return self.client.post('/auth/login',
                                data={'email': email, 'password': password},
                                follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    ## Basic test to check test setup
    def test_main_page(self):
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    ## Auth tests
    def test_valid_user_registration(self):
        response = self.register('user3@example.com', 'password')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account creation successful!', response.data)

    def test_duplicate_user_registration(self):
        response = self.register('user1@example.com', 'p')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User user1@example.com is already registered.',
                      response.data)

    def test_valid_login(self):
        response = self.login('user1@example.com', 'p')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'user1@example.com', response.data)

    def test_login_incorrect_email(self):
        response = self.login('wrong@example.com', 'p')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Incorrect email.', response.data)

    def test_login_incorrect_password(self):
        response = self.login('user1@example.com', 'wrong')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Incorrect password.', response.data)

    def test_logout(self):
        response = self.login('user1@example.com', 'p')
        self.assertIn(b'user1@example.com', response.data)
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are now logged out.', response.data)
        self.assertNotIn(b'user1@example.com', response.data)

    ## Places tests
    def test_locations(self):
        response = self.client.get('/locations?lat=52.2042&lng=0.118223')
        self.assertIn(b'The Eagle', response.data)

    def test_add_place(self):
        self.login('user1@example.com', 'p')
        response = self.client.post(
            '/add',
            data={'name': 'test place',
                  'description': 'test description',
                  'postcode': 'SW1A 1AA'},
            follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Location added!', response.data)

    def test_add_place_unauthorised(self):
        response = self.client.get('/add', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>Log In - Places</title>', response.data)

    def test_search_places(self):
        response = self.client.post(
            '/search',
            data={'name': 'The Eagle', 'description': '', 'postcode': ''},
            follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'The Eagle', response.data)
        # Check average rating display
        self.assertIn(b'4.5', response.data)

    def test_individual_place_page(self):
        # Check display of individual page on place/<place_id>
        response = self.client.get('/place/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'The Eagle', response.data)
        self.assertNotIn(b'Add review', response.data)
        self.login('user1@example.com', 'p')
        response = self.client.get('/place/1')
        self.assertIn(b'Add review', response.data)

    def test_add_review(self):
        self.login('user1@example.com', 'p')
        response = self.client.post(
            '/place/1',
            data={'rating': 3, 'review': 'average'},
            follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'average', response.data)
        self.assertIn(b'4', response.data)


if __name__ == '__main__':
    unittest.main()
