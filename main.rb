require 'tk'

root = TkRoot.new 
root.title = "Selenium Script Converter"

content = Tk::Tile::Frame.new root
frame = Tk::Tile::Frame.new( content ) { width 400; height 150; }

lIn = Tk::Tile::Label.new content do
  text 'Input File'
end

$filename = TkVariable.new
eFilename = Tk::Tile::Entry.new content do
  textvariable $filename
end

lOut = Tk::Tile::Label.new content do
  text 'Output Folder'
end

$outputfn = TkVariable.new
eOutputfn = Tk::Tile::Entry.new content do
  textvariable $outputfn
end

bBrowseIn_click = Proc.new do
  eFilename.value = $filename = Tk.getOpenFile

  if $filename != nil and $filename != ""
    if $filename !~ /\.py$/
      Tk::messageBox :message => "Input file must be a python file (end in .py)."
    elsif eOutputfn.value == ""
      fn = /.*([\/\\])([^\\\/\n]+)\.py$/.match( $filename )
      eOutputfn.value = File.dirname( $filename ) + fn[1] + fn[2] + fn[1]
    end
  end
end

bBrowseIn = TkButton.new content do
  text "Browse"
end
bBrowseIn.comman = bBrowseIn_click

bBrowseOut_click = Proc.new do
  eOutputfn.value = $outputfn = Tk.chooseDirectory
end

bBrowseOut = TkButton.new content do
  text "Browse"
end
bBrowseOut.comman = bBrowseOut_click



bSubmit_click = Proc.new do
   
end

bSubmit = TkButton.new content do
  text "Convert"
end
bSubmit.comman = bSubmit_click



content.grid :column => 0, :row => 0
frame.grid :column => 0, :row => 0, :columnspan => 8, :rowspan => 4 

eFilename.grid :column => 1, :row => 1, :columnspan => 6, :sticky => "ew", :pady => 10, :padx => 5
eOutputfn.grid :column => 1, :row => 2, :columnspan => 6, :sticky => 'we', :pady => 10, :padx => 5

bBrowseIn.grid :column => 7, :row => 1, :sticky => 'we', :pady => 5, :padx => 5
bBrowseOut.grid :column => 7, :row => 2, :sticky => 'we', :pady => 5, :padx => 5
bSubmit.grid :column => 7, :row => 3, :sticky => 'we', :pady => 5, :padx => 5

lOut.grid :column => 0, :row => 2, :sticky => 'w', :pady => 5, :padx => 10
lIn.grid :column => 0, :row => 1, :sticky => 'w', :pady => 5, :padx => 10

Tk.mainloop
