from multiprocessing import Process, Queue
from datetime import datetime
from selenium.webdriver import PhantomJS
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from const import * # Constants
import os, time

class Child:
    def __init__( self, cq, wq, num, runnum ):
        # Our output queue (childqueue)
        self.cq = cq

        # Our input queue (workqueue)
        self.wq = wq

        # Our child number
        self.num = num

        # Our timestamp
        self.timestamp = datetime.now( ).strftime( "%Y-%m-%d_%H-%M-%S" )

        # Log directory
        self.log = os.path.dirname( os.path.abspath( __file__ ) ) + "\\logs\\" + self.timestamp + "\\" + str( num + 1 ) + "\\"

        # Run number, used to have different logs and error screenshots
        self.run = str( runnum )
        
        # Our driver instance
        self.driver = None

        # Our process        
        self.proc = Process( target=self.think, args=( ) )
        
        self.msg( "LOADING" )

        self.proc.start( )
    
    ####################################################################################################
    # msg( msg )
    # Formats a message for this child to be printed out.
    def msg( self, message ):
        print( "Child #" + str( self.num + 1 ) + ": " + message )
    ####################################################################################################
        

    def think( self ):
        wq = self.wq
        cq = self.cq

        DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0'
        dcaps = { 'acceptSslCerts': True, 'loadImages': False }

        if not os.path.isdir( self.log ):
            os.makedirs( self.log )

        self.driver = PhantomJS( desired_capabilities=dcaps, service_args=['--ignore-ssl-errors=true'], service_log_path=( self.log + "ghostdriver_" + self.run + ".log" ) )
     
        self.msg( "STARTING" )

        while not wq.empty( ):
            func = wq.get( True, 5 )
            res = []
            start = 0
            
            try:
                start = time.clock( )
                func( self.driver )
            except Exception as e:
                self.logError( str( e ) )
                cq.put( [ self.num, FAILED, ( time.clock( ) - start ), str( e ) ] )
            else:
                cq.put( [ self.num, DONE, ( time.clock( ) - start ), "" ] )

        self.driver.quit( )

    def logError( self, e ):
        self.driver.save_screenshot( self.log + 'error_' + self.run + '.png' ) 

    def is_alive( self ):
        if self.proc != None:
            return self.proc.is_alive( )
        else:  
            return False

    def is_dead( self ):
        return self.proc == None

    def restart( self ):
        self.msg( "RESTARTING" )

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

