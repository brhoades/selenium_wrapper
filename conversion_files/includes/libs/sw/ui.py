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

        # Next time jobs per second are updated
        self.nextJobTime = self.nextStats + 10 

        # Cached jobs per second string
        self.jpstr = None

        # Frames for loading
        self.loadFrame = [ "-", "\\", "|", "/" ]

        # Current frame
        self.curFrame  = 0

        # Dimensions and subwindow for statistics section
        self.STATS_HEIGHT  = 7
        self.STATS_WIDTH   = self.x( )-2

        self.stats = self.scr.subwin( self.STATS_HEIGHT-1, self.STATS_WIDTH, 
                self.y( )-self.STATS_HEIGHT, 1 )
        
        # Dimensions and subwindow for options section
        self.OPTIONS_HEIGHT = self.y( ) - self.STATS_HEIGHT 
        self.OPTIONS_WIDTH  = 20

        self.opts = self.scr.subwin( self.OPTIONS_HEIGHT, self.OPTIONS_WIDTH, 1, 
                self.x( ) - self.OPTIONS_WIDTH ) 

        # Main area
        self.MAIN_HEIGHT = self.y( ) - 2 - self.STATS_HEIGHT
        self.MAIN_WIDTH  = self.x( ) - 2 - self.OPTIONS_WIDTH
        
        self.main = self.scr.subwin( self.MAIN_HEIGHT, self.MAIN_WIDTH, 1, 1 )

        self.drawMainScreen( )

    def x( self ):
        return self.scr.getmaxyx( )[1]

    def y( self ):
        return self.scr.getmaxyx( )[0]

    def drawMainScreen( self ):
        self.scr.nodelay( True ) # Don't wait on key presses

        # Allow color
        print self.scr.has_color( ) 
        return
        self.scr.start_color( )

        self.scr.border( )

        # Draw our title at the top
        self.scr.addstr( 0, 3, "Selenium Wrapper Console" )

        # Line for key window
        self.scr.vline( 1, self.x( )-self.OPTIONS_WIDTH, 0, self.y( )-self.STATS_HEIGHT )

        i = 0
        for l in self.options:
            self.opts.addstr( i*2, 2, l )
            i += 1

        # Line for stats window
        self.scr.hline( self.y( )-self.STATS_HEIGHT-1, 1, 0, self.STATS_WIDTH )

        self.scr.refresh( )

    def think( self ):
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

        self.updateMain( )
        self.updateStats( )

    def updateMain( self ):
        # Change dash frame
        self.curFrame += 1
        if self.curFrame > len( self.loadFrames ):
            self.curFrame = 0
        
        # Draw each child with an appropriate background color / anim


    def updateStats( self ):
        statstrs = [ ]
        t = time.time( )

        # Clear our window
        self.stats.clear( )

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

        # Jobs per minute
        if t > self.nextJobTime and len( times ) > 0:
            jps = ( len( times ) / ( t - self.pool.started ) )

            if jps > 1:
                self.jpstr = ''.join( [ "Jobs/s: ", format( jps ) ] )
            else:
                self.jpstr = ''.join( [ "Jobs/m: ", format( jps * 60 ) ] )
            
            self.nextJobTime += 10 
        
        if self.jpstr is not None:
            statstrs.append( self.jpstr )


        adj = 2 # Amount we are shifting right in characters
        k = 0   # Amount we are shifting vertically
        for st in statstrs:
            stl = len( st ) # String length
            if ( adj + stl ) >= self.STATS_WIDTH:
                k += 1
                adj = 2
            self.stats.addstr( k, adj, st )
            adj += stl + 3
        self.stats.refresh( )

