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
  print "Payload received from '", payload.first['id'], "' with '", payload.size, "' elements.\n"

  payload.each do |p|
    id = db.get_first_value "SELECT id FROM clients WHERE name=?", p['id']

    case p['type']
      when R_START
        if id == nil
          db.execute "INSERT INTO clients (name,active,lastping) VALUES (?,?,?)", [ p['id'], 1, Time.now.to_i ]
          id = db.get_first_value "SELECT id FROM clients WHERE name=?", p['id']
          print "New client '", p['id'], "'\n"
        else
          db.execute "UPDATE clients SET active=? WHERE id=?", [ 1, id ]
          print "Client '", p['id'], "' initialized\n"  
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
        print "Client still alive.\n"

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
