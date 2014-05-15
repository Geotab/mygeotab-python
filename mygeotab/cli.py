import os.path
import ConfigParser
import sys

import click

import mygeotab
import mygeotab.api


class Session(object):
    def __init__(self):
        self.credentials = None

    @staticmethod
    def get_config_file():
        return os.path.join(os.path.expanduser('~'), '.mygeotabsession')

    def save(self):
        if self.credentials:
            config = ConfigParser.ConfigParser()
            config.add_section('credentials')
            config.set('credentials', 'username', self.credentials.username)
            config.set('credentials', 'session_id', self.credentials.session_id)
            config.set('credentials', 'database', self.credentials.database)
            config.set('credentials', 'server', self.credentials.server)
            with open(self.get_config_file(), 'wb') as configfile:
                config.write(configfile)

    def load(self):
        config = ConfigParser.ConfigParser()
        config.read(self.get_config_file())
        username = config.get('credentials', 'username')
        session_id = config.get('credentials', 'session_id')
        database = config.get('credentials', 'database')
        server = config.get('credentials', 'server')
        self.credentials = mygeotab.api.Credentials(username, session_id, database, server)

    def get_api(self):
        if self.credentials:
            return mygeotab.api.API.load(self.credentials)
        return None

    def login(self, username, password=None, database=None, server=None):
        if server:
            api = mygeotab.api.API(username, password, database, None, server)
        else:
            api = mygeotab.api.API(username, password, database)
        self.credentials = api.authenticate()
        self.save()

    def logout(self):
        self.credentials = None
        self.save()
        sys.exit(0)


@click.command(help='Log in to a MyGeotab server')
@click.argument('username')
@click.password_option()
@click.option('--database', default=None, help='The company name or database name')
@click.option('--server', default=None, help='The server (ie. my4.geotab.com)')
@click.pass_obj
def login(session, username, password, database, server):
    try:
        session.login(username, password, database, server)
        if session.credentials:
            click.echo('Logged in as: %s' % session.credentials)
    except mygeotab.api.AuthenticationException:
        click.echo('Incorrect credentials. Please try again.')


@click.command(help='Log out from a MyGeotab server')
@click.pass_obj
def logout(session):
    session.logout()


@click.command(help="Launch a MyGeotab console")
@click.pass_obj
def play(session):
    if not session.credentials:
        click.echo("Not logged in. Please login using the `login` command to set up this console")
        sys.exit(1)
    methods = dict(api=session.get_api())
    mygeotab_version = 'MyGeotab Python Library {0}'.format(mygeotab.__version__)
    python_version = 'Python {0} on {1}'.format(sys.version.replace('\n', ''), sys.platform)
    auth_line = ('Logged in as: %s' % session.credentials) if session.credentials else 'Not logged in'
    banner = '\n'.join([mygeotab_version, python_version, auth_line])
    try:
        from IPython import embed

        embed(banner1=banner, user_ns=methods)
    except ImportError:
        import code

        code.interact(banner, local=methods)


@click.group()
@click.pass_context
def main(ctx):
    """An interactive Python API console for MyGeotab

    First, please run the `login` command to log in and store credentials.

    Then use `play` to use the console. The credentials are stored on your filesystem, so there's no need to
    log in each time you want to use the console.
    """
    ctx.obj = Session()
    try:
        ctx.obj.load()
    except IOError:
        pass


main.add_command(play)
main.add_command(login)
main.add_command(logout)

if __name__ == '__main__':
    main()