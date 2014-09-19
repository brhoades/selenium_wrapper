require 'sinatra'
require 'sqlite3'
require 'json'

db = SQLite3::Database.new "reports.db"

set :bind, '0.0.0.0'

get '/' do
  print "Got some weird get request on /", "\n\n"
end

post '/report' do
  # Incoming data is JSON
  print "\n\n", JSON.parse( request.body.read.to_s ), "\n\n"
end
