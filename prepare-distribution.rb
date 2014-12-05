# Cleans up / slims down, then zips an output folder for distribution
require 'FileUtils'

$sz = "C:\\Program Files\\7-Zip\\7z.exe"

# What are we doing?

print "Select function: \n"
print "1) Prepare Converter\n"
print "2) Prepare Script for Distribution\n\n"

print "Make a choice: "

sel = gets.chomp.to_i

begin
  if sel == 2
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

    print "\n\n"

    out    = File.expand_path "out"
    target = File.expand_path list[sel-1]
    targetzip = target + ".zip"
    logs   = File.join target, "logs"

    print "Moving logs: "
    FileUtils.mv( logs, out ) if File.exists? logs
    print "DONE\n"

    print "Removing *.pyc files: "
    # Remove pyc files
    Dir['#{target}/*'].each { |f| FileUtils.rm f if f =~ /\.pyc$/ }
    print "DONE\n"

    if File.exist? targetzip
      print "Removing old zip: "
      FileUtils.rm targetzip
      print "DONE\n"
    end
    print "Compressing: "
    `"#{$sz}" a -mx9 "#{targetzip}" "#{target}"`
    print "DONE\n"

    print "Restoring logs: "
    FileUtils.mv( File.join( out, "logs" ), target ) if File.exists?( File.join( out, "logs" ) )
    print "DONE\n"
    
    print "\n\n"
  else
    print "Cleaning up *.pyc: "
    target = File.expand_path ".."
    targetzip = target + ".zip"
    Dir['conversion_files/**/*'].each { |f| FileUtils.rm f and print( f, "\n" ) if f =~ /\.pyc$/ }
    print "DONE\n"

    print "Creating zip: "
    `"#{$sz}" -a -mx9 "#{targetzip}" "in/" "conversion_files/" "doc/" ".git/" "*.rb" "README.md" "*.bat" "Gemfile" ".gitignore"`
    print "DONE\n"
  end
rescue
  print "Exception: ", $@.to_s, "\n"
end

print "Press return to finish\n"
gets
