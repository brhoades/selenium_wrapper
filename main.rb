require_relative 'convert.rb'
require_relative 'ui.rb'

# Check for command line arguments
OptionsParser.new do |o|
  o.banner = "Usage: main.rb [options] script.py"
  
  o.on "-i", "--images", "Exported script should load images."
  o.on "-o", "--overwrite", "Overwrite any conflicting files on output."

end

# Prepare our fiber's home
$th = nil

# Start our UI loop
Tk.mainloop
