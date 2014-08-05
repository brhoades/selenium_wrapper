from multiprocessing import Process, Queue
from selenium import webdriver
from selenium.webdriver.phantomjs.service import Service as PhantomJSService
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from sw.const import * # Constants
from sw.formatting import formatError, errorLevelToStr
import time, os
from pprint import pformat
from datetime import datetime

class Child:
    ################################################################################################
    # __init__( self, cq, wq, num, log, images )
    # Initialize our Child
    #   Initializes our child and then starts it. It takes our pool's childqueue, our pool's workqueue,
    #   our child's number to report back statuses, our base log directory, and whether or not we load 
    #   images.
    def __init__( self, cq, wq, num, log, images ):
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

        # Logging level
        self.level = INFO 

        # Do we load images
        self.images = images

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
            'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0'

        # Monkeypatch our PhantomJS class in, which disables images
        webdriver.phantomjs.webdriver.Service = PhantomJSNoImages

        # Workaround for internal SSL woes
        dcaps = { 'acceptSslCerts': True }

        if not os.path.isdir( self.log ):
            os.makedirs( self.log )

        try: 
            # Initialize our driver with our custom log directories and preferences (capabilities)
            self.driver = webdriver.PhantomJS( desired_capabilities=dcaps, service_log_path=( self.log + "ghostdriver.log" ), \
                                               service_args=[ '--load-images=' + str( self.images ).lower( ), 
                                                              '--disk-cache=true',
                                                              '--ignore-ssl-errors=yes' ] )
        except Exception as e:
            self.logError( "Webdriver failed to load: " + str( e ), True )
            self.msg( "WEBDRIVER ERROR" )
            try: 
                self.driver.quit( )
            except:
                return
            return

        # Insert ourself into webdriver
        self.driver.child = self

        # Push a STARTING message to our pool, if we print it we risk scrambling text in stdout
        cq.put( [ self.num, READY, time.time( ), "" ] )

        # Write to our log another message indicating we are starting our runs
        self.logMsg( "Child process started and loaded" )

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
                cq.put( [ self.num, FAILED, ( time.time( ) - start ), str( e ) ] )
                break
            else:
                t = time.time( ) - start
                cq.put( [ self.num, DONE, ( time.time( ) - start ), "" ] )
                self.logMsg( "Successfully finished job (" + format( t ) + "s)" )

        # Quit after we have finished our work queue, this kills the phantomjs process.
        self.driver.quit( )
    ################################################################################################



    ################################################################################################
    # logError( self, e )
    # Log Screenshot of Error with Exception
    #   Renders a screenshot of what it sees then writes it to our log directory as error_#.png
    #   Also takes the exception we received and exports it as text
    def logError( self, e, noScreenshot=False ):
        if not noScreenshot:
            self.driver.save_screenshot( self.log + 'error.png' ) 

        o = pformat( formatError( e, "log" ) )
        self.logMsg( o, CRITICAL )
    ################################################################################################



    ################################################################################################
    # logMsg( self, e )
    # Logs a Message
    #   Writes to our message log
    def logMsg( self, e, level=NOTICE ):
        # Get our timestamp
        timestamp = datetime.now( ).strftime( "%H:%M:%S" )

        # Determine if we're logging this low
        if level >= self.level:
            f = open( self.log + 'log.txt', 'a+' )
            f.write( "[%s] %s\t%s\n" % ( timestamp, errorLevelToStr( level ), e ) ) 
            f.close( )
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
        self.log = self.baselog + str( self.num + 1 ) + "-" + self.run + "\\"

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
