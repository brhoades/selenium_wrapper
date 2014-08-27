================
Selenium Wrapper
================

Selenium Wrapper is a project designed to make 
`WebDriver <http://docs.seleniumhq.org/projects/webdriver/>`_-based 
`Selenium <http://docs.seleniumhq.org/>`_  more feasible for load testing. Using 
`PhantomJS <http://phantomjs.org/>`_ and `GhostDriver <https://github.com/detro/ghostdriver>`_, 
it can spawn off as many child processes running provided test suites as your processor can 
handle. These test suites are optimized for sites becoming slow and not responding, and 
wait for elements to appear with minimal CPU usage (unlike native WebDriver). Unlike 
stock Selenium, this wrapper also offers logging capabilities, automatic screenshots, and
launching arbitrary numbers of tests running simultaneously from one window. 

***************
Project Outline
***************

Selenium Wrapper is composed of two related components. The first component used and seen is 
the converter. The converter is used to take a 
`Selenium IDE <http://docs.seleniumhq.org/docs/02_selenium_ide.jsp>`_-exported Python
WebDriver script and convert it for usage with the wrapper, the second component. The wrapper
is as described above, a framework making load testing possible with Selenium. The converter 
creates a folder which contains the wrapped script and can be transported between any number of 
computers. 

************
Installation
************

If initializing a brand new installation and not having a prepackaged converter, first checkout
the repository::

  git clone https://github.com/brhoades/selenium_wrapper.git

^^^^^^^^^^^^^^^
Converter Setup
^^^^^^^^^^^^^^^

Install `ActiveTCL <http://www.activestate.com/activetcl/downloads>`_. After installing, 
navigate to the directory cloned into and run::

  bundle install

^^^^^^^^^^^^^
Wrapper Setup
^^^^^^^^^^^^^

Prepare a python installation for the converter program. Python 2.7.7 is the supported 
Python version. Create a folder named ``python277`` in ``conversion_files/``. Now
`install Python <https://www.python.org/download/releases/2.7.7/>`_ for the correct platform. 

On Windows, perform an 
`administrative installation <http://technet.microsoft.com/en-us/library/cc759262(v=ws.10).aspx>`_ 
of Python. Target the folder created above and finish the installation.

Use pip to install `Selenium <https://pypi.python.org/pypi/selenium>`_ for Python into the local 
directory. Alternatively, manually download and install 
`the module <https://pypi.python.org/pypi/selenium>`_ locally into the Python libraries::

  pip install selenium

Also install the latest version of `PhantomJS <http://phantomjs.org/download.html>`_ and put it 
(in its folder) in the previously created ``python277/`` folder. The folder name may need to 
be update in ``conversion_files/run.bat`` if it is not 1.9.7.

Now run the conversion program::

  ruby main.rb

^^^^^^^^^^^^^^^^^^^^^^
Converter Distribution
^^^^^^^^^^^^^^^^^^^^^^

To ease other's usage of the converter, consider packaging it into an exe using 
`OCRA <https://github.com/larsch/ocra>`_. The following will install the gem and run the compiler::
  gem install ocra
  ocra_compile.bat

This will automatically generate a portable version of the converter in an exe.

================
Script Converter
================

*****
Usage
*****

The converter ``main.rb`` or ``selenium_convert.exe`` will launch after about 15 seconds 
(results may vary). This converter has the files necessary to create a portable Python 
installation with Selenium and PhantomJS. 

.. image:: images/converter_main.png

Browsing to a file will automatically choose a directory with the matching name to output to in 
``out/``. If the file is properly exported from selenium, it will be converted into a wrapped 
script. There are several options which will augment the way the wrapper runs. 

- Images (*off*) will enable loading images in the headless browser.
- Python (*on*) will copy the included python installation to the output directory.
- Overwrite (*off*) will overwrite the output directory without prompting.

After selecting your input Python file and (optionally) your output folder, hit convert.

Conversion will take a while. It will initialize a new directory, copy a slimmed down Python 
install into it, and then convert the script into a form which utilizes the included Selenium 
wrapper. Once finished, it will prompt you to tell you so. Progress can be monitored in the 
black terminal that opened when the exe/script was initially ran.

Conversion will automatically strip any assertions or clears from the script provided. 
Assertions are not currently supported as the wrapper does not currently wrap itself in a 
unit testing suite. Any ``driver.find_element_by(...).send_keys( "text" )`` is wrapped 
into a :py:meth:`sw.utils.sendKeys` function. This eliminates the need for a .clear( ) 
statement and saves time. Conversion also replaces any ``find_element_by_`` segments with 
:py:meth:`sw.utils.sleepwait` which is a controlled (and CPU-optimized) function to wait for an 
element.

**********
Directives
**********

There are directives which may be inserted into the source script's function which will be 
parsed by the converter into wrapper functions. Variables can be used in their arguments 
as the converter turns the directives into functions after conversion.


- ``#log message``
  - This will write to our child's log "message". Directly calls :py:meth:`sw.child.logMsg`
- ``#msg message``
  - Writes "Child #: message" to the console. Calls :py:meth:`sw.child.msg`
- ``#wait element kwargs``
  - This calls :py:meth:`sw.utils.waitToDisappear` and takes any of the kwargs as the second argument. Please reference that function for further details about its arguments and other options.
  - ``#wait overlay type=id``
    - Waits for the element with id=overlay to disappear
  - ``#wait overlay type=name, stayGone=3``
    - Waits for the element with name=overlay to disappear and waits an additional 3 seconds for it to not come back.
  - ``#wait blurydiv timeout=5``
    - Waits for id=blurydiv to disappear. If it doesn't after 5 seconds, returns.
  - ``#wait blurydiv waitTimeout=5``
    - Waits for id=blurydiv to disappear. Gives the element 5 seconds to appear first before waiting for it to disappear. Default time to appear is 1 second.
- ``#error message``
  - Throws an error, which takes a screenshot, logs the screenshot name, and logs "message" to the log. Calls :py:meth:`sw.child.logMsg` with level=CRITICAL level.
- ``#screenshot``
  - Takes a screenshot which appears as error_#.png within the child's log directory. The log references the file name when this is called. Calls :py:meth:`sw.child.screenshot`

******************
Options Directives
******************
By including at the top of your script ``#OPTIONS`` with a following comment block, the converter will parse options into the output script::

  #OPTIONS
  #gd option="text"
  #import module

Available options:
 - ``#gd option="text"``
  - Passes the string ``option="text"`` directly to GhostDriver's desired capabilities. Currently only the following are supported:
   - ``#gd proxy="google.com:443"``
   - ``#gd proxy-type="http"``
 - ``#import module``
   - Includes this import in the output (wrapped) script. This is useful for including, for example, random to randomly choose a user from a table.

