from multiprocessing import Process, Queue, Value
from selenium import webdriver
from selenium.webdriver.phantomjs.service import Service as PhantomJSService
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from sw.const import * # Constants
from sw.formatting import formatError, errorLevelToStr
from sw.cache import ElementCache 
import time, os, traceback, subprocess
from pprint import pformat
from datetime import datetime
from selenium.common.exceptions import *

class Child:
    """Initializes our child and then starts it. It takes our pool's childqueue, our pool's workqueue,
    our child's number to report back statuses, our base log directory, and a collection of options.

    :param cq: ChildQueue, this is passed from :class:`sw.pool` and is used to transmit the status of the child
        to our pool.
    :param wq: WorkQueue, also passed from :class:`sw.pool` and child pops a function off of it to run (a job) 
        when it finishes a job / starts initially.
    :param num: Number of the child relevant to :class:`sw.pool`'s self.data array. This index is used to 
        easily communicate results and relate them to the child in that array. `num` is also used when printing
        out a status message.
    :param log: Base log directory which we spit logs and screenshots into.
    :param options: Dict from kwargs which contains directives to pass to GhostDriver.

    :return: Child (self)
    """
    def __init__( self, cq, wq, num, log, options ):
        # Our output queue (childqueue)
        self.cq = cq

        # Our input queue (workqueue)
        self.wq = wq

        # Our child number
        self.num = num

        # Our driver instance
        self.driver = None

        # Our log folder which never changes
        self.log = log

        # Our log handle
        self.lh = "" 

        # Logging level
        self.level = INFO 

        # Do we load images and other options
        self.options = options

        # Storage for our function we get
        self.func  = None

        # How long we sleep in loops
        self.sleepTime = 1

        # Our per page element cache.
        self.cache = ElementCache( )

        # Our current status
        self.status = Value( 'i', STARTING )
        

        # Now start
        self.start( )



    def think( self ):
        """The meat of the wrapper, where the main thinking is done. Takes no arguments, just reads from 
           self variables set in :py:class:`sw.Child`. PhantomJS is added into the python path by run.bat, so
           that is already handled.

           :return: None
        """

        # Push a STARTING message to our pool
        self.display( DISP_START )

        wq = self.wq
        cq = self.cq

        # This changes our useragent to something that shouldn't trigger websense
        DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = \
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)'

        # Monkeypatch our PhantomJS class in, which disables images
        webdriver.phantomjs.webdriver.Service = PhantomJSNoImages

        # Workaround for internal SSL woes
        dcaps = { 'acceptSslCerts': True }

        sargs = [ ''.join( [ '--load-images=', str( self.options['images'] ).lower( ) ] ),
                  '--disk-cache=true',
                  '--ignore-ssl-errors=yes' ]

        if 'proxy' in self.options:
            sargs.append( ''.join( [ '--proxy=', self.options['proxy'] ] ) )
        if 'proxytype' in self.options:
            sargs.append( ''.join( [ '--proxy-type=', self.options['proxytype'] ] ) )

        try: 
            # Initialize our driver with our custom log directories and preferences (capabilities)
            self.driver = webdriver.PhantomJS( desired_capabilities=dcaps, service_log_path=os.path.join( self.log, "ghostdriver.log" ), \
                                               service_args=sargs )
        except Exception as e:
            self.logMsg( ''.join( [ "Webdriver failed to load: ", str( e ), "\n", traceback.format_exc( ) ] ), CRITICAL )
            try: 
                self.driver.quit( )
            except:
                return
            return

        # Insert ourself into webdriver
        self.driver.child = self

        # Change our implicit wait time
        self.driver.implicitly_wait( 0 )

        cq.put( [ self.num, READY, "" ] )

        # Write to our log another message indicating we are starting our runs
        self.logMsg( "Child process started and loaded" )

        # While our work queue isn't empty...
        while not wq.empty( ):
            func = wq.get( True, 5 )
            self.func = func
            res = []
            start = 0

            # Still running
            self.status = RUNNING
            
            # Try, if an element isn't found an exception is thrown
            try:
                self.cache.clear( )
                start = time.time( )
                self.display( DISP_GOOD )
                func( self.driver )
            except TimeoutException as e:
                self.logMsg( ''.join( [ "Stack trace: ", traceback.format_exc( ) ] ), CRITICAL )
                
                self.display( DISP_ERROR )
                self.logMsg( "Timeout when finding element." )
            except Exception as e:
                self.logError( str( e ) ) # Capture the exception and log it
                self.logMsg( ''.join( [ "Stack trace: ", traceback.format_exc( ) ] ), CRITICAL )

                cq.put( [ self.num, FAILED, ( time.time( ) - start ), str( e ) ] )
                break
            else:
                self.display( DISP_FINISH )
                t = time.time( ) - start
                cq.put( [ self.num, DONE, ( time.time( ) - start ), "" ] )
                self.logMsg( ''.join( [ "Successfully finished job (", format( t ), "s)" ] ) )
                time.sleep( 0.5 )

        # Quit after we have finished our work queue, this kills the phantomjs process.
        self.driver.quit( )
        self.display( DISP_DONE )
        self.status = STOPPED



    def logError( self, e, noScreenshot=False ):
        """Log Screenshot of Error with Exception
           Renders a screenshot of what it sees then writes it to our log directory as error_#.png
           Also takes the exception we received and exports it as text

           :param e: Unicode json-encoded string from a webdriver-thrown error.
           :param False noScreenshot: Whether or not to take a screenshot of the error.
           :return: None
        """

        o = pformat( formatError( e, "log" ) )
        self.logMsg( o, CRITICAL )

        if not noScreenshot:
            self.screenshot( CRITICAL )



    def screenshot( self, level=NOTICE ):
        """Saves a screenshot to error_#.png and prints a message into the log specifying the file logged to.
           
           :param NOTICE level: This determines whether or not the error message will be logged according to the
               level set in self.level. The screenshot will print anyway. If this error is not greater or equal to the level specified in self.level,
               it is not printed. If it is, the message is printed into log.txt with the level specified by the timestamp.
           :return: None
        """
        fn = ""
        i = 0
        # If we are writing several errors, number them appropriately
        if not os.path.exists( self.log ):
            self.logMsg( ''.join( [ "Cannot write to a log directory that doesn't exist. ", self.log ] ), CRITICAL )
            return

        while True:
            fn = os.path.join( self.log, ''.join( [ 'error_', str( i ), '.png' ] ) )
            i += 1
            if not os.path.isfile( fn ):
                break

        self.driver.save_screenshot( fn ) 
        self.logMsg( ''.join( [ "Wrote screenshot to: ", fn ] ), level )



    def logMsg( self, e, level=NOTICE, **kwargs ):
        """Writes to our message log if level is greater than or equal to our level (in self.log).
        
           :param e: The message to be written to the log.
            
           :param NOTICE level: This determines whether or not the error message will be logged according to the
               level set in self.level. If this error is not greater or equal to the level specified in self.level,
               it is not printed. If it is, the message is printed into log.txt with the level specified by the timestamp.

           :Kwargs:
              * **locals** (*None*): Optional locals dict to print out cleanly.
           :return: None
        """
        locals = kwargs.get( 'locals', None )

        # Send error if appropriate
        if level >= ERROR:
            self.display( DISP_ERROR )

        # Determine if we're logging this low
        if level < self.level:
            return

        # Get our timestamp
        timestamp = datetime.now( ).strftime( "%H:%M:%S" )
        
        # String
        w = ''.join( [ "[", timestamp, "] ", errorLevelToStr( level ), "\t", e, "\n" ] )

        # Locals if specified
        if locals != None:
            self.logMsg( ''.join( [ "Local variables: ", pformat( locals ) ] ), level )

        # This typically errors out the first time through
        try: 
            self.lh.write( w ) 
        except:
            self.lh = open( os.path.join( self.log, ''.join( [ 'log-', str( self.num + 1 ), '.txt' ] ) ), 'a+', 0 )
            self.lh.write( w ) 



    def display( self, t ):
        """Sends a display message to the main loop, which is then translated to the UI."""
        self.cq.put( [ self.num, DISPLAY, t ] )



    def is_alive( self ):
        """
           Checks if the child's process is still running, if it is then it returns True, otherwise False.
           There's a check for if the process is None, which is set when a child terminates.

           :return: Boolean for if Child process is still active (different from if a child is processing data).
           """
        if self.proc != None:
            return self.proc.is_alive( )
        else:  
            return False



    def start( self, flag=DISP_LOAD ):
        """Starts our child process off properly, used after a restart typically.
           
           :param DISP_LOAD flag:
           :return: None
        """
        # Not stopped anymore
        self.status = STARTING

        # Create our path
        if not os.path.isdir( self.log ):
            os.makedirs( self.log )

        # Open our handle
        self.lh = open( os.path.join( self.log, ''.join( [ 'log-', str( self.num + 1 ), '.txt' ] ) ), 'a+' )

        # Show loading
        self.display( flag )

        # Our process 
        self.proc = Process( target=self.think, args=( ) )
        self.proc.start( )



    def restart( self, msg="restarting", flag=None ):
        """Restarts the child process and gets webdriver running again.

           :param "RESTARTING" msg: A message to print out in parenenthesis.
           :param None flag: 
           :return: None
        """
        if flag is not None:
            self.stop( msg, flag )
            self.start( flag )
        else:
            self.stop( msg )
            self.start( )



    def stop( self, msg="", flag=FINISHED ):
        """Stops a child process properly and sets its self.proc to None. Optionally takes a message
           to print out.
        
           :param "" msg: A message to show in parenthesis on the console next to ``Child #: STOPPING (msg)``.
           :param FINISHED flag:
           :return: None
        """
        if self.proc == None:
            return
        elif self.status == RUNNING and self.func is not None:
            self.wq.put( self.func ) # Put our job back on the queue so one doesn't disappear

        # Prevent the pool from trying to restart us
        self.status = flag

        if msg != "":
            self.logMsg( ''.join( [ "Stopping child process: \"", msg, "\"" ] ) )
        else:
            self.logMsg( "Stopping child process" )

        # Kill our process
        if self.proc != None:
            if os.name != "posix":
                subprocess.call( [ 'taskkill', '/F', '/T', '/PID', str( self.proc.pid ) ], stdout=open( os.devnull, 'wb' ) )
            else:
                subprocess.call( [ 'pkill', '-TERM', '-P', str( self.proc.pid ) ], stdout=open( os.devnull, 'wb' ) )
            self.proc.join( )
            self.proc = None

        # Inform the TUI that we're done.
        self.display( DISP_DONE )

        # Close our log
        self.lh.close( )



class PhantomJSNoImages( PhantomJSService ):
    """This class sits atop our PhantomJSService class included in webdriver to implemention service_args
       inclusion, which we pass by default --load-images=no to disable images.

       :param PhantomJSService: Pass this function the PhantomJSService class so that it can patch on top of it.
       :return: PhantomJsNoImages (self)
    """
    def __init__( self, *args, **kwargs ):
        service_args = kwargs.setdefault( 'service_args', [] )

        super( PhantomJSNoImages, self ).__init__( *args, **kwargs )
