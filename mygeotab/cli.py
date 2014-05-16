# -*- coding: utf-8 -*-

import os.path

try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import sys

import click

import mygeotab
import mygeotab.api


class Session(object):
    def __init__(self):
        self.credentials = None

    @staticmethod
    def _get_config_file():
        return os.path.join(os.path.expanduser('~'), '.mygeotabsession')

    def save(self):
        if self.credentials:
            config = configparser.ConfigParser()
            config.add_section('credentials')
            config.set('credentials', 'username', self.credentials.username)
            config.set('credentials', 'session_id', self.credentials.session_id)
            config.set('credentials', 'database', self.credentials.database)
            config.set('credentials', 'server', self.credentials.server)
            with open(self._get_config_file(), 'w') as configfile:
                config.write(configfile)
        else:
            open(self._get_config_file(), 'w').close()

    def load(self):
        config = configparser.ConfigParser()
        config.read(self._get_config_file())
        try:
            username = config.get('credentials', 'username')
            session_id = config.get('credentials', 'session_id')
            database = config.get('credentials', 'database')
            server = config.get('credentials', 'server')
            self.credentials = mygeotab.api.Credentials(username, session_id, database, server)
        except configparser.NoSectionError:
            self.credentials = None

    def get_api(self):
        if self.credentials:
            return mygeotab.api.API.from_credentials(self.credentials)
        return None

    def login(self, username, password=None, database=None, server=None):
        if server:
            api = mygeotab.api.API(username, password, database, server)
        else:
            api = mygeotab.api.API(username, password, database)
        self.credentials = api.authenticate()
        self.save()

    def logout(self):
        self.credentials = None
        self.save()
        sys.exit(0)


@click.command(help='Log in to a MyGeotab server')
@click.option('--user', '-u', prompt='Username')
@click.password_option()
@click.option('--database', default=None, help='The company name or database name')
@click.option('--server', default=None, help='The server (ie. my4.geotab.com)')
@click.pass_obj
def login(session, user, password, database, server):
    """
    Logs into a MyGeotab server and stores the returned credentials

    :param session: The current Session object
    :param username: The username used for MyGeotab servers. Usually an email address.
    :param password: The password associated with the username. Optional if `session_id` is provided.
    :param database: The database or company name. Optional as this usually gets resolved upon authentication.
    :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
    """
    try:
        session.login(user, password, database, server)
        if session.credentials:
            click.echo('Logged in as: %s' % session.credentials)
    except mygeotab.api.AuthenticationException:
        click.echo('Incorrect credentials. Please try again.')


@click.command(help='Log out from a MyGeotab server')
@click.pass_obj
def logout(session):
    """
    Logs out from a MyGeotab server, removing the saved credentials

    :param session: The current Session object
    """
    session.logout()


@click.command(help="Launch an interactive MyGeotab console")
@click.pass_obj
def console(session):
    """An interactive Python API console for MyGeotab

    After logging in via the `login` command, the console automatically populates a variable, `api` with an instance
    of the MyGeotab API object. The credentials are stored on your filesystem, so there's no need to log in each time
    you use the console.

    If IPython is installed, it will launch an interactive IPython console instead of the built-in Python console. The
    IPython console has numerous advantages over the stock Python console, including: colors, pretty printing,
    command auto-completion, and more
    """
    if not session.credentials:
        click.echo("Not logged in. Please login using the `login` command to set up this console")
        sys.exit(1)
    methods = dict(api=session.get_api())
    mygeotab_version = 'MyGeotab Python Console {0}'.format(mygeotab.__version__)
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
@click.version_option()
@click.pass_context
def main(ctx):
    """MyGeotab Python SDK command line tools

    You must first `login` if this is your first time using these tools.
    """
    ctx.obj = Session()
    try:
        ctx.obj.load()
    except IOError:
        pass


main.add_command(console)
main.add_command(login)
main.add_command(logout)

if __name__ == '__main__':
    main()