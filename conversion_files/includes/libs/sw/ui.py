import time, curses, curses.textpad
from math import *
from sw.formatting import *

class Ui:
    """The UI class houses the curses instance which in turn enables all user-requested actions while displaying
       relevant information. Only one instance of UI should ever be initialized. Initialization handles all the color 
       constants generation along with defining all subwindows statically.

       :param screen: Used with the wrapping function provided by curses. This is a curses screen that has
           just been created.
       :param pool: Reference to our owning pool. This pool will be monitored and displayed on the main status window.

       :return: UI (self)
    """
    def __init__( self, screen, pool ):
        # The curses screen
        self.scr = screen
        self.scr.clear( )

        # The pool we're a UI for.
        self.pool = pool

        # Options for buttons to press
        self.options = [ "c+- - Children", "j+- - Jobs", "p   - Pause", "q   - Quit" ]

        # Toggled options
        self.altopts = [ "c+- - Children", "j+- - Jobs", "p   - Unpause", "s   - Start" ]

        # Options bits, true if alternate
        self.optbits = [ False for i in range(len(self.options)) ]

        self.bits = [ "c", "j", "p", "q" ]

        # Key buffer
        self.keys = [ ]

        self.last = [ None for i in range(4) ]

        # Next time we update the screen
        self.nextUpdate = time.time( )

        self.screenUpdateTime = 0.1 

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

        # Colors
        curses.init_pair( DISP_LOAD,  curses.COLOR_BLACK, curses.COLOR_YELLOW )
        curses.init_pair( DISP_START, curses.COLOR_BLACK, curses.COLOR_YELLOW )
        curses.init_pair( DISP_GOOD,  curses.COLOR_WHITE, curses.COLOR_BLACK )
        curses.init_pair( DISP_ERROR, curses.COLOR_BLACK, curses.COLOR_RED )
        curses.init_pair( DISP_WAIT,  curses.COLOR_WHITE, curses.COLOR_BLUE )
        curses.init_pair( DISP_DONE,  curses.COLOR_BLACK, curses.COLOR_WHITE )
        curses.init_pair( DISP_FINISH,  curses.COLOR_BLACK, curses.COLOR_GREEN )

        self.scr.nodelay( True ) # Don't wait on key presses
        curses.curs_set( 0 )     # Invisible Cursor
        self.scr.border( )       # Draws a pretty border around the window

        self.scr.refresh( )



    def drawMainScreen( self, first=False ):
        """Renders the initial screen and sets up options for curses. Draws
           the border around the screen and the separators for the various sections
           with the title.

           :param False first: Whether this is the call by the UI initialization.
           :returns: None
        """
        if first:
            self.scr.addstr( 0, 3, "Selenium Wrapper Console" ) # Puts a message up top
            self.scr.vline( 1, self.x( )-self.OPTIONS_WIDTH, 0, self.y( )-self.STATS_HEIGHT )

            # Line for stats window
            self.scr.hline( self.y( )-self.STATS_HEIGHT-1, 1, 0, self.STATS_WIDTH )
        
        # Draw spaces
        for l in range(len(self.options)*2):
            self.opts.addstr( l, 2,  ( self.OPTIONS_WIDTH-3 )*" " )

        i = 0
        for l in self.options:
            if not self.optbits[i/2]:
                self.opts.addstr( i, 2, l )
            else:
                self.opts.addstr( i, 2, self.altopts[i/2] )
            i += 2

        self.scr.refresh( )



    def think( self ):
        """Calls several other functions which need to be checked constantly. Includes
           :func:`updateStats`, :func:`updateKeys`, and :func:`updateMain`. 
           The last one is called every time think is, while the other two are called every 
           self.nextUpdate seconds.

           :returns: None
        """
        self.updateMain( )
        if time.time( ) >= self.nextUpdate:
            self.nextUpdate = time.time( ) + self.screenUpdateTime
            self.updateStats( )
            self.updateKeys( )



    def sleep( self, amount ):
        """Handles sleeping while listening for button presses. The hardcoded subsleep (0.01s)
           amount is an appropriate resolution that allows for seemingly instant button press responses
           without consuming an entire core (when constantly listening).
        
           :param amount: Float for amount of seconds to wait while listening to button presses.
             This is accurately followed to a resolution of 0.01s.
           :returns: None
        """
        end = amount + time.time( )
        while time.time( ) < end:
            time.sleep( 0.01 )
            key = self.scr.getch( )

            # Catch keys which do nothing
            if key == -1 and len( self.keys ) > 0:
                clear = [ "p", "q", "s", "+", "-" ]
                for c in clear:
                    if c in self.keys:
                        del self.keys[:]
                        break
                continue
            elif key == curses.KEY_ENTER:
                del self.keys[:]
                continue
            elif key == curses.KEY_BACKSPACE:
                del self.keys[-1]
                continue

            # Flip between all our accepted keys
            if key == ord( "q" ) or key == ord( "s" ): 
                self.keys = [ chr( key ) ]
                curses.flash( )
                self.toggleKey( "q" )

                if self.pool.status >= STOPPED:
                    # Start
                    self.pool.start( )
                else:
                    # Quit
                    self.pool.stop( )

            elif key == ord( "p" ) and not self.pool.status >= STOPPED:
                self.keys = [ chr( key ) ]
                curses.flash( )
                self.toggleKey( chr( key ) )

                if self.pool.status == PAUSED: 
                    # Unpause
                    self.pool.start( )
                else:
                    # Pause
                    self.pool.stop( PAUSED )
            else: # This is either an unaccepted key, or a command key
                self.handleCommandKeys( key )



    def handleCommandKeys( self, key ):
        """Part of our :func:`sleep` function which checks if any of our accepted keys
        are pressed. It handles the logic for interpreting presses while recording and
        discarding them. The render of keys in the bottom right of the screen is done by
        :func:`updateKeys`.

        :param key: The key to process / store. If it's +/-, the all recorded keys that are
         relevant are executed.
        :returns: None
        """
        # If we have more than 8 keys and this key isn't +/-, clear everything and return
        if len( self.keys ) >= 8 and key != ord( "+" ) and key != ord( "-" ):
            self.keys = [ ]
            return

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

                ##Now do operations specific to each command
                if "j" in self.keys:
                    if "+" in self.keys:
                        for i in range(num):
                            self.pool.workQueue.put( self.pool.func )
                    if "-" in self.keys:
                        for i in range(num):
                            if not self.pool.workQueue.empty( ):
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

    def updateMain( self ):
        """Prints out a number for each of our children with an appropriate color
           for each corresponding with the last status message they reported. Refreshes
           the screen when done.
            
           :return: None
        """
        # Draw each child with an appropriate background color / anim
        y = 1 # Our cursor's y position
        x = 1 # ^ but x
        for c in self.pool.children:
            if c is None: # Children are None for a while, these are ignored
                continue
            s = ''.join( [ "#", str( c.num + 1 ) ] )

            if type( self.pool.data[c.num][DISPLAY] ) == int:
                self.main.addstr( y, x, s, curses.color_pair( self.pool.data[c.num][DISPLAY] ) )
            else:
                self.main.addstr( y, x ,s )

            y += 2 # Scoot down two lines for each number
            if y > self.y( ) - self.STATS_HEIGHT - 4:
                x += 3 # Over three, an extra character to space
                y = 0

        self.main.refresh( )



    def updateStats( self ):
        """Updates the statistics field within our window. Completely clears all of it initally
           then slowly goes through and reads from each individual pool value to rebuild it.
           This is called from :func:`think` and refreshes several times per second.

           :return: None
        """
        statstrs = [ ]
        jpstr = None
        t = time.time( )

        this = [ len( self.pool.children ), self.pool.successful( ) + self.pool.failed( ), self.pool.workQueue.qsize( ) ]
        if self.last[0] != this[0] or self.last[1] != this[1] or self.last[2] != this[2]: 
            # Store this for next time
            self.last = this

            # Clear our window
            self.stats.clear( )

            # Number of Children
            statstrs.append( ''.join( [ "Children: ", str( len( self.pool.children ) ) ] ) )

            # Number of Active Children
            numactive = 0
            for c in self.pool.children:
                if c is not None and c.status( ) == RUNNING:
                    numactive += 1
            statstrs.append( ''.join( [ "Act: ", str( numactive ) ] ) )

            # Number of Jobs Left
            statstrs.append( ''.join( [ "Jobs Left: ", str( self.pool.workQueue.qsize( ) ) ] ) )

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
                
            if jpstr is not None:
                statstrs.append( jpstr )

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
        """Handles rendering any relevant keys recorded from user input. It reads
           from self.keys to do this.

           :return: None
        """
        k = 1
        y = self.y( ) - self.STATS_HEIGHT-3
        self.opts.addstr( y, k, " "*(self.OPTIONS_WIDTH-2) )

        if len( self.keys ) > 0:
            for c in self.keys:
                self.opts.addstr( y, k, c )
                k += 1
        
        self.opts.refresh( )



    def toggleKey( self, key ):
        """Toggles a key display on the right hand side.

           :param key: A key that's listed on the right hand pane to toggle to an alternate option.
           :return: None
        """
        i = self.bits.index(key)
        self.optbits[i] = not self.optbits[i] 
        
        self.drawMainScreen( )



        
    def x( self ):
        """Accessor for returning the x size of the curses screen.

           :return: Integer of the number of characters along the x axis of the screen.
        """
        return self.scr.getmaxyx( )[1]



    def y( self ):
        """Accessor for returning the y size of the curses screen.

           :return: Integer of the number of characters along the y axis of the screen.
        """
        return self.scr.getmaxyx( )[0]



def getInput( stdscr, kwargs ):
    """Gets our prerun information. It first displays all information it's already loaded in, and 
       asks if the user wishes to change anything.
    """
    stdscr.nodelay( True )   # Don't wait on key presses
    curses.curs_set( 0 )     # Invisible Cursor
    stdscr.refresh( )
    kwarray = [ ]
    kwcharmap = { }
    kwmap = { }

    kwarray.append( "Run Settings" )
    kwarray.append( 'children' )
    kwmap['children'] = [ "# Children", 1 ]
    kwmap['stagger']  = [ "Stagged Spawn", False ]
    kwarray.append( 'stagger' )
    kwmap['jobs']     = [ "# Jobs", 1 ]
    kwarray.append( 'jobs' )
    
    kwarray.append( "" )
    kwarray.append( "Pool Settings" )
    kwmap['level']    = [ "Log Lvl (0-5)", 1 ]
    kwarray.append( 'level' )
    kwmap['images']   = [ "Get Images", False ]
    kwarray.append( 'images' )
    kwarray.append( "" )

    kwarray.append( "Reporting Settings" )
    kwmap['report']   = [ "Server", None ]
    kwarray.append( 'report' )
    kwmap['run']      = [ "Run Name", "auto" ]
    kwarray.append( 'run' )
    kwmap['project']  = [ "Project Name", "auto" ]
    kwarray.append( 'project' )
    kwmap['id']       = [ "Client Name", "auto" ]
    kwarray.append( 'id' )

    i = 0 
    off = 0
    tab = 15
    KWARGS_MAX = 50
    for key in kwarray:
        y = i + 1
        x = 2
        if key in kwmap:
            default = str( kwmap[key][1] )
            val = str( kwargs.get( key, default ) )
            size = len( kwmap[key][0] )
            char = str( chr( ord('a') + i - off ) )
            kwcharmap[char] = key

            s = ''.join( [ char, ") ",
                kwmap[key][0],
                ":",
                ( " "*( tab-size ) )
                ] )
            stdscr.addstr( y, x, s )
            kwmap[key].append( stdscr.subwin( 1, 50, y, x + len( s ) ) )
            kwmap[key][2].addstr( val )
            kwmap[key][2].refresh( )
        else:
            stdscr.addstr( y, x, key )
            off += 1
        
        i += 1

    maxx = stdscr.getmaxyx( )[1]
    maxy = stdscr.getmaxyx( )[0]

    stdscr.addstr( maxy-3, 1, "Enter selection to change below or just press Enter to start." )
    stdscr.addstr( maxy-2, 1, "Selection: " )

    curses.curs_set( 1 )
    ebox = stdscr.subwin( 1, 2, maxy-2, len( "Selection: " ) + 1 )
    entry = curses.textpad.Textbox( ebox, insert_mode=True )
    entry.stripspaces = 1

    stdscr.refresh( )

    entry.edit( )
    res = entry.gather( )

    while res != "":
        if not res in kwcharmap:
            stdscr.addstr( maxy-4, 1, "Invalid Selection '" + res + "'" )
        else:
            stdscr.addstr( maxy-4, 1, " " * KWARGS_MAX )
            win = kwmap[kwcharmap[res]][2]
            ewin = curses.textpad.Textbox( win, insert_mode=True )
            ewin.stripspaces = 1
            ewin.edit( )
            out = ewin.gather( ).rstrip( )
            if out != "" and out is not None:
                key = kwcharmap[res]
                default = kwmap[key][1]
                try:
                    if type( default ) is int:
                        kwargs[key] = int( out )
                    elif type( default ) is float:
                        kwargs[key] = float( out )
                    elif type( default ) is long:
                        kwargs[key] = long( out )
                    elif type( default ) is str:
                        kwargs[key] = str( out )
                    elif type( default ) is bool:
                        kwargs[key] = bool( out )
                    else:
                        kwargs[key] = out
                except Exception as e:
                    win.clear( )
                    win.addstr( str( kwargs.get( key, default ) ) )
                    win.refresh( )
                    stdscr.addstr( maxy-4, 1, "Error \"" + str( e ) + "\"" )

        stdscr.refresh( )
        ebox.clear( )
        entry.edit( ) 
        res = entry.gather( ).rstrip( )

    # Make sure kwargs has everything set, we set the defaults here
    for key in kwmap:
        if key not in kwargs:
            kwargs[key] = kwmap[key][1]
