from sw.pool import *
import sys, time


####################################################################################################
# main( func, file )
#   Just gets called from our selenium script and wraps around our mainloop / pool coordination.
#   Takes __file__ from our main file in to make a log folder in the proper location.
def main( func, file, **kwargs ):
    print( "\nLibraries loaded!\n\n" )
    numTimes = 1
    children = 3 
    images = False
    staggered = False

    if len( sys.argv ) > 1:
        numTimes = int( sys.argv[1] )
    if len( sys.argv ) > 2:
        children = int( sys.argv[2] )
    if len( sys.argv ) > 3:
        staggered = sys.argv[3]
        if staggered == "y":
            staggered = True
        else:  
            staggered = False
     
    print( "\n" + ( "=" * 40 ) )

    kwargs['staggered'] = staggered

    pool = ChildPool( children, numTimes, func, file, kwargs )

    mainLoop( pool )

    pool.reportStatistics( True )

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
