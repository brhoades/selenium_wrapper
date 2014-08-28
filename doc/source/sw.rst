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

This will install the Ruby gems required for the converter to function.

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
(in its folder) in the previously created ``conversion_files/python277`` folder. The folder
path may need to be updated in ``conversion_files/run.bat`` if it is not 1.9.7.

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
into a :py:func:`sw.utils.sendKeys` function. This eliminates the need for a .clear( ) 
statement and saves time. Conversion also replaces any ``find_element_by_`` segments with 
:py:func:`sw.utils.sleepwait` which is a controlled (and CPU-optimized) function to wait for an 
element.

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

=======
Wrapper
=======
The wrapper is automatically applied to the source script when the converter finishes. It is
intended to be as transparent as possible after conversion, requiring minimal user interaction
to get it running. Below is a real test run of a script::

  .../out/example_script>run.bat
  You may press enter to use the default values in parenthesis.
  Number of Children (3): 3
  Number of Jobs to Run (3): 3
  Stagger Children Spawning (n): n

  Libraries loaded!



  ========================================
  Preparing 3 children to do 3 jobs.
  Child #1: LOADING
  Child #2: LOADING
  Child #3: LOADING
  Child #3: STARTING
  Child #2: STARTING
  Child #1: STARTING

  ========================================
  Successful: 0   Failed: 0
  Total: 0   Remaining: 3
  Children (peak): 3   Children (active): 3
  No data to extrapolate or average from
  ========================================

  Child #2: DONE (141.88s)
  Child #2: STOPPING (DONE)
  Child #3: DONE (142.62s)
  Child #3: STOPPING (DONE)
  Child #1: DONE (149.2s)
  Child #1: STOPPING

  ========================================
  Successful: 3   Failed: 0
  Total: 3   Remaining: 0
  Children (peak): 3   Children (active): 0
  Failure Rate: 0.0%
  Average / Estimates:
    Time per job: 144.57s
    Jobs/s: 0.02   Jobs/m: 1.21   Jobs/hr: 72.35   Jobs/day: 1736.39
  ========================================

  Press any key to continue . . .

Running ``run.bat`` on Windows will present the user with questions for how the script will operate. 
It simply passes arguments on to ``run_test.py``, with the order discussed below.

.. code-block::
  Number of Children (3): 3

The number of children determines the number of concurrent `PhantomJS` processes the script will run.
Although the default number is 3, users with a more powerful processor will find themselves capable 
of running over 20, though this varies wildly with the script ran. This is largely dependent on processing
power but about 50-70 Mb of RAM is used as well.

.. code-block::
  Number of Jobs to Run (3): 3

The jobs option determines the number of times the recorded script will run. Every child process 
will pull from a job queue (of this length) when it starts and will do so until the queue is empty 

.. code-block::
  Stagger Children Spawning (n): n

The last option, staggered child spawning, is intended to distribute load throughout a site more evenly. 
Without staggering and with a high number of children, the load will be very pinpointed at an exact point
of the site consistently, at least at the beginning. This options spawns children 5 seconds apart.

The options used in the example are equivalent to just running this::

  python out/example_script.py

It pulls the default options internally for the script.

Standard argument order and format is like so::

  python out/example_script.py <number of jobs> <number of children> <staggered (y/n)>
