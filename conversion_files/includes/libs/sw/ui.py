import time, curses
from math import *
from sw.formatting import *

class Ui:
    def __init__( self, screen, pool ):
        # The curses screen
        self.scr = screen

        # The pool we're a UI for.
        self.pool = pool

        # Options for buttons to press
        self.options = [ "c+- - Children", "j+- - Jobs", "p   - Pause", "h   - Help", "q   - Quit" ]

        # Key buffer
        self.keys = [ ]

        # Our last stats entry
        self.last = [ None for i in range(3) ]

        # Next time we update the screen
        self.nextUpdate = time.time( )

        self.screenUpdateTime = 1

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

        # Colors
        curses.init_pair( STAT_LOAD,  curses.COLOR_BLACK, curses.COLOR_YELLOW )
        curses.init_pair( STAT_START, curses.COLOR_BLACK, curses.COLOR_YELLOW )
        curses.init_pair( STAT_GOOD,  curses.COLOR_WHITE, curses.COLOR_BLACK )
        curses.init_pair( STAT_ERROR, curses.COLOR_BLACK, curses.COLOR_RED )
        curses.init_pair( STAT_WAIT,  curses.COLOR_WHITE, curses.COLOR_BLUE )
        curses.init_pair( STAT_DONE,  curses.COLOR_BLACK, curses.COLOR_WHITE )



    def drawMainScreen( self ):
        """Renders the initial screen and sets up options for curses. Draws
           the border around the screen and the separators for the various sections
           with the title.

           :returns: None
        """
        self.scr.nodelay( True ) # Don't wait on key presses
        curses.curs_set( 0 )     # Invisible Cursor
        self.scr.border( )       # Draws a pretty border around the window
        self.scr.addstr( 0, 3, "Selenium Wrapper Console" ) # Puts a message up top

        # Line for key window
        self.scr.vline( 1, self.x( )-self.OPTIONS_WIDTH, 0, self.y( )-self.STATS_HEIGHT )

        i = 0
        for l in self.options:
            self.opts.addstr( i, 2, l )
            i += 2

        # Line for stats window
        self.scr.hline( self.y( )-self.STATS_HEIGHT-1, 1, 0, self.STATS_WIDTH )

        self.scr.refresh( )



    def think( self ):
        if time.time( ) >= self.nextUpdate:
            self.nextUpdate = time.time( ) + self.screenUpdateTime
            self.updateMain( )
            self.updateStats( )
            self.updateKeys( )



    def sleep( self, amount ):
        """Handles sleeping while listening for button presses. The hardcoded subsleep (0.05s)
           amount is an appropriate resolution that allows for seemingly instant button press responses
           without consuming an entire core (when constantly listening).
        
           :param amount: Float for amount of seconds to wait while listening to button presses.
             This is accurately followed to a resolution of 0.05s.
           :returns: None
        """
        end = amount + time.time( )
        while time.time( ) < end:
            key = self.scr.getch( )
            if key == -1:
                if "p" in self.keys or "q" in self.keys:
                    self.keys = [ ]
            elif key == curses.KEY_ENTER:
                self.keys = [ ]
            else:
                # Flip between all our accepted keys
                if key == ord( "q" ) and not self.pool.stopped: 
                    self.pool.stop( )
                    curses.flash( )
                    self.keys = [ "q" ]
                elif key == ord( "p" ):
                    print "P"
                    self.keys = [ "p" ]
                    # Pause
                else:
                    # If we have more than 4 keys and this key isn't +/-, clear everything and return
                    if len( self.keys ) >= 4 and key != ord( "+" ) and key != ord( "-" ):
                        self.keys = [ ]

                    if key == ord( "j" ) or key == ord( "c" ):
                        # Check we have no other commands queued, else clear.
                        if "j" in self.keys or "c" in self.keys:
                            self.keys = [ ]

                        self.keys.append( chr( key ) )
                    elif key == ord( "+" ) or key == ord( "-" ):
                        self.keys.append( chr( key ) )

                        # This key acts as an executor
                        if not "j" in self.keys and not "c" in self.keys:
                            self.keys = [ ]
                        else:
                            # Look for numbers
                            for c in self.keys:
                                if c.isdigit( ):
                                    break
                            else:
                                self.keys.append( "1" ) #assume 1

                            # Execute command
                            ##Get the number we're increasing
                            num = [ ] 
                            for c in self.keys:
                                if c.isdigit( ):
                                   num.append( c ) 
                            num = int( ''.join( num ) )

                            if "j" in self.keys:
                                if "+" in self.keys:
                                    for i in range(num):
                                        self.pool.numJobs += 1
                                        self.pool.workQueue.put( self.pool.func )
                                if "-" in self.keys:
                                    for i in range(num):
                                        if not self.pool.workQueue.empty( ):
                                            self.pool.numJobs -= 1
                                            self.pool.workQueue.get( False, False )
                            elif "c" in self.keys:
                                if "+" in self.keys:
                                    for i in range(num):
                                        self.pool.newChild( )
                                if "-" in self.keys:
                                    for i in range(num):
                                        self.pool.endChild( )

                            # Clear keys for next command
                            self.keys = [ ]

                    elif key >= ord( "0" ) and key <= ord( "9" ):
                        self.keys.append( chr( key ) )
                time.sleep( 0.05 )



    def updateMain( self ):
        """Prints out a number for each of our children with an appropriate color
           for each corresponding with the last status message they reported. Refreshes
           the screen when done.
            
           :returns: None
        """
        # Draw each child with an appropriate background color / anim
        y = 0 # Our cursor's y position
        x = 0 # ^ but x
        for c in self.pool.children:
            if c is None: # Children are None for a while, these are ignored
                continue
            s = ''.join( [ "#", str( c.num + 1 ) ] )

            self.main.addstr( y, x, s, curses.color_pair( self.pool.data[c.num][STATUS] ) )

            y += 2 # Scoot down two lines for each number
            if y > self.y( ) - self.STATS_HEIGHT - 4:
                x += 3 # Over three, an extra character to space
                y = 0

        self.main.refresh( )



    def updateStats( self ):
        """Updates the statistics field within our window. Completely clears all of it initally
           then slowly goes through and reads from each individual pool value to rebuild it.
           This is called from :func:`sw.ui.think` and refreshes several times per second.

           :return: None
        """
        statstrs = [ ]
        jpstr = None
        t = time.time( )

        this = [ len( self.pool.children ), self.pool.successful( ) + self.pool.failed( ) ]
        if self.last[0] != this[0] or self.last[1] != this[1]: 
            # Store this for next time
            self.last = this

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
            avgtime = avg( times )
            statstrs.append( ''.join( [ "Avg Job: ", format( avgtime ), "s" ] ) )

            # Jobs per minute
            if len( times ) > 0:
                jpm = ( 60 / avgtime )

                if jpm > 1:
                    jpstr = ''.join( [ "Jobs/m: ", format( jpm ) ] )
                else:
                    jpstr = ''.join( [ "Jobs/s: ", format( jpm / 60 ) ] )
                
                self.nextJobTime += 10 
            
            if jpstr is not None:
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



    def updateKeys( self ):
        k = 1
        y = self.y( ) - self.STATS_HEIGHT-3
        self.opts.addstr( y, k, " "*(self.OPTIONS_WIDTH-2) )

        if len( self.keys ) > 0:
            for c in self.keys:
                self.opts.addstr( y, k, c )
                k += 1
        
        self.opts.refresh( )



    def x( self ):
        return self.scr.getmaxyx( )[1]



    def y( self ):
        return self.scr.getmaxyx( )[0]
