import os

from flask_migrate import Migrate

from app import create_app, db
from app.models import User, Role, Permissions, Post, Comment

app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db, directory=os.path.join(os.path.dirname(__file__), 'migrations'))


@app.shell_context_processor
def make_shell_context() -> dict:
    return dict(db=db, User=User, Role=Role, Permissions=Permissions, Post=Post, Comment=Comment)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    with app.app_context():
        Role.insert_roles()
    app.run()
