import curses, curses.textpad, re
import urlparse, requests, json

class InitialSettings:
    def __init__( self, stdscr, kwargs ):
        """Gets our prerun information. It first displays all information it's already loaded in, and 
           asks if the user wishes to change anything.
        """
        stdscr.nodelay( True )   # Don't wait on key presses
        curses.curs_set( 0 )     # Invisible Cursor

        self.stdscr = stdscr
        self.kwargs = kwargs

        self.kwarray = [ ]
        self.kwcharmap = { }
        self.kwmap = { }

        curses.init_pair( 100, curses.COLOR_BLACK, curses.COLOR_RED )
        curses.init_pair( 101, curses.COLOR_BLACK, curses.COLOR_YELLOW )

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
        self.entry.edit( )
        res = self.entry.gather( ).rstrip( )
        done = False

        while not done:
            if not res in self.kwcharmap:
                self.error( ''.join( [ "Invalid Selection '", res, "'" ] ) )
            else:
                key = self.kwcharmap[res]
                win = self.kwmap[key][2]        # our setting's window
                default = self.kwmap[key][1]    # the default value

                ewin = curses.textpad.Textbox( win, insert_mode=True )
                ewin.stripspaces = 1
                ewin.edit( )

                out = ewin.gather( ).rstrip( )
                win.clear( )
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
                    elif default is None:
                        if out == "None" or out == "" or out == "none":
                            out = None

                    if ( default is None and not out is None ) or out != default:
                        # Check everything out
                        if key == 'project':
                            reg = re.findall( r'([^0-9A-Za-z\-])', out )
                            if reg:
                                self.error( ''.join( [ "Project name cannot include ", reg[0] ] ) )
                                continue
                        elif key == 'report':
                            o = bool( urlparse.urlparse( out ).netloc )
                            if not o:
                                self.error( "Reporting server must be a HTTP URL" )
                                continue
                        elif key == 'run':
                            reg = re.findall( r'([^0-9A-Za-z\-\_])', out )
                            if reg:
                                self.error( ''.join( [ "Run name cannot include ", reg[0] ] ) )
                                continue

                    # Finally add it in and go on
                    self.kwargs[key] = out
                    win.addstr( str( out ) )
                except Exception as e:
                    win.addstr( str( self.kwargs.get( key, default ) ) )
                    self.error( e )

                win.refresh( )
                self.error( )

            doneCheck = False
            while not doneCheck: 
                self.stdscr.refresh( )
                self.ebox.clear( )
                self.entry.edit( ) 
                res = self.entry.gather( ).rstrip( )
                if res == "":
                    done = True
                    if not self.checkValues( ):
                        done = False
                    else:
                        break
                else:
                    break



    def checkValues( self ):
        r = None
        rep = self.kwargs.get( 'report', None )
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
                            if response["projectRequired"] and self.kwargs.get( 'project', None ) is None:
                                self.error( "Server explicity requires a project name" )
                                return False
                    except Exception as e:
                        pass
                    if err is None:
                        err = "Handshake failed; not a reporting server"
                else:
                    err = "Connection to reporting server failed"
            if err is not None:
                self.error( ''.join( [ err, ", press enter again to ignore" ] ), "Warning" )
                return False
        return True
                                


    def error( self, msg=None, type="Error" ):
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
        i = 0 
        off = 0
        tab = 15
        for key in self.kwarray:
            y = i + 1
            x = 2
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
                self.stdscr.addstr( y, x, key )
                off += 1
            
            i += 1

