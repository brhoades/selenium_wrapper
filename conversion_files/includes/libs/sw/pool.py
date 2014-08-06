from multiprocessing import Process, Queue
from sw.child import Child
import time, os
import datetime
from sw.const import * # Constants
from sw.formatting import * 



class ChildPool:
    ################################################################################################
    # __init__( self, numChildren, numJobs, func )
    # Initializes our Pool
    #   Takes in number of desired children, number of jobs to queue up, and the function to run 
    #   numJobs times. After storing, it initializes numChildren children which then start themselves. 
    #   Also grabs our main file location to make a log folder in an appropriate location.
    def __init__( self, numChildren, numJobs, func, file, kwargs ):
        # Our children
        self.children = [ None for x in range(numChildren) ]
        
        # Statistics and data per child
        self.data = [ [ 0, 0, [ ], 0, [ ] ] for x in range(numChildren) ]

        # Our one way queue from our children
        self.childQueue = Queue( )

        # Our work for children
        self.workQueue = Queue( )

        # Populate our work queue
        for x in range(numJobs):
            self.workQueue.put( func )

        # Number of times each child runs, stored on the child statistics list
        #   as a countdown later
        self.numJobs = numJobs

        # Number of children to start
        self.numChildren = numChildren

        # Our function
        self.func = func

        # Time between statistics reporting
        self.timePerReport = 60 

        # Don't report statistics for another minute
        self.nextStat = time.clock( ) + int( self.timePerReport*1.1 )

        # Our timestamp
        self.timestamp = datetime.datetime.now( ).strftime( "%Y-%m-%d_%H-%M-%S" )

        # Do we get images?
        self.options = kwargs

        # General log directory, shared by all children
        self.log = os.path.dirname( os.path.abspath( file ) ) + "\\logs\\" + self.timestamp + "\\"

        print( "Preparing " + str( numChildren ) + " " + ( "child" if numChildren == 1 else "children" ) 
               + " to do " + str( numJobs ) + " job" + ( "s" if numJobs != 1 else "" ) + "." )
        for i in range( numChildren ):
            self.newChild( )

        # Mark our start time
        self.started = time.time( )
    ################################################################################################



    ################################################################################################
    # newChild( self, i=None )
    # Makes a New Child
    #   Creates a new child which starts itself. If i is none, it grabs the next available array
    #   index, assuming it was initialized for this many children.
    def newChild( self, i=None ):
        # Create our data's home
        if i == None:
            for i,c in enumerate( self.children ):
                if c == None:
                    break # This gets us our first empty i
        
        self.children[i] = Child( self.childQueue, self.workQueue, i, self.log, self.options )
    ################################################################################################



    ################################################################################################
    # reportStatistics( self )
    # Reports Statistics
    #   Translates statistics into the archaic form used by my old stats function in utils.py.
    #   Map and reduce are used to get things quickly out of the self.data 2-d array. This function
    #   is only called every self.timePerReport seconds as set in this class's initialization func.
    def reportStatistics( self, force=False ):
        # Check if it's time yet
        if force or ( time.clock( ) >= self.nextStat and len( self.data[0] ) > 0 ):
            self.nextStat = time.clock( ) + self.timePerReport
            
            # Reduces our good/bad results into a single "this many succeeded, this many failed" number.
            # Maps our times into a single list.
            good = reduce( lambda x, y: x + y, map( lambda x: x[SUCCESSES], self.data ) )
            bad  = reduce( lambda x, y: x + y, map( lambda x: x[FAILURES], self.data ) )
            timetaken = map( lambda x: x[TIMES], self.data )
            timetaken = [ item for sublist in timetaken for item in sublist ] # Flatten

            waiting = map( lambda x: x[WAIT_TIMES], self.data )
            waiting = [ item for sublist in waiting for item in sublist ] # Flatten
            
            stats( good, bad, timetaken, self.children, self.numJobs, self.started, waiting ) 
    ################################################################################################



    ################################################################################################
    # think( self )
    # Pool's Think Function
    #   Runs through a single think loop; called as many times as our main loop pleases.
    #   Check children are alive/restart if there are more jobs. Checks queues and parses any data.
    def think( self ): 
        # Check our queues
        while not self.childQueue.empty( ):
            r = self.childQueue.get( False )
            i = r[NUMBER]

            if r[RESULT] == DONE:
                self.data[i][SUCCESSES] += 1
                self.data[i][TIMES].append( r[TIMES] )
                self.data[i][WAIT_TIMES].append( self.data[i][WAIT_TIME] )
                self.data[i][WAIT_TIME] = 0 
                self.children[i].msg( "DONE (" + str( format( r[TIME] ) ) + "s)" )

            elif r[RESULT] == FAILED:
                self.data[i][FAILURES] += 1

                # When we get a failure we put the job back on the queue
                self.workQueue.put( self.func )
                self.children[i].msg( formatError( r[ERROR] ) ) 

            elif r[RESULT] == READY:
                self.children[i].msg( "STARTING" )

            elif r[RESULT] == WAIT_TIME:
                self.data[i][WAIT_TIME] += r[TIME]

        # Check that children are alive, restart
        for i in range(self.numChildren):
            if not self.children[i].is_alive( ) and not self.workQueue.empty( ):
                #FIXME: Check if we need more workers or if one is alive / without job to take this
                self.children[i].restart( )
            elif not self.children[i].is_alive( ) \
                 and not self.children[i].is_done( ) and self.workQueue.empty( ):
                self.children[i].stop( "DONE" )

        # Statistics reporting
        self.reportStatistics( )
    ################################################################################################



    ################################################################################################
    # done( self )
    # Are We Done?
    #   Returns a True/False if the pool is done processing jobs. Called continuously by our main 
    #   loop. When False, the program terminates.
    def done( self ):
        if self.childQueue.empty( ) and self.workQueue.empty( ):
            for c in self.children:
                if c.is_alive( ):
                    return False
        else:
            return False
        return True
    ################################################################################################



    ################################################################################################
    # stop( self )
    # Stop the Pool
    #   Stops our pool, killing all children.
    def stop( self ):
        for c in self.children:
            c.stop( )
    ################################################################################################
