================
Selenium Wrapper
================

Selenium Wrapper is a project designed to make 
`WebDriver <http://docs.seleniumhq.org/projects/webdriver/>`_-based 
`Selenium <http://docs.seleniumhq.org/>`_  more feasible for load testing. Using 
`PhantomJS <http://phantomjs.org/>`_ and `GhostDriver <https://github.com/detro/ghostdriver>`_, 
it can spawn off as many child processes running provided test suites as your processor can 
handle. These test suites are optimized for sites becoming slow and not responding, and 
wait for elements to appear with minimal CPU usage. Unlike 
stock Selenium, this wrapper also offers logging capabilities, automatic screenshots, and
launching arbitrary numbers of tests running simultaneously from one window. 

***************
Project Outline
***************

Selenium Wrapper is composed of two major tools. The first tool used and seen is 
the converter. The converter is used to take a `Selenium IDE <http://docs.seleniumhq.org/docs/02_selenium_ide.jsp>`_-exported Python
WebDriver script and convert it for usage with the wrapper, the second tool. The wrapper
is a framework making load testing possible with Selenium and is mostly transparent. The converter 
creates a folder which contains the wrapped script and can be transported between computers to be ran
without extra installs. 

