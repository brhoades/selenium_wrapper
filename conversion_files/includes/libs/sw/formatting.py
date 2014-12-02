from sw.const import *

def format( t, precision=2 ):
    """Formats a Float into a displayable form, rounding it, and converting to a string.
       
       :param t: Input Float to round.
       :param 2 precision: Precision to round to.

       :return: String, ex: ``54.32``.
    """
    return str( round( t, precision ) )



def formatError( res, type="message" ):
    """Formats the WebDriver JSON-encoded error message from an exception for easier printing. In the end, this amounts
       to replacing escaped quotation marks, parsing the JSON message, and extracting the 'errorMessage' key.
       The message is also trimmed to 80 characters.

       :param res: The JSON-encoded string from a WebDriver exception.
       :param message type: The type of message passed to this function. If it isn't the default,
           regex ignores it. If not specified json isn't parsed and the error in its entirety is
           passed back.
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



def errorLevelToStr( level, parens=True ):
    """Takes a numeric error level and translates it into a string for displaying in a 
       log.
       
       :param level: The level to translate into a loggable string.
       :param True parens: If the level will be contained in parenthesis
       :return: String of the level in parenthesis.
    """
    r = ""
    if level == NOTICE:
        r = "NOTICE"
    elif level == WARNING:
        r = "WARNING"
    elif level == ERR: 
        r = "ERROR"
    elif level == CRITICAL:
        r = "CRITICAL"
    elif level == INFO:
        r = "INFO"
    elif level == NONE and parens == True:
        parens = False
    
    if parens:
        return ''.join( [ "(", r, ")", (10-len(r))*" " ] )
    else:
        return ''.join( [ r, (10-len(r))*" " ] )



def avg( numbers ):
    """Averages a list of numbers. Handles lists of length zero.
       
       :param numbers: A list of numbers.
       :return: The average
    """

    if len( numbers ) == 0:
        return 0
    else:
        return( sum( numbers ) / len( numbers ) )
