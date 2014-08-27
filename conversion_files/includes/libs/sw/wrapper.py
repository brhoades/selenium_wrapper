from sw.pool import *
import sys, time, curses


def main( func, file, **kwargs ):
    """ Is called from our wrapped script. Parses any arguments passed to our script from the command
        line and then starts and manages our pool.

        :param func: The function that will be ran continously to simulate load.
        :param file: Usually __file__, the name of a script in the directory that log/ will be in.
        :returns: None
    """
    print( "\nLibraries loaded!\n\n" )
    numTimes = 1
    children = 3 
    images = False
    staggered = False

    if len( sys.argv ) > 1:
        numTimes = int( sys.argv[1] )
    if len( sys.argv ) > 2:
        children = int( sys.argv[2] )
    if len( sys.argv ) > 3:
        if sys.argv[3] == "y":
            staggered = True
     
    kwargs['staggered'] = staggered

    pool = Pool( children, numTimes, func, file, kwargs )

    curses.wrapper( mainLoop, pool )

    pool.reportStatistics( True )

    pool.stop( )



def mainLoop( stdscr, pool ):
    """Takes the pool created previously and just loops around it. Currently it just calls the pool's
        think function repeatedly.

        :param stdscr: Our standard screen from curses.
        :param pool: Our created child pool in :func:`main`.
        :returns: None
    """

    pool.curses = stdscr
    stdscr.border( )
    stdscr.nodelay( True ) # Don't wait on key presses
    stdscr.addstr( 0, 3, "Selenium Wrapper Console" )
    stdscr.vline( 1, stdscr.getmaxyx( )[1]-20, 0, stdscr.getmaxyx( )[0]-2 )

    options = [ "q - Quit", "c+- - Children", "j+- - Jobs" ]
    sx = stdscr.getmaxyx( )[1]-18
    sy = 2
    i = 0

    for l in options:
        stdscr.addstr( sy + i*2, sx, l )
        i += 1
    stdscr.refresh( )

    while not pool.done( ) and not stdscr.getch( ) == ord("q"):
        pool.think( )
        time.sleep( 0.1 )
