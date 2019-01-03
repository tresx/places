import os
import unittest

from places import create_app
from places.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb'):
    _data_sql = f.read().decode('utf-8')


class TestPlaces(unittest.TestCase):

    def setUp(self):

        # App fixture
        # TODO: Set up temporary postgres database URL
        app = create_app({
            'TESTING': True,
            'DATABASE_URL': None,
        })

        with app.app_context():
            init_db()
            # TODO: This needs rewriting to work with psycopg2
            get_db().executescript(_data_sql)

        self.app = app

        # Client fixture
        self.client = app.test_client()

        # Runner fixture
        self.runner = app.test_cli_runner()

    def test_something(self):
        self.assertEqual('foo', 'foo')


if __name__ == '__main__':
    unittest.main()
