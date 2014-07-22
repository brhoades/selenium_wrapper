require 'tk'

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
      elsif eOutputfn.value == ""
        fn = /.*([\/\\])([^\\\/\n]+)\.py$/.match( $filename )
        $outputfn = eOutputfn.value = File.dirname( $filename ) + fn[1] + fn[2] + fn[1]
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

# Convert button logic
bSubmit_click = Proc.new do  
  # Pull one final time from entry fields
  $outputfn = eOutputfn.value
  $filename = eFilename.value
  
  # Check that we aren't running
  if $th.is_a? Thread and $th.alive? 
    error "Already running conversion routine, please wait. You will be prompted on completion."
    return
  elsif $th.is_a? Thread
    $th.join
  end

  ### Check input
  # Check that input file exists and is from Selenium
  if File.file? $filename and not isSeleniumFile? $filename
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
  if File.directory? $outputfn and Dir.exists? $outputfn and not File.file? $outputfn
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
    $res = convert $filename, $outputfn 
    error "Complete!"
  end
end

# Convert button, linked into logic
bSubmit = TkButton.new content do
  text "Convert"
end
bSubmit.comman = bSubmit_click

###################################################################################################
# UI Positioning
###################################################################################################

content.grid :column => 0, :row => 0
frame.grid :column => 0, :row => 0, :columnspan => 8, :rowspan => 4 

eFilename.grid :column => 1, :row => 1, :columnspan => 6, :sticky => "ew", :pady => 10, :padx => 5
eOutputfn.grid :column => 1, :row => 2, :columnspan => 6, :sticky => 'we', :pady => 10, :padx => 5

bBrowseIn.grid :column => 7, :row => 1, :sticky => 'we', :pady => 5, :padx => 5
bBrowseOut.grid :column => 7, :row => 2, :sticky => 'we', :pady => 5, :padx => 5
bSubmit.grid :column => 7, :row => 3, :sticky => 'we', :pady => 5, :padx => 5

lOut.grid :column => 0, :row => 2, :sticky => 'w', :pady => 5, :padx => 10
lIn.grid :column => 0, :row => 1, :sticky => 'w', :pady => 5, :padx => 10

###################################################################################################
# Miscellaneous UI-related Functions
###################################################################################################

# Throw up an error window
def error( text, die=false )
  Tk::messageBox :message => text

  exit if die
end

##Unused
# Intended to be a console window so you can monitor progress
def prepareOutputWin( root )
  window = TkToplevel.new root
  window['title'] = "Conversion Details"
  window['geometry'] = "400x500"

  text = TkText.new window do
    width 350
    height 400
    state 'disabled'
    wrap 'none'
    borderwidth 1
  end

  eCancel = TkButton.new window

  eCancel_click = Proc.new do
  end

  eCancel = TkButton.new window do
    text "Cancel"
  end
  eCancel.comman = eCancel_click

  window.grid :row => 0, :column => 0, :rowspan => 6, :columnspan => 1
  text.grid :row => 0, :column => 0, :rowspan => 5
  eCancel.grid :row => 5, :column => 0
end
