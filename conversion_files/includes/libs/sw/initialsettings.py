import curses, curses.textpad, re
import urlparse, requests, json

class InitialSettings:
    def __init__( self, stdscr, kwargs ):
        """Initializing this class more or less handles every part of the initial settings menu.
           There are no other parts of it which needs to be called, as the initialize function will go through
           and call every function it needs in order. This function should be initialized with the wrapper for curses
           around it with the kwargs passed to our wrapper function included.
            
           Initial settings presents the user with the default options (or whatever kwargs were included) and allows
           them to go through either individually change or review every one, while at the same time validating them.

           :param stdscr: Provided by the curses wrapper, just the screen object that will be printed to.
           :param kwargs: The keyword arguments provided to :func:`sw.wrapper.main`
           :returns InitialSettings: (self)
        """
        stdscr.nodelay( True )   # Don't wait on key presses
        curses.curs_set( 0 )     # Invisible Cursor

        self.stdscr = stdscr
        self.kwargs = kwargs

        self.kwarray = [ ]      # Contains our options to print out. This includes any titles and text after letters you see
        self.kwmap = { }        # Maps a kwarg to an array [ default value string, default value ] ie [ 'None', '' ]
        self.kwcharmap = { }    # Maps a key to kwarg text (ie 'a' => 'numJobs')

        curses.init_pair( 100, curses.COLOR_BLACK, curses.COLOR_RED )
        curses.init_pair( 101, curses.COLOR_BLACK, curses.COLOR_YELLOW )
        curses.init_pair( 102, curses.COLOR_GREEN, curses.COLOR_BLACK )

        self.maxx = self.stdscr.getmaxyx( )[1]
        self.maxy = self.stdscr.getmaxyx( )[0]
        self.KWARGS_MAX = 80

        self.stdscr.clear( )

        self.setupDefaults( )

        self.renderList( )
        
        # Draw our selection box
        self.stdscr.addstr( self.maxy-3, 1, "Type letter and hit enter to select or press enter to start" )
        self.stdscr.addstr( self.maxy-2, 1, "Selection: " )

        curses.curs_set( 1 )
        self.ebox = self.stdscr.subwin( 1, 2, self.maxy-2, len( "Selection: " ) + 1 )
        self.entry = curses.textpad.Textbox( self.ebox, insert_mode=True )
        self.entry.stripspaces = 1
        
        self.stdscr.refresh( )

        # Digest input and changes to the options we presented
        self.handleInput( )

        # Make sure self.kwargs has everything set, we set the defaults here
        for key in self.kwmap:
            if key not in self.kwargs:
                if self.kwmap[key][1] == "auto" or self.kwmap[key][1] == "None":
                    self.kwmap[key][1] = None
                self.kwargs[key] = self.kwmap[key][1]



    def handleInput( self ):
        """This method is a giant loop which calls most other functions. It waits for key presses,
           validates them, then loops through getting input for what was pressed, validating the
           input, then seeing if the user is ready to terminate... more or less.

           :returns None:
        """
        first = True
        done = False
        res = ""

        while not done:
            if not res in self.kwcharmap and not first:
                self.error( ''.join( [ "Invalid Selection '", res, "'" ] ) )
            elif not first:
                key = self.kwcharmap[res]
                win = self.kwmap[key][2]        # our setting's window
                ewin = curses.textpad.Textbox( win, insert_mode=True )
                ewin.stripspaces = 1
                ewin.edit( )

                out = ewin.gather( ).rstrip( )
                win.clear( )
                out = self.processEntry( out, key, win )
                if out == -1:
                    continue

                win.refresh( )
                self.error( )

            doneCheck = False
            while not doneCheck: 
                self.stdscr.refresh( )
                self.ebox.clear( )
                self.entry.edit( ) 
                res = self.entry.gather( ).rstrip( )
                first = False
                if res == "":
                    done = True
                    if not self.checkValues( ):
                        done = False
                    else:
                        break
                else:
                    break



    def processEntry( self, out, key, win ):
        """Called as part of :func:`handleInput`, this method checks for the type
           of the default value and transforms the input to that... unless the default is
           None, in which case it assumes String.

           It will also check for specific kwargs, such as report, which upon entry it validates
           it as being a real URL.

           :param String out: Input given from the user to fill the field specified by key.
           :param String key: The letter the user entered, which points to a kwarg and its default value.
           :param win: A curses window object for the area where the value was written. It is often written back over
             after the value is interpreted. For example, in a field where the default value for a kwarg is bool the field
             evaluates anything not /f(alse)?/i or /no?/i as True and writes "True" to the field. 
           
           :returns None:
        """
        default = self.kwmap[key][1]    # the default value

        try:
            if type( default ) is int:
                out = int( out ) 
            elif type( default ) is float:
                out = float( out )
            elif type( default ) is long:
                out = long( out )
            elif type( default ) is str:
                out = str( out )
            elif type( default ) is bool:
                if out == "False" or out == "false" or out == "f" \
                        or out == "n" or out == "no" or out == "No":
                    out = False
                out = bool( out )
            elif default is None or default == "auto":
                if out == "None" or out == "none" or out == "auto":
                    out = None
                elif default == "auto":
                    out = "auto"

            if ( default is None and not out is None ) or out != default:
                # Check everything out
                if key == 'project':
                    reg = re.findall( r'([^0-9A-Za-z\-])', out )
                    if reg:
                        self.error( ''.join( [ "Project name cannot include ", reg[0] ] ) )
                        return -1
                elif key == 'report':
                    o = bool( urlparse.urlparse( out ).netloc )
                    if not o:
                        self.error( "Reporting server must be a HTTP URL" )
                        return -1
                elif key == 'run':
                    reg = re.findall( r'([^0-9A-Za-z\-\_])', out )
                    if reg:
                        self.error( ''.join( [ "Run name cannot include ", reg[0] ] ) )
                        return -1

            # Finally add it in and go on
            if default == "auto" and ( out == "auto" or out == "" ):
                self.kwargs[key] = None
                out = "auto"
            else:
                self.kwargs[key] = out
            win.addstr( str( out ) )
        except Exception as e:
            win.addstr( str( self.kwargs.get( key, default ) ) )
            self.error( e )

        return out


    def checkValues( self ):
        """Checks values after the user enters a blank character (they ask to begin). The primary function this serves
           is to check that the reporting server exists, if specified, by resolving the address, doing a handshake, and 
           seeing what requirements, if any, the server has. Currently the only supported requirement is for the project
           field to not be blank.
           
           :returns None:
        """
        r = None
        rep = self.kwargs.get( 'report', None )
        run = self.kwargs.get( 'run', None )
        err = None
        if rep is not None:
            try: 
                r = requests.post( rep, data=json.dumps( { "HELLOAREYOUTHERE": None } ), timeout=1, headers={'content-type': 'application/json'} )
            except Exception as e:
                err = str( e ) 
                if len( err ) > 30:
                    err = ''.join( [ err[:27], "..." ] )
            if r is None:
                err = "Failure connecting to reporting server"
            elif r.status_code != requests.codes.ok:
                err = ''.join( [ "Received HTTP status code ", str( r.status_code ) ] )
            else:
                if r.text != None:
                    try:
                        response = r.json( )
                        if "YESIAMHERE" in response:
                            if response["projectRequired"]:
                                if self.kwargs.get( 'project', None ) is None:
                                    self.error( "Server explicity requires a project name" )
                                    return False
                    except Exception as e:
                        if err is None:
                            err = "Handshake failed; not a reporting server"
                        pass
                else:
                    err = "Connection to reporting server failed"
            if run is None and self.kwargs.get( 'project', None ) is not None:
                self.error( "Must include a run name with a project name" )
                return False # Returns false because this cannot be ignored.
        if err is not None:
            self.error( ''.join( [ err, ", press enter again to ignore" ] ), "Warning" )
            return False
        return True




    def error( self, msg=None, type="Error" ):
        """Prints an error in a standard way above the user input field. The default type, Error, results in a red message,
           while any other value will print a yellow one.

           :param msg: The message to print out as an error.
           :param type: The type of error to print out, any value that's not Error will be yellow. This type will prefix msg.
           :returns None:
        """
        if msg != None:
            self.error( ) # Clear ourselves
            color = 100
            if type != "Error":
                color = 101
            self.stdscr.addstr( self.maxy-5, 1, ''.join( [ type, ": ", str( msg ) ]  ), curses.color_pair( color ) )
        else:
            self.stdscr.addstr( self.maxy-5, 1, " " * self.KWARGS_MAX )
        self.stdscr.refresh( )



    def setupDefaults( self ):
        """This method loads into kwmap and kwarray the defaults for various kwargs as well as the titles to print
           in front of them on the display screen. It does nothing more than just loading the values up, :func:`renderList`
           does the dirty work.

           :returns None:
        """
        self.kwarray.append( "Run Settings" )
        self.kwarray.append( 'children' )
        self.kwmap['children'] = [ "# Children", 1 ]
        self.kwmap['stagger']  = [ "Stagger Spawn", False ]
        self.kwarray.append( 'stagger' )
        self.kwmap['jobs']     = [ "# Jobs", 1 ]
        self.kwarray.append( 'jobs' )
        
        self.kwarray.append( "" )
        self.kwarray.append( "Pool Settings" )
        self.kwmap['level']    = [ "Log Lvl (0-5)", 1 ]
        self.kwarray.append( 'level' )
        self.kwmap['images']   = [ "Get Images", False ]
        self.kwarray.append( 'images' )
        self.kwarray.append( "" )

        self.kwarray.append( "Reporting Settings" )
        self.kwmap['report']   = [ "Server", None ]
        self.kwarray.append( 'report' )
        self.kwmap['run']      = [ "Run Name", "auto" ]
        self.kwarray.append( 'run' )
        self.kwmap['project']  = [ "Project Name", None ]
        self.kwarray.append( 'project' )
        self.kwmap['id']       = [ "Client Name", "auto" ]
        self.kwarray.append( 'id' )



    def renderList( self ):
        """Renders all values prepared from :func:`setupDefaults` on the screen, but only once. This method is never
           called again, so it's assumed all the values are kept pristine. In addition to printing all the titles and
           kwargs on screen, it adds into kwmap a 3rd index (kwmap[key][2]) which is a reference to the subwindow for
           that kwarg's value. So, in the future, to modify f's display value::
             self.kwmap['f'][2].addstr( 'New Value' )
           
           :returns None:
        """
        i = 0 
        off = 0
        tab = 15
        for key in self.kwarray:
            y = i + 1
            x = 2
            # This is a configurable field
            if key in self.kwmap:
                default = str( self.kwmap[key][1] )
                val = str( self.kwargs.get( key, default ) )
                size = len( self.kwmap[key][0] )
                char = str( chr( ord('a') + i - off ) )
                self.kwcharmap[char] = key

                # Get our first column out there
                s = ''.join( [ char, ") ",
                    self.kwmap[key][0],
                    ":",
                    ( " "*( tab-size ) )
                    ] )
                self.stdscr.addstr( y, x, s )
                
                # Now print our field
                self.kwmap[key].append( self.stdscr.subwin( 1, 50, y, x + len( s ) ) )
                self.kwmap[key][2].addstr( val )
                self.kwmap[key][2].refresh( )
            else:
                # This is a title field
                self.stdscr.addstr( y, x, key, curses.color_pair( 102 ) )
                off += 1
            
            i += 1

