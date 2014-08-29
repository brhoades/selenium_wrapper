import time, sys
from selenium.common.exceptions import *

class ElementCache:
    """Creates an object to store WebDriver elements on specific pages so subsequent lookups don't require scanning the DOM.

    :return: ElementCache (self)
    """
    def __init__( self ):
        self.cache = { }

    def add( self, url, e, **kwargs ):
        """Add an element to the cache. It is stored by a handle and deleted automatically after a full run.

        :param url: The URL of element e.
        :param e: The `Webelement` to be stored.
        
        :Kwargs:
          * **id** (*None*): Identifier for e on the passed url. 
          * **type** (*None*): Type of the identifier for e on the passed url.
          * **handle** (*None*): (separate from id/type) A handle to identify this element by internally (unique).

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
        """Gets an element from the internal cache stored on the given url. If it doesn't exist, returns None.

        :param url: The current url to search the cache for.
        
        :Kwargs:
          * **id** (*None*): Identifier for the element in the cache, on the passed url. 
          * **type** (*None*): Type of the identifier for the element in the cache, on the passed url.
          * **handle** (*None*): (separate from id/type) A handle to identify this element by internally (unique).

        :return: :py:class:`~selenium.webdriver.remote.webelement.WebElement` for the cached item if a matching element exists. None if not.
        """
        id = kwargs.get( "id", None )
        type = kwargs.get( "type", None )
        handle = kwargs.get( "handle", None )

        if handle == None and ( id == None or type == None ):
           raise NameError( "Must name either a type and an id or a handle in kwargs. ") 
         
        if handle == None:
            handle = '_'.join( [ id, type ] )

        if not url in self.cache:
            return None

        if not handle in self.cache[url]:
            return None

        e = self.cache[url][handle][1]
        try:
            e.get_attribute( "class" )
        except NoSuchAttributeException:
            pass
        except:
            return None

        return e

    def clear( self ):
        """Clears the internal cache, deleting all cached elements. Typically called after every run of our test function.
        
        :return: None
        """
        self.cache = { }
