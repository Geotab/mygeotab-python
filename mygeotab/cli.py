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


@click.command()
@click.argument('username')
@click.password_option()
@click.option('--database', default=None)
@click.option('--server', default=None)
@click.pass_obj
def login(session, username, password, database, server):
    session.login(username, password, database, server)
    if session.api:
        click.echo('%s' % session.api.credentials)


@click.command()
@click.pass_obj
def logout(session):
    session.logout()

@click.command()
@click.pass_obj
def play(session):
    if not session.api:
        click.echo("Not logged in. Please login using the `mygeotab login` command")
        sys.exit(1)
    methods = dict(api=session.api)
    code.interact(
        'MyGeotab Python Library {0}\nPython {1} on {2}\n{3}'.format(mygeotab.__version__,
                                                                     sys.version.replace('\n', ''),
                                                                     sys.platform,
                                                                     session.api.credentials if session.api and session.api.credentials else 'Not logged in'),
        local=methods)


@click.group()
@click.pass_context
def main(ctx):
    try:
        ctx.obj = pickle.load(open(Session.get_save_path()))
    except IOError:
        ctx.obj = Session()


main.add_command(play)
main.add_command(login)
main.add_command(logout)

if __name__ == '__main__':
    main()