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
# stats( good, bad, timetaken, children, times )
# Prints Statistics
#   Prints out success / fail counts, total / remaining jobs, failure rate, number of children,
#   and then averages / extrapolations. It requires good / bad count (#), and then arrays of times taken,
#   the child processes, and number of times (#). 
def stats( good, bad, timetaken, children, times ):   
    print( "\n" + ( "=" * 40 ) )
    print( "Successful: " + str( good ) + ( " " * 3 ) + "Failed: " + str( bad ) )
    print( "Total: " + str( good + bad ) + ( " " * 3 ) + "Remaining: " + str( times * len( children ) - good ) )
    print( "Children: " + str( len( children ) ) )
    avg = 0
    for time in timetaken:
        avg += time
    if len( timetaken ) > 0:
        print( "Failure Rate: " + format( bad / float( good + bad ) * 100 ) + "%" );

        avg /= len( timetaken )
        print( "Average / Estimates:" )
        print( "  Time per job: " + format( avg ) + " seconds" )
        print( "  Jobs/s: " + format( 1 / avg ) + ( " " * 3 ) + "Jobs/m: "  + format( 60 / avg ) + ( " " * 3 )+ "Jobs/hr: " 
               + format( 60 * 60 / avg ) + ( " " * 3 ) + "Jobs/day: " + format( 60 * 60 * 24 / avg ) )
    else:
        print "No data to extrapolate or average from"
    print( ( "=" * 40 ) + "\n" )
####################################################################################################
