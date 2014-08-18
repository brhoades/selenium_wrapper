import os, time, traceback
from const import *



####################################################################################################
# loadScript( driver, jqs )
# Loads JavaScript
#   This function takes our webdriver object in and injects some JavaScript.
def loadScript( driver, jqs ):
    driver.execute_script( \
        "var script = document.createElement( 'script' ); \
        script.type = 'text/javascript'; \
        script.src = '" + jqs + "'; \
        document.getElementsByTagName('head')[0].appendChild( script );" )
####################################################################################################



####################################################################################################
# jQCheck( driver )
# jQuery Check
#   This function takes our webdriver object in and checks if the current loaded page has jQuery on it.
#   If it doesn't, it tries to load it. It will pause the script for up to one second after loading,
#   after that it just returns False so that the exists script will stop holding things up. This
#   usually only happens on pages where some Javascript has failed.
def jQCheck( driver ):
    jqCheck = "return typeof jQuery != 'undefined'"          # Some StackOverflow post recommended this bit of code
    loadScript( driver, "http://code.jquery.com/jquery-2.1.1.min.js" )
    timeout = 1                                              # Number of seconds before we give up 

    if not bool( driver.execute_script( jqCheck ) ):         #FIXME: Add a check that makes sure we haven't held up
        driver.child.logMsg( "jQuery not loaded into browser, inserting manually.", INFO )
        loadScript( driver, jq )

        start = time.time( )
        while not bool( driver.execute_script( jqCheck ) ) and time.time( ) - start < timeout:
            time.sleep( driver.child.sleepTime )
        if not bool( driver.execute_script( jqCheck ) ):
            driver.child.logMsg( "jQuery failed to load into browser after " + str( timeout ) + "s.", WARNING  )
            return False                              # False, jQuery isn't loaded
        else:
            driver.child.logMsg( "jQuery loaded into browser successfully after " + format( str( time.time( ) - start ) ) + "s.", INFO )
            return True                               # True, it is
    else:
        return True
####################################################################################################



####################################################################################################
# exists( driver, element, type, noDriver )
# Check if Element Exists
#   Takes our webdriver object, an element name, and a type. Flips through a list of element types to 
#   run quick Javascript to check if the element exists. This is done because find_element_by.* has
#   a timeout where it waits for an element to appear for about 15 seconds. We try to only use that
#   if absolutely needed as a double check. An exception is when we don't have jQuery and can't use 
#   the last two, fancy, javascript checks, this bypasses them and directly goes to the webdriver test. 
def exists( driver, element, type, noDriver=False ):
    res = ""
    s = ""

    if not jQCheck( driver ):
        res = True
        noDriver = False
        child.logMsg( "Unable to properly load jQuery on page: " + driver.current_url, CRITICAL )

    # First block is for testing with javascript, which is very quick.
    if res == "":
        s = elementBySelector( element, type )
        try: 
            s += " return( e != null && typeof e != 'undefined' && !e.disabled && " \
                 + " e.is( ':visible' ) && !e.is( ':disabled' ) ); "
            res = driver.execute_script( s )
        except Exception as e:
            driver.child.logMsg( "Error in Javascript ('" + element + "', '" + type + "')", ERROR )
            driver.child.logMsg( str( e ), ERROR )
            driver.child.logMsg( traceback.format_exc( ), ERROR )
            res = False

    res = bool( res )
    
    if noDriver:
        return( res )

    # Second block for a more rigorous test with webdriver. This is time consuming and slow... only done if needed
    if res == True:
        e = ""
        try: 
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
        except Exception as e:
            return False

        if isDisplayed( e ) and isEnabled( e ):
            return True                             # This prevents things such as clear overlays from confusing our exist check

    return False
####################################################################################################



####################################################################################################
# sleepwait( driver, element, type, timeout=15 )
# Sleeps While Waiting for Element
#   The original brainchild of my wrapper, this function simply checks if an element exists( ) and 
#   sleeps until timeout for it. It always returns the element even if it fails.
#   Lightconfirm means any existance of the element (javascript or wd) counts as existing. This is lighter on the system.
def sleepwait( driver, element, type, **kwargs ):
    start = time.time( )
    timeout = kwargs.get( 'timeout', 15 )
    lightconfirm = kwargs.get( 'lightconfirm', False )
    
    if not exists( driver, element, type, lightconfirm ):
        driver.child.logMsg( "Beginning wait for element \"%s\" of type \"%s\"." % ( element, type ), NOTICE )

        while not exists( driver, element, type, lightconfirm ):
            if time.time( ) - start < timeout: 
                break
            time.sleep( driver.child.sleepTime )
        else:
            return element 
    else:
        return element

    driver.child.logMsg( "Element \"%s\" of type \"%s\" will not be found on page \"%s\"." % ( element, type, driver.current_url ), ERROR )
    return element
####################################################################################################



####################################################################################################
# sendKeys( driver, element, type, text )
# Sends Keys to Element
#   Drop in replacement for webdriver's sendkeys.
def sendKeys( driver, element, type, text ):
    if type == "id":
        driver.execute_script( "document.getElementById('" + element + "').value = '" + text + "'" )
    elif type == "name":
        driver.execute_script( "document.getElementsByName( '" + element + "' )[0].value = '" + text + "'" )
####################################################################################################



####################################################################################################
# waitToDisappear( driver, element, waitForElement=True, stayGone=0, recur=False, timeout=20, type="id"
#                  offset=0, waitTimeout = 1 )
# Waits for a Element to Disappear
#   Adapted from a previous, more specialized function to wait for any div with the id element 
#   to disappear, and wait until then. If stayGone is not 0, we will keep checking for stayGone 
#   seconds. If recur is selected we don't print out redundant information. With a timeout
#   we won't wait longer than timeout seconds
def waitToDisappear( driver, element, **kwargs ):
    waitForElement = kwargs.get( 'waitForElement', True )
    waitTimeout    = kwargs.get( 'waitTimeout', 1 )
    stayGone       = kwargs.get( 'stayGone', 0 )
    recur          = kwargs.get( 'recur', False )
    timeout        = kwargs.get( 'timeout', 20 )
    type           = kwargs.get( 'type', 'id' )
    offset         = kwargs.get( 'offset', 0 )
    start          = time.time( ) - offset

    # Do an initial wait for our element to appear. Any confirmation is confirmation (light).
    if waitForElement:
        sleepwait( driver, element, type, timeout=waitTimeout, lightconfirm=True )
        if not exists( driver, element, type, True ):
            # If we should wait for it and it's not here... leave.
            return

    if exists( driver, element, type, True ):
        start_inner = time.time( )
        if not recur:
            driver.child.logMsg( "Waiting for %s" % ( element ), INFO )

        while exists( driver, element, type, True ):
            if time.time( ) - start > timeout:
                driver.child.logMsg( "Element did not reappear within %ss, timed out." % ( str(timeout) ) )
                break #this skips the else
            time.sleep( driver.child.sleepTime )
        else:
            driver.child.cq.put( [ driver.child.num, WAIT_TIME, time.time( ) - start_inner ] )
            driver.child.logMsg( "Element \"%s\" disappeared!" % ( element ), INFO )

            if stayGone > 0:
                w = stayGone + time.time( )
                while w - time.time( ) >= 0:
                    if exists( driver, element, type, True ):
                        driver.logMsg( "Element came back!" )
                        kwargs['offset'] = time.time( ) - start
                        kwargs['recur'] = True

                        waitToDisappear( driver, element, kwargs )
                    time.sleep( driver.child.sleepTime )
####################################################################################################



####################################################################################################
# isDisplayed( e )
# Is e Displayed
#   Does a check to see if e is displayed... Catches exceptions safely. Often when we want to see
#   if an element is displayed, it isn't even on the page. This can kill the program.
def isDisplayed( e ):
    try:
        if e.is_displayed( ):
            return True
    except:
        return False
    return False
####################################################################################################



####################################################################################################
# isEnabled( e )
# Is e Enabled
#   Does a check to see if e is enabled... Catches exceptions.
def isEnabled( e ):
    try:
        if e.is_enabled( ):
            return True
    except:
        return False
    return False
####################################################################################################



####################################################################################################
# urlExtractRedirect( driver, variable, value )
# URL Extract and Redirect
#   Should extract a variable from driver.current_url, then plop its value on to url and redirect.
def urlExtractRedirect( driver, variable, value ):
    url = driver.current_url

    driver.child.logMsg( "urlExtractRedirect\nBEFORE: " + url )
    
    r = re.compile( r"(?P<start>[\?\&])%s=(?P<value>[^\&]+)$" % variable )

    if not url.match( r ):
        driver.logMsg( "WARNING: URL Doesn't appear to contain a variable in this manner: ?" + variable + "= or &" + variable + "=" )
        return
    
    re.sub( r, "\g<start>" + variable + "=" + value, url )

    driver.logMsg( "AFTER: " + url )
    driver.get( url )
####################################################################################################

def elementBySelector( element, type ):
    if type == "id": 
        s = "e = jQuery( document.getElementById( '" + element + "' ) );"
    elif type == "name":
        s = "e = null; if( document.getElementsByName( '" + element + "' ).length > 0 ) { " \
            + "e = jQuery( document.getElementsByName( '" + element + "' )[0] ) };" 
    elif type == "xpath":
        s = "e = jQuery( document.evaluate( \""+element+"\", document, null, XPathResult.ANY_TYPE, null ).iterateNext( ) );"
    elif type == "link_text":
        s = "e = jQuery( 'a:contains(\\'" + element + "\\')' );" 
    elif type == "css_selector":
        s = "e = jQuery( '" + element + "' );"

    return( s )
