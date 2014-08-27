import re, json, time
from const import *



def format( t ):
    """Formats a Float into a displayable form, rounding it into converting to a string.
       
       :param t: Input float.
       :return: String that's formatted like so: ``54.32``.
    """
    return str( round( t, 2 ) )



def formatError( res, type="message" ):
    """Formats the GhostDriver json-encoded error message for easier printing. In the end, this amounts
       to replacing escaped quotation marks, parsing the JSON message, and extracting the 'errorMessage' portion.
       It also trims the message to 81 characters if it is over that.

       :param res: The json-encoded string from a webdriver exception.
       :param message type: The type of message passed to this function. If it isn't the default,
           regex ignores it. 
       :return: String of the formatted `res` initially passed in.
    """
    a = re.compile( r"Message: [a-z]'({.+})'" )

    if a.match( str( res ) ):
        res = re.sub( r"\\'", "'", res )                          # unescape single quotes or json freaks out
        res = re.sub( r"\\\\\"", "\\\"", res )                    # same but with double escaped quotes

        res = a.match( str( res ) )
        res = res.groups( )[0]

        try: 
            t = json.loads( res )
            res = t
        except:
            type = None
        
        if type == "message":
            res = res['errorMessage']

    if len( res ) > 80 and type != "log":
        res = res[0:80]
    return res


def childMessage( num, msg ):
    """Consistently formats a message to be print out to the console for this child.
       
       :param num: The number of the child we are printing a message for.
       :param msg: The message for the child. Formatted like so: ``Child #num: msg``
       :return: None
    """
    #print( ''.join( [ "Child #", str( num + 1 ), ": ", msg ] ) )



def stats( good, bad, timetaken, children, times, starttime ):
    """Prints out statistics for the current running pool.

       This includes the following:
         * Successful/failed jobs
         * Total jobs done
         * Remaining jobs
         * Failure rate
         * Number of children currently and at peak
         * Average time per job
         * Average jobs per minute, seconds, and more


       :param good: The number of jobs completed successfully.
       :param bad: The number of jobs that failed.
       :param timetaken: An array of job completion times from all children.
       :param children: An array of our pool's children. Counted and checked if alive for display.
       :param times: The number of jobs initially given to our pool.
       :param starttime: A timestamp for when our pool started. 
       :return: None
    """
    
    print( ''.join( [ "\n", ( "=" * 40 ) ] ) )
    print( ''.join( [ "Successful: ", str( good ), ( " " * 3 ), "Failed: ", str( bad ) ] ) )
    print( ''.join( [ "Total: ", str( good + bad ), ( " " * 3 ), "Remaining: ", str( times - good ) ] ) )

    active = 0
    for c in children:
        if c.is_alive( ) and not c.is_done( ):
            active += 1
    print( ''.join( [ "Children (peak): ",  str( len( children ) ),  ( " " * 3 ),  "Children (active): ", str( active ) ] ) )

    if len( timetaken ) > 0:
        print( ''.join( [ "Failure Rate: ", format( bad / float( good + bad ) * 100 ), "%" ] ) );

        # This gives us our jobs per second
        jps = good / ( time.time( ) - starttime )

        print( "Average / Estimates:" )
        print( ''.join( [ "  Time per job: ", format( avg( timetaken ) ), "s" ] ) )
        print( ''.join( [ "  Jobs/s: ", format( jps ), ( " " * 3 ), "Jobs/m: ", format( jps * 60 ), ( " " * 3 ), "Jobs/hr: ", 
               format( jps * 60 * 60 ), ( " " * 3 ), "Jobs/day: ", format( jps * 60 * 60 * 24 ) ] ) )
    else:
        print "No data to extrapolate or average from"
    print( ''.join( [ ( "=" * 40 ), "\n" ] ) )



def errorLevelToStr( level ):
    """Takes a numeric error level and translates it into a string for displaying in a 
       log.
       
       :param level: The level to translate into a loggable string.
       :return: String of the level in parenthesis.
    """
    if level == NOTICE:
        return "(NOTICE)  "
    if level == WARNING:
        return "(WARNING) "
    if level == ERROR: 
        return "(ERROR)   "
    if level == CRITICAL:
        return "(CRITICAL)"
    if level == INFO:
        return "(INFO)    "
    if level == NONE:
        return "          "
    return



def avg( numbers ):
    """Averages a list of numbers.
       
       :param numbers: A list of numbers.
       :return: The average
    """
    if len( numbers ) == 0:
        return 0
    else:
        return( sum( numbers ) / len( numbers ) )
