import json, requests, time, os, getpass, socket, base64
from multiprocessing import Queue
from sw.const import * 

class Report:

    def __init__( self, pool ):
        self.pool = pool

        # This machine's identifier
        self.id = pool.options.get( 'id', None )
        
        # The name for the current run, some sort of unique identifier
        self.run = pool.options.get( 'run', None )

        self.site = pool.options.get( 'report', None )

        self.enabled = self.site is not None

        # Set on an error transmitting
        self.nextSend = 0

        self.pingFreq = 60

        # Ping Frequency
        self.nextPing = time.time( ) + self.pingFreq

        # Our queue of things to submit to our server
        self.queue = Queue( )

        if not self.enabled:
            return



    def send( self, payload, type ):
        if not self.enabled:
            return

        # Encode identifying information and the time
        payload['id']   = self.id( )
        payload['run']  = self.run
        payload['time'] = time.time( )

        self.queue.put( payload )



    # Thinking
    def think( self ):
        t = time.time( )
        if t > self.nextPing:
            self.ping( ) 
        if self.nextSend != 0 and t < self.nextSend:
            return
        if self.queue.qsize( ) == 0 or not self.enabled:
            return

        # We try to smash all of our data into a single array, which is then in
        # a hash. This way we can trasmit everything in one fell swoop.
        data = [ ]

        while self.queue.qsize( ) > 0:
            m = None
            try:
                m = self.queue.get( False )
            except Empty:
                break
            data.append( m )

        if len( data ) > 0:
            payload = { "payload": data }
            r = requests.post( self.site, data=json.dumps( payload ) )

            # There was a failure
            if r.status_code != requests.codes.ok:
                # Put our data back in the send queue
                for m in data:
                    self.queue.put( m )
                # Wait 5 seconds before we try again
                self.nextSend = t + 5



    # Individual reporting functions

    def start( self ):
        self.send( { }, R_START )

    def stop( self ):
        self.send( { }, R_STOP )

    def jobStart( self ):
        self.send( { }, R_JOB_START )

    def jobFinish( self, timetaken ):
        data = { 'timetaken': timetaken }

        self.send( data, R_JOB_COMPLETE )

    def jobFail( self, error, screenshot=None ):
        data = { }
        data['error'] = error
        if screenshot is not None:
            with open( screenshot, "rb") as img:
                data['screenshot'] = base64.b64encode( img.read( ) ) 
        
        self.send( data, R_JOB_FAIL )

    def newChild( self ):
        self.send( { }, R_NEW_CHILD )

    def endChild( self ):
        self.send( { }, R_END_CHILD )

    def ping( self ):
        self.nextPing = time.time( ) + self.pingFreq
        self.send( { }, R_ALIVE )

    # Generators
    def id( self ):
        # If we have a prespecified id, use that
        if not self.id:
            # Generate one, user@machinename
            user = getpass.getuser( )
            machine = socket.gethostname( )
            self.id = ''.join( [ user, '@', machine ] )

        return self.id
