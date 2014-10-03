require 'rufus-scheduler'
require 'json'

require_relative 'functions/range_overlap.rb'

$sched = Rufus::Scheduler.new

######################
# TIMEOUT CHECK
#
$sched.every '15s' do
  # Look at active runs
  $db.execute( "SELECT id,name,starttime FROM runs WHERE endtime=-1" ) do |rid, run_name, runstarttime|
    $db.execute( "SELECT L.id,L.lastping,L.name FROM children AS C, clients as L WHERE C.rid=? AND C.endtime=-1 AND l.id=C.cid", rid ) do |cid, lastping, name|
      next if Time.now.to_i - lastping < CLIENT_TIMEOUT # Likely in progress

      $db.execute "UPDATE children SET endtime=? WHERE rid=? AND cid=? AND endtime=-1", [ Time.now.to_i, rid, cid ]

      print name, ": TIMEOUT\n"
    end

    # Check if there are other clients in this run, if there aren't it's done
    # FIXME: Currently this just times out a run after 600 w/ no clients 
    if RUN_TIMEOUT + runstarttime < Time.now.to_i \
        and $db.get_first_value( "SELECT count(*) FROM clients WHERE rid=?", rid ) <= 0
      $db.execute "UPDATE runs SET endtime=? WHERE id=?", [ Time.now.to_i, rid ]

      print run_name, ": RUN TIMEOUT\n"
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
  
  print "#"*40, "DEBUGGING: \n"
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
        clienttimes << Range.new( start.to_i, endt.to_i ) 
      end
      print "\nRID: ", rid, "\nClients: ", col['clients'], "\nJobs: ", col['jobs'], "\nStart: ", col['start'], "\nEnd: ", col['end']
      print "\nTime: ", clienttimes

      tallied = tally_range clienttimes 
      col['peak-concurrent'] = tallied.values.max
      col['avg-concurrent']  = ( tallied.values.reduce( :+ ) / tallied.size.to_f ).round 3

      col['avg-jpm'] = col['jobs'] / ( endtime - starttime )
      col['peak-jpm'] = "TBD"

      print "\nPeak Concur: ", col['peak-concurrent'], "\nAvg Concur: ", col['avg-concurrent']
      print "\nAvg JPM: ", col['avg-jpm'], "\nPeak JPM: ", col['peak-jpm'], "\n\n"
    end
  end
  print "#"*40, "\n\n"

end
