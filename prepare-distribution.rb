# Cleans up / slims down, then zips an output folder for distribution
require 'FileUtils'

# Gets all folders in out/
list = Dir["out/*"]
list.map! { |l| l if File.directory? l }.compact! if list.size > 0

i = 0
list.each do |l|
  print i + 1, ") ", list[i], "\n"
  i += 1
end

print "Make a selection to package: "
sel = gets.chomp.to_i

out    = File.expand_path "out"
target = File.expand_path list[sel-1]
logs   = File.join target, "logs"

FileUtils.mv( logs, out ) if File.exists? logs

# Remove pyc files
Dir['**/*'].each { |f| FileUtils.rm f if f =~ /\.pyc$/ }

print "Compressing\n"
sz = "C:\\Program Files\\7-Zip\\7z.exe"
`"#{sz}" a -mx9 "#{target + ".zip"}" "#{target}"`

FileUtils.mv( File.join( out, "logs" ), target ) if File.exists?( File.join( out, "logs" ) )
