from sw.pool import Pool
from sw.ui import Ui, getInput
import sys, time, curses


def main( func, file, **kwargs ):
    """ Is called from our wrapped script. Parses any arguments passed to our script from the command
        line and then starts and manages our pool.

        :param func: The function that will be ran continously to simulate load.
        :param file: Usually __file__, the name of a script in the directory that log/ will be in.
        :returns: None
    """
    # Get options and defaults 
    curses.wrapper( getInput, kwargs )

    pool = Pool( func, file, kwargs )

    curses.wrapper( mainLoop, pool )

    pool.stop( )



def mainLoop( stdscr, pool ):
    """Takes the pool created previously and just loops around it. Currently it just calls the pool's
        think function repeatedly.

        :param stdscr: Our screen from curses.
        :param pool: Our created child pool in :func:`main`.
        :returns: None
    """

    pool.ui = Ui( stdscr, pool )

    pool.ui.drawMainScreen( True )

    while True:
        pool.think( )
        pool.ui.think( )
        pool.ui.sleep( 0.1 )
