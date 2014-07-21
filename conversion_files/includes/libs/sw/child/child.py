from multiprocessing import Process, Queue

import datetime
from selenium.webdriver import PhantomJS
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from childpool import *

class Child:
    def __init__( self, pool, num ):
        # Our Pool
        self.pool = pool

        # Our child number
        self.num = num

        # Our timestamp
        self.timestamp = datetime.now( ).strftime( "%Y-%m-%d_%H-%M-%S" )

        # Log directory
        self.log = os.path.dirname( os.path.abspath( __file__ ) ) + "\\logs\\" + self.timestamp + "\\" + str( num + 1 ) + "\\"

        # Run number, used to have different logs and error screenshots
        self.run = str( self.pool.data[num][FAILURES] )
        
        # Our driver instance
        self.driver = None

        # Our process        
        self.proc = Process( target=self.think, args=( self ) )
        
        self.msg( "LOADING" )

        self.proc.start( )

        return self
    
    ####################################################################################################
    # msg( msg )
    # Formats a message for this child to be printed out.
    def msg( self, message ):
        print( "Child #" + str( self.num + 1 ) + ": " + message )
    ####################################################################################################
        

    def think( self ):
        DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0'
        dcaps = { 'acceptSslCerts': True, 'loadImages': False }

        if not os.path.isdir( error_path ):
            os.makedirs( error_path )

        self.driver = PhantomJS( desired_capabilities=dcaps, service_args=['--ignore-ssl-errors=true'], service_log_path=( error_path + "ghostdriver_" + self.run + ".log" ) )
     
        self.msg( "STARTING" )

        while not self.pool.workQueue.empty( ):
            func = self.pool.workQueue.get( True, 5 )
            res = []
            start = 0
            
            try:
                start = time.clock( )
                func( self.driver )
            except Exception as e:
                self.logError( str( e ) )
                self.pool.childQueue.put( [ self.num, FAILURE, ( time.clock( ) - start ), str( e ) ] )
            else:
                self.pool.childQueue.put( [ self.num, SUCCESS, ( time.clock( ) - start ), "" ] )

            q.put( res )
       # self.driver.quit( )

    def logError( self, e ):
        self.driver.save_screenshot( error_path + 'error_' + self.run + '.png' )
