#Summary
selenium_wrapper is a project designed to make webdriver-based selenium more feasible for load testing a website. 
Using PhantomJS and GhostDriver, it can spawn off as many child processes running provided test suites as your 
processor can handle. These test suites are optimized for sites becoming slow and not responding, and wait for
elements to appear (unlike native webdriver). Unlike stock selenium, this wrapper also offers logging capabilities,
automatic screenshots, and launching arbitrary numbers of tests running simultaneously from one window.

#Overview
selenium_wrapper is composed of two very related components. The first component used is the converter. The converter is designed to take a Selenium IDE-exported webdriver script and convert it into a new script which uses the second part, the wrapper. The wrapper's main idea is that described above: to make it plausible to load test with selenium. The converter creates a folder which contains the wrapped script and can be transported between any number of computers.

#Install
If coming from a fresh repo with no prepackaged executeable:

> git clone https://github.com/brhoades/selenium_wrapper.git

### Converter Setup

Install [ActiveTCL](http://www.activestate.com/activetcl/downloads). After installing you may navigate to the directory you cloned into and run:

> bundle install


### Wrapper Setup
Prepare a python installation for the converter program. Python 2.7.7 is the supported Python version. Create a folder named `python277` in `conversion_files/`. Now [install Python](https://www.python.org/download/releases/2.7.8/) for your platform. 

On Windows, perform an [administrative installation](http://technet.microsoft.com/en-us/library/cc759262\(v=ws.10\).aspx) of Python. Target the folder created above and finish your installation.

Use pip to install selenium for Python into your local directory. You can alternatively, manually download and install [the module](https://pypi.python.org/pypi/selenium).

> pip install selenium

Also install the latest version of [PhantomJS](http://phantomjs.org/download.html) and put it (in its folder) in the previously created python277 folder. The folder name may need to be update in `conversion_files/run.bat` if it is not 1.9.7.

Now you may run the conversion program. 

> ruby main.rb

### Converter Distribution


selenium_convert will launch after about 30 seconds (your results may vary). It has, compressed in the exe, 
a full install of python with all the conversion scripts for any webdriver-based selenium program given to it. 
When it starts, these are extracted into temporary memory so they can be used, which causes the lengthy delay.

#Usage
Browsing to a file will automatically choose a directory with the matching name to output to. If the file
is properly exported from selenium, it will be converted into a wrapped script. After selecting your input 
python file and your output folder, hit convert.

Conversion will take a while. It will initialize a new directory, copy a slimmed down python install into it,
and then convert the script into a form which utilizes the included selenium webdriver wrapper. Once finished,
it will prompt you to tell you so. Progress can be monitored in the black terminal that opened when the exe was
initially ran.
