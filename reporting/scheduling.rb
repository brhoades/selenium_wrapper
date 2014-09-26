require 'rufus-scheduler'

$sched = Rufus::Scheduler.new
$sched.every '15s' do
  # Look at active runs
  $db.execute( "SELECT id,starttime FROM runs WHERE endtime=-1" ) do |rid, runstarttime|
    $db.execute( "SELECT L.id,L.lastping,L.name FROM children AS C, clients as L WHERE C.rid=? AND C.endtime=-1 AND l.id=C.cid", rid ) do |cid, lastping, name|
      next if Time.now.to_i - lastping < CLIENT_TIMEOUT # Likely in progress

      $db.execute "UPDATE children SET endtime=? WHERE rid=? AND cid=?", [ Time.now.to_i, rid, cid ]
      $db.execute "UPDATE runs SET endtime=? WHERE id=?", [ Time.now.to_i, rid ]

      print name, ": TIMEOUT\n"
    end
  end
end
