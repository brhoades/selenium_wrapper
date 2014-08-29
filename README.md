# Summary
selenium_wrapper is a project designed to make webdriver-based selenium more feasible for load testing a website. 
Using PhantomJS and GhostDriver, it can spawn off as many child processes running provided test suites as your 
processor can handle. These test suites are optimized for sites becoming slow and not responding, and wait for
elements to appear (unlike native webdriver). Unlike stock selenium, this wrapper also offers logging capabilities,
automatic screenshots, and launching arbitrary numbers of tests running simultaneously from one window.

[Full Documentation](http://brhoades.github.io/selenium_wrapper)
