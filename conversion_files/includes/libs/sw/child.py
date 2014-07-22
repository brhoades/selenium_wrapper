from multiprocessing import Process, Queue
from selenium.webdriver import PhantomJS
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from const import * # Constants
import time, os

class Child:
    ################################################################################################
    # __init__( self, cq, wq, num, log )
    # Initialize our Child
    #   Initializes our child and then starts it. It takes our pool's childqueue, our pool's workqueue,
    #   our child's number to report back statuses, and our base log directory.
    def __init__( self, cq, wq, num, log ):
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

        # Although ignoring sslcerts works, not loading images does not.
        dcaps = { 'acceptSslCerts': True, 'loadImages': False }

        if not os.path.isdir( self.log ):
            os.makedirs( self.log )

        # Initialize our driver with our custom log directories and preferences (capabilities)
        self.driver = PhantomJS( desired_capabilities=dcaps, service_args=['--ignore-ssl-errors=true'], \
            service_log_path=( self.log + "ghostdriver_" + self.run + ".log" ) )
     
        self.msg( "STARTING" )

        # While our work queue isn't empty...
        while not wq.empty( ):
            func = wq.get( True, 5 )
            res = []
            start = 0
            
            # Try, if an element isn't found an exception is thrown
            try:
                start = time.clock( )
                func( self.driver )
            except Exception as e:
                self.logError( str( e ) ) # Capture the exception and log it
                cq.put( [ self.num, FAILED, ( time.clock( ) - start ), str( e ) ] )
            else:
                cq.put( [ self.num, DONE, ( time.clock( ) - start ), "" ] )

        # Quit after we have finished our work queue, this kills the phantomjs process.
        self.driver.quit( )
    ################################################################################################

    ################################################################################################
    # logError( self, e )
    # Log Screenshot of Error
    #   Renders a screenshot of what it sees then writes it to our log directory as error_#.png
    def logError( self, e ):
        self.driver.save_screenshot( self.log + 'error_' + self.run + '.png' ) 
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
            self.msg( "STOPPING (" + msg + ")" )
        else:
            self.msg( "STOPPING" )

        self.proc.terminate( )
        self.proc.join( )
        self.proc = None
    ################################################################################################
