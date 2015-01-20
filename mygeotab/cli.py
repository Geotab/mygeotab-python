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
        return os.path.join(os.path.expanduser('~'), '.mygeotab')

    @staticmethod
    def _section_name(database):
        return 'session:{0}'.format(database)

    @staticmethod
    def session_names(config):
        if not config:
            return []
        names = []
        section_names = config.sections()
        for name in section_names:
            if ':' in name:
                names.append(name.split(':')[-1])
        return names

    def save(self):
        if not self.credentials:
            return
        config = configparser.ConfigParser()
        config.read(self._get_config_file())
        database = self.credentials.database

        if 'session' not in config.sections():
            config.add_section('session')
        config.set('session', 'last_database', database)

        section_name = self._section_name(database)
        if section_name not in config.sections():
            config.add_section(section_name)
        config.set(section_name, 'username', self.credentials.username)
        config.set(section_name, 'session_id', self.credentials.session_id)
        config.set(section_name, 'database', self.credentials.database)
        config.set(section_name, 'server', self.credentials.server)

        with open(self._get_config_file(), 'w') as configfile:
            config.write(configfile)

    def load(self, name=None):
        config = configparser.ConfigParser()
        config.read(self._get_config_file())
        try:
            if name is None:
                name = config.get('session', 'last_database')
            section_name = self._section_name(name)
            username = config.get(section_name, 'username')
            session_id = config.get(section_name, 'session_id')
            database = config.get(section_name, 'database')
            server = config.get(section_name, 'server')
            self.credentials = mygeotab.api.Credentials(username, session_id, database, server)
        except configparser.NoSectionError:
            self.credentials = None

    def get_sessions(self):
        config = configparser.ConfigParser()
        config.read(self._get_config_file())
        return self.session_names(config)

    def get_api(self):
        if self.credentials:
            return mygeotab.api.API.from_credentials(self.credentials)
        return None

    def login(self, username, password=None, database=None, server=None):
        if server:
            api = mygeotab.api.API(username=username, password=password, database=database, server=server)
        else:
            api = mygeotab.api.API(username=username, password=password, database=database)
        self.credentials = api.authenticate()
        self.save()

    def logout(self):
        if self.credentials:
            database = self.credentials.database
            section_name = self._section_name(database)
            config = configparser.ConfigParser()
            config.read(self._get_config_file())
            if config.get('session', 'last_database') == database:
                config.remove_option('session', 'last_database')
            config.remove_section(section_name)
            with open(self._get_config_file(), 'w') as configfile:
                config.write(configfile)
        self.credentials = None
        sys.exit(0)


@click.command(help='Log in to a MyGeotab server')
@click.option('--user', '-u', prompt='Username')
@click.option('--password', '-p', prompt='Password', hide_input=True)
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
            click.echo('Logged in as: %s\n\nUse `mygeotab console` to access the console.' % session.credentials)
    except mygeotab.api.AuthenticationException:
        click.echo('Incorrect credentials. Please try again.')


@click.command(help='Lists active sessions')
@click.pass_obj
def sessions(session):
    """
    Shows the current logged in sessions

    :param session: The current Session object
    """
    active_sessions = session.get_sessions()
    if len(active_sessions) == 0:
        click.echo('(No active sessions)')
        return
    for active_session in active_sessions:
        click.echo(active_session)


@click.command(help='Log out from a MyGeotab server')
@click.argument('database', nargs=1, required=False)
@click.pass_obj
def logout(session, database=None):
    """
    Logs out from a MyGeotab server, removing the saved credentials

    :param session: The current Session object
    :param database: The database name to log out from
    """
    session.load(database)
    session.logout()


@click.command(help="Launch an interactive MyGeotab console")
@click.argument('database', nargs=1, required=False)
@click.pass_obj
def console(session, database=None):
    """An interactive Python API console for MyGeotab

    After logging in via the `login` command, the console automatically populates a variable, `api` with an instance
    of the MyGeotab API object. The credentials are stored on your filesystem, so there's no need to log in each time
    you use the console.

    If IPython is installed, it will launch an interactive IPython console instead of the built-in Python console. The
    IPython console has numerous advantages over the stock Python console, including: colors, pretty printing,
    command auto-completion, and more.

    By default, all library objects are available as locals in the console, with api

    :param session: The current Session object
    :param database: The database name to open a console to
    """
    if not session.credentials:
        click.echo('Not logged in. Please login using the `login` command to set up this console')
        sys.exit(1)
    session.load(database)
    api = session.get_api()

    try:
        api.call('Get', 'User', search=dict(name=session.credentials.username))
    except mygeotab.api.AuthenticationException:
        click.echo('Your session has expired. Please login again using the `login` command')
        session.logout()
        sys.exit(1)

    methods = dict(api=api)
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
main.add_command(sessions)

if __name__ == '__main__':
    main()