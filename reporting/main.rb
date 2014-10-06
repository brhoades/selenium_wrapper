require 'sinatra/base'
require 'sinatra/assetpack'

require 'sqlite3'

require_relative 'processing.rb'
require_relative 'const.rb'
require_relative 'scheduling.rb'

$db = SQLite3::Database.new "reports.db"

def header( title )
  erb :header, :locals => { :title => title }
end

def footer
  erb :footer
end

set :public_folder, "assets"

class Reporting < Sinatra::Base
  register Sinatra::AssetPack

  assets do
    serve '/bootstrap',     from: 'bootstrap'
    serve '/font-awesome',  from: 'assets/font-awesome'
    serve '/js',            from: 'js'
    serve '/css',           from: 'css'
    serve '/data',          from: 'assets'
  end

set :bind, '0.0.0.0'

  post '/report' do
    status 200
    process_report
  end

  get /recentruns/ do
    if File.exists? "assets/recent-runs.json"
      File.open "assets/recent-runs.json"
    end
  end

  get /^([^\.]*)$/ do
    m = $1
    m = :index if $1 == nil
    erb m, :locals => { :header => method(:header), :footer => method(:footer) }
  end

  run!
end

