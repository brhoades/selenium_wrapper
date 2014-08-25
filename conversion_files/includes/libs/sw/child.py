from multiprocessing import Process, Queue
from selenium import webdriver
from selenium.webdriver.phantomjs.service import Service as PhantomJSService
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from sw.const import * # Constants
from sw.formatting import formatError, errorLevelToStr
from sw.cache import *
import time, os, traceback
from pprint import pformat
from datetime import datetime
import cProfile, pstats, StringIO
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
    :param log: Base log directory which a child will create a `num`-`self.run` folder in to log to.
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

        self.cache = ElementCache( )

        self.start( )



    def msg( self, message ):
        """Formats a message for this child to be printed out.

        :param msg: The message to be printed out to the console.
        :return: None
        """
        print( "Child #" + str( self.num + 1 ) + ": " + message )



    def think( self ):
        """The beef of the wrapper, where the main thinking is done. Takes no arguments, just reads from 
           self variables set in :class:`sw.Child`. PhantomJS is added into the python path by run.bat, so
           that is already handled.

           :return: None
        """

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

        # While our work queue isn't empty...
        while not wq.empty( ):
            func = wq.get( True, 5 )
            res = []
            start = 0
            
            # Try, if an element isn't found an exception is thrown
            try:
                self.cache.clear( )
                start = time.time( )
                func( self.driver )
            except TimeoutException as e:
                self.logMsg( "Stack trace: " + traceback.format_exc( ), CRITICAL )
                
                self.msg( "TIMEOUT" )
                self.logMsg( "Timeout when finding element." )
            except Exception as e:
                self.logError( str( e ) ) # Capture the exception and log it
                self.logMsg( "Stack trace: " + traceback.format_exc( ), CRITICAL )

                cq.put( [ self.num, FAILED, ( time.time( ) - start ), str( e ) ] )
                break
            else:
                t = time.time( ) - start
                cq.put( [ self.num, DONE, ( time.time( ) - start ), "" ] )
                self.logMsg( "Successfully finished job (" + format( t ) + "s)" )

        # Quit after we have finished our work queue, this kills the phantomjs process.
        self.driver.quit( )



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
        """Saves a screenshot to `num`-`run`/error_#.png and prints a message into the log specifying the file logged to.
           
           :param NOTICE level: This determines whether or not the error message will be logged according to the
               level set in self.level. The screenshot will print anyway. If this error is not greater or equal to the level specified in self.level,
               it is not printed. If it is, the message is printed into log.txt with the level specified by the timestamp.
           :return: None
        """
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



    def logMsg( self, e, level=NOTICE ):
        """Writes to our message log if level is greater than or equal to our level (in self.log).
        
           :param e: The message to be written to the log.
            
           :param NOTICE level: This determines whether or not the error message will be logged according to the
               level set in self.level. If this error is not greater or equal to the level specified in self.level,
               it is not printed. If it is, the message is printed into log.txt with the level specified by the timestamp.
           :return: None
        """
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



    def is_done( self ):
        """Check if a child is done. When a child process is finished its self.proc is set to None.
           
           :return: Boolean for if Child is finished processing data. This is usually signal to kill the subprocess.
        """
        return self.proc == None



    def start( self ):
        """Starts our child process off properly, used after a restart typically.
           
           :return: None
        """
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



    def restart( self, msg="RESTARTING" ):
        """Restarts the child process and gets webdriver running again.

           :param "RESTARTING" msg: A message to print out in parenenthesis.
           :return: None
        """
        self.stop( "RESTARTING" )
        self.stop( msg )
        self.start( )



    def stop( self, msg="" ):
        """Stops a child process properly and sets its self.proc to None. Optionally takes a message
           to print out.
        
           :param "" msg: A message to show in parenthesis on the console next to ``Child #: STOPPING (msg)``.
           :return: None
        """
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



class PhantomJSNoImages( PhantomJSService ):
    """This class sits atop our PhantomJSService class included in webdriver to implemention service_args
       inclusion, which we pass by default --load-images=no to disable images.

       :param PhantomJSService: Pass this function the PhantomJSService class so that it can patch on top of it.
       :return: PhantomJsNoImages (self)
    """
    def __init__( self, *args, **kwargs ):
        service_args = kwargs.setdefault( 'service_args', [] )

        super( PhantomJSNoImages, self ).__init__( *args, **kwargs )
