import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage

    COV = coverage.coverage(branch=True, include='Flasky/app/*')
    COV.start()

import sys
import click

from flask_migrate import Migrate

from app import create_app, db
from app.models import User, Role, Permissions, Post, Comment

app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db, directory=os.path.join(os.path.dirname(__file__), 'migrations'))


@app.shell_context_processor
def make_shell_context() -> dict:
    return dict(db=db, User=User, Role=Role, Permissions=Permissions, Post=Post, Comment=Comment)


@app.cli.command()
@click.option('--coverage/--no-coverage', 'coverage_', default=False,
              help='Run tests under code coverage.')
def test(coverage_):
    """Run the unit tests."""
    if coverage_ and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print(f'HTML version: file://{covdir}/index.html')
        COV.erase()


if __name__ == '__main__':
    with app.app_context():
        Role.insert_roles()
    app.run()
