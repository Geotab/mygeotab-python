import code
import os.path
import pickle
import sys

import click

import mygeotab
import mygeotab.api


class Session(object):
    def __init__(self):
        self.api = None

    @staticmethod
    def get_save_path():
        return os.path.join(os.path.expanduser('~'), '.mygeotabsession')

    def _save(self):
        pickle.dump(self, open(self.get_save_path(), 'w+'))

    def get_call(self):
        if self.api:
            return self.api.call
        return lambda: None

    def login(self, username, password=None, database=None, server=None):
        if server:
            self.api = mygeotab.api.API(username, password, database, None, server)
        else:
            self.api = mygeotab.api.API(username, password, database)
        self.api.authenticate()
        self._save()

    def logout(self):
        self.api = None
        self._save()
        sys.exit(0)


@click.command(help='Log in to a MyGeotab server')
@click.argument('username')
@click.password_option()
@click.option('--database', default=None, help='The company name or database name')
@click.option('--server', default=None, help='The server (ie. my4.geotab.com)')
@click.pass_obj
def login(session, username, password, database, server):
    session.login(username, password, database, server)
    if session.api:
        click.echo('%s' % session.api.credentials)


@click.command(help='Log out from a MyGeotab server')
@click.pass_obj
def logout(session):
    session.logout()


@click.command(help="Launch a MyGeotab console")
@click.pass_obj
def play(session):
    if not session.api:
        click.echo("Not logged in. Please login using the `login` command to set up this console")
        sys.exit(1)
    methods = dict(api=session.api)
    mygeotab_version = 'MyGeotab Python Library {0}'.format(mygeotab.__version__)
    python_version = 'Python {0} on {1}'.format(sys.version.replace('\n', ''), sys.platform)
    has_credentials = session.api and session.api.credentials
    auth_line = ('Logged in as: %s' % session.api.credentials) if has_credentials else 'Not logged in'
    code.interact('\n'.join([mygeotab_version, python_version, auth_line]), local=methods)


@click.group()
@click.pass_context
def main(ctx):
    """An interactive Python API console for MyGeotab

    First, please use the `login` command to login and store credentials

    Then, you can use `play` to use the console. The credentials are stored on your filesystem, so there's no need to
    login each time you want to use the console.
    """
    try:
        ctx.obj = pickle.load(open(Session.get_save_path()))
    except IOError:
        ctx.obj = Session()


main.add_command(play)
main.add_command(login)
main.add_command(logout)

if __name__ == '__main__':
    main()