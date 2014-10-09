import json, requests, time, os, getpass, socket, base64, traceback
import Queue as Q
from sw.const import * 

class Report:
    """Report handles all the reporting events sent from the Pool, currently it exclusively sends these upstream to a
       server which then does further handling. The events are sent from the pool via calls to this instance's functions
       that in turn call :func:`send`.

       Reporting can be disabled by excluding the report option from the kwargs of :func:`main`. This has the
       same effect as not including the #report="url" option within the options header of a script before conversion. This URL
       should point to the included sinatra server in reporting/ like so: "http://reporting-server.com:4567/report". 

       Other options include a id="" option which allows you to specify a custom computer ID. Similarly, including run="" allows
       you to choose a specific run to join. Note that the run will be created if it doesn't already exist and will be used for 
       all subsequent script calls until removed.

       :param pool: Reference to our owning pool. This is primarily to access pool.options and not used much elsewhere. 

       :return: Report (self)
    """

    def __init__( self, pool ):
        self.pool = pool

        # This machine's identifier
        self.ID = pool.options.get( 'id', None )
        
        # The name for the current run, some sort of unique identifier
        self.run = pool.options.get( 'run', None )

        self.site = pool.options.get( 'report', None )

        self.enabled = self.site is not None

        if not self.enabled:
            return

        # Set these, these are initialized when we get a response from the server
        self.rid = None
        self.cid = None

        # Set on an error transmitting
        self.nextSend = 0

        self.pingFreq = 60

        self.tries = 5

        # Ping Frequency
        self.nextPing = time.time( ) + self.pingFreq

        # Our queue of things to submit to our server
        self.queue = Q.Queue( )

        self.func = self.pool.func.__name__

        pool.logMsg( ''.join( [ "Reporting to URL: ", self.site ] ) )



    def send( self, payload, type ):
        """Send enables a payload to be parsed and added into our local queue for transmission
           reporting server, where applicable. It is called as a sort of wrapper function from all
           of the individual reporting functions (such as :func:`endchild`) to facilitate
           standard transmission of the data upstream.

           Currently (to be fixed) it encodes repeat information in every single payload including
           all identifying characteristics about the run, pool, and our id. There's major issue for this
           except for further stressing network bandwidth and the JSON parser.
            
           :param payload: A hash of information to send upstream to our reporting server.
           :param type: The R_* constant identifier for the type of payload included. 
        """
        #FIXME: Remove duplicate header information and just have a identifying header at the top of all
        #payloads.
           
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
        """The think function called by our pool periodically. If enabled, it checks for the need to ping
           (keepalive) or if the next payload is ready to send. This function also handles the transmission of
           our payload.

           If our report.queue has content in it, it prepares to send everything upstream. The payload is transmitted
           in JSON with the following general format::
             { 
                "cid" => #, // Our client ID assigned by the server, nil if we don't have one yet.
                "rid" => #, // Our run ID assined by the server, ^
                "payload" => 
                    [
                        { 
                            "type" => R_START,    // For example, this is the type of payload here.
                            "time" => UNIX_EPOCH, // Since sometimes the Queue has a delay in transmission, each
                                                  // payload contains it own timestamp.
                            // Some miscellaneous identifying information goes in here that's deprecated
                            // and unused.

                            // If the type involves a child:
                            "ChildID" => #, // The index of our child in pool.children / pool.data

                            // If the type involves a job:
                            "timetaken" => UNIX_EPOCH //The time the job took to complete.
                        },
                        
                        //{  another here },
                        ...
                    ]

             }

          The JSON above is arranged and then attempts to open a HTTP request to the provided server. If it fails,
          it tries 5 more times every 5 seconds with a timeout of 1 second. It attemps to send the JSON up via post
          and then waits for an HTTP 200 or similar before considering it a success. If R_START was included in the 
          payload, the server will respond with a cid and a rid for the client which it then stores internally for 
          future reports.

          :returns: None
        """
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

            # Preparing header for payload
            payload['cid'] = self.cid
            payload['rid'] = self.rid

            self.pool.logMsg( ' '.join( [ 'Sending', str( len( data ) ), 'payload(s) to server.' ] ), NOTICE )
            r = None
            try:
                r = requests.post( self.site, data=json.dumps( payload ), timeout=1, headers={'content-type': 'application/json'} )
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
                self.pool.logMsg( ''.join( [ "Response from server: ", str( r.text ) ] ) )
        
                response = r.json( )

                if 'cid' in response:
                    self.cid = response['cid']
                if 'rid' in response:
                    self.rid = response['rid']
                self.tries = 5



    # Individual reporting functions

    def start( self ):
        """Sends a start notification payload.

           :returns: None
        """
        self.send( { }, R_START )

    def stop( self ):
        """Sends a stop notification payload.
        
           :returns: None
        """
        self.send( { }, R_STOP )

    def jobStart( self, child ):
        """Sends a job start notification payload.
            
           :param child: The index of the child reporting in pool.children/pool.data.
           :returns: None
        """
        self.send( { "childID": child }, R_JOB_START )

    def jobFinish( self, timetaken, child ):
        """Sends a job finish notification payload.

           :param timetaken: The time it took for the job to finish, recorded
             internally.
           :param child: The index of the child reporting in pool.children/pool.data.
           :returns: None
        """
        data = { 'timetaken': timetaken, 'childID': child }

        self.send( data, R_JOB_COMPLETE )

    def jobFail( self, error, child, screenshot=None ):
        """Sends a job failed notification payload.

           :param error: The error text that was included with the error.
           :param child: The index of the child reporting in pool.children/pool.data.
           :param None screenshot: A image from selenium's screenshot to be encoded in base64 
             for sending (optional).
           :returns: None
        """

        data = { 'error': error, 'childID': child }

        if screenshot is not None:
            with open( screenshot, "rb") as img:
                data['screenshot'] = base64.b64encode( img.read( ) ) 
        
        self.send( data, R_JOB_FAIL )

    def newChild( self, child ):
        """Sends a new child notification payload. This is called even when a child
           is restarted.

           :param child: The index of the child reporting in self.children/pool.data.
           :returns: None
        """
        self.send( { 'childID': child }, R_NEW_CHILD )

    def endChild( self, child ):
        """Sends a child process killed notification payload.

           :param child: The index of the child reporting in self.children/pool.data.
           :returns: None
        """
        self.send( { 'childID': child }, R_END_CHILD )

    def ping( self ):
        """Sends a keepalive notice to the server, effectively keeping this client and
           its run from timing out.

           :returns: None
        """
        self.nextPing = time.time( ) + self.pingFreq
        self.send( { }, R_ALIVE )

    # Generators
    def id( self ):
        """If self.id was not already set by the user, it generates a deterministic ID 
           based on the user running the script and the machine's name.

           :returns: None
        """
        # If we have a prespecified id, use that
        if not self.ID:
            # Generate one, user@machinename
            user = getpass.getuser( )
            machine = socket.gethostname( )
            self.ID = ''.join( [ user, '@', machine ] )

        return self.ID
