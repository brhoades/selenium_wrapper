require 'tk'
require 'tkextlib/tile'  
require 'highline/import'

###################################################################################################
# UI Logic
###################################################################################################

# Creates our root window and frame with appropriate dimensions
root = TkRoot.new
root.title = "Selenium Script Converter"

content = Tk::Tile::Frame.new root
frame = Tk::Tile::Frame.new content do
  width 400
  height 150
end

#########################################
# Labels and their Entry Boxes
########################################

# Input File Label on the left
lIn = Tk::Tile::Label.new content do
  text 'Input File'
end

# Input file entry box, is auto updated after browsing
$filename = TkVariable.new
eFilename = Tk::Tile::Entry.new content do
  textvariable $filename
end

# Output folder label
lOut = Tk::Tile::Label.new content do
  text 'Output Folder'
end

# Output file, auto updated after browsing for it or browsing for input file and empty
$outputfn = TkVariable.new
eOutputfn = Tk::Tile::Entry.new content do
  textvariable $outputfn
end

#########################################
# Input/Output Buttons
########################################

# Input Browse button logic. Basically update the entry field and then, if the output filename is empty,
# update it with the file name as a folder
bBrowseIn_click = Proc.new do
  if eFilename.value != ""
    $filename = eFilename.value
  else
    $filename = './'
  end
  
  out = Tk.getOpenFile 'filetypes' => [ [ 'Python Scripts', '*.py' ] ], 'initialdir' => File.dirname( $filename )

  if out != ""
    eFilename.value = $filename = out

    if $filename != nil and $filename != ""
      if $filename !~ /\.py$/
        Tk::messageBox :message => "Input file must be a python file (end in .py)."
      else
        inp = /[\/\\]in(put)?/
        $filename.sub!( inp, "" ) if inp.match( $filename )
        $outputfn = eOutputfn.value = outputFN $filename 
      end
    end
  end
end

# Input browse button, linked into logic
bBrowseIn = TkButton.new content do
  text "Browse"
end
bBrowseIn.comman = bBrowseIn_click

# Output browse button logic, fairly straight forward except chooseDirectory instead of chooseFile
bBrowseOut_click = Proc.new do
  if eOutputfn.value != ""
    $outputfn = eOutputfn.value
  else
    $outputfn = './'
  end
  
  out = Tk.chooseDirectory 'initialdir' => File.dirname( $outputfn )

  if out != ""
    eOutputfn.value = $outputfn = out
  end
end

# Output browse button, linked into logic
bBrowseOut = TkButton.new content do
  text "Browse"
end
bBrowseOut.comman = bBrowseOut_click

#########################################
# Convert Button
########################################

bSubmit_click = Proc.new do  
  # Pull one final time from entry fields
  $outputfn = eOutputfn.value
  $filename = eFilename.value
  
  # Check that we aren't running
  if $th.is_a? Thread and $th.alive? 
    error "Already running conversion routine, please wait. You will be prompted on completion."
    return
  elsif $th.is_a? Thread
    begin
      $th.join
    rescue 
      raise
    ensure
      $th = nil
    end
  end

  ### Check input
  # Check that input file exists and is from Selenium
  if not File.file? $filename
    error "Input file does not appear to exist. Conversion cannot continue."  
    return
  end

  if not isSeleniumFile? $filename
    action = Tk::messageBox \
      :type => 'yesno', :icon => 'question', :title => 'File unrecognized', \
      :message => "Input file does not appear to be exported from the Selenium IDE " \
                  + "in the proper format. It should be a Python 2.7 unittest-wrapped for Webdriver. " \
                  + "Continuing may have unknown effects, are you sure you wish to continue?" 
    if action == "no"
      return
    end
  end

  # Check if output folder exists
  if File.directory? $outputfn and Dir.exists? $outputfn and not File.file? $outputfn and not $overwrite
    action = Tk::messageBox \
      :type => 'yesno', :icon => 'question', :title => 'Folder Exists', \
      :message => "Output folder already exists. Files within the folder that conflict will be " \
                  + "overwritten. Continue with conversion?"
    if action == "no"
      return
    end
  end

  if File.file? $outputfn
    error "Output folder is a file, it should be a folder or nonexistant."
    return
  end

  $th = Thread.new do 
    $options[:python] = $python
    $options[:images] = $images
    $options[:recopy] = false
    $options[:overwrite] = $overwrite

    $res = convert $filename, $outputfn
    error "Complete!"
  end
end

# Convert button, linked into logic
bSubmit = TkButton.new content do
  text "Convert"
  default
end
bSubmit.comman = bSubmit_click

#########################################
# Checkboxes
########################################

# Checkbox for disabling images
$images = TkVariable.new
$images.set_bool_type false

tImages = Tk::Tile::CheckButton.new content do
  text "Images"
  variable $images
end

# Checkbox for including python
$python = TkVariable.new
$python.set_bool_type true

tPython = Tk::Tile::CheckButton.new content do
  text "Python"
  variable $python
end

# Checkbox for including python
$overwrite = TkVariable.new 
$images.set_bool_type false

tOverwrite = Tk::Tile::CheckButton.new content do
  text "Overwrite"
  variable $overwrite
end

###################################################################################################
# UI Positioning
###################################################################################################

content.grid          :column => 0, :row => 0
frame.grid            :column => 0, :row => 0, :columnspan => 8, :rowspan => 4 

eFilename.grid        :column => 1, :row => 1, :columnspan => 6, :sticky => "ew", :pady => 10, :padx => 5
eOutputfn.grid        :column => 1, :row => 2, :columnspan => 6, :sticky => 'we', :pady => 10, :padx => 5

bBrowseIn.grid        :column => 7, :row => 1, :sticky => 'we', :pady => 5, :padx => 5
bBrowseOut.grid       :column => 7, :row => 2, :sticky => 'we', :pady => 5, :padx => 5
bSubmit.grid          :column => 7, :row => 3, :sticky => 'we', :pady => 5, :padx => 5

lOut.grid             :column => 0, :row => 2, :sticky => 'w', :pady => 5, :padx => 10
lIn.grid              :column => 0, :row => 1, :sticky => 'w', :pady => 5, :padx => 10

tImages.grid          :column => 0, :row => 3, :sticky => 'we', :pady => 5, :padx => 10
tPython.grid          :column => 1, :row => 3, :sticky => 'e', :pady => 5
tOverwrite.grid       :column => 2, :row => 3, :sticky => 'e', :pady => 5

###################################################################################################
# Miscellaneous UI-related Functions
###################################################################################################

# Throw up an error window
def error( text, die=false )
  if not $options[:silent]
    Tk::messageBox :message => text
  else
    print "ERROR: ", text, "\n"
  end

  exit if die
end

def ask_continue
  exit unless agree "are you sure you wish to continue?"
end
