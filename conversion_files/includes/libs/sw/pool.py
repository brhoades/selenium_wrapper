from multiprocessing import Process, Queue
from sw.child import Child
import time, os, datetime, curses
from sw.const import * # Constants
from sw.formatting import * 
from sw.report import *



class Pool:
    """Stores parameters across all children, sets out log directory, initializes our data arrays,
        records start times, and pops `numJobs` functions into a Queue. Abstracts and makes it easier to
        manage scores of child processes. Also has a :func:`think` process to continuously manage them.

        :param func: The function reference that will be put into our work queue `numJobs` times.
        :param file: Filename with directory of our script which contained `func`. This is used to create a relative log directory.
        :param kwargs: Kwargs dict passed to :func:`main`, eventually passes arguments on to GhostDriver. 
            'stagger' is pulled from this dict if it exists.
        :returns: Pool (self)
    """
    def __init__( self, func, file, kwargs ):
        # Our children
        self.children = [ ]
        
        # Statistics and data per child
        self.data = [ ]

        self.status = STARTING

        # Our one way queue from our children
        self.childQueue = Queue( )

        # Our work for children
        self.workQueue = Queue( )

        # Options to be passed to children
        self.options = kwargs

        # Starting children
        self.startChildren = self.options['children']

        # Our function
        self.func = func

        # General log directory, shared by all children
        self.log = os.path.join( os.path.dirname( os.path.abspath( file ) ), "logs", datetime.datetime.now( ).strftime( "%Y-%m-%d_%H-%M-%S" ) ) 
        os.makedirs( self.log )

        # Marks our start time, set when first child sends starting
        self.started = None

        # Our pool log
        self.lh = open( os.path.join( self.log, 'pool.txt' ), 'w+', 0 )

        # Our log level
        self.level = self.options['level']

        if self.level != NOTICE and self.level != NONE:
            self.logMsg( ''.join( [ "Internal log level overriden to: ", errorLevelToStr( self.level, False ) ] ) , NONE ) 

        # Our reporting object
        self.reporting = Report( self )

        ####### Settings ########

        # Time between children spawning
        self.staggeredTime = 5

        ####### One Offs ########
        # Populate our work queue
        for x in range(self.options['jobs']):
            self.workQueue.put( func )

        # Next time we'll spawn a child
        self.nextSpawn = time.time( )

        self.logMsg( "Pool starting" )
        self.reporting.start( )



    def newChild( self ):
        """Creates a new :class:`child` which will in turn start itself. 

        :returns: None
        """
        # First see if there's another child that's stopped
        for c in self.children:
            if c.status( ) >= STOPPED:
                c.start( )
                self.logMsg( ''.join( [ "Respawning old child (#", str( c.num + 1 ), ")" ] ) )
                self.reporting.newChild( c.num )
                return

        self.data.append( [ 0, 0, DISP_LOAD, [ ] ] )

        self.reporting.newChild( len( self.children ) )

        self.children.append( Child( self.childQueue, self.workQueue, len( self.children ), self.log, self.options ) )

        self.logMsg( ''.join( [ "Spawned new child (#", str( len( self.children ) ), ")" ] ) )



    def endChild( self, i=None ):
        """Removes the last created :class:`child`, called by GUI.

        :param None i: The index of the child process to kill. If not specified, it chooses
           the last child in the pool.children array that is alive.
        :returns: None
        """
        if len( self.children ) == 0:
            return

        c = None

        if i == None:
            for c in self.children[::-1]:
                if c.status( ) <= RUNNING:
                    break
        else:
            c = self.children[i]

        if c == None:
            return

        if c.status( ) == RUNNING:
            self.workQueue.put( self.func )
            self.logMsg( "Readding terminated child's job" )
        else:
            self.logMsg( "Not running a job, status: " + str( c.status( ) ) )
        if c.status( ) <= RUNNING:  
            self.reporting.endChild( c.num ) # Report that we're ending a child

        c.stop( "Stopped by GUI", STOPPED )
        self.logMsg( ''.join( [ "Stopping child (#", str( c.num + 1 ), ")" ] ) )
        self.reporting.stop( )



    def successful( self ):
        """Reports the number of jobs successfully completed so far.

        :returns: Integer for number of jobs successfully completed.
        """
        if len( self.data ) > 0:
            return reduce( lambda x, y: x + y, map( lambda x: x[SUCCESSES], self.data ) )
        else:
            return 0



    def failed( self ):
        """Reports failed jobs so far.

        :returns: Integer for number of failed jobs.
        """
        if len( self.data ) > 0:
            return reduce( lambda x, y: x + y, map( lambda x: x[FAILURES], self.data ) )
        else:
            return 0

    

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

        self.reporting.think( )

        # Check our queues
        while not self.childQueue.empty( ):
            r = self.childQueue.get( False )
            i = r[NUMBER]

            if r[RESULT] == DONE:
                self.data[i][SUCCESSES] += 1
                self.data[i][TIMES].append( r[TIME] )
                self.reporting.jobFinish( r[TIME], i )

            elif r[RESULT] == FAILED:
                curses.flash( )

                self.data[i][FAILURES] += 1
                self.reporting.jobFail( r[ERROR], i )

                # When we get a failure we put the job back on the queue
                self.workQueue.put( self.func )

            elif r[RESULT] == READY and self.started == None:
                self.started = time.time( )

            elif r[RESULT] == DISPLAY:
                self.data[i][DISPLAY] = r[TIME]

        # Still spawning children, ignore their status until done.
        if self.status == STARTING:
            left = self.startChildren - len( self.children )
            # We have children left to spawn, spawn one
            if left > 0 and time.time( ) > self.nextSpawn:
                self.newChild( )
                if self.options['stagger']:
                    self.nextSpawn = time.time( ) + self.staggeredTime
            # Done spawning children, so done starting
            elif left == 0:
                self.status = RUNNING
        # Constant check to see if children and running and to automatically restart them
        elif self.status == RUNNING: 
            # Check that children are alive, restart
            for c in self.children:
                #Check if we need more workers or if one is alive / without job to take this
                if c.status( ) >= FINISHED and not self.workQueue.empty( ):
                    count = 0
                    # Get a count of starting children which haven't grabbed a job yet.
                    for d in self.children:
                        if d.status( ) < RUNNING:
                            count += 1
                    # If even after these children start we don't have enough workers for the job queue, start this one too
                    if self.workQueue.qsize( ) - count > 0:
                        c.start( "Automatic start as more work is available." )
                        self.reporting.newChild( c.num )
                        self.logMsg( "Starting additional child as more work is available." )
                # Clean up leftover children that have manually terminated but still have processes
                elif c.status( ) >= FINISHED and c.proc is not None and self.workQueue.empty( ):
                    self.reporting.endChild( c.num )
                    c.stop( "DONE (cleanup of old processes)" )
                    self.logMsg( ''.join( [ "Stopping child as no more work is available (#", str( c.num + 1 ), ")" ] ) )



    def done( self ):
        """Returns a True/False if the pool is done processing jobs. Called continuously by our main 
        loop. When False, the program terminates.

        :return: Boolean for if there are children still running work.
        """
        if self.status >= STOPPED: 
            return True

        if self.childQueue.empty( ) and self.workQueue.empty( ):
            for c in self.children:
                if c.status( ) <= PAUSED:
                    return False
        else:
            return False

        return True



    def logMsg( self, msg, level=NOTICE ):
        """Logs a message to our log file in a consistent format. Depends on pool.lh 
           already being initialized and ready for writing. Does not flush the handle.
            
           :param msg: The message to be logged.
           :param NOTICE level: The level of the message included. If the level is not
             greater than or equal to the user-specified level, the message is discarded.
           :returns: None
        """
        # Get our timestamp
        timestamp = datetime.datetime.now( ).strftime( "%H:%M:%S" )
        
        # String
        w = ''.join( [ "[", timestamp, "] ", errorLevelToStr( level ), "\t", msg, "\n" ] )

        if level >= self.level:
            self.lh.write( w )



    def stop( self, type=STOPPED ):
        """Stops the pool cleanly and terminates all the children in it.
           Currently handles pausing too until I need special functionality.
        
        :param STOPPED type: Type of stopping this is, either pausing or stopping.
        :return: None
        """
        self.logMsg( "Pool stopped, stopping all children." )

        for c in self.children:
            self.endChild( c.num )

        self.status = type 
        self.reporting.stop( )
        


    def start( self ):
        """Restarts a pool after it's been stop( )ed.

        :return: None
        """
        self.logMsg( "Pool started, starting all children." )
        for c in self.children:
            c.start( )
            self.reporting.newChild( c.num )
        
        self.status = RUNNING
        self.reporting.start( )
