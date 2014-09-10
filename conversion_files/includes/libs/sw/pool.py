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
        self.children = [ ]
        
        # Statistics and data per child
        self.data = [ ]

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

        # Max children ever
        self.maxChildren = numChildren

        # Our function
        self.func = func

        # Our timestamp
        self.timestamp = datetime.datetime.now( ).strftime( "%Y-%m-%d_%H-%M-%S" )

        self.options = kwargs

        staggered = kwargs.get( 'staggered', True )

        # General log directory, shared by all children
        self.log = os.path.join( os.path.dirname( os.path.abspath( file ) ), "logs", self.timestamp ) 

        # Marks our start time, set when first child sends starting
        self.started = None

        # Starting for now
        self.starting = True

        # Not stopped yet
        self.stopped = False

        # Children left
        self.childrenLeft = numChildren

        # Next time we'll spawn a child
        self.nextSpawn = time.time( )

        # Time between children spawning
        self.staggeredTime = 5



    def newChild( self ):
        """Creates a new :class:`child` which will in turn start itself. 

        :returns: None
        """
        # First see if there's another child that's stopped
        for c in self.children:
            if c.stopped:
                c.start( )
                return

        self.data.append( [ 0, 0, STAT_LOAD, [ ] ] )

        self.children.append( Child( self.childQueue, self.workQueue, len( self.children ), self.log, self.options ) )
        
        self.maxChildren += 1



    def endChild( self ):
        """Removes the last created :class:`child`.

        :returns: None
        """
        if len( self.children ) == 0:
            return
        lastc = None
        for c in self.children:
            if not c.stopped:
                lastc = c
        if lastc is not None:
            lastc.stop( )

    def successful( self ):
        """Reports the number of jobs successfully completed so far.

        :returns: Integer for number of jobs successfully completed.
        """
        return reduce( lambda x, y: x + y, map( lambda x: x[SUCCESSES], self.data ) )



    def failed( self ):
        """Reports failed jobs so far.

        :returns: Integer for number of failed jobs.
        """
        return reduce( lambda x, y: x + y, map( lambda x: x[FAILURES], self.data ) )

    

    def timeTaken( self, sum=False ):
        """Reports how long everything has taken so far.

        :param False sum: Whether or not to return the sum of the time taken on jobs.
        :returns: List of individual job run times if sum is False, otherwise the amount of time taken as a float.
        """
        times = [ item for sublist in map( lambda x: x[TIMES], self.data ) for item in sublist ] # Flatten

        if sum:
            return sum( times )
        else:
            return times



    def think( self ): 
        """Runs through a single think loop; called by :py:func:`sw.wrapper.mainLoop` until there is no more work remaining.
        Check children are alive/restart if there are more jobs. Checks queues and parses any data.

        :returns: None
        """

        # Check our queues
        while not self.childQueue.empty( ):
            r = self.childQueue.get( False )
            i = r[NUMBER]

            if r[RESULT] == DONE:
                self.data[i][SUCCESSES] += 1
                self.data[i][TIMES].append( r[TIME] )

            elif r[RESULT] == FAILED:
                self.data[i][FAILURES] += 1

                # When we get a failure we put the job back on the queue
                self.workQueue.put( self.func )

            elif r[RESULT] == READY and self.started == None:
                self.started = time.time( )

            elif r[RESULT] == STATUS_UP:
                self.data[i][STATUS] = r[TIME]

        # Still spawning children, ignore their status until done.
        if self.starting and not self.stopped:
            if self.childrenLeft > 0 and time.time( ) > self.nextSpawn:
                self.newChild( )
                if self.options['staggered']:
                    self.nextSpawn = time.time( ) + self.staggeredTime
                self.childrenLeft -= 1
            elif self.childrenLeft == 0:
                self.starting = False
        elif not self.stopped: 
            # Check that children are alive, restart
            for i in range(self.numChildren):
                if not self.children[i].is_alive( ) and not self.workQueue.empty( ) and not self.children[i].stopped:
                    #FIXME: Check if we need more workers or if one is alive / without job to take this
                    self.children[i].restart( )
                elif not self.children[i].is_alive( ) \
                     and not self.children[i].is_done( ) and self.workQueue.empty( ) and not self.children[i].stopped:
                    self.children[i].stop( "DONE" )



    def done( self ):
        """Returns a True/False if the pool is done processing jobs. Called continuously by our main 
        loop. When False, the program terminates.

        :return: Boolean for if there are children still running work.
        """
        if self.stopped:
            return True

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

        self.stopped = True
