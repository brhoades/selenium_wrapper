from multiprocessing import Process, Queue
from selenium import webdriver
from selenium.webdriver.phantomjs.service import Service as PhantomJSService
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from sw.const import * # Constants
from sw.formatting import formatError, errorLevelToStr
import time, os, traceback
from pprint import pformat
from datetime import datetime
import cProfile, pstats, StringIO

class Child:
    ################################################################################################
    # __init__( self, cq, wq, num, log, options )
    # Initialize our Child
    #   Initializes our child and then starts it. It takes our pool's childqueue, our pool's workqueue,
    #   our child's number to report back statuses, our base log directory, and a collection of options.
    def __init__( self, cq, wq, num, log, options ):
        # Our output queue (childqueue)
        self.cq = cq

        # Our input queue (workqueue)
        self.wq = wq

        # Our child number
        self.num = num

        # Run number, used to have different logs and error screenshots after restarting
        self.run = 0 
        
        # Our driver instance
        self.driver = None

        # Our log folder, which is changed each time start is called (so see start)
        self.log = ""

        # The base log folder, which never changes.
        self.baselog = log

        # Our log handle
        self.lh = "" 

        # Logging level
        self.level = INFO 

        # Do we load images
        self.options = options

        # How long we sleep in loops
        self.sleepTime = 1

        self.start( )
    ################################################################################################



    ################################################################################################
    # msg( self, message )
    # Formats a message for this child to be printed out.
    def msg( self, message ):
        print( "Child #" + str( self.num + 1 ) + ": " + message )
    ################################################################################################



    ################################################################################################
    # think( self )
    #   The beef of the script, where the main thinking is done. Takes no arguments, just reads from 
    #   self variables. PhantomJS is added into the python path automatically, so nothing has to be done
    #   there.
    def think( self ):
        wq = self.wq
        cq = self.cq

        # This changes our useragent to something that shouldn't trigger websense
        DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = \
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)'

        # Monkeypatch our PhantomJS class in, which disables images
        webdriver.phantomjs.webdriver.Service = PhantomJSNoImages

        # Workaround for internal SSL woes
        dcaps = { 'acceptSslCerts': True }

        sargs = [ '--load-images=' + str( self.options['images'] ).lower( ),
                  '--disk-cache=true',
                  '--ignore-ssl-errors=yes' ]

        if 'proxy' in self.options:
            sargs.append( '--proxy=' + self.options['proxy'] )
        if 'proxytype' in self.options:
            sargs.append( '--proxy-type=' + self.options['proxytype'] )

        try: 
            # Initialize our driver with our custom log directories and preferences (capabilities)
            self.driver = webdriver.PhantomJS( desired_capabilities=dcaps, service_log_path=os.path.join( self.log, "ghostdriver.log" ), \
                                               service_args=sargs )
        except Exception as e:
            self.logMsg( "Webdriver failed to load: " + str( e ) + "\n " + traceback.formatexc( ), CRITICAL )
            self.msg( "WEBDRIVER ERROR" )
            try: 
                self.driver.quit( )
            except:
                return
            return

        # Insert ourself into webdriver
        self.driver.child = self

        # Change our implicit wait time
        self.driver.implicitly_wait( 0 )

        # Push a STARTING message to our pool, if we print it we risk scrambling text in stdout
        cq.put( [ self.num, READY, time.time( ), "" ] )

        # Write to our log another message indicating we are starting our runs
        self.logMsg( "Child process started and loaded" )

        pr = cProfile.Profile( )
        pr.enable( )
        # While our work queue isn't empty...
        while not wq.empty( ):
            func = wq.get( True, 5 )
            res = []
            start = 0
            
            # Try, if an element isn't found an exception is thrown
            try:
                start = time.time( )
                func( self.driver )
            except Exception as e:
                self.logError( str( e ) ) # Capture the exception and log it
                self.logMsg( "Stack trace: " + traceback.format_exc( ), CRITICAL )

                cq.put( [ self.num, FAILED, ( time.time( ) - start ), str( e ) ] )
                break
            else:
                t = time.time( ) - start
                cq.put( [ self.num, DONE, ( time.time( ) - start ), "" ] )
                self.logMsg( "Successfully finished job (" + format( t ) + "s)" )
        pr.disable( )
        f = open( os.path.join( self.log, 'stats.txt' ), 'w' )
        ps = pstats.Stats( pr, stream=f ).strip_dirs( ).sort_stats( 'cumtime' ).print_stats( )
        f.close( )

        # Quit after we have finished our work queue, this kills the phantomjs process.
        self.driver.quit( )
    ################################################################################################



    ################################################################################################
    # logError( self, e )
    # Log Screenshot of Error with Exception
    #   Renders a screenshot of what it sees then writes it to our log directory as error_#.png
    #   Also takes the exception we received and exports it as text
    def logError( self, e, noScreenshot=False ):

        o = pformat( formatError( e, "log" ) )
        self.logMsg( o, CRITICAL )

        if not noScreenshot:
            self.screenshot( CRITICAL )
    ################################################################################################



    
    ################################################################################################
    # screenshot( level=NOTICE )
    # Logs a screenshot and prints a message.
    def screenshot( self, level=NOTICE ):
        fn = ""
        i = 0
        # If we are writing several errors, number them appropriately
        if not os.path.exists( self.log ):
            self.logMsg( "Cannot write to a log directory that doesn't exist. " + self.log, CRITICAL )
            return

        while True:
            fn = os.path.join( self.log, 'error_' + str( i ) + '.png' )
            i += 1
            if not os.path.isfile( fn ):
                break

        self.driver.save_screenshot( fn ) 
        self.logMsg( "Wrote screenshot to: " + fn, level )
    ################################################################################################



    ################################################################################################
    # logMsg( self, e, level )
    # Logs a Message
    #   Writes to our message log if level is what we are logging at.
    def logMsg( self, e, level=NOTICE ):
        # Determine if we're logging this low
        if level < self.level:
            return

        # Get our timestamp
        timestamp = datetime.now( ).strftime( "%H:%M:%S" )
        
        # string
        w = "[%s] %s\t%s\n" % ( timestamp, errorLevelToStr( level ), e )

        # This typically errors out the first time through
        try: 
            self.lh.write( w ) 
        except:
            self.lh = open( os.path.join( self.log, 'log.txt' ), 'a+', 0 )
            self.lh.write( w ) 
    ################################################################################################



    ################################################################################################
    # is_alive( self )
    # Is Child Alive
    #   Checks if the child's process is still running, if it is then it returns True, otherwise False.
    #   There's a check for if the process is None, which is set when a child terminates.
    def is_alive( self ):
        if self.proc != None:
            return self.proc.is_alive( )
        else:  
            return False
    ################################################################################################



    ################################################################################################
    # is_done( self )
    # Is Child Done
    #   Check if a child is done. When a child process is finished its self.proc is set to None.
    def is_done( self ):
        return self.proc == None
    ################################################################################################



    ################################################################################################
    # start( self )
    # Start Child
    #   Starts our child process off properly, used after a restart typically.
    def start( self ):
        # Move our run number up since we are starting
        self.run = str( int( self.run ) + 1 )

        # Log directory, unique so that each
        self.log = os.path.join( self.baselog, str( self.num + 1 ) + "-" + self.run )

        # Create our path
        if not os.path.isdir( self.log ):
            os.makedirs( self.log )

        # Open our handle
        self.lh = open( os.path.join( self.log, 'log.txt' ), 'a+' )

        # Our process        
        self.proc = Process( target=self.think, args=( ) )
        self.msg( "LOADING" )
        self.proc.start( )

    ################################################################################################



    ################################################################################################
    # restart( self )
    # Restarts Child
    #   Restarts the child process and gets webdriver running again.
    def restart( self ):
        self.stop( "RESTARTING" )
        self.start( )

    ################################################################################################



    ################################################################################################
    # stop( self, msg="" )
    # Stops Child
    #   Stops a child process properly and sets its self.proc to None. Optionally takes a message
    #   to print out.
    def stop( self, msg="" ):
        if self.proc == None:
            return

        if msg != "":
            self.logMsg( "Stopping child process: \"%s\"" % ( msg ) )
            self.msg( "STOPPING (%s)"  % ( msg ) )
        else:
            self.logMsg( "Stopping child process" )
            self.msg( "STOPPING" )

        self.proc.terminate( )
        self.proc.join( )
        self.proc = None

        self.lh.close( )
    ################################################################################################



####################################################################################################
# PhantomJSNoImages
# Monkey Patched Class to Disable Images
#   This class sits atop our PhantomJSService class included in webdriver to implemention service_args
#   inclusion, which we pass by default --load-images=no to disable images.
class PhantomJSNoImages( PhantomJSService ):
    def __init__( self, *args, **kwargs ):
        service_args = kwargs.setdefault( 'service_args', [] )

        super( PhantomJSNoImages, self ).__init__( *args, **kwargs )
####################################################################################################
