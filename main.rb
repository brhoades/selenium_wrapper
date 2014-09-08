require_relative 'convert.rb'
require_relative 'ui.rb'

require 'optparse'

$options = { images: false, recopy: false, overwrite: false }

# Check for command line arguments
OptionParser.new do |opts|
  opts.banner = "Usage: main.rb [options] script.py"
  
  opts.on "-m", "--[no-]images", "Exported script should load images." do |o|
    $options[:images] = o
  end
  
  opts.on "-o", "--[no-]overwrite", "Overwrite any conflicting files on output." do |o|
    $options[:overwrite] = o
  end

  opts.on "-c", "--[no-]recopy", "Recopy missing or different files." do |o|
    $options[:recopy] = o
  end

  opts.on "-p", "--[no-]python", "Include python in installation (Windows only)." do |o|
    $options[:python] = o
  end

  opts.on "-i", "--script [SCRIPT]", String, "Script to convert, UI isn't launched if this is specified" do |s|
    s = File.realpath s
    $options[:silent] = true

    ### Check input
    # Check that input file exists and is from Selenium
    if not File.file? s
      error "Input file does not appear to exist. Conversion cannot continue.\n" 
      exit
    end

    if not isSeleniumFile? s
      error "Input file does not appear to be exported from the Selenium IDE " \
                    + "in the proper format. It should be a Python 2.7 unittest-wrapped for Webdriver. " \
                    + "Continuing may have unknown effects, "
      ask_continue
    end

    # Splits apart our directory and file name
    fn = /.*([\/\\])([^\\\/\n]+)\.py$/.match s

    out = File.dirname( s ) + fn[1] + "out" + fn[1] + fn[2] + fn[1]

    # Check if output folder exists
    if File.directory? out and Dir.exists? out and not File.file? out and not $options[:overwrite]
      print "WARNING: Output folder already exists. Files within the folder that conflict will be " \
                  + "overwritten, "
      ask_continue
    end

    if File.file? out
      error "Output folder is a file, it should be a folder or nonexistant."
      exit
    end

    convert s, out
    print "Complete!\n"
    exit
  end

  opts.on "-h", "--help", "Show this message." do
    puts opts
    exit
  end

end.parse!

# Prepare our fiber's home
$th = nil

# Start our UI loop
Tk.mainloop
