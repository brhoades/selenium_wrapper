import re, json

####################################################################################################
# format( t )
# Formats a Float into a displayable form (rounds it and converts to string)
def format( t ):
    return str( round( t, 2 ) )
####################################################################################################


####################################################################################################
# formatError( res )
# Formats an Error Message
#   Previously formatted an error message provided by ChromeDriver via regex.
def formatError( res ):
    a = re.compile( r"Message: [a-z]'({.+})'" )             # Currently in the format for chromeDriver

    res = re.sub( r"\\'", "'", res )                        # unescape single quotes or json freaks out
    res = re.sub( r"\\\\\"", "\\\"", res )                    # same but with double escaped quotes

    if a.match( str( res ) ):
        res = a.match( str( res ) )
        res = res.groups( )[0]
        
        res = json.loads( res )
        res = res['errorMessage']

    if len( res ) > 80:
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
# stats( good, bad, timetaken, children, times )
# Prints Statistics
#   Prints out success / fail counts, total / remaining orders, failure rate, number of children,
#   and then averages / extrapolations. It requires good / bad count (#), and then arrays of times taken,
#   the child processes, and number of times (#). 
def stats( good, bad, timetaken, children, times ):   
    print( "\n" + ( "=" * 40 ) )
    print( "Successful: " + str( good ) + ( " " * 3 ) + "Failed: " + str( bad ) )
    print( "Total: " + str( good + bad ) + ( " " * 3 ) + "Remaining: " + str( times * len( children ) - good ) )
    print( "Failure Rate: " + format( bad / float( good + bad ) * 100 ) + "%" );
    print( "Children: " + str( len( children ) ) )
    avg = 0
    for time in timetaken:
        avg += time
    if len( timetaken ) > 0:
        avg /= len( timetaken )
        print( "Average / Estimates:" )
        print( "  Time per order: " + format( avg ) + " seconds" )
        print( "  Orders/s: " + format( 1 / avg ) + ( " " * 3 ) + "Orders/m: "  + format( 60 / avg ) + ( " " * 3 )+ "Orders/hr: " 
               + format( 60 * 60 / avg ) + ( " " * 3 ) + "Orders/day: " + format( 60 * 60 * 24 / avg ) )
    else:
        print "No data to extrapolate or average from"
    print( ( "=" * 40 ) + "\n" )
####################################################################################################
