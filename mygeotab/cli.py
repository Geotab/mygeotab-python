import code
import sys
import os.path
import pickle

import click

from mygeotab import __version__
from mygeotab.api import *

@click.command()
@click.pass_context
def login(ctx):
    print 'forgotten'


@click.command()
@click.pass_context
def play(ctx):
    api = ctx.obj['api']
    credentials = ctx.obj['credentials']
    code.interact(
        'MyGeotab Python Library {0}\nPython {1} on {2}\n{3}'.format(__version__, sys.version.replace('\n', ''),
                                                                     sys.platform,
                                                                     credentials if credentials else 'Not logged in'),
        local=locals())


@click.group()
@click.pass_context
def main(ctx):
    api = None
    credentials = None
    try:
        credentials = pickle.load(open(os.path.join(os.path.expanduser('~'), '.mygeotabcredentials')))
        api = API.load(credentials)
    except IOError:
        pass
    ctx.obj['api'] = api
    ctx.obj['credentials'] = credentials


main.add_command(play)
main.add_command(login)

if __name__ == '__main__':
    main(obj={})