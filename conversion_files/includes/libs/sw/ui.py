import time
from sw.formatting import *

class Ui:
    def __init__( self, screen, pool ):
        # The curses screen
        self.scr = screen

        # The pool we're a UI for.
        self.pool = pool

        # Options for buttons to press
        self.options = [ "c+- - Children", "j+- - Jobs", "p - Pause", "q - Quit" ]

        # Last time stats were updated
        self.nextStats = time.time( )

        self.STATS_HEIGHT  = 7
        self.STATS_WIDTH   = self.scr.getmaxyx( )[1]-2

        self.OPTIONS_HEIGHT = self.STATS_HEIGHT + 1
        self.OPTIONS_WIDTH  = 20

        self.drawMainScreen( )

    def drawMainScreen( self ):
        self.scr.border( )
        self.scr.nodelay( True ) # Don't wait on key presses

        # Draw our title at the top
        self.scr.addstr( 0, 3, "Selenium Wrapper Console" )

        # Line for key panel
        self.scr.vline( 1, self.scr.getmaxyx( )[1]-self.OPTIONS_WIDTH, 0, self.scr.getmaxyx( )[0]-self.STATS_HEIGHT )

        # Calculate the dimensions of our key panel
        sx = self.scr.getmaxyx( )[1]-( self.OPTIONS_WIDTH - 2 )
        sy = 2
        i = 0

        for l in self.options:
            self.scr.addstr( sy + i*2, sx, l )
            i += 1

        self.scr.hline( self.scr.getmaxyx( )[0]-self.STATS_HEIGHT, 1, 0, self.STATS_WIDTH )
        self.scr.refresh( )

    def think( self ):
        self.options = self.options

        # Check for keypresses
        key = self.scr.getch( )
        
        if key == ord( "q" ):
            self.pool.stop( )
        elif key == ord( "p" ):
            print "P"
            # Pause
        elif key == ord( "c" ):
            print "C"
            # Change # Children
        elif key == ord( "j" ):
            print "J"
            # Change # Jobs

        
        if self.nextStats > time.time( ):
            self.nextStats = time.time( ) + 1

        self.updateStats( )

    def updateStats( self ):
        statstrs = [ ]

        # Wipe the box
        for i in range( 1, self.STATS_HEIGHT-1 ):
            self.scr.addstr( self.scr.getmaxyx( )[0]-self.STATS_HEIGHT+i, 1, " "*self.STATS_WIDTH )

        # Number of Children
        statstrs.append( ''.join( [ "Children: ", str( len( self.pool.children ) ) ] ) )

        # Number of Active Children
        numactive = 0
        for c in self.pool.children:
            if c is not None and c.is_alive and not c.is_done:
                numactive += 1
        statstrs.append( ''.join( [ "Act: ", str( numactive ) ] ) )

        # Number of Jobs Left
        statstrs.append( ''.join( [ "Jobs Left: ", str( self.pool.numJobs - self.pool.successful( ) ) ] ) )

        # Number of Jobs Successful
        statstrs.append( ''.join( [ "Successful: ", str( self.pool.successful( ) ) ] ) )

        # Number of Failed Jobs
        statstrs.append( ''.join( [ "Failed: ", str( self.pool.failed( ) ) ] ) )

        # Average Job Time
        times = self.pool.timeTaken( )
        statstrs.append( ''.join( [ "Avg Job: ", format( avg( times ) ), "s" ] ) )

        adj = 2
        k = 0
        for st in statstrs:
            stl = len( st )
            if ( adj + stl ) >= self.STATS_WIDTH:
                k += 1
                adj = 2
            self.scr.addstr( self.scr.getmaxyx( )[0]-self.STATS_HEIGHT+( 1 + 1*k ), adj, st )
            adj += stl + 3
        self.scr.refresh( )

