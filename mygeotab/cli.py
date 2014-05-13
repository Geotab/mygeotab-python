import code
import sys

import click

from mygeotab import __version__
from mygeotab.api import *


@click.command()
def main():
    code.interact(
        'MyGeotab Python Library {0}\nPython {1} on {2}'.format(__version__, sys.version.replace('\n', ''), sys.platform),
        local=globals())


if __name__ == '__main__':
    main()