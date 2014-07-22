from multiprocessing import Process, Queue
from sw.child import Child
import time
from const import * # Constants
from sw.formatting import * 


class ChildPool:
    def __init__( self, numChildren, numJobs, func ):
        # Our children
        self.children = [ None for x in range(numChildren) ]
        
        # Statistics and data per child
        self.data = [ [ 0, 0, [ ] ] for x in range(numChildren) ]

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
        self.timePerReport = 30 

        # Don't report statistics for another minute
        self.nextStat = time.clock( ) + int( self.timePerReport*1.1 )

        print( "Preparing " + str( numChildren ) + " children to make " + str( numJobs ) + " orders total." )
        for i in range( numChildren ):
            self.newChild( )


    def newChild( self, i=None ):
        # Create our data's home
        if i == None:
            for i,c in enumerate( self.children ):
                if c == None:
                    break # This gets us our first empty i
        
        self.children[i] = Child( self.childQueue, self.workQueue, i, self.data[i][FAILURES] )

    def reportStatistics( self ):
        # Check if it's time yet
        if time.clock( ) >= self.nextStat and len( self.data[0] ) > 0:
            self.nextStat = time.clock( ) + self.timePerReport
            
            # Reduces our good/bad results into a single "this many succeeded, this many failed" number.
            # Maps our times into a single list.
            good = reduce( lambda x, y: x + y, map( lambda x: x[SUCCESSES], self.data ) )
            bad  = reduce( lambda x, y: x + y, map( lambda x: x[FAILURES], self.data ) )
            timetaken = map( lambda x: x[TIMES], self.data )
            timetaken = [ item for sublist in timetaken for item in sublist ] # Flatten
            
            stats( good, bad, timetaken, self.children, self.numJobs ) 

    # Runs through a single think loop. Called as many times as our main loop pleases.
    # Check children are alive/restart if there are more jobs
    # Check queues, parse data
    def think( self ): 
        # Check our queues
        while not self.childQueue.empty( ):
            r = self.childQueue.get( False )
            i = r[NUMBER]

            if r[RESULT] == DONE:
                self.data[i][SUCCESSES] += 1
                self.data[i][TIMES].append( r[TIMES] )
                self.children[i].msg( "DONE (" + str( format( r[TIME] ) ) + "s)" )
            elif r[RESULT] == FAILED:
                self.data[i][FAILURES] += 1
                # When we get a failure we put the job back on the queue
                self.workQueue.put( self.func )
                self.children[i].msg( formatError( r[ERROR] ) ) 

        # Check that children are alive, restart
        for i in range(self.numChildren):
            if not self.children[i].is_alive( ) and not self.workQueue.empty( ):
                self.children[i].restart( )
            elif not self.children[i].is_alive( ) \
                 and not self.children[i].is_dead( ) and self.workQueue.empty( ):
                self.children[i].stop( "DONE" )

        # Statistics reporting
        self.reportStatistics( )

    def done( self ):
        if self.childQueue.empty( ) and self.workQueue.empty( ):
            for c in self.children:
                if c.is_alive( ) or not c.is_dead( ):
                    return False


    def stop( self ):
        for c in self.children:
            c.stop( )

