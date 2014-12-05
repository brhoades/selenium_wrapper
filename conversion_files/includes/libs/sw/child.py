from multiprocessing import Process, Value
from selenium import webdriver
from selenium.webdriver.phantomjs.service import Service as PhantomJSService
from sw.const import * # Constants
from sw.formatting import formatError, errorLevelToStr
from sw.cache import ElementCache 
import time, os, traceback, subprocess
from pprint import pformat
from datetime import datetime
from selenium.common.exceptions import *

class Child:
    """An abstraction upon a process for our :class:`~sw.pool.Pool`. Serves to more easily house a separate process and
    communicate with it crossprocess. A Child is not entirely a separate container that is spawned from Pool and given
    free reign. The bulk of a Child is stored on the primary thread with the Pool, UI, and Reporting. However, 
    :py:func:`~sw.child.Child.think` is on a separate `multiprocessing.Process` along with the provided *func* and
    GhostDriver / PhantomJS. All communication between Pool and Child is conducted over Child.statusVar (:py:func:`~multiprocessing.Value`) and
    Child.cq / Child.wq (:py:class:`~multiprocessing.Queue`) to avoid locks (they are multiprocess-safe).
    
    The off-thread child handles its own log, status reporting, error reporting, and getting new jobs. Once the process
    is started control is handed back over to the Pool which then manages the processes. 

    
    :param cq: ChildQueue reference from :class:`~sw.pool.Pool`. Used to transmit the status of this Child
        to our Pool.
    :param wq: WorkQueue reference from :class:`~sw.pool.Pool`. This Child pops a function off this Queue 
        then executes it, then repeats.
    :param num: Number of the Child relevant to :class:`~sw.pool.Pool`'s self.data array. This index is used to 
        easily communicate results and relate them to the child in that array. This number is actually one less
        than the index displayed on the console (which starts at 1 for the end user's sake).
    :param log: Base log directory which we spit logs and screenshots into. Just a string which should never change.
    :param options: Dict of kwargs which contain specific options passed to our wrapper.

    :return: Child (self)
    """
    def __init__( self, cq, wq, num, log, options ):
        self.cq = cq # Our shared output queue (childqueue) (multiprocessing)
        self.wq = wq  # Our shared input queue (workqueue) (multiprocessing)

        self.num = num
        self.driver = None
        self.log = log
        self.lh = "" 
        self.options = options
        self.level = self.options.get( 'level', NOTICE )
        self.func  = None
        self.sleepTime = self.options.get( 'childsleeptime', 1 )
        self.cache = ElementCache( )
        self.statusVar = Value( 'i', STARTING )
        
        self.start( )



    def think( self ):
        """This method is spawned on a separate process from our main thread. It takes no arguments, just reads from 
           self variables set in :py:class:`~sw.child.Child` that are multiprocess-safe: wq, cq, and statusVar (and various 
           static variables). It also uses various on class variables for storage which are not touched by pool.

           The purpose of this method is to cleanly start a loop of running PhantomJS with a fresh function pulled from
           wq every time. When think ends, our Child process ends as well.

           :return: None
        """

        # Change our status ASAP so users actually see it change to black (and know the Child started).
        self.display( DISP_START )

        wq = self.wq
        cq = self.cq

        # This allows custom service arguments to be forced into PhantomJS, as it is not supported with the Python
        # bindings by default.
        webdriver.phantomjs.webdriver.Service = PhantomJSNoImages

        sargs = [ ''.join( [ '--load-images=', str( self.options['images'] ).lower( ) ] ),
                  ''.join( [ '--disk-cache=', str( self.options.get( 'browsercache', "true" ) ).lower( ) ] ),
                  ''.join( [ '--ignore-ssl-errors=', str( self.options.get( 'ignoresslerrors', "yes" ) ).lower( ) ] ) ]

        if 'proxy' in self.options:
            sargs.append( ''.join( [ '--proxy=', self.options['proxy'] ] ) )
        if 'proxytype' in self.options:
            sargs.append( ''.join( [ '--proxy-type=', self.options['proxytype'] ] ) )

        try: 
            self.driver = webdriver.PhantomJS( service_log_path=os.path.join( self.log, self.options.get( 'ghostdriverlog', "ghostdriver.log" ) ), service_args=sargs )
        except Exception as e:
            self.logMsg( ''.join( [ "Webdriver failed to load: ", str( e ), "\n", traceback.format_exc( ) ] ), CRITICAL )
            try: 
                self.driver.quit( )
            except:
                return
            return

        # This enables custom callbacks from WebDriver to this Child. Primarily used to read options and throw errors. Usage
        # can be seen in `sw.utils`.
        self.driver.child = self

        # WebDriver, by default, waits 15 seconds while intensively scanning the DOM for an element. This forces it to
        # throw an error instantly if the element does not exist.
        self.driver.implicitly_wait( 0 )

        cq.put( [ self.num, READY, "" ] )

        self.logMsg( "Child process started and loaded" )

        while not wq.empty( ):
            # Block and wait otherwise exceptions are thrown. I've never seen it fail to get something here as
            # there's a check below.
            self.func = wq.get( True, 5 )
            res = []
            start = 0

            # Below we set to an error / done and wait.

            # FIXME: Waiting a second to show a status isn't appropriate. The Pool should change the status
            # for the child after enough time has elapsed.
            self.status( RUNNING )
            
            try:
                self.cache.clear( )
                start = time.time( )
                self.display( DISP_GOOD )
                cq.put( [ self.num, MESSAGE, time.time( ), R_JOB_START ] )
                self.func( self.driver )
            except TimeoutException as e:
                self.display( DISP_ERROR )

                screen = self.logError( str( e ) )
                self.logMsg( ''.join( [ "Stack trace: ", traceback.format_exc( ) ] ), CRITICAL )
                
                cq.put( [ self.num, FAILED, ( time.time( ) - start ), str( e ), screen ] )
                self.logMsg( "Timeout when finding element." )
                time.sleep( 1 )
            except Exception as e:
                self.display( DISP_ERROR )

                screen = self.logError( str( e ) ) # Capture the exception and log it
                self.logMsg( ''.join( [ "Stack trace: ", traceback.format_exc( ) ] ), CRITICAL )

                cq.put( [ self.num, FAILED, ( time.time( ) - start ), str( e ), screen ] )
                time.sleep( 1 )
                break
            else:
                self.display( DISP_FINISH )

                t = time.time( ) - start
                cq.put( [ self.num, DONE, ( time.time( ) - start ), "" ] )
                self.logMsg( ''.join( [ "Successfully finished job (", format( t ), "s)" ] ) )
                time.sleep( 0.5 )

        # This line will cleanly kill PhantomJs for us.
        self.driver.quit( )
        self.display( DISP_DONE )
        self.status( FINISHED )



    def logError( self, e, screenshot=True ):
        """Takes a JSON-encoded Selenium exception's text and spits it into the log in a more meaningful format.
            Can optionally take a screenshot too.

           :param e: Unicode JSON-encoded string from a WebDriver-thrown exception. *Must be a String*.
           :param True screenshot: Take a screenshot of the error automatically.

           :return: String for screenshot location, if any.
        """

        o = pformat( formatError( e, "log" ) )
        self.logMsg( o, CRITICAL )

        if screenshot:
            return self.screenshot( CRITICAL )



    def screenshot( self, level=NOTICE ):
        """Saves a screenshot to error_#.png and prints a message into the log specifying the file logged to.
           
           :param NOTICE level: This determines whether or not the error message will be logged according to the
               level set in self.level. The screenshot will print anyway. If this error is not greater or equal to the level specified in self.level,
               it is not printed. If it is, the message is printed into log.txt with the level specified by the timestamp.
           :return: String for screenshot location
        """
        fn = ""
        i = 0
        # If we are writing several errors, number them appropriately
        if not os.path.exists( self.log ):
            raise ValueError( ''.join( [ "Cannot write to a log directory that doesn't exist. ", self.log ] ), CRITICAL )
            return

        while True:
            fn = os.path.join( self.log, ''.join( [ 'error_', str( i ), '.png' ] ) )
            i += 1
            if not os.path.isfile( fn ):
                break

        self.driver.save_screenshot( fn ) 
        self.logMsg( ''.join( [ "Wrote screenshot to: ", fn ] ), level )

        return fn



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
        """Sends a display message to the main loop, which is then translated to the UI.
           
           :param t: The status this child will now show, a constant starting with DISP in const.py.

           :returns: None
        """
        self.cq.put( [ self.num, DISPLAY, t ] )



    def is_alive( self ):
        """Checks if the child's process is still running, if it is then it returns True, otherwise False.
           There's a check for if the process is None, which is set when a child terminates.

           :return: Boolean for if Child process is still active (different from if a child is processing data).
        """
        if self.proc != None:
            return self.proc.is_alive( )
        else:  
            return False



    def status( self, type=None ):
        """Uses a multiprocess-safe variable to transmit our status upstream. These values are listed under
           universal status types in const.py. The status types allow better logging and, for example, prevent
           children that were already terminated from being terminated again (and throwing an exception).

           When called with a type it will set this child's status on both the main process and the child's 
           process. When called without it, it reads from the status variable.

           :param None type: The new value of our status.

           :returns: If type isn't specified, our status. If it is, it sets our type and returns None.
        """
        if type is None:
            return self.statusVar.value
        else:
            with self.statusVar.get_lock( ):
                self.statusVar.value = type



    def start( self, flag=DISP_LOAD ):
        """Starts our child process off properly, used after a restart typically.
           
           :param DISP_LOAD flag: A custom flag to change the display color of the child, if desired.
           :return: None
        """
        # Not stopped anymore
        self.status( STARTING )

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
           :param None flag: A custom flag to change the display color of the child, if desired.

           :return: None
        """
        if flag is not None:
            self.stop( msg, flag )
            self.start( flag )
        else:
            self.stop( msg )
            self.start( )



    def stop( self, msg="", flag=FINISHED, disp_flag=DISP_DONE ):
        """Stops a child process properly and sets its self.proc to None. Optionally takes a message
           to print out.
        
           :param "" msg: A message to show in parenthesis on the console next to ``Child #: STOPPING (msg)``.
           :param FINISHED flag: A custom status flag for if the child is finished, paused, stopped, or whatever is desired.
           :param DISP_DONE disp_flag: A custom display flag for the status of the child after stopping.

           :return: None
        """
        if self.proc == None:
            return

        # Prevent the pool from trying to restart us
        self.status( flag )

        if msg != "":
            self.logMsg( ''.join( [ "Stopping child process: \"", msg, "\"" ] ) )
        else:
            self.logMsg( "Stopping child process" )

        # Kill our process
        if self.proc != None:
            if os.name != "posix":
                subprocess.call( [ 'taskkill', '/F', '/T', '/PID', str( self.proc.pid ) ], stdout=open( os.devnull, 'wb' ), stderr=open( os.devnull, 'wb' ) )
            else:
                subprocess.call( [ 'pkill', '-TERM', '-P', str( self.proc.pid ) ], stdout=open( os.devnull, 'wb' ), stderr=open( os.devnull, 'wb' ) )
            self.proc.join( )
            self.proc = None

        # Inform the TUI that we're done.
        self.display( disp_flag )

        # Close our log
        self.lh.close( )
        

    def flush( self ):
        """Flushes our log so that messages are retained on an internal error.

           :return: None
        """

        self.lh.flush( )



class PhantomJSNoImages( PhantomJSService ):
    """This class sits atop our PhantomJSService class included in webdriver to implemention service_args
       inclusion, which we pass by default --load-images=no to disable images.

       :param PhantomJSService: Pass this function the PhantomJSService class so that it can patch on top of it.
       :return: PhantomJsNoImages (self)
    """
    def __init__( self, *args, **kwargs ):
        service_args = kwargs.setdefault( 'service_args', [] )

        super( PhantomJSNoImages, self ).__init__( *args, **kwargs )
