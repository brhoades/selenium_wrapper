
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
`OCRA <https://github.com/larsch/ocra>`_. `OCRA`_ will convert the ruby file into a preinterpreted format
which does not require a ruby installation to run. The following will install the gem and run the compiler::

  gem install ocra
  ocra_compile.bat
