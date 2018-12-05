import os
from dotenv import load_dotenv

from flask import Flask


def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY='dev',
        DATABASE=os.getenv('DATABASE_URL')
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        basedir = os.path.abspath(os.path.dirname(__file__))
        load_dotenv(os.path.join(basedir, 'config.env'))
        app.config.update(
            SECRET_KEY=os.getenv('SECRET_KEY'),
            API_KEY=os.getenv('API_KEY')
        )

    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # A simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import places
    app.register_blueprint(places.bp)
    app.add_url_rule('/', endpoint='index')

    return app

app = create_app()
