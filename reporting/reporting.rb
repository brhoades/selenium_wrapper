require 'sinatra'
require 'sqlite3'
require 'json'

require_relative 'processing.rb'

# Reporting Constants
R_START             = 0
R_JOB_START         = 1
R_JOB_COMPLETE      = 2
R_JOB_FAIL          = 3
R_STOP              = 4
R_ALIVE             = 5
R_NEW_CHILD         = 6
R_END_CHILD         = 7

# Timeout for how long before an automatically generated run
# is not fair game to join. Also controls how long before a run
# with no recent jobs completed or clients used is terminated.
RUN_TIMEOUT         = 600

# Timeout for how long after we don't hear from a client, that they
# are deactivated.
CLIENT_TIMEOUT      = 180

db = SQLite3::Database.new "reports.db"

set :bind, '0.0.0.0'

get '/' do
  print "Got some weird get request on /", "\n\n"
end

before do
  # Look at active runs
  db.execute( "SELECT id,starttime FROM runs WHERE endtime=-1" ) do |rid, runstarttime|
    db.execute( "SELECT L.id,L.lastping,L.name FROM children AS C, clients as L WHERE C.rid=? AND C.endtime=-1 AND l.id=C.cid", rid ) do |cid, lastping, name|
      next if Time.now.to_i - lastping < CLIENT_TIMEOUT # Likely in progress

      db.execute "UPDATE children SET endtime=? WHERE rid=? AND cid=?", [ Time.now.to_i, rid, cid ]
      db.execute "UPDATE runs SET endtime=? WHERE id=?", [ Time.now.to_i, rid ]

      print name, ": TIMEOUT\n"
    end
  end
end

post '/report' do
  process_report db
end
