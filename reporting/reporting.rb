require 'sinatra'
require 'sqlite3'
require 'json'

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

db = SQLite3::Database.new "reports.db"

set :bind, '0.0.0.0'

get '/' do
  print "Got some weird get request on /", "\n\n"
end

post '/report' do
  status 200
  # Incoming data is JSON
  payload =  JSON.parse( request.body.read.to_s )
  payload = payload['payload']
  id = nil
  rid = nil
  print "Payload received from '", payload.first['id'], "' with '", payload.size, "' elements.\n"

  payload.each do |p|
    if id == nil
      id  = db.get_first_value "SELECT id FROM clients WHERE name=?", p['id']
    end
    if rid == nil and id != nil
      if p['run'] != p['run'].to_i.to_s 
        rid = db.get_first_value "SELECT rid FROM clients WHERE id=?", id
      else
        rid = p['run']
      end
    end

    case p['type']
      when R_START
        # They aren't in our database, look.
        if id == nil
          db.execute "INSERT INTO clients (name,active,lastping) VALUES (?,?,?)", [ p['id'], 1, p['time'] ]
          id = db.get_first_value "SELECT id FROM clients WHERE name=?", p['id']
          print "New client '", p['id'], "'\n"
        else
          db.execute "UPDATE clients SET active=? AND lastping=? WHERE id=?", [ 1, p['time'], id ]
          print "Client '", p['id'], "' initialized\n"  
        end

        print "Run: '", p['run'], "'\n"

        # Were we given a run? If not do one of two things:
        #   1) Look for a run which was created in the past RUN_TIMEOUT seconds. If we find one, put ourselves into it. They
        #      must be using the same function.
        #   2) If the above can't be satisfied, create a new run with our function name.
        if p['run'] == nil
          rid = db.get_first_value "SELECT id FROM runs WHERE function_name=? AND endtime='-1' AND ?-starttime<=?", [ p['func'], Time.now.to_i, RUN_TIMEOUT ]
          print "Func: ", p['func'], "\tTime now: ", Time.now.to_i.to_s, "\tTimeout: ", RUN_TIMEOUT.to_s, "\n\n"
          if rid != nil
            p['run'] = db.get_first_value "SELECT name FROM runs WHERE id=?", rid
            print "Joining prior run '", p['run'], "' (", rid, ")\n"
          end
          if p['run'] == nil
            # Generate a run
            p['run'] = p['func'] + "_" + Time.now.strftime( '%Y-%m-%d_%H:%M:%S' )
            db.execute "INSERT INTO runs (name, starttime, function_name) VALUES (?,?,?)", [ p['run'], p['time'], p['func'] ]
            rid = db.get_first_value "SELECT id FROM runs WHERE name=?", p['run']
            db.get_first_value "UPDATE clients SET rid=? WHERE id=?", [ rid, id ]
            print "Autocreated new run '", p['run'], "' (", rid, ")\n" 
          end
        end


      when R_JOB_START
        next if id == nil
        print "Job start notification.\n"

      when R_JOB_COMPLETE
        next if id == nil
        print "Job completed notification.\n"

      when R_JOB_FAIL
        next if id == nil
        print "Job failed notification.\n"

      when R_STOP
        next if id == nil
        print "Client stop notification.\n"

      when R_ALIVE
        next if id == nil
        db.execute "UPDATE CLIENTS set lastping=? WHERE id=?", [ p['time'], id ]
        print "Client ", p['id'], " is still alive.\n"

      when R_NEW_CHILD
        next if id == nil 
        print "New child notification.\n"
      
      when R_END_CHILD
        next if id == nil
        print "End child notification.\n"
    end
  end

  "Hello"
end
