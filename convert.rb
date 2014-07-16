###################################################################################################
# Conversion Logic 
###################################################################################################

def convert( filename, outputfn, options={} )
  file = []
  func = []
  base_url = ""
  start = false

  # Read in our input file  
  File.new( filename, "r" ).each_line { |l| file << l }

  # Now find our "main" test method (should == file name) in a loop
  fn = File.basename filename, ".py"
  print fn, "\n"
  file.each do |l|
    if l =~ /^[\s]{4}def\s#{fn}\(self\):$/ 
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

    # Once we find the function, copy everything until the end of the block
    if start
      if l !~ /^[\s]{8,}/
        break
      end

      # Catch for driver = self.driver
      if l =~ /^[\s]+driver[\s]*=[\s]*self\.driver.*$/
        next
      end

      func << l
    end
  end

  # Now apply regexes for my custom functions
  func.map! do |l|
    l.sub /find_element_by_([A-Za-z_]+)\((".+")\)/, "find_element_by_#{$1}( sleepwait( driver, #{$2}, \"#{$1}\" ) )" 
  end

  # Change the definition to not use self, it should have "driver"
  # For simplicity's sake, the name of the function will be static too
  func.first.sub! /[^\s\(\)]+\(self\)/, "test_func( driver )"


  ##################
  # Prep for printing
  ##################

  # Drop the base_url at the beginning of the function
  func.insert 1, "        base_url = #{base_url}"

  # Snip all lines by 4 spaces
  func.map! { |l| l.sub /^[\s]{4}/, "" }

  # Now prepare the header
  func.unshift "\n"
  func.unshift "import time\n"
  func.unshift "from selenium_wrapper import *\n"

  # and the footer
  func << "\n" << "\n"
  func << "if __name__ == '__main__':\n" 
  func << " "*4 + "main( )\n"

  ################
  # Output to file
  ################
  handle = prepareDirectory outputfn 
    

end

def prepareDirectory( outputfn )
  if not Dir.exists? outputfn
    Dir.mkdir outputfn
  end



end

def isSeleniumFile?( filename )
  i = 0
  unittest = false
  selenium = false
  webdriver = false
  
  File.new( filename, "r" ).each_line do |l|
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
