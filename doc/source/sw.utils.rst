================================
Utilities Module :mod:`sw.utils` 
================================

This module primarily serves as a holder for all directly webdriver-facing functions. These functions
usually serve only the purpose of interfacing with elements on the page and possibly logging when an 
error occurs. A lot of the code of these functions revolves around waiting.

.. _common-params:

*****************
Common Parameters
*****************
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
 
*********
Functions
*********

.. automodule:: sw.utils
   :members:
   :undoc-members:
   :show-inheritance:
