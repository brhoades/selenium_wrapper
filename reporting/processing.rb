require 'json'

def process_report( ) 
  # Incoming data is JSON
  req =  JSON.parse( request.body.read.to_s )
  payload = req['payload']
  cid = nil
  rid = nil
  response = { }

  ### Handle keys if we have them already

  if req.has_key? 'cid'
    cid = req['cid']
    if cid != nil
      $db.execute( "INSERT INTO messages (cid,time) VALUES (?,?)", [ cid, Time.now.to_i ] )
    end
  end

  if req.has_key? 'rid'
    rid = req['rid']
  end

  payload.each do |p|
    if ( p['type'] >= R_JOB_START and p['type'] <= R_JOB_FAIL ) or p['type'] >= R_NEW_CHILD \
      and p.has_key? 'childID'
      # This will be the last child with our index
      chid = $db.get_first_value "SELECT id FROM children WHERE cid=? AND rid=? AND \"index\"=? ORDER BY id DESC LIMIT 1", [ cid, rid, p['childID'] ]
    end



    case p['type']



      when R_START
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

          # If we still don't have a run
          if p['run'] == nil
            # Generate a run
            p['run'] = p['func'] + "_" + Time.now.strftime( '%Y-%m-%d_%H:%M:%S' )
            $db.execute "INSERT INTO runs (name, starttime, endtime, function_name, auto) VALUES (?,?,-1,?,?)", [ p['run'], p['time'], p['func'], 1 ]
            rid = $db.get_first_value "SELECT MAX(id) FROM runs"

            print p['id'], ": NEW RUN ", p['run'], " (", rid, ")\n"
          end
        end

        if cid == nil
          $db.execute "INSERT INTO clients (name,rid) VALUES (?,?)", [ p['id'], rid ]
          cid = $db.get_first_value " SELECT MAX(id) FROM clients"

          print p['id'], ": NEW CLIENT (", cid, ")\n"
        end

          response['rid'] = rid
          response['cid'] = cid



      when R_JOB_START
        next if cid == nil
        print p['id'], ": JOB START (#", p['childID']+1, ")\n"



      when R_JOB_COMPLETE
        next if cid == nil
        $db.execute "INSERT INTO jobs (chid,timetaken,endtime) VALUES (?,?,?)", [ chid, p['timetaken'], p['time'] ]
        print p['id'], ": JOB COMPLETE (#", p['childID']+1, ")\n"



      when R_JOB_FAIL
        next if cid == nil
        # First find out which child this is
        if p.has_key? 'screenshot'
          $db.execute "INSERT INTO errors (chid,screenshot,text,time) VALUES (?,?,?,?)",
            [ chid, p['screenshot'], p['error'], p['time'] ]
        else
          $db.execute "INSERT INTO errors (chid,text,time) VALUES (?,?,?)",
            [ chid, p['error'], p['time'] ]
        end

        print p['id'], ": JOB FAILED (#", p['childID']+1, ")\n"



      when R_STOP
        next if cid == nil

        # End all children which haven't ended already
        $db.execute "UPDATE children SET endtime=? WHERE rid=? and endtime=-1", [ p['time'], rid ]

        # Check if the run has any more clients
        res = $db.get_first_value "SELECT 1 FROM runs, children WHERE runs.id=? AND runs.id=children.rid AND children.endtime=-1", rid
        if res == nil
          # We only automatically end a run that's automatically generated
          if $db.get_first_value( "SELECT auto FROM runs WHERE id=?", rid ) == 1
            $db.execute "UPDATE runs SET endtime=? WHERE id=?", [ p['time'], rid ] 
          end
        end

        print p['id'], ": STOP\n"



      when R_NEW_CHILD
        next if cid == nil 

        # Are there other children with this index/cid/rid?
        oid = $db.get_first_value( "SELECT id FROM children WHERE rid=? AND cid=? and 'index'=?", [ rid, cid, p['childID'] ] )
        if oid != nil
          print p['id'], ": OLD CHILD (#", p['childID']+1,") TIMED OUT\n"
          $db.execute "UPDATE children SET endtime=? WHERE id=?", [ p['time'], oid ]
        end

        $db.execute "INSERT INTO children (cid,rid,\"index\",starttime,endtime) VALUES (?,?,?,?,?)", [ cid, rid, p['childID'], p['time'], -1 ] 

        print p['id'], ": NEW CHILD (#", p['childID']+1, ")\n"
      


      when R_END_CHILD
        next if cid == nil

        $db.execute "UPDATE children SET endtime=? WHERE id=?", [ p['time'], chid ]

        print p['id'], ": END CHILD (#", p['childID']+1, ")\n"
    end
  end
  
  response['response'] = 'success' if( not response.has_key? 'response' )
  response.to_json
end
