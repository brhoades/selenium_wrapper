SUMMARY
==========================
selenium_wrapper is a project designed to make webdriver-based selenium more feasible for load testing a website. 
Using PhantomJS and GhostDriver, it can spawn off as many child processes running provided test suites as your 
processor can handle. These test suites are optimized for sites becoming slow and not responding, and wait for
elements to appear (unlike native webdriver). Unlike stock selenium, this wrapper also offers logging capabilities,
automatic screenshots, and launching arbitrary numbers of tests running simultaneously from one window.

STARTING
==========================
selenium_convert will launch after about 30 seconds (your results may vary). It has, compressed in the exe, 
a full install of python with all the conversion scripts for any webdriver-based selenium program given to it. 
When it starts, these are extracted into temporary memory so they can be used, which causes the lengthy delay.

USAGE
==========================
Browsing to a file will automatically choose a directory with the matching name to output to. If the file
is properly exported from selenium, it will be converted into a wrapped script. After selecting your input 
python file and your output folder, hit convert.

Conversion will take a while. It will initialize a new directory, copy a slimmed down python install into it,
and then convert the script into a form which utilizes the included selenium webdriver wrapper. Once finished,
it will prompt you to tell you so. Progress can be monitored in the black terminal that opened when the exe was
initially ran.
