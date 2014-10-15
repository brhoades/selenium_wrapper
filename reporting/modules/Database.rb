require 'mysql2'

require 'connection_pool'

class Database
  def initialize( cfg )
    @cfg = cfg['db']
    @db = ConnectionPool.new { Mysql2::Client.new host: @cfg['host'], username: @cfg['user'], \
                               password: @cfg['pass'], database: @cfg['name'] }
    

  end

  def execute( query, args=[], opts={} )
    r = nil

    @db.with do |conn|
      # Must be an array
      if not args.is_a? Array
        args = [ args ]
      end

      if opts.size == 0
        opts[:as] = :array
      end

      # Substitute values into query securely
      query.gsub!(/\?/) do |s|
        inp = args.shift
        if inp.is_a? String
          '"' + conn.escape( inp ) + '"'
        else
          conn.escape inp.to_s
        end
      end

      if args.size > 0
        print "ERROR: More args than ?'s (", args.size, ")\n"
      end

      r = conn.query( query, opts ).to_a

      # flatten if doesn't need to be 2d
      r.map! do |i|
        if i.is_a? Array and i.size == 1
          i.first
        else
          i
        end
      end

    end
    r
  end

  def get_first_value( query, args=[], opts={} )
    r = self.execute( query, args, opts )

    if r.is_a? Array
      r.first
    else
      r
    end
  end
end 
