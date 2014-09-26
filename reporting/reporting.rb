require 'sinatra'
require 'sqlite3'
require 'json'

require_relative 'processing.rb'
require_relative 'const.rb'
require_relative 'scheduling.rb'

$db = SQLite3::Database.new "reports.db"

set :bind, '0.0.0.0'

post '/report' do
  process_report
end
