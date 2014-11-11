require 'zip/zip'
require 'fileutils'

###################################################################################################
# Conversion Logic 
###################################################################################################
#
def convert_keywords( file, filename )
  start = false     # Indicator for the start of our function
  startOps = false  # Indicator for the start of our $options header
  base_url = ""     # Stores our base url
  i = -1 
  func = [ ]
  kwargs = [ ]
  imports = [ ]

  fn = File.basename filename, ".py"
  file.each do |l|
    i += 1
    if l =~ /^[\s]{4}def\stest_[^\(]+\(self\):$/ 
      start = true
      func << l
      next
    elsif i == 0 and l =~ /^#OPTIONS/i
      startOps = true
      next
    end

    ################################################################################################
    # $options Parsing Section
    # If we found #$options at the top of the file, parse any following comment as $options.
    # Anything that is prefixed with #p is assumed to be a function parameter
    #
    if startOps
      if l =~ /^#p (.*)/i
        kwargs << $1.strip
      end
      
      if l =~ /^#(import.*)/
        imports << $1.strip
      end

      startOps = false if l !~ /^#/
      next
    end

    ################################################################################################
    # Catch for the base_url
    if l =~ /self\.base_url[\s]*=[\s]*(.*)$/
      base_url = $~.captures.first
    end
 
    # Once we find the function, copy everything until the end of the block
    if start
      ##############################################################################################
      # Custom catches for user commands
      if l =~ /([\s]+)\#wait ([^\s]*)( .*)?/i
        if $3 == nil or $3 == ""
          func << ( $1 + "waitToDisappear( driver, #{$2} )\n" )
        else
          $3.strip!
          func << ( $1 + "waitToDisappear( driver, #{$2}, #{$3} )\n" )
        end
        next
      end

      if l =~ /([\s]+)\#log (.+)/
        func << ( $1 + "driver.child.logMsg( '#{$2}' )\n" )
        next
      end

      if l =~ /([\s]+)\#msg (.+)/
        func << ( $1 + "driver.child.msg( '#{$2}' )\n" )
        next
      end

      if l =~ /([\s]+)\#error (.+)/
        func << ( $1 + "driver.child.errorMsg( '#{$2}' )\n" )
        next
      end

      if l =~ /([\s]+)\#screenshot/
        func << ( $1 + "driver.child.screenshot( )\n" )
        next
      end
      ################################################################################################


      if l =~ /self\.base_url/
        # Catch for references to self.base_url
        l.sub! /self\.base_url/, "base_url"
      end

      # Replace a tab with four spaces
      l.gsub! /[\t]/, (" "*4)

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
  
  return func, kwargs, imports, base_url
end

def convert_func_swap( func, kwargs )
  # Now apply regexes for my custom functions
  func.map! do |l|
    if l !~ /\.send_keys/
      #                                            The positive lookahead here is to make sure we don't get greedy with the .+ and capture .send_keys or .select_by_text
      l.sub /driver\.find_element_by_([A-Za-z_]+)\(([ur]?".+")\)(?=\.[A-Za-z_]{3,}|\s?\)\.[A-Za-z_]{3,})/ do
        "sleepwait( driver, #{$2}, \"#{$1}\" )" 
      end
    else
      l.sub /driver\.find_element_by_([A-Za-z_]+)\(([ur]?".+")\)\.send_keys\(\"([^"]+)\"\)/ do
        "sendKeys( driver, #{$2}, \"#{$1}\", \"#{$3}\" )"
      end
    end
  end

  # Change the definition to not use self, it should have "driver"
  # For simplicity's sake, the name of the function will be static too
  func.first.sub! /[^\s\(\)]+\(self\)/, "test_func( driver )"

  # Right afterwards set the window resolution
  func.insert( 1, ( " "*8 ) + "driver.set_window_size( 1920, 1080 )\n" )

  # Get our args sorted out
  if $options[:images] == true
    kwargs << "images=True"

  else
    kwargs << "images=False"
  end

  kwargs.each do |k|
    if k =~ /proxy\-type/
      kwargs[kwargs.index( k )].gsub! /\-/, ""
    end
  end
end

def convert_print_prep( func, kwargs, base_url, imports )
  # Drop the base_url at the beginning of the function
  func.insert 1, "        base_url = #{base_url}\n"

  # Snip all lines by 4 spaces
  func.map! { |l| l.sub /^[\s]{4}/, "" }

  # Now prepare the header
  func.unshift "\n"
  func.unshift "from selenium.webdriver.support.ui import Select\n"
  func.unshift "from sw.wrapper import main\n"
  func.unshift "from sw.utils import *\n"
  func.unshift "from sw.const import *\n"
  func.unshift "sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '\\\\includes\\\\libs\\\\')\n"
  func.unshift "import sys, os, time\n"
  imports.each do |i|
    func.unshift i + "\n"
  end

  # Declare UTF-8
  func.unshift "# -*- coding: utf-8 -*-\n"

  # and the footer
  func << "\n" << "\n"
  func << "if __name__ == '__main__':\n" 
  func << " "*4 + "main( test_func, __file__, #{kwargs.join ", "} )\n"
end

def convert( filename, outputfn )
  file = []
  func = []
  kwargs = [] 
  base_url = ""
  imports = []      # Manually added imports later

  # Grab our $options and make sure keys exist
  $options[:python] = true unless $options.has_key? :python
  $options[:images] = false unless $options.has_key? :images
  $options[:recopy] = false unless $options.has_key? :recopy

  # Read in our input file  
  File.new( filename, "r:UTF-8" ).each_line { |l| file << l }
  func, kwargs, imports, base_url = convert_keywords file, filename
  convert_func_swap func, kwargs

  ##################
  # Prep for printing
  ##################

  convert_print_prep func, kwargs, base_url, imports

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
  cf = File.join scriptpath, "conversion_files"
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
  if not Dir.exists? File.join( cf, "python27" ) and $options[:python]
    if not File.exists? cf+"python27.zip"
      error "Missing packaged Python 2.7.8 installation folder or zip in conversion_files, this is required for the \"Include Python\"//\"--python\" option.\n\nThe conversion process cannot continue."
      return nil
    else
      # Extract our python27.zip folder
      phasePrint "Extracting Python", i+=0.5, max
      error "Extracting python27.zip, this may take some time.\n\nIt is quicker to extract this by hand into the conversion_files folder using 7-zip or Peazip, as they are capable of using multiple cores."
      unzip "#{cf}python27.zip", cf
    end
  end

  i = i.floor if i.is_a? Float
  phasePrint "Copying Python to Output Folder", i+=1, max
  print "  This will take some time\n"
  # Copy Python over to the directory
  if not Dir.exists? File.join( outputfn, "python27" ) and $options[:python]
    FileUtils.cp_r File.join( cf, "python27" ), outputfn
  end

  phasePrint "Initializing File Structure", i+=1, max
  FileUtils.cp File.join( cf, "run.bat" ), outputfn

  FileUtils.cp_r File.join( cf, "includes" ), outputfn

  return File.new( File.join( outputfn, "run_test.py" ), "w+:UTF-8" )
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

# Gets out output folder name from input filename and the main script
def outputFN( input )
  # This gets our parent folder name and then puts in out/ the base file name of the conversion script.
  File.join File.dirname( __FILE__ ), "out", File.basename( input, ".py" ) 
end

