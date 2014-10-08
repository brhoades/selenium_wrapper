require 'mysql2'

class Database
  def initialize( cfg )
    @cfg = cfg['db']
    @db = Mysql2::Client.new host: @cfg['host'], username: @cfg['user'], password: @cfg['pass'], database: @cfg['name']
  end

  def execute( query, args=[], opts={} )
    # Must be an array
    if not args.is_a? Array
      args = [ args ]
    end

    if opts.size == 0
      opts[:as] = :array
    end

    # Substite values into query securely
    query.gsub!(/\?/) do |s|
      @db.escape args.shift.to_s
    end

    if args.size > 0
      print "ERROR: More args than ?'s (", args.size, ")\n"
    end

    r = @db.query( query, opts ).to_a

    # flatten if doesn't need to be 2d
    r.map! do |i|
      if i.is_a? Array and i.size == 1
        i.first
      else
        i
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
