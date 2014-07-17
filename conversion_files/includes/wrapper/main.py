from selenium.webdriver import PhantomJS
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re, sys, time, os
from multiprocessing import Process, Queue
from datetime import datetime

READY = 3

def jQCheck( driver ):
    cwd = os.path.dirname(os.path.abspath(__file__))
    jq = cwd + "\includes\jquery-1.11.1.min.js"
    timeout = 1 
    i = 0

    if bool(driver.execute_script("return typeof jQuery == 'undefined'")):
        start = time.clock( )
        while bool(driver.execute_script("return typeof jQuery == 'undefined'")) and time.clock( ) - start < timeout:
            if i % 10:
                driver.execute_script( "var jq = document.createElement('script');jq.src = '" + jq + "';document.getElementsByTagName('head')[0].appendChild(jq);" )
            i += 1
            time.sleep( 0.1 )
        if bool(driver.execute_script("return typeof jQuery == 'undefined'")):
            return False
        else:
            return True

def exists( driver, element, type="id" ):
    res = ""

    if type == "xpath" or type == "link_text" or type == "css_selector":
        if not jQCheck( driver ):
            res = True

    if res == "":
        if type == "id": 
            res = driver.execute_script( "return( !!document.getElementById('" + element + "') )" )
        elif type == "name":
            res = driver.execute_script( "return( document.getElementsByName('" + element + "').length > 0 )" )
        elif type == "xpath":
            res = driver.execute_script( "return( !!document.evaluate( '" + element + "', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null ).singleNodeValue )" )
        elif type == "link_text":
            res = driver.execute_script( "return( !!jQuery( \"a:contains('" + element + "')\" ).length > 0 )" )
        elif type == "css_selector":
            res = driver.execute_script( "return( jQuery( \"" + element + "\" ).length > 0 )" )

    if res == True:
        e = ""
        if type == "id":
            e = driver.find_element_by_id( element )
        elif type == "name":
            e = driver.find_element_by_name( element )
        elif type == "xpath":
            e = driver.find_element_by_xpath( element )
        elif type == "link_text":
            e = driver.find_element_by_link_text( element )
        elif type == "css_selector":
            e = driver.find_element_by_css_selector( element )

        if e.is_displayed( ):
            return True

    return False

def sleepwait( driver, element, type, timeout=15 ):
    start = time.clock( )
    while not exists( driver, element, type ) and int( time.clock( ) - start ) < timeout:
        time.sleep( .1 )
        print( "ELEMENT ("+type+"): " + element )
    else:
        return element 

    print( "WARNING: " + element + " will not be found!" )
    return element

def blurrywait( driver ):
    element = "salesforceSource_blurybackground"

    i = 0
    if exists( driver, element ):
      e = driver.find_element_by_id( element ) 
      while e.is_displayed( ):
        if not exists( driver, element ):
          break
    
def format( t ):
    return str(round(t, 2))

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

def format( t ):
    return str(round(t, 2))

def stats( good, bad, timetaken, children, times ):   
    print( "\n" + ("="*40) )
    print( "Successful: " + str(good) + (" "*3) + "Failed: " + str(bad) )
    print( "Total: " + str(good+bad) + (" "*3) + "Remaining: " + str(times*len(children)-good) )
    print( "Failure Rate: " + format(bad/float(good+bad)*100) + "%" );
    print( "Children: " + str( len( children ) ) )
    avg = 0
    for time in timetaken:
        avg += time
    if len(timetaken) > 0:
        avg /= len(timetaken)
        print( "Average / Estimates:" )
        print( "  Time per order: " + format(avg) + " seconds" )
        print( "  Orders/s: " + format(1/avg) + (" "*3) + "Orders/m: "  + format(60/avg) + (" "*3)+ "Orders/hr: " 
               + format(60*60/avg) + (" "*3) + "Orders/day: " + format(60*60*24/avg) )
    else:
        print "No data to extrapolate or average from"
    print( ( "="*40 ) + "\n" )

def formatError( res ):
    a = re.compile(r"Message: [a-z]'([A-Za-z\s\:]+)\\n")

    if a.match( str( res ) ):
        r = a.match( str( res ) )
        return "ERROR: \"" + r.groups( )[0] + "\""
    else:
        return res

def childMessage( num, msg ):
    print( "Child #" + str( num + 1 ) + ": " + msg )

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
  
    last = 0
    # Cycle and watch
    while len( processes ) > 0:
        time.sleep( 1 )
        for q in queues:
            x = queues.index( q )
            while not q.empty( ):
                res = q.get( )
                if res[0] == False:
                    res[2] = formatError( res[2] )
                    childMessage( x, "ERROR - " + res[2] )
                    results.append( res[0] )
                elif res[0] == True:
                    times.append( res[1] )
                    childMessage( x, "DONE (" + format( res[1] ) + "s)" )
                    results.append( res[0] )
                    childstats[x][3] += 1
                elif res[0] == READY:
                    childMessage( x, "STARTING" )

        for p in processes:
            i = processes.index( p )
            if not p.is_alive( ) and childstats[i][4]:
                if childstats[i][3] >= numtimes: 
                    childMessage( i, "FINISHED" )
                    childstats[i][4] = False
                    p.join( )
                    next
                else:
                    childMessage( i, "DEAD" )
                p.join( )

                childstats[i][2] += 1
                processes[i] = Process( target=runFullTest, args=( numtimes, queues[i], func, childstats[i] ) )
                processes[i].start( )
                childMessage( i, "LOADING" ) 

        if len(results) >= step+last:
            last = len(results)
            good = 0
            bad = 0
            for r in results:
                if r == True:
                    good += 1   
                else:
                    bad += 1
            stats( good, bad, times, processes, numtimes )
