import time
from selenium.common.exceptions import *

class ElementCache:
    """Creates an object to store WebDriver elements on specific pages so subsequent lookups do not require scanning the DOM. 

    A great deal of time on some pages is spent looking for elements which have already been found. If the page does not change,
    any previously used element link will be valid (barring changed CSS). ElementCache wraps a hash table which uses the URL with
    element name and type for a key to point to a :py:class:`~selenium.webdriver.remote.webelement.WebElement`. This is in turn used 
    for every call to :func:`~sw.utils.exists` before searching for the element (via :func:`get`), as the hash lookup is nearly free compared
    to a page search. 

    self.cache is, as mentioned above, a hash. The hash takes the following format::

        { 
            "<URL where elements are valid>" => {
                "<element identifying characteristic>_<identifying field>" => [ <expiration unix timestamp, if any>, <`WebElement` reference to loginbutton> ],
                [...]

            },
            [...]
        }
    
    A mock example::
    
        { 
            "http://website.com/pageiamon.html" => {
                "loginbutton_id" => [ 1416592420, <`WebElement` reference to loginbutton> ],
                "banner_name"    => [ None,       <`WebElement` reference to banner> ],
                [...]

            },
            [...]
        }
                
    
    self.cache is effectively a double hash that points to an array. Checks are performed on the element before returned, so an invalid or expired element
    should never be returned. At the end of every run the owning :py:class:`~sw.child.Child` object manually clears the ElementCache as, for almost all test cases,
    the elements will be long expired.

    :return: ElementCache (self)
    """
    def __init__( self ):
        self.cache = { }

    def add( self, url, e, **kwargs ):
        """Add an element to the cache (ElementCache.cache). It is stored by a handle and deleted automatically after a full run.

        :param url: The URL of element *e*.
        :param e: The :py:class:`~selenium.webdriver.remote.webelement.WebElement` to be stored.
        
        :Kwargs:
          * **id** (*None*): Identifier for *e* on the passed URL. 
          * **type** (*None*): Type of the identifier for *e* on the passed URL.
          * **handle** (*None*): (separate from *id*/*type*) A handle to identify this element by internally (unique). A handle is constructed from *id* and *type*
            if one is not provided. If one is provided, *id*/*type* are ignored since this is their only purpose.

        :return: None
        """
        id = kwargs.get( "id", None )
        type = kwargs.get( "type", None )
        handle = kwargs.get( "handle", None )

        if handle == None and ( id == None or type == None ):
            raise NameError( "Must name either a type and an id or a handle in kwargs. ") 

        if handle == None:
            handle = '_'.join( [ id, type ] )

        if not url in self.cache:
            self.cache[url] = { }

        self.cache[url][handle] = [ None, e ]

    def get( self, url, **kwargs ):
        """Gets an element from the internal cache stored on the given URL. If trying to use the element responds by throwing
        a :py:class:`~selenium.common.exceptions.NoSuchAttributeException` or by not throwing an exception, we return the element. If we get anything
        else we return None. Expiration is also checked here.

        :param url: The current URL to search the cache for.
        
        :Kwargs:
          * **id** (*None*): Identifier for the element in the cache, on the passed *URL*. Must be passed with *type*.
          * **type** (*None*): Type of the identifier for the element in the cache, on the passed *URL*. Must be passed with *id*.
          * **handle** (*None*): (separate from *id*/*type*) A handle to identify this element by internally (unique). A handle is constructed from *id* and *type*
            if one is not provided. If one is provided, *id*/*type* are ignored since this is their only purpose.

        :return: :py:class:`~selenium.webdriver.remote.webelement.WebElement` for the respective *URL*/*handle* if a matching element exists, otherwise None.
        """
        id = kwargs.get( "id", None )
        type = kwargs.get( "type", None )
        handle = kwargs.get( "handle", None )

        if handle == None and ( id == None or type == None ):
           raise NameError( "Must name either a type and an id or a handle in kwargs. ") 
         
        if handle == None:
            handle = '_'.join( [ id, type ] )

        if not url in self.cache or not handle in self.cache[url]:
            return None

        # Check for expiration here rather than in a think function. Child is going to clear us anyway,
        # and if the element is not called there is no point in wasting cycles worrying about unused
        # elements.
        data = self.cache[url][handle]
        if data[0] is not None and data[0] <= time.time( ):
            e = None
        else:
            e = data[1]

        # There is likely a better way of doing this, but this is a simple, single call to GhostDriver and is cheap.
        try:
            e.get_attribute( "class" )
        except NoSuchAttributeException:
            pass
        except:
            return None

        return e

    def clear( self ):
        """Clears the internal cache, deleting all cached elements. Not configurable as, if cache is enabled, it is called by 
        :py:func:`~sw.child.Child.think` after every job by this cache's child.
        
        :return: None
        """
        self.cache = { }
