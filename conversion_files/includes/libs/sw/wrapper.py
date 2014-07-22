from sw.pool import *
import sys, time

def main( func ):
    print( "\nLibraries loaded!\n\n" )
    numTimes = 1
    children = 3 

    if len( sys.argv ) > 1:
        numTimes = int( sys.argv[1] )
    if len( sys.argv ) > 2:
        children = int( sys.argv[2] )
     
    print( "\n" + ( "=" * 40 ) )

    pool = ChildPool( children, numTimes, func )

    mainLoop( pool )

def mainLoop( pool ):
    while not pool.done( ):
        pool.think( )
        time.sleep( 0.1 )
    
    pool.stop( )
