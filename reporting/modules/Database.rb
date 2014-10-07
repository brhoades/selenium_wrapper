require 'mysql'

class Database
  def initialize( cfg )
    @cfg = cfg['db']
    @db = Mysql.new @cfg['host'], @cfg['user'], @cfg['pass'], @cfg['name']
  end

  def execute( query, args=[] )
    # Must be an array
    if not args.is_a? Array
      args = [ args ]
    end

    # Substite values into query securely
    query.gsub!(/\?/) do |s|
      @db.escape_string args.shift.to_s
    end

    if args.size > 0
      print "ERROR: More args than ?'s (", args.size, ")\n"
    end

    @db.query query
  end

  def get_first_value( query, args=[] )
    self.execute( query, args ).first
  end
end 
