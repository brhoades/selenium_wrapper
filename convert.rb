require 'zip/zip'
require 'fileutils'

###################################################################################################
# Conversion Logic 
###################################################################################################

def convert( filename, outputfn, options={} )
  file = []
  func = []
  base_url = ""
  start = false

  # Read in our input file  
  File.new( filename, "r:UTF-8" ).each_line { |l| file << l }

  # Now find our "main" test method (should == file name) in a loop
  fn = File.basename filename, ".py"
  file.each do |l|
    if l =~ /^[\s]{4}def\stest_[^\(]+\(self\):$/ 
      start = true
      func << l
      next
    end

    # Catch for the base_url
    if l =~ /self\.base_url[\s]*=[\s]*(.*)$/
      base_url = $~.captures.first
    end

    if l =~ /self\.base_url/
      # Catch for (soon to be invalid) references to self.base_url
      l.sub! /self\.base_url/, "base_url"
    end

    # Replace a tab with four spaces
    l.gsub! /[\t]/, (" "*4)

    # Once we find the function, copy everything until the end of the block
    if start
      if l !~ /^[\s]{8,}/
        break
      end

      # Catch for driver = self.driver
      if l =~ /^[\s]+driver[\s]*=[\s]*self\.driver.*$/
        next
      end

      # Catch for assetions, currently just removing
      if l =~ /self\.assert/ or l =~ /AssertionError/
        next
      end

      # Catch for .clear, which isn't needed usually
      if l =~ /\.clear\(\)$/
        next
      end

      func << l
    end
  end

  # Now apply regexes for my custom functions
  func.map! do |l|
    if l !~ /\.send_keys/
      #                                            The positive lookahead here is to make sure we don't get greedy with the .+ and capture .send_keys or .select_by_text
      l.sub /find_element_by_([A-Za-z_]+)\(([ur]?".+")\)(?=\.[A-Za-z_]{3,}|\s?\)\.[A-Za-z_]{3,})/ do
        "find_element_by_#{$1}( sleepwait( driver, #{$2}, \"#{$1}\" ) )" 
      end
    else
      l.sub /driver\.find_element_by_([A-Za-z_]+)\(([ur]?".+")\)\.send_keys\(\"([^"]+)\"\)/ do
        "sendKeys( driver, sleepwait( driver, #{$2}, \"#{$1}\" ), \"#{$1}\", \"#{$3}\" )"
      end
    end
  end

  # Change the definition to not use self, it should have "driver"
  # For simplicity's sake, the name of the function will be static too
  func.first.sub! /[^\s\(\)]+\(self\)/, "test_func( driver )"

  # Right afterwards set the window resolution
  func.insert( 1, ( " "*8 ) + "driver.set_window_size( 1920, 1080 )\n" )

  kwargs = ""
  # Get our args sorted out
  if $images.bool == true
    kwargs = "images=True"
  else
    kwargs = "images=False"
  end
  
  ##################
  # Prep for printing
  ##################

  # Drop the base_url at the beginning of the function
  func.insert 1, "        base_url = #{base_url}\n"

  # Snip all lines by 4 spaces
  func.map! { |l| l.sub /^[\s]{4}/, "" }

  # Now prepare the header
  func.unshift "\n"
  func.unshift "import time\n"
  func.unshift "from selenium.webdriver.support.ui import Select\n"
  func.unshift "from sw.wrapper import main\n"
  func.unshift "from sw.utils import *\n"
  func.unshift "sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '\\\\includes\\\\libs\\\\')\n"
  func.unshift "import sys, os\n"

  # Declare UTF-8
  func.unshift "# -*- coding: utf-8 -*-\n"

  # and the footer
  func << "\n" << "\n"
  func << "if __name__ == '__main__':\n" 
  func << " "*4 + "main( test_func, __file__, #{kwargs} )\n"

  ################
  # Output to file
  ################
  handle = prepareDirectory outputfn 

  func.map { |l| handle.write l }

  handle.close
end

# Prepare our desired directory. This includes extracting Python to that location, creating a .bat wrapper, and touching a file to launch everything.
# We return our handle to the touched file.
def prepareDirectory( outputfn )
  scriptpath = File.dirname __FILE__
  cf = scriptpath+"/conversion_files/"
  i = 0 
  max = 3

  print "#"*40, "\n", "Preparing Directory\n", "#"*40, "\n\n"

  phasePrint "Create Base Folder / Check Dependencies", i+=1, max
  # Make our base directory
  if not Dir.exists? outputfn
    FileUtils.mkdir_p outputfn
  end

  # See if our conversion_files folder exists, this is required
  if not Dir.exists? cf 
    error "Missing conversion_files folder:\n#{cf}\n\nThe conversion process cannot continue."
    return nil
  end

  # Check for the python cache extracted folder
  if not Dir.exists? cf+"python277/" and $python.bool
    if not File.exists? cf+"python277.zip"
      error "Missing packaged Python 2.7.7 installation folder or zip in conversion_files, this is required for the \"Include Python\" option.\n\nThe conversion process cannot continue."
      return nil
    else
      # Extract our python277.zip folder
      phasePrint "Extracting Python", i+=0.5, max
      error "Extracting python277.zip, this may take some time.\n\nIt is quicker to extract this by hand into the conversion_files folder using 7-zip or Peazip, as they are capable of using multiple cores."
      unzip "#{cf}python277.zip", cf
    end
  end

  i = i.floor if i.is_a? Float
  phasePrint "Copying Python to Output Folder", i+=1, max
  print "  This will take some time\n"
  # Copy Python over to the directory
  if not Dir.exists? outputfn + "python277/" and $python.bool
    FileUtils.cp_r cf + "python277", outputfn
  end

  phasePrint "Initializing File Structure", i+=1, max
  FileUtils.cp cf + "run.bat", outputfn

  FileUtils.cp_r cf + "includes", outputfn
  
  return File.new( outputfn + "run_test.py", "w+:UTF-8" )
end

def phasePrint( title, num, max )
  print "Phase ", num, " of ", max, ": ", title, "\n"
end

# Does a simple, dirty check to see if the file is of a typical Selenium webdriver format.
# It just scans the imports...
def isSeleniumFile?( filename )
  i = 0
  unittest = false
  selenium = false
  webdriver = false
  
  File.new( filename, "r:UTF-8" ).each_line do |l|
    i += 1

    if l =~ /^from selenium/
      selenium = true
    end

    if l =~ /^from selenium\.webdriver/
      webdriver = true
    end

    if l =~ /^import .*unittest/
      unittest = true
    end

    if i > 10
      break
    end
  end

  return unittest & selenium & webdriver
end

# Found online then modified to my liking. Just recursively unzips to a destination
def unzip( fn, dest )
  Zip::ZipFile.open fn do |z|
    z.each do |f|
      fpath = File.join dest, f.name
      FileUtils.mkdir_p File.dirname fpath 
      z.extract( f, fpath ) unless File.exist? fpath
    end
  end
end
