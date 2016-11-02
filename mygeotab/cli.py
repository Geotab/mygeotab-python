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
import mygeotab.dates


class Session(object):
    def __init__(self):
        self.credentials = None

    @staticmethod
    def _get_config_file():
        config_path = click.get_app_dir(mygeotab.__title__)
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        return os.path.join(config_path, 'config.ini')

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
                sections = config.sections()
                if len(sections) < 1:
                    self.credentials = None
                    return
                section_name = sections[-1]
            else:
                section_name = self._section_name(name)
            username = config.get(section_name, 'username')
            session_id = config.get(section_name, 'session_id')
            database = config.get(section_name, 'database')
            server = config.get(section_name, 'server')
            self.credentials = mygeotab.api.Credentials(username, session_id, database, server)
        except configparser.NoSectionError:
            self.credentials = None
        except configparser.NoOptionError:
            self.credentials = None

    def get_sessions(self):
        config = configparser.ConfigParser()
        config.read(self._get_config_file())
        return self.session_names(config)

    def get_api(self):
        if self.credentials:
            return mygeotab.api.from_credentials(self.credentials)
        return None

    def login(self, username, password=None, database=None, server=None):
        if server:
            api = mygeotab.api.API(username=username, password=password, database=database,
                                   server=server)
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
            config.remove_section(section_name)
            with open(self._get_config_file(), 'w') as configfile:
                config.write(configfile)
        self.credentials = None
        sys.exit(0)


def login(session, user, password, database=None, server=None):
    """
    Logs into a MyGeotab server and stores the returned credentials

    :param session: The current Session object
    :param user: The username used for MyGeotab servers. Usually an email address.
    :param password: The password associated with the username. Optional if `session_id` is provided.
    :param database: The database or company name. Optional as this usually gets resolved upon authentication.
    :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
    """
    if not user:
        user = click.prompt("Username", type=str)
    if not password:
        password = click.prompt("Password", hide_input=True, type=str)
    try:
        with click.progressbar(length=1, label="Logging in...") as bar:
            session.login(user, password, database, server)
            bar.update(1)
        if session.credentials:
            click.echo('Logged in as: %s' % session.credentials)
            session.load(database)
        return session.get_api()
    except mygeotab.api.AuthenticationException:
        click.echo('Incorrect credentials. Please try again.')
        sys.exit(0)


@click.group(invoke_without_command=True, help='Lists active sessions')
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
@click.argument('database', nargs=1, required=True)
@click.pass_obj
def remove(session, database):
    """
    Removes a session from the saved credentials

    :param session: The current Session object
    :param database: The database name to log out from
    """
    session.load(database)
    session.logout()


@click.command(help="Launch an interactive MyGeotab console")
@click.argument('database', nargs=1, required=False)
@click.option('--user', '-u')
@click.option('--password', '-p')
@click.option('--server', default=None, help='The server (ie. my4.geotab.com)')
@click.pass_obj
def console(session, database=None, user=None, password=None, server=None):
    """An interactive Python API console for MyGeotab

    If IPython is installed, it will launch an interactive IPython console instead of the built-in Python console. The
    IPython console has numerous advantages over the stock Python console, including: colors, pretty printing,
    command auto-completion, and more.

    By default, all library objects are available as locals in the script, with 'myg' being the active API object

    :param session: The current Session object
    :param database: The database name to open a console to
    :param user: The username used for MyGeotab servers. Usually an email address.
    :param password: The password associated with the username. Optional if `session_id` is provided.
    :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
    """
    local_vars = _populate_locals(database, password, server, session, user)
    version = 'MyGeotab Console {0} [Python {1}]'.format(mygeotab.__version__,
                                                         sys.version.replace('\n', ''))
    auth_line = ('Logged in as: %s' % session.credentials) if session.credentials else 'Not logged in'
    banner = '\n'.join([version, auth_line])
    try:
        from IPython import embed

        embed(banner1=banner, user_ns=local_vars)
    except ImportError:
        import code

        code.interact(banner, local=local_vars)


@click.command(help="Run a Python script with the user credentials already populated")
@click.argument('script', nargs=1, required=True, type=click.Path(exists=True))
@click.argument('database', nargs=1, required=False)
@click.option('--user', '-u')
@click.option('--password', '-p')
@click.option('--server', default=None, help='The server (ie. my4.geotab.com)')
@click.pass_obj
def run(session, script=None, database=None, user=None, password=None, server=None):
    """Runs a script with pre-populated saved credentials

    By default, all library objects are available as locals in the script, with 'myg' being the active API object

    :param session: The current Session object
    :param script: The script file to execute
    :param database: The database name to open a console to
    :param user: The username used for MyGeotab servers. Usually an email address.
    :param password: The password associated with the username. Optional if `session_id` is provided.
    :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
    """
    local_vars = _populate_locals(database, password, server, session, user)
    with open(script) as f:
        compiled_script = compile(f.read(), script, 'exec')
        exec(compiled_script, globals(), local_vars)

@click.group()
@click.version_option()
@click.pass_context
def main(ctx):
    """MyGeotab Python SDK command line tools

    You probably want to use the `console` command
    """
    ctx.obj = Session()
    try:
        ctx.obj.load()
    except IOError:
        pass

def _populate_locals(database, password, server, session, user):
    if not session.credentials:
        login(session, user, password, database, server)
    session.load(database)
    api = session.get_api()
    if not api:
        # This DB hasn't been logged into before
        api = login(session, user, password, database, server)
    try:
        api.get('User', name=session.credentials.username)
    except mygeotab.api.AuthenticationException:
        # Credentials expired, try logging in again
        click.echo('Your session has expired. Please login again.')
        api = login(session, user, password, database, server)
    return dict(myg=api, mygeotab=mygeotab, dates=mygeotab.dates)

main.add_command(console)
main.add_command(run)
sessions.add_command(remove)
main.add_command(sessions)

if __name__ == '__main__':
    main()
