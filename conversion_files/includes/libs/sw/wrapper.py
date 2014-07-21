from selenium.webdriver import PhantomJS
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from sw.pool import ChildPool
import re, sys, time, os

def main( func ):
    print( "\nLibraries loaded!\n\n" )
    numTimes = 1
    children = 3 

    if len( sys.argv ) > 1:
        numTimes = int( sys.argv[1] )
    if len( sys.argv ) > 2:
        children = int( sys.argv[2] )
     
    print( "\n" + ( "=" * 40 ) )

    pool = ChildPool( numTimes, children, func )

    mainLoop( pool )

def mainLoop( pool ):
    while True:
        pool.think( )
