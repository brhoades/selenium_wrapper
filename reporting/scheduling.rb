require 'rufus-scheduler'
require 'json'

require_relative 'functions/range_overlap.rb'
require_relative 'functions/checksum.rb'

$sched = Rufus::Scheduler.new

######################
# TIMEOUT CHECK
#
$sched.every '15s' do
  # Look at active runs
  $db.execute( "SELECT id,name,starttime FROM runs WHERE endtime=-1" ) do |rid, run_name, runstarttime|
    $db.execute( "SELECT L.id,L.name FROM children AS C, clients as L WHERE C.rid=? AND C.endtime=-1 AND L.id=C.cid", rid ) do |cid, name|
      $db.execute( "SELECT time FROM messages WHERE cid=? ORDER BY id DESC LIMIT 1", cid ) do |lastping|
        lastping = lastping.first
        next if Time.now.to_i - lastping < CLIENT_TIMEOUT # Likely in progress

        $db.execute "UPDATE children SET endtime=? WHERE rid=? AND cid=? AND endtime=-1", [ Time.now.to_i, rid, cid ]

        print name, ": TIMEOUT\n"
      end

      # Check if there are other clients in this run, if there aren't it's done
      # FIXME: Currently this just times out a run after 600 w/ no clients 
      if RUN_TIMEOUT + runstarttime < Time.now.to_i \
        and $db.get_first_value( "SELECT count(C.id) FROM clients AS L, children as C WHERE L.id=? AND L.rid=? AND C.cid=L.id AND C.endtime=-1", [ cid, rid ] ) <= 0
        $db.execute "UPDATE runs SET endtime=? WHERE id=?", [ Time.now.to_i, rid ]

        print run_name, ": RUN TIMEOUT\n"
      end
    end
  end
end

$sched.every '15s', :first_in => 3 do
  rids = [] 
  jobs = []
  children = []
  checksum = nil
  datafile = "assets/recent-runs.json"

  # Grab the top five runs
  $db.execute( "SELECT id FROM runs ORDER BY id DESC LIMIT 5" ).each do |rid|
    jobs << ( $db.get_first_value "SELECT count(*) FROM jobs AS J, children AS C WHERE J.chid=C.id AND C.rid=?", rid ) 
    children << ( $db.execute "SELECT count(*), starttime, endtime FROM children WHERE rid=?", rid ).flatten
    rids << rid 
  end

  checksum = get_checksum( rids.zip( jobs, children ) ) 

  # If we already have cached data, open it and check using cached data
  if File.exists? datafile and $old_checksum == nil
    File.open( datafile ) do |f|
      old = JSON.load f
      $old_checksum = old[0]['checksum']
    end
  end

  # We don't continue if our checksums aren't different and the file is still there
  if $old_checksum != checksum or not File.exists? datafile
    print "Aggregating and calculating recent runs data.\n\tThis can take a while."
    # Our output json blob. It's an array of hashes where each individual hash contains
    # information for a row in a table, seen in views/index.erb
    out = Array.new
    
    print "\n\n", "#"*40, "\nDEBUGGING:\n"
    # Cycle through the runs
    rids.each do |rid|
      col = Hash.new
      $db.execute( "SELECT name,starttime,endtime from runs WHERE id=?", rid ) do |run_name,starttime,endtime|
        # Straight copy overs first
        col['name'] = run_name
        col['clients'] = $db.get_first_value "SELECT count(id) FROM clients WHERE rid=?", rid
        # Jobs are bound to a child (who completed them)
        col['jobs'] = $db.get_first_value "SELECT count(J.id) FROM jobs AS J, children AS C WHERE C.id=J.chid AND C.rid=?", rid

        # Choose an appropriate format for time 
        format = ""
        if endtime == -1
          col['elapsed'] = Time.at( Time.now.to_i - starttime ).utc
        else
          col['elapsed'] = Time.at( endtime - starttime ).utc
        end

        if col['elapsed'].to_i > 3600
          format += "%Hh"
        end
        if col['elapsed'].to_i > 60
          format += "%Mm"
        end
        if col['elapsed'].to_i % 60 != 0
          format += "%Ss"
        end 
        
        if format == ""
          col['elapsed'] = "0s"
        else
          col['elapsed'] = col['elapsed'].strftime format
        end

        #####################################
        # Get our concurrent sessions formatted. This returns a tally of the amount of concurrent sessions
        # from the start of the run to the end in the form of a hash. We discard children which ran for no less than
        # half the time of the average job.
        avgjob = $db.get_first_value "SELECT sum(timetaken)/count(timetaken) FROM jobs as J, children AS C WHERE C.id=J.chid AND C.rid=?", rid
        if avgjob == nil
          mavgjob = 0
        else
          mavgjob = avgjob/4
        end
        clienttimes = Array.new
        $db.execute( "SELECT starttime,endtime FROM children WHERE rid=? AND ( endtime-starttime>? OR ( endtime=-1 AND ?-starttime>? ) )", [ rid, mavgjob, Time.now.to_i, mavgjob ] ) do |start,endt| 
          if endt == "-1"
            endt = Time.now.to_i
          end

          clienttimes << Range.new( start.to_i, endt.to_i ) 
        end
        print "\nRID: ", rid, "\nClients: ", col['clients'], "\nJobs: ", col['jobs'], "\nStart: ", starttime, "\nEnd: ", endtime
        print "\nTime: ", clienttimes

        tallied = tally_range clienttimes 
        if tallied != nil and tallied.size > 0
          col['peak-concurrent'] = tallied.values.max
          col['avg-concurrent']  = ( tallied.values.reduce( :+ ) / tallied.size.to_f ).round 3
        else
          col['peak-concurrent'] = "-"
          col['avg-concurrent']  = "-"
        end

        if endtime - starttime > 0 or ( endtime == -1 and Time.now.to_i - starttime != 0 )
          endtime = Time.now.to_i if endtime == -1
          col['avg-jpm'] = ( col['jobs'] / ( endtime - starttime ) * 60 ).round 2
        else
          col['avg-jpm'] = "-"
        end

        print "\nPeak Concur: ", col['peak-concurrent'], "\nAvg Concur: ", col['avg-concurrent']
        print "\nAvg JPM: ", col['avg-jpm'], "\n\n"

        out << col
      end
    end
    
    if out.size > 0
      out[0]['checksum'] = checksum
    else
      out << { :checksum => checksum }
    end

    print "#"*40, "\n\n"

    # Write to data file
    File.open( datafile, "w" ) do |f|
      f.write out.to_json
      $old_checksum = out[0]['checksum']
    end
  end
end
