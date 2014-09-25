import json, requests, time, os, getpass, socket, base64, traceback
import Queue as Q
from sw.const import * 

class Report:

    def __init__( self, pool ):
        self.pool = pool

        # This machine's identifier
        self.ID = pool.options.get( 'id', None )
        
        # The name for the current run, some sort of unique identifier
        self.run = pool.options.get( 'run', None )

        self.site = pool.options.get( 'report', None )

        self.enabled = self.site is not None

        # Set on an error transmitting
        self.nextSend = 0

        self.pingFreq = 60

        self.tries = 5

        # Ping Frequency
        self.nextPing = time.time( ) + self.pingFreq

        # Our queue of things to submit to our server
        self.queue = Q.Queue( )

        if not self.enabled:
            return

        self.func = self.pool.func.__name__

        pool.logMsg( ''.join( [ "Reporting to URL: ", self.site ] ) )



    def send( self, payload, type ):
        if not self.enabled:
            return

        # Encode identifying information and the time
        payload['id']   = self.id( )
        payload['run']  = self.run
        payload['func'] = self.func
        payload['time'] = time.time( )
        payload['type'] = type

        # Log payload
        self.pool.logMsg( "Sending payload to queue: " + str( payload ), DEBUG )

        self.queue.put( payload )



    # Thinking
    def think( self ):
        t = time.time( )
        if not self.enabled:
            return
        if t > self.nextPing:
            self.ping( ) 
        if self.nextSend != 0 and t < self.nextSend:
            return
        if self.queue.qsize( ) == 0:
            return

        # We try to smash all of our data into a single array, which is then in
        # a hash. This way we can trasmit everything in one fell swoop.
        data = [ ]

        while self.queue.qsize( ) > 0:
            m = None
            try:
                m = self.queue.get( False )
            except Q.Empty as e:
                break
            data.append( m )

        if len( data ) > 0:
            payload = { "payload": data }
            self.pool.logMsg( ' '.join( [ 'Sending', str( len( data ) ), 'payload(s) to server.' ] ), NOTICE )
            r = None
            try:
                r = requests.post( self.site, data=json.dumps( payload ), timeout=0.5, headers={'content-type': 'application/json'} )
            except Exception as e:
                self.pool.logMsg( "Fatal error with reporting, probably failed to connect: ", CRITICAL )
                self.pool.logMsg( traceback.format_exc( ), CRITICAL )
                if self.tries > 0:
                    self.tries -= 1
                    self.pool.logMsg( ''.join( [ "Disabling reporting after ", str( self.tries ), " more tries." ] ), CRITICAL )
                    self.nextSend = t + 5
                else:
                    self.pool.logMsg( "Disabling reporting.", CRITICAL )
                    self.enabled = False
                    return

                # Put our data back in the send queue
                for m in data:
                    self.queue.put( m )
                return

            # There was a failure
            if r.status_code != requests.codes.ok:
                self.pool.logMsg( ''.join( [ "Payload failed to send with HTTP status code: ", str( r.status_code ) ] ), CRITICAL )
                # Put our data back in the send queue
                for m in data:
                    self.queue.put( m )
                # Wait 5 seconds before we try again
                self.nextSend = t + 5
            else:
                self.pool.logMsg( ''.join( [ "Sent payload successfully with status ", str( r.status_code ) ] ) , INFO )
                self.tries = 5



    # Individual reporting functions

    def start( self ):
        self.send( { }, R_START )

    def stop( self ):
        self.send( { }, R_STOP )

    def jobStart( self, child ):
        self.send( { "childID": child }, R_JOB_START )

    def jobFinish( self, timetaken, child ):
        data = { 'timetaken': timetaken, 'childID': child }

        self.send( data, R_JOB_COMPLETE )

    def jobFail( self, error, child, screenshot=None ):
        data = { 'error': error, 'childID': child }

        if screenshot is not None:
            with open( screenshot, "rb") as img:
                data['screenshot'] = base64.b64encode( img.read( ) ) 
        
        self.send( data, R_JOB_FAIL )

    def newChild( self, child ):
        self.send( { 'childID': child }, R_NEW_CHILD )

    def endChild( self, child ):
        self.send( { 'childID': child }, R_END_CHILD )

    def ping( self ):
        self.nextPing = time.time( ) + self.pingFreq
        self.send( { }, R_ALIVE )

    # Generators
    def id( self ):
        # If we have a prespecified id, use that
        if not self.ID:
            # Generate one, user@machinename
            user = getpass.getuser( )
            machine = socket.gethostname( )
            self.ID = ''.join( [ user, '@', machine ] )

        return self.ID
