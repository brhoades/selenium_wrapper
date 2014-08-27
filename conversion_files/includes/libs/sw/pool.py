from multiprocessing import Process, Queue
from sw.child import Child
import time, os
import datetime
from sw.const import * # Constants
from sw.formatting import * 



class Pool:
    """Stores parameters across all children, sets out log directory, initializes our data arrays,
        records start times, and pops `numJobs` functions into a Queue. Abstracts and makes it easier to
        manage scores of child processes. Also has a :func:`think` process to continuously manage them.

        :param numChildren: Number of children the pool will start with.
        :param numJobs: Number of jobs to fill our work queue with.
        :param func: The function reference that will be put into our work queue `numJobs` times.
        :param file: Filename with directory of our script which contained `func`. This is used to create a relative log directory.
        :param kwargs: Kwargs dict passed to :func:`main`, eventually passes arguments on to GhostDriver. 
            'staggered' is pulled from this dict if it exists.
        :returns: Pool (self)
    """
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
        self.timePerReport = 100 

        # Don't report statistics for another minute
        self.nextStat = time.time( ) + int( self.timePerReport*1.1 )

        # Our timestamp
        self.timestamp = datetime.datetime.now( ).strftime( "%Y-%m-%d_%H-%M-%S" )

        self.options = kwargs

        staggered = kwargs.get( 'staggered', True )

        # General log directory, shared by all children
        self.log = os.path.join( os.path.dirname( os.path.abspath( file ) ), "logs", self.timestamp ) 

        #print( ''.join( [ "Preparing ", str( numChildren ), " ", ( "child" if numChildren == 1 else "children" ), \
        #       " to do ", str( numJobs ), " job", ( "s" if numJobs != 1 else "" ), "." ] ) )

        # Marks our start time, set when first child sends starting
        self.started = None

        # Starting for now...
        self.starting = True

        # Children left
        self.childrenLeft = self.numChildren

        # Next time we'll spawn a child
        self.nextSpawn = time.time( )

        # Time between children spawning
        self.staggeredTime = 5



    def newChild( self, i=None ):
        """Creates a new :class:`child` which will in turn start itself. If i is none, it grabs the next available array
        index, assuming it was initialized for this many children (will grab an index that doesn't exist if not).

        :param None i: Index for child process within pool's data structure. 
        :returns: None
        """
        if i == None:
            for i,c in enumerate( self.children ):
                if c == None:
                    break # This gets us our first empty i
        
        self.children[i] = Child( self.childQueue, self.workQueue, i, self.log, self.options )



    def reportStatistics( self, force=False ):
        """Translates statistics into the archaic form used by the :func:`sw.formatting.stats`.
        Map and reduce are used to get things quickly out of the self.data 2-d array. This function
        is only called every self.timePerReport seconds as set in this class's initialization func.

        :param False force: Forces a report of statistics. Only called by the script itself when done.
        :returns: None
        """
        # Check if it's time yet
        if force or ( time.time( ) >= self.nextStat and len( self.data[0] ) > 0 ):
            self.nextStat = time.time( ) + self.timePerReport
            
            # Reduces our good/bad results into a single "this many succeeded, this many failed" number.
            # Maps our times into a single list.
            good = reduce( lambda x, y: x + y, map( lambda x: x[SUCCESSES], self.data ) )
            bad  = reduce( lambda x, y: x + y, map( lambda x: x[FAILURES], self.data ) )
            timetaken = map( lambda x: x[TIMES], self.data )
            timetaken = [ item for sublist in timetaken for item in sublist ] # Flatten

            stats( good, bad, timetaken, self.children, self.numJobs, self.started ) 



    def think( self ): 
        """Runs through a single think loop; called by :func:`sw.mainmainLoop` until there is no more work remaining.
        Check children are alive/restart if there are more jobs. Checks queues and parses any data.

        :returns: None
        """

        # Check our queues
        while not self.childQueue.empty( ):
            r = self.childQueue.get( False )
            i = r[NUMBER]

            if r[RESULT] == DONE:
                self.data[i][SUCCESSES] += 1
                self.data[i][TIMES].append( r[TIMES] )
                self.children[i].msg( ''.join( ["DONE (", str( format( r[TIME] ) ), "s)" ] ) )

            elif r[RESULT] == FAILED:
                self.data[i][FAILURES] += 1

                # When we get a failure we put the job back on the queue
                self.workQueue.put( self.func )
                self.children[i].msg( ''.join( [ "ERROR: ", formatError( r[ERROR] ) ] ) ) 

            elif r[RESULT] == READY:
                if self.started == None:
                    self.started = time.time( )
                self.children[i].msg( "STARTING" )

        # Still spawning children, ignore their status until done.
        if self.starting == True:
            if self.childrenLeft > 0 and time.time( ) > self.nextSpawn:
                self.newChild( )
                if self.options['staggered']:
                    self.nextSpawn = time.time( ) + self.staggeredTime
                self.childrenLeft -= 1
            elif self.childrenLeft == 0:
                self.starting = False
        else: 
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



    def done( self ):
        """Returns a True/False if the pool is done processing jobs. Called continuously by our main 
        loop. When False, the program terminates.

        :return: Boolean for if there are children still running work.
        """
        if self.childQueue.empty( ) and self.workQueue.empty( ):
            for c in self.children:
                if c.is_alive( ):
                    return False
        else:
            return False

        return True



    def stop( self ):
        """Stops the pool cleanly and terminates all the children in it.
        
        :return: None
        """
        for c in self.children:
            c.stop( )
