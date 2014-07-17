from selenium.webdriver import PhantomJS
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re, sys, time, os
from multiprocessing import Process, Queue
from datetime import datetime

# Queue Results
FAILED = False
DONE = True
READY = 2 

#childstats indicies
TIMESTAMP      = 0
CHILD_NUMBER   = 1
FAILURES       = 2
SUCESSES       = 3
ACTIVE         = 4

def runFullTest( numtimes, q, func, d ):
    DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0'
    DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.loadImages'] = False
    dcaps = { 'acceptSslCerts': True }
    error_path = os.path.dirname(os.path.abspath(__file__)) + "\\logs\\" + d[0] + "\\" + str(d[1]) + "\\"
    if not os.path.isdir( error_path ):
        os.makedirs( error_path )
    driver = PhantomJS( desired_capabilities=dcaps, service_args=['--ignore-ssl-errors=true'], service_log_path=( error_path + "ghostdriver_" + str(d[2]) + ".log" ) )
 
    q.put( [ READY ] )
    
    good = 0
    bad  = 0
    timetaken = []

    for x in range(numtimes):
        res = []
        start = 0
        
        try:
            start = time.clock( )
            func( driver )
        except Exception as e:
            driver.save_screenshot( error_path + 'error_' + str( d[2] ) + '.png' )
            res = [ False, ( time.clock( ) - start ), str( e ) ]
        else:
            res = [ True, ( time.clock( ) - start ), "" ]

        q.put( res )
    driver.quit( )

def main( func ):
    print( "\nLibraries loaded!\n\n" )
    numtimes = 1
    children = 3 
    step = 5
    killChromeInstances = True

    if len(sys.argv) > 1:
        numtimes = int(sys.argv[1])
    if len(sys.argv) > 2:
        children = int(sys.argv[2])

    print( "Preparing " + str( children ) + " children running " + str( numtimes ) + " times each:" )
    processes = []
    queues = []
    times = []
    results = []
    childstats = []
    for x in range(children):
        q = Queue( )

        childstats.append( [ datetime.now( ).strftime( "%Y-%m-%d_%H-%M-%S" ), x+1, 1, 0, True ] )

        childMessage( x, "LOADING" )
        p = Process( target=runFullTest, args=( numtimes, q, func, childstats[-1] ) )
        p.start( )

        processes.append( p )
        queues.append( q )
    
    print( "\n" + ("="*40) )

    mainLoop( processes, queues, times, results, childstats )

def mainLoop( processes, queues, times, results, childstats ):
    last = 0
    # Cycle and watch
    while len( processes ) > 0:
        time.sleep( 1 )

        # Check if we have anything new to chew on
        for q in queues:
            x = queues.index( q )

            # Chew on this queue until we deplete it
            while not q.empty( ):
                res = q.get( )

                if res[0] == FAILED:   # This process (w/ index x) threw an exception
                    res[2] = formatError( res[2] )
                    childMessage( x, "ERROR - " + res[2] )
                    results.append( res[0] )
                elif res[0] == DONE:  # This process reported finished with a job
                    times.append( res[1] )
                    childMessage( x, "DONE (" + format( res[1] ) + "s)" )
                    results.append( res[0] )
                    childstats[x][SUCCESSES] += 1
                elif res[0] == READY:
                    childMessage( x, "STARTING" )
                    next
                results.append( res[0] )

        for p in processes:
            i = processes.index( p )
            if not p.is_alive( ) and childstats[i][ACTIVE]:
                if childstats[i][SUCCESSES] >= numtimes: 
                    childMessage( i, "FINISHED" )
                    childstats[i][ACTIVE] = False
                    p.join( )
                    next
                else:
                    childMessage( i, "DEAD" )
                p.join( )

                childstats[i][FAILURES] += 1
                processes[i] = Process( target=runFullTest, args=( numtimes, queues[i], func, childstats[i] ) )
                processes[i].start( )
                childMessage( i, "LOADING" ) 

        if len(results) >= step+last:
            last = len(results)
            good = mapgithub 
            bad = 0
            stats( good, bad, times, processes, numtimes )
