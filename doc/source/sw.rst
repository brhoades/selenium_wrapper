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

When initializing a brand new installation and not having a prepackaged converter, first checkout
the repository::

  git clone https://github.com/brhoades/selenium_wrapper.git

^^^^^^^^^^^^^^^
Converter Setup
^^^^^^^^^^^^^^^

Install `Ruby <https://www.ruby-lang.org/en/>`_ and then the appropriate
`ActiveTCL <http://www.activestate.com/activetcl/downloads>`_ library for your version.
After installing, navigate to the directory cloned into and run::

  bundle install

This will install the Ruby gems required for the converter to function.

^^^^^^^^^^^^^
Wrapper Setup
^^^^^^^^^^^^^

Prepare a python installation for the converter program. Python 2.7.8 is the supported 
Python version. Now `Install Python <https://www.python.org/download/releases/2.7.8/>`_ 
for the correct platform. 

Use `pip <https://pip.pypa.io/en/latest/installing.html>`_ to install the
`Selenium Library <https://pypi.python.org/pypi/selenium>`_ and `Splunklib <https://github.com/splunk/splunk-sdk-python>`_:: 

  pip install selenium splunklib

Also install the latest version of the `PhantomJS binary <http://phantomjs.org/download.html>`_ for your 
platform.

Currently a distributed setup where a separate install of Python is shipped with each script
is only possible for Windows. For other operating systems, there will need to be a system wide
installation on every machine participating. For these other operating systems ensure that the
"Python" option is unchecked on the converter.

"""""""""""""
Windows Setup
"""""""""""""

`Install Python`_ into the default folder. The fewer modules that are included, the better. 
Excluding ``lib-tk``, documentation, and testing suites will streamline things. 
This folder will later be copied to the correct spot.

Install `pip`_ into your Python installation. Afterwards, use pip to install the `Selenium Library`_ 
and `Splunklib <https://github.com/splunk/splunk-sdk-python>`_::

  pip install selenium splunklib

Now install the `curses extension package <http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses>`_.

Finally copy/move the Python folder that was just created to ``conversion_utils/python27``. 
Extract the ``phantomjs-release.zip`` for Windows and put the binary within the ``python27`` folder as well.

To run the conversion program::

  ruby main.rb

^^^^^^^^^^^^^^^^^^^^^^
Converter Distribution
^^^^^^^^^^^^^^^^^^^^^^

To ease other's usage of the converter, consider packaging it into an exe using 
`OCRA <https://github.com/larsch/ocra>`_. `ORCA`_ will convert the ruby file into a preinterpreted format
which does not require a ruby installation to run. The following will install the gem and run the compiler::

  gem install ocra
  ocra_compile.bat

================
Script Converter
================

Conversion will take a while in Windows. It will initialize a new directory, copy a slimmed down Python 
install into it, and then convert the script into a form which utilizes the included Selenium 
wrapper. Once finished, it will prompt you to tell you so. Progress can be monitored in the 
black terminal that opened when the exe/script was initially ran.

Assertions or known useless code will be automatically stripped from the script provided. 
Assertions are not currently supported as the wrapper does not currently wrap itself in a 
unit testing suite. Most functions used in the script will be replaced with in house functions,
such as ``driver.find_element_by(...).send_keys( "text" )`` which is wrapped 
into a :py:func:`sw.utils.sendKeys` function. This eliminates the need for a .clear( ) 
statement and saves time. Conversion also replaces any ``find_element_by_`` segments with 
:py:func:`sw.utils.sleepwait` which is a controlled (and CPU-optimized) function to wait for an 
element.


***********
Usage - GUI
***********

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

***********
Usage - CLI
***********

Running ``main.rb`` with ``--help`` returns command line usage information::

  Usage: main.rb [options] script.py
      -m, --[no-]images                Exported script should load images.
      -o, --[no-]overwrite             Overwrite any conflicting files on output.
      -c, --[no-]recopy                Recopy missing or different files.
      -p, --[no-]python                Include python in installation (Windows onl
  y).
      -i, --script [SCRIPT]            Script to convert, UI isn't launched if thi
  s is specified
      -h, --help                       Show this message.

Typical usage will always include the options ``-poi`` followed by a script. For example::
  ruby main.rb -poi in/test_script.py

This will package Python into the folder ``out/test_script/`` and drop the converted script in there as well.

**********
Directives
**********

There are directives which may be inserted into the source script's function which will be 
parsed by the converter into wrapper functions. Variables can be used in their arguments 
as the converter turns the directives into functions after conversion.

Available Directives:
  - ``#log message``

    - This will write to our child's log "message". Directly calls :py:func:`sw.child.logMsg`
  - ``#msg message``

    - Writes "Child #: message" to the console. Calls :py:func:`sw.child.msg`
  - ``#wait element kwargs``

    - This calls :py:func:`sw.utils.waitToDisappear` and takes any of the kwargs as the second argument. 
      Please reference that function for further details about its arguments and other options.
    - ``#wait overlay type=id``

      - Waits for the element with id=overlay to disappear
    - ``#wait overlay type=name, stayGone=3``

      - Waits for the element with name=overlay to disappear and waits an additional 3 seconds 
        for it to not come back.
    - ``#wait blurydiv timeout=5``

      - Waits for id=blurydiv to disappear. If it doesn't after 5 seconds, returns.
    - ``#wait blurydiv waitTimeout=5``

      - Waits for id=blurydiv to disappear. Gives the element 5 seconds to appear first before 
        waiting for it to disappear. Default time to appear is 1 second.
  - ``#error message``

    - Throws an error, which takes a screenshot, logs the screenshot name, and logs "message" 
      to the log. Calls :py:func:`sw.child.logMsg` with level=CRITICAL level.
  - ``#screenshot``

    - Takes a screenshot which appears as error_#.png within the child's log directory. The log 
      references the file name when this is called. Calls :py:func:`sw.child.screenshot`

.. _options-directives:

******************
Options Directives
******************

By including at the top of your script ``#OPTIONS`` with a following comment block, the converter will parse options into the output script. These options will appear in the defaults for initial settings.::

  #OPTIONS
  #p option="text"
  #import module

Available options:
  - Ghostdriver

    - ``#p proxy="string"``
      - Specifies a custom proxy server for Ghostdriver to route all PhantomJS traffic through. Default: ""
    - ``#p proxy-type="type"``
      - Specify the type of proxy. Possible options are socks5 and http. Default: ""
    - ``#p images=True/False``
      - Case sensitive for True or False. Specifies whether Ghostdriver loads images. Default: False
    - ``#p browsercache=True/False``
      - Case sensitive for True or False. Specifies whether to cache web content such as images on the disk (rather than in the RAM for a short period of time). Default: True
    - ``#p ignoresslerrors="yes"/"no"``
      - Specifies whether to ignore errors about an invalid or expired SSL certificate. Default: "yes"
    - ``#p ghostdriverlog="filename"``
      - Specifies the name of the log file for ghostdriver. Default: "ghostdriver.log"

  - Splunk Connection

    - ``#p report="server FQDN or IP"``
      - This parameter toggles reporting. If this parameter is left to the default (blank) reporting will not happen. Default: None
    - ``#p report_port=8089``
      - The port to connect to the reporting Splunk server at. Default: 8089
    - ``#p report_user="username""``
      - The username to authenticate with with Splunk, must be an admin or have permission to run remote commands. Default: None
    - ``#p report_pass="password"``
      - The password for the username used to connect to Splunk. Default: None
    - ``#p report_index="testing"``
      - The index to insert all data into within Splunk. Default: None

  - Reporting Details

    - ``#p id="auto"``
      - Machine name used to report to the reporting server. If left at the default, it's generated in the format ``user@hostname``. Default: "auto"
    - ``#p project="Project Name"``
      - Project name, usually used in reporting to group together a bunch of common runs. Default: None
    - ``#p run="Run Name"``
      - Run name to send to the reporting server. This is another defining characteristic that is used in conjunction with script name to specify parts of a larger project. Default: None
    - ``#p script="Script Name"``
      - Script name which is used in reporting to distinguish different runs in a project.

  - Selenium Configuration

    - ``#p cache=True/False``
      - Case sensitive for True or False. Specify whether found elements in PhantomJS should be cached. In pages with a great deal of AJAX this is recommended to save CPU resources searching for elements. There has not been any noticeable drawback to this option in testing. Default: True
    - ``#p childsleeptime=#``
      - Amount of time in seconds waited inbetween searches for an element on a page. Low numbers increase CPU usage. Default: 1 
    - ``#p lightconfirm=True/False``
      - Case sensitive for True or False. If True, when checking if an element exists there will be no check for visibility or clickibility. This is practical for individual function usage in a script, globally False is the most acceptable option. Default: False

  - General

    - ``#p level=-1-9``
      - Logging level, where -1 is all errors including debugging, 0 is all errors, and 1 is notices. A full list of options can be found in const.py in the selenium module directory. Default: 1 
    - ``#p logformat="DATESTR"``
      - Custom folder names for the log folder. Default: "%Y-%m-%d_%H-%M-%S"
    - ``#p jobs=#``
      - Custom number of jobs to run initially. Default: 1
    - ``#p children=#``
      - Custom number of children to have initially. Default: 1
    - ``#p stagger=True/False``
      - Case sensitive for True/False. Determines if children spawnining will be staggered over time. Default: False
    - ``#p staggertime=#``
      - How far apart to stagger child launching in seconds. Default: 5
    - ``#p initsettings=True/False``
      - Case sensitive for True/False. If False, the initial settings wizard will be skipped. Error checking on provided parameters is skipped. Default: True
    - ``#import module``
      - Includes this import in the output (wrapped) script. This is useful for including, for example, random to randomly choose a user from a table.
  


=======
Wrapper
=======

The wrapper can be launched by using ``run.bat`` in Windows or ``python run_test.py`` in Unix-like systems. 
Everything is automatically prepared, so upon launch the first screen is the initial settings wizard.

****************
Initial Settings
****************

.. image:: images/initialsettings.png

The initial settings wizard allows configuration and validation of settings before running. Each option has a respective
options directive seen in :ref:`options-directives` including the option to disable the initial settings wizard entirely. 

^^^^^^^^^^^^
Run Settings
^^^^^^^^^^^^

.. code-block:: none

   a) # Children:     1
   b) Stagger Spawn:  False
   c) # Jobs:         1

**# Children**
determines the number of concurrent `PhantomJS`_ processes the script will run.
Although the default number is 1, users with a more powerful processor will find themselves capable 
of running over 20, though this varies wildly with the script ran. Scripts with a great deal of waiting on page elements
can run with more concurrent instances than those which are actively clicking or navigating.

**Stagger Spawn**
, which is short for staggered child spawning, is intended to distribute load throughout a site more evenly. 
Without staggering and with a high number of children, the load will be very pinpointed at an exact point
of the site consistently, at least at the beginning. This options spawns children 5 seconds apart by default but can be configured
using :ref:`staggertime <options-directives>`.

**# Jobs**
determines the number of times the recorded script will run. Every child process 
will pull from a job queue (of this length) when it starts and will do so until the queue is empty 


^^^^^^^^^^^^^
Pool Settings
^^^^^^^^^^^^^

.. code-block:: none

   Pool Settings
   d) Log Lvl (0-5):  -1
   e) Get Images:     False

**Log Level (0-5)**
See `Logging`_

**Get Images**
Determines whether `PhantomJS`_ will bother to download images. If during recording an image was clicked on, it must either have 
an alt tag for this option to be false.

^^^^^^^^^^^^^^^^^^
Reporting Settings
^^^^^^^^^^^^^^^^^^

.. code-block:: none

  Reporting Settings
  f) Server:         None
  g) Port:           8089
  h) User:           None
  i) Password:       None
  j) Index:          None
  k) Project Name:   None
  l) Run Name:       None
  m) Script Name:    None
  n) Client Name:    auto


**Server, Port, User, Password, Index**
These options are all Splunk installation specific. Splunk must allow remote connections from the client's host on a port, default is 8089
via the `REST API <http://docs.splunk.com/Documentation/Splunk/latest/RESTAPI/RESTcontents>`. Details about the Splunklib module and how it is used
can be found in `~sw.reporting` and official documentation `on Splunk's website <http://docs.splunk.com/DocumentationStatic/PythonSDK/1.1/client.html>`.

**Project Name**
is a layer of abstraction on individual recorded runs with various scripts. It is considered to be the highest level of abstraction to group together these runs, spanning over
days or months. A project would ideally contain a multitude of runs. There are checks done to make sure Project Name is used and valid.

**Run Name**
is a layer of abstraction on individual scripts ran within a period of time, usually expected to be less than a day. Runs may contain one or more scripts to do various load testing.
Run names are checked for valid characters as well.

**Script Name**
is the final layer of abstraction on an individual execution of a script. A script may be unique or may not within a run.

**Client Name**
is usually left on auto. When autogenerated it takes the format ``user@computername``.

*******
Logging
*******

Logging is automatically performed and there is currently not an option to turn it off. All logs
are within a timestamped folder in ``logs/``. Each child then create its own log in in that subfolder with the format
``logs/<timestamp>/log-#.log``, where the number is the child's number printed to the console. This 
log will contain detailed information about errors, time taken, and the status of the script.

Logging levels can be configured with the :ref:`level <options-directives>` directive or within the initial settings wizard. 
Possible levels are as follows: 

There are several levels as seen in ``conversion_files/includes/libs/sw/const.py``:

.. literalinclude:: sw/const.py
   :lines: 38-49 
   :language: python

With the lowest log level, ``INFO``, this is an example of a log that is prepared:

.. code-block:: none

  [15:37:14] (NOTICE)   Child process started and loaded
  [15:37:20] (NOTICE)   Beginning wait for element "accounts" of type "link_text".
  [15:37:35] (NOTICE)   Beginning wait for element "OrderPage_Row_6" of type "name".
  [15:37:42] (NOTICE)   Beginning wait for element "clear_overlay" of type "id".
  [15:37:46] (NOTICE)   In waitToDisappear "clear_overlay" was never there to begin with.
  [15:37:46] (INFO)     Waiting for "clear_overlay"
  [15:37:49] (INFO)     Element "clear_overlay" disappeared!
  [15:37:50] (NOTICE)   Beginning wait for element "clear_overlay" of type "id".
  [15:37:54] (NOTICE)   In waitToDisappear "clear_overlay" was never there to begin with.
  [15:37:57] (NOTICE)   Beginning wait for element "AmountPage_Row_27" of type "name".
  [15:38:02] (INFO)     Waiting for "clear_overlay"
  [15:38:04] (INFO)     Element "clear_overlay" disappeared!
  [15:38:05] (NOTICE)   Beginning wait for element "clear_overlay" of type "id".
  [15:38:08] (NOTICE)   In waitToDisappear "clear_overlay" was never there to begin with.
  [15:38:08] (INFO)     Waiting for "clear_overlay"
  [15:38:10] (INFO)     Element "clear_overlay" disappeared!
  [15:38:10] (INFO)     Waiting for "clear_overlay"
  [15:38:13] (INFO)     Element "clear_overlay" disappeared!
  [15:38:13] (NOTICE)   Beginning wait for element "clear_overlay" of type "id".
  [15:38:16] (NOTICE)   In waitToDisappear "clear_overlay" was never there to begin with.
  [15:38:17] (INFO)     Waiting for "clear_overlay"
  [15:38:19] (INFO)     Element "clear_overlay" disappeared!
  [15:38:19] (INFO)     Waiting for "clear_overlay"
  [15:38:21] (INFO)     Element "clear_overlay" disappeared!
  [15:38:22] (NOTICE)   Beginning wait for element "clear_overlay" of type "id".
  [15:38:25] (NOTICE)   In waitToDisappear "clear_overlay" was never there to begin with.
  [15:38:25] (INFO)     Waiting for "clear_overlay"
  [15:38:27] (INFO)     Element "clear_overlay" disappeared!
  ===================== <More Waiting>
  [15:39:18] (INFO)     Waiting for "clear_overlay"
  [15:39:25] (INFO)     Element "clear_overlay" disappeared!
  [15:39:36] (NOTICE)   Successfully finished job (141.878000021s)
  [15:39:36] (NOTICE)   Stopping child process: "DONE"

On the lowest log level, the wrapper gives a great deal of information about where it is waiting
for debugging purposes. Waits are only documented if they are engaged; if an element can already
be selected, no time is wasted waiting and the script directly interacts with it. The timestamp 
on the far left is the exact time in which the message was printed, the next field is the log level
that this was printed at--- if ``child.level`` were greater than this, it wouldn't print. The final
field is the message itself.

Also placed within the log directory are any screenshots that were taken either as a directive 
within the script or for an error. Any time a screenshot is created, it is noted in the respective
child's log file where it was stored and at what time. For example, here is a log where an error was
encountered:

.. code-block:: none 
  :emphasize-lines: 6 
  
  [14:15:48] (NOTICE)   Child process started and loaded
  [14:15:52] (NOTICE)   Beginning wait for element "Accounts" of type "link_text".
  [14:15:57] (NOTICE)   Choosing grower #16
  [15:37:57] (NOTICE)   Beginning wait for element "AmountPage_Row_27" of type "name".
  [14:16:07] (ERROR)    'sleepwait() takes exactly 3 arguments (4 given)'
  [14:16:08] (ERROR)    Wrote screenshot to: /home/test/script_converter/out/test_script/logs/2014-08-26_14-15-45/error_0.png
  [14:16:08] (ERROR)    Stack trace: Traceback (most recent call last):
    File "/home/test/script_converter/out/test_script/includes/libs/sw/child.py", line 144, in think
      func( self.driver )
    File "/home/test/script_converter/out/test_script/run_test.py", line 30, in test_func
      waitToDisappear( driver, 'AmountPage_Row_27' )
    File "/home/test/script_converter/out/test_script/includes/libs/sw/utils.py", line 212, in waitToDisappear
      sleepwait( driver, element, type, kwargs )
    TypeError: sleepwait() takes exactly 3 arguments (4 given)
  [14:16:08] (NOTICE)   Stopping child process: "RESTARTING"  

The highlighted line shows where the screenshot was written to, ``error_#.png``. Every new error increments this number.
 
