require 'rufus-scheduler'
require 'json'

$sched = Rufus::Scheduler.new

######################
# TIMEOUT CHECK
#
$sched.every '15s' do
  # Look at active runs
  $db.execute( "SELECT id,starttime FROM runs WHERE endtime=-1" ) do |rid, runstarttime|
    $db.execute( "SELECT L.id,L.lastping,L.name FROM children AS C, clients as L WHERE C.rid=? AND C.endtime=-1 AND l.id=C.cid", rid ) do |cid, lastping, name|
      next if Time.now.to_i - lastping < CLIENT_TIMEOUT # Likely in progress

      $db.execute "UPDATE children SET endtime=? WHERE rid=? AND cid=? AND endtime=-1", [ Time.now.to_i, rid, cid ]
      #FIXME Could be other clients, don't die off yet
      $db.execute "UPDATE runs SET endtime=? WHERE id=?", [ Time.now.to_i, rid ]

      print name, ": TIMEOUT\n"
    end
  end
end

$sched.every '1m', :first_in => 1 do
  rids = [] 
  jobs = []
  old  = nil 
  datafile = "assets/recent-runs.json"
  # Grab the top five runs
  $db.execute( "SELECT id FROM runs ORDER BY id DESC LIMIT 5" ).each do |rid|
    jobs << ( $db.get_first_value "SELECT count(*) FROM jobs AS J, children AS C WHERE J.chid=C.id AND C.rid=?", rid ) 
    rids << rid 
  end
  
  # If we already have cached data, open it and check using cached data
  if File.exists? datafile
    File.open( datafile ) do |f|
      old = JSON.load f
      
      # Nothing has changed, same runs
      return if ( old['rids'] & rids ).empty? and ( old['total-jobs'] & jobs ).empty?
    end
  end

  print "Aggregating and calculating recent runs data.\n\tThis can take a while."
  # Our output json blob. It's an array of hashes where each individual hash contains
  # information for a row in a table, seen in views/index.erb
  out = Array.new
  
  # Cycle through the runs
  rids.each do |rid|
    col = Hash.new
    $db.execute( "SELECT name,starttime,endtime from runs WHERE id=?", rid ) do |run_name,starttime,endtime|
      # Straight copy overs first
      col['name'] = run_name
      col['clients'] = $db.get_first_value "SELECT count(id) FROM clients WHERE rid=?", rid
      # Jobs are bound to a child (who completed them)
      col['jobs'] = $db.get_first_value "SELECT count(J.id) FROM jobs AS J, children AS C WHERE C.id=J.chid AND C.rid=?", rid
      col['start'] = Time.at( Time.new( starttime ) )
      col['end'] = Time.at( Time.new( endtime ) )

      #####################################
      # Get our concurrent sessions formatted. This returns a tally of the amount of concurrent sessions
      # from the start of the run to the end in the form of a hash. We discard children which ran for no less than
      # half the time of the average job.
      avgjob = $db.get_first_value "SELECT sum(time)/count(time) FROM jobs as J, children AS C WHERE C.id=J.chid AND C.rid=?", rid
      mavgjob = avgjob/4
      clienttimes = Array.new
      $db.execute( "SELECT starttime,endtime FROM children WHERE rid=? AND endtime-starttime>?", [ rid, mavgjob ] ) do |start,endt| 
        clienttimes << Range.new( start, endt ) 
      end
      print "\n\nTimes: ", clienttimes, "\n\n"
    end
  end

end
