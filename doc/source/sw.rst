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
