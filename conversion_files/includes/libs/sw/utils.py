"""This module primarily serves as a holder for all directly webdriver-facing functions. These functions
   usually serve only the purpose of interfacing with elements on the page and possibly logging when an 
   error occurs. A lot of the code of these functions revolves around waiting.

   .. _common-params:

   -----------------
   Common Parameters
   -----------------
   These parameters apply for functions in this module which link back to this documentation. In particular:
   :func:`sleepwait`, :func:`waitToDisappear`, and :func:`exists`.

   :Common Params:
     * **driver** -- The webdriver instance that is being acted on by this script.
     * **element** -- An identifier for the element to search for.
     * **type** -- The type of `element`'s identifier. 
     
   :Common Kwargs: 
     * **timeout** (*15*) -- The amount of time, in seconds, before continuing on if the element is not found. Note that in
       some functions, such as :func:`sleepwait`, this can be fatal to the script. A timeout in sleepwait will cause the 
       script to either kill the child process (if `die` is enabled) or return `None` which webdriver cannot interface with.
     * **lightConfirm** (*False*) -- Only checks if an element exists, does not verify if it is enabled or visible. This saves
       some CPU usage but can be dangerous in the case of a disabled web prompt.
     * **cache** (*True*) -- Determines if elements will be cached internally within our :mod:`sw.child` process. This uses
       RAM over the a single run of the script, but has been shown to have speed savings in situations with a great deal
       of waiting. See :mod:`sw.cache` for more information.
     * **url** (*driver.current_url*) -- Current URL of the page webdriver is on. If this is not specified it is pulled from our
       webdriver every time, which can get expensive over the lifetime of a script with a lot of waiting. This is only used if
       `cache` is enabled and is otherwise ignored.
     * **thinkTime** (*child.sleepTime*) -- The time the script waits between polling for an element's existance. This is usually 
       the child's sleep time, but for :func:`waitToDisappear` it is twice that.
     * **die** (*True*) -- Whether or not the function kills the child if this is not found. Even if False, in the case of :func:`sleepwait`
       at least, there will usually be a fatal error anyway, especially if a :py:class:`~selenium.webdriver.remote.webelement.WebElement` 
       is expected to be returned. :func:`sleepwait` typically returns a :py:class:`~selenium.webdriver.remote.webelement.WebElement`
       but if the element is not found (and `die` is False) returns None. 
 
   ---------
   Functions
   ---------
"""
import os, time, traceback
from const import *



def loadScript( driver, js ):
    """Creates a new script object and appends it to the header.

       :Parameters:
         * :ref:`driver <common-params>`
         * **js** -- URL to a JavaScript file that will be inserted and loaded on this page.
       :return: None
    """

    driver.execute_script_async( \
        "var script = document.createElement( 'script' ); \
        script.type = 'text/javascript'; \
        script.src = '" + js + "'; \
        document.getElementsByTagName('head')[0].appendChild( script );" )



def jQCheck( driver, timeout=1 ):
    """This function takes our webdriver object in and checks if the current loaded page has jQuery on it.
       If it doesn't, it tries to load it. It will pause the script for up to `timeout` seconds after loading,
       after that it just returns False so that the exists script will stop holding things up.

       .. deprecated:: 0.1 
          JavaScript is no longer used to check for elements before running webdriver checks.

       :Parameters:
         * :ref:`driver <common-params>`
         * **timeout** (*1*) -- How long to wait for jQuery to load before continuing on. 
       :return: Boolean, True if jQuery is loaded False if it did not load.
    """

    jqCheck = "return typeof jQuery != 'undefined'"          # Some StackOverflow post recommended this bit of code
    loadScript( driver, "http://code.jquery.com/jquery-2.1.1.min.js" )

    if not bool( driver.execute_script( jqCheck ) ):         #FIXME: Add a check that makes sure we haven't held up
        driver.child.logMsg( "jQuery not loaded into browser, inserting manually.", INFO )
        loadScript( driver, jq )

        start = time.time( )
        while not bool( driver.execute_script( jqCheck ) ) and time.time( ) - start < timeout:
            time.sleep( driver.child.sleepTime )
        if not bool( driver.execute_script( jqCheck ) ):
            driver.child.logMsg( ''.join( [ "jQuery failed to load into browser after ", str( timeout ), "s." ] ), WARNING  )
            return False                              # False, jQuery isn't loaded
        else:
            driver.child.logMsg( ''.join( [ "jQuery loaded into browser successfully after ", format( time.time( ) - start ), "s." ] ), INFO )
            return True                               # True, it is
    else:
        return True



def exists( driver, element, type, **kwargs ):
    """Checks if an element exists with the WebDriver functions. Catches and handles exceptions if it doesn't.
       Previously there was an issue where the find_element_by... would wait for 15 seconds to find the element,
       but that has been resolved. If an element is in the DOM, does a final check to see if it is displayed and
       available.

       :Parameters:
         * :ref:`driver <common-params>`
         * :ref:`element <common-params>`
         * :ref:`type <common-params>`
       :Kwargs:
         * :ref:`lightConfirm <common-params>` 
         * :ref:`cache <common-params>`
         * :ref:`url <common-params>`
       :return: Boolean if doesn't exist, :py:class:`~selenium.webdriver.remote.webelement.WebElement` if it does.
    """

    lightConfirm = kwargs.get( 'lightConfirm', False )
    cache        = kwargs.get( 'cache', True )
    current_url  = kwargs.get( 'url', driver.current_url )

    e = None

    if cache:
        e = driver.child.cache.get( current_url, id=element, type=type )

    if e is None:
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

    if cache:
        driver.child.cache.add( current_url, e, id=element, type=type )

    if lightConfirm or ( isDisplayed( e ) and isEnabled( e ) ):
        return e 

    return False

def sleepwait( driver, element, type, **kwargs ):
    """The original brainchild of this wrapper, this function simply checks if an element exists( ) and 
       sleeps until timeout for it. It always returns something, even if it fails.

       :Parameters:
         * :ref:`driver <common-params>`
         * :ref:`element <common-params>`
         * :ref:`type <common-params>`

       :Kwargs:
         * :ref:`die <common-params>` -- This is only passed to subfunctions. :py:func:`waitToDisappear` never ends the script if something does not
            disappear.
         * :ref:`timeout <common-params>`
         * :ref:`thinkTime <common-params>`
         * :ref:`cache <common-params>`
         * :ref:`url <common-params>`
         * :ref:`lightConfirm <common-params>`
       :return: Boolean if doesn't exist, :py:class:`~selenium.webdriver.remote.webelement.WebElement` if it does.
    """
    start = time.time( )
    timeout      = kwargs.get( 'timeout', 15 )
    lightConfirm = kwargs.get( 'lightConfirm', False )
    cache        = kwargs.get( 'cache', True )
    url          = kwargs.get( 'url', driver.current_url )
    die          = kwargs.get( 'die', True )
    thinkTime = kwargs.get( 'thinkTime', driver.child.sleepTime )
    
    e = exists( driver, element, type, url=url, cache=cache, lightConfirm=lightConfirm )
    if not e:
        driver.child.logMsg( ''.join( [ "Beginning wait for element\"", element, "\" of type \"", type, "\"." ] ), NOTICE )

        while not e:
            if time.time( ) - start > timeout: 
                break
            time.sleep( thinkTime )

            e = exists( driver, element, type, url=url, cache=cache, lightConfirm=lightConfirm )
        else:
            return e 
    else:
        return e

    if die:
        driver.child.logMsg( ''.join( [ "Element will not be found on page \"", 
            driver.current_url, "\"." ] ), ERROR, locals=locals( ) )
        driver.child.restart( "element missing" )
        # Wait to be killed
        time.sleep( 10 )
    return False



def sendKeys( driver, element, type, text ):
    """Drop in, faster replacement for :py:meth:`~selenium.webdriver.remote.webelement.WebElement.send_keys`. Currently 
       only supports fields with an `id` or `name` identifier. 

       :Parameters:
          * :ref:`driver <common-params>`
          * :ref:`element <common-params>`
          * :ref:`type <common-params>`
          * **text** -- The text to type into the element.
       :return: None
    """
    sleepwait( driver, element, type, lightConfirm=True )

    if type == "id":
        driver.execute_script( ''.join( [ "document.getElementById( '", element, "' ).value = '", text, "'" ] ) )
    elif type == "name":
        driver.execute_script( ''.join( [ "document.getElementsByName( '", element, "' )[0].value = '", text, "'" ] ) )



def waitToDisappear( driver, element, **kwargs ):
    """Waits for an element to disappear from the page. Useful for transparent overlays that appear routinely
       as those block all input on the page (which angers WebDriver). Optionally can wait for an element to reappear
       and call itself again to wait longer.
       
       :Parameters:
          * :ref:`driver <common-params>`
          * :ref:`element <common-params>`
       :Kwargs:
         * :ref:`type <common-params>` (*"id"*)
         * :ref:`die <common-params>` -- This is only passed to subfunctions. :py:func:`waitToDisappear` never ends the script if something does not
           disappear.
       :(wait-related):
         * :ref:`timeout <common-params>` (*60*)
         * :ref:`thinkTime <common-params>` (*2*)
         * **stayGone** (*0*) -- Amount of time in seconds we wait, checking that the element is really gone.
         * **waitForElement** (*True*) -- If the element doesn't initially exist on the page, this controls if waitToDisappear waits for it first.
         * **waitTimeout** (*3*) -- Number of seconds we wait for the element to appear. If the element doesn't exist after this timeout,
           the function returns.
       :(internal):
         * :ref:`cache <common-params>`
         * **offset** (*0*) -- Used internally so timeout still applies to recursive calls. This offsets the next timeout by the amount of time
           waited in the previous call.
         * **recur** (*False*) -- Internally used to not print to the log if this function calls itself again.
       :return: None
    """
    waitForElement = kwargs.get( 'waitForElement', True )
    waitTimeout    = kwargs.get( 'waitTimeout', 3 )
    stayGone       = kwargs.get( 'stayGone', 0 )
    thinkTime      = kwargs.get( 'thinkTime', driver.child.sleepTime*2 )
    recur          = kwargs.get( 'recur', False )
    timeout        = kwargs.get( 'timeout', 60 )
    type           = kwargs.get( 'type', 'id' )
    offset         = kwargs.get( 'offset', 0 )
    cache          = kwargs.get( 'cache', True )
    die            = kwargs.get( 'die', True ) 

    start          = time.time( ) - offset
    url            = driver.current_url

    # Do an initial wait for our element to appear. Any confirmation is confirmation (light).
    if waitForElement:
        kwargs['die'] = False # Override die just in case element doesn't exist
        kwargs['timeout'] = waitTimeout
        sleepwait( driver, element, type, **kwargs )
        if not exists( driver, element, type, **kwargs ):
            driver.child.logMsg( ''.join( [ "In waitToDisappear \"", element, "\" was never there to begin with." ] ) )
            # If we should wait for it and it's not here... leave.
            return
        else:
            if not recur:
                driver.child.logMsg( ''.join( [ "Waiting for \"", element, "\"" ] ), INFO )
            time.sleep( thinkTime )

        kwargs['die'] = die
        kwargs['timeout'] = timeout

        while exists( driver, element, type, **kwargs ):
            if time.time( ) - start > timeout:
                driver.child.logMsg( ''.join( [ "Element did not disappear within ", str( timeout ), "s, timed out." ] ), 
                        CRITICAL, locals=locals( ) )
                if die:
                    driver.child.restart( "timed out" )
                    # Wait to be killed
                    time.sleep( 10 )

                break #this skips the else
            time.sleep( thinkTime )
        else:
            driver.child.logMsg( ''.join( [ "Element \"", element, "\" disappeared!" ] ), INFO )

            if stayGone > 0:
                w = stayGone + time.time( )
                while w - time.time( ) >= 0:
                    if exists( driver, element, type, **kwargs ):
                        driver.child.logMsg( "Element came back!" )
                        kwargs['offset'] = time.time( ) - start
                        kwargs['recur'] = True

                        waitToDisappear( driver, element, **kwargs )
                    time.sleep( thinkTime )



def isDisplayed( e ):
    """Does a check to see if the element is displayed while catching exceptions safely. Often when the script needs
       to see if an element is displayed, it isn't even on the page. This can kill the program.

       :param e: An active :py:class:`~selenium.webdriver.remote.webelement.WebElement` that will be checked if it is displayed.
       :return: Boolean where True if the element is displayed and False if it is not.
    """
    try:
        if e.is_displayed( ):
            return True
    except:
        return False

    return False



def isEnabled( e ):
    """Does a check to see if an element is enabled while capturing exceptions safely. Often when the script needs
       to see if an element is enabled, it isn't. This normally kills the script and is undesireable.

       :param e: An active :py:class:`~selenium.webdriver.remote.webelement.WebElement` that will be checked if 
         it is enabled (can type into / click).
       :return: Boolean where True if the element is enabled and False if it is not.
    """
    try:
        if e.is_enabled( ):
            return True
    except:
        return False
    return False



#   Should extract a variable from driver.current_url, then plop its value on to url and redirect.
#def urlExtractRedirect( driver, variable, value ):
#    url = driver.current_url
#
#    driver.child.logMsg( "urlExtractRedirect\nBEFORE: " + url )
#    
#    r = re.compile( r"(?P<start>[\?\&])%s=(?P<value>[^\&]+)$" % variable )
#
#    if not url.match( r ):
#        driver.logMsg( "WARNING: URL Doesn't appear to contain a variable in this manner: ?" + variable + "= or &" + variable + "=" )
#        return
#    
#    re.sub( r, "\g<start>" + variable + "=" + value, url )
#
#    driver.logMsg( "AFTER: " + url )
#    driver.get( url )
