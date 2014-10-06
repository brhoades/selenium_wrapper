require 'json'

def process_report( ) 
  # Incoming data is JSON
  payload =  JSON.parse( request.body.read.to_s )
  payload = payload['payload']
  id = nil
  rid = nil
  chid = nil

  payload.each do |p|
    if id == nil
      id = $db.get_first_value "SELECT id FROM clients WHERE name=?", p['id']
      $db.execute( "UPDATE clients SET lastping=? WHERE id=?", [ Time.now.to_i, id ] ) if id != nil
    end
    if rid == nil and id != nil
      if p['run'] != p['run'].to_i.to_s 
        rid = $db.get_first_value "SELECT rid FROM clients WHERE id=?", id
      else
        rid = p['run']
      end
    end
    if ( p['type'] >= R_JOB_START and p['type'] <= R_JOB_FAIL ) or p['type'] >= R_NEW_CHILD \
      and p.has_key? 'childID'
      # This will be the last child with our index
      chid = $db.get_first_value "SELECT id FROM children WHERE cid=? AND rid=? AND \"index\"=? ORDER BY id DESC LIMIT 1", [ id, rid, p['childID'] ]
    end

    case p['type']
      when R_START
        # They aren't in our database, look.
        if id == nil
          $db.execute "INSERT INTO clients (name,lastping) VALUES (?,?)", [ p['id'], Time.now.to_i ]
          id = $db.get_first_value "SELECT id FROM clients WHERE name=?", p['id']
          print p['id'], ": NEW CLIENT\n"
        else
          $db.execute "UPDATE clients SET lastping=? WHERE id=?", [ Time.now.to_i, id ]
          print p['id'], ": ACTIVATED\n"  
        end

        # Were we given a run? If not do one of two things:
        #   1) Look for a run which was created in the past RUN_TIMEOUT seconds. If we find one, put ourselves into it. They
        #      must be using the same function.
        #   2) If the above can't be satisfied, create a new run with our function name.
        if p['run'] == nil
          rid = $db.get_first_value "SELECT id FROM runs WHERE function_name=? AND endtime='-1' AND ?-starttime<=? AND auto=1", [ p['func'], Time.now.to_i, RUN_TIMEOUT ]
          if rid != nil
            p['run'] = $db.get_first_value "SELECT name FROM runs WHERE id=?", rid
            print p['id'], ": JOINING RUN ", p['run'], "\n"
          end
          if p['run'] == nil
            # Generate a run
            p['run'] = p['func'] + "_" + Time.now.strftime( '%Y-%m-%d_%H:%M:%S' )
            $db.execute "INSERT INTO runs (name, starttime, endtime, function_name, auto) VALUES (?,?,-1,?,?)", [ p['run'], p['time'], p['func'], 1 ]
            rid = $db.get_first_value "SELECT id FROM runs WHERE name=?", p['run']
            $db.get_first_value "UPDATE clients SET rid=? WHERE id=?", [ rid, id ]
            print p['id'], ": NEW RUN ", p['run'], "\n"
          end
        end


      when R_JOB_START
        next if id == nil

        print p['id'], ": JOB START (#", p['childID']+1, ")\n"

      when R_JOB_COMPLETE
        next if id == nil
        $db.execute "INSERT INTO jobs (chid,time) VALUES (?,?)", [ chid, p['timetaken'] ]
        
        print p['id'], ": JOB COMPLETE (#", p['childID']+1, ")\n"

      when R_JOB_FAIL
        next if id == nil
        # First find out which child this is
        if p.has_key? 'screenshot'
          $db.execute "INSERT INTO errors (chid,screenshot,text) VALUES (?,?,?)",
            [ chid, p['screenshot'], p['error'] ]
        else
          $db.execute "INSERT INTO errors (chid,text) VALUES (?,?)",
            [ chid, p['error'] ]
        end

        print p['id'], ": JOB FAILED (#", p['childID']+1, ")\n"

      when R_STOP
        next if id == nil

        # End all children which haven't ended already
        $db.execute "UPDATE children SET endtime=? WHERE rid=? and endtime=-1", [ p['time'], rid ]

        # Check if the run has any more clients
        res = $db.get_first_value "SELECT 1 FROM runs, children WHERE runs.id=? AND runs.id=children.rid AND children.endtime=-1", rid
        if res == nil
          # We only automatically end a run that's automatically generated
          if $db.get_first_value( "SELECT auto FROM runs WHERE id=?", rid ) == 1
            $db.execute "UPDATE runs SET endtime=? WHERE rid=?", [ p['time'], rid ] 
          end
        end

        print p['id'], ": STOP\n"

      when R_ALIVE
        next if id == nil
        $db.execute "UPDATE clients set lastping=? WHERE id=?", [ Time.now.to_i, id ]

        print p['id'], ": PING\n"

      when R_NEW_CHILD
        next if id == nil 

        # Are there other children with this index/cid/rid?
        oid = $db.get_first_value( "SELECT id FROM children WHERE rid=? AND cid=? and 'index'=?", [ rid, id, p['childID'] ] )
        if oid != nil
          print p['id'], ": OLD CHILD (#", p['childID']+1,") TIMED OUT\n"
          $db.execute "UPDATE children SET endtime=? WHERE id=?", [ p['time'], oid ]
        end

        $db.execute "INSERT INTO children (cid,rid,\"index\",starttime,endtime) VALUES (?,?,?,?,?)", [ id, rid, p['childID'], p['time'], -1 ] 

        print p['id'], ": NEW CHILD (#", p['childID']+1, ")\n"
      
      when R_END_CHILD
        next if id == nil

        $db.execute "UPDATE children SET endtime=? WHERE id=?", [ p['time'], chid ]

        print p['id'], ": END CHILD (#", p['childID']+1, ")\n"
    end
  end

  "Hello"
end
