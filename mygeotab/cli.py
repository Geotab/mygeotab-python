import code
import sys
import os.path
import pickle

import click

from mygeotab import __version__
from mygeotab.api import *

@click.command()
def forget():
    print 'forgotten'


@click.command()
@click.pass_context
def main(ctx):
    try:
        credentials = pickle.load(open(os.path.join(os.path.expanduser('~'), '.mygeotabcredentials')))
    except IOError:
        credentials = None

    code.interact(
        'MyGeotab Python Library {0}\nPython {1} on {2}'.format(__version__, sys.version.replace('\n', ''),
                                                                sys.platform),
        local=globals())


if __name__ == '__main__':
    main()