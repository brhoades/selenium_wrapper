from sw.pool import *
import sys, time


####################################################################################################
# main( func )
#   Just gets called from our selenium script and wraps around our mainloop / pool coordination.
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

    pool.reportStatistics( )

    pool.stop( )
####################################################################################################

####################################################################################################
# mainLoop( pool )
#   Takes the pool created previously and just loops around it. Currently it just thinks, but in the
#   future I may toss some more stuff out there.
def mainLoop( pool ):
    while not pool.done( ):
        pool.think( )
        time.sleep( 0.1 )
####################################################################################################
