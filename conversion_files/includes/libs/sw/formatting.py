import re, json, time
from const import *



####################################################################################################
# format( t )
# Formats a Float into a displayable form (rounds it and converts to string)
def format( t ):
    return str( round( t, 2 ) )
####################################################################################################



####################################################################################################
# formatError( res )
# Formats an Error Message
#   Formats the GhostDriver json-encoded error message for easier printing.
def formatError( res, type="message" ):
    a = re.compile( r"Message: [a-z]'({.+})'" )

    res = re.sub( r"\\'", "'", res )                        # unescape single quotes or json freaks out
    res = re.sub( r"\\\\\"", "\\\"", res )                    # same but with double escaped quotes

    if a.match( str( res ) ):
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
####################################################################################################



####################################################################################################
# childMessage( num, msg )
# Formats a message for child to be printed out.
def childMessage( num, msg ):
    print( "Child #" + str( num + 1 ) + ": " + msg )
####################################################################################################



####################################################################################################
# stats( good, bad, timetaken, children, times, starttime, waittime )
# Prints Statistics
#   Prints out success / fail counts, total / remaining jobs, failure rate, number of children,
#   and then averages / extrapolations. It requires good / bad count (#), and then arrays of times taken,
#   the child processes, number of times (#), and our start time in seconds. Also, we pass the time we've spent 
#   waiting.
def stats( good, bad, timetaken, children, times, starttime, waittime ):   
    print( "\n" + ( "=" * 40 ) )
    print( "Successful: " + str( good ) + ( " " * 3 ) + "Failed: " + str( bad ) )
    print( "Total: " + str( good + bad ) + ( " " * 3 ) + "Remaining: " + str( times - good ) )

    active = 0
    for c in children:
        if c.is_alive( ) and not c.is_done( ):
            active += 1
    print( "Children (peak): " + str( len( children ) ) + ( " " * 3 ) + "Children (active): " + str( active ) )

    if len( timetaken ) > 0:
        print( "Failure Rate: " + format( bad / float( good + bad ) * 100 ) + "%" );

        # This gives us our jobs per second
        jps = good / ( time.time( ) - starttime )

        print( "Average / Estimates:" )
        print( "  Time per job: " + format( avg( timetaken ) ) + "s" )
        print( "  Time waiting: " + format( avg( waittime ) ) + "s ("   
               + format( avg( waittime ) / avg( timetaken ) * 100 ) + "%)" )
        print( "  Jobs/s: " + format( jps ) + ( " " * 3 ) + "Jobs/m: "  + format( jps * 60 ) + ( " " * 3 ) + "Jobs/hr: " 
               + format( jps * 60 * 60 ) + ( " " * 3 ) + "Jobs/day: " + format( jps * 60 * 60 * 24 ) )
    else:
        print "No data to extrapolate or average from"
    print( ( "=" * 40 ) + "\n" )
####################################################################################################



####################################################################################################
# errorLevelToStr( level )
# Translates an Error Level to a String
#   This function takes a numeric error level and translates it into a string for displaying in a 
#   log.
def errorLevelToStr( level ):
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
####################################################################################################



####################################################################################################
# avg( numbers )
# Averages List
def avg( numbers ):
    if len( numbers ) == 0:
        return 0
    else:
        return( sum( numbers ) / len( numbers ) )
####################################################################################################
