require 'digest/md5'

# Idea behind this is that it's very expensive to calculate run statistics (mainly tallying).
# So we create a sort of checksum/hash of the data used. This way when we come across a check
# if the data is up to date, it's just a simple comparsion.
#
# This is passed in a zipped 2d array where each index is an individual run with its # of children
# and jobs.
def get_checksum( data )
  largest = 1

  # Find the largest number and buffer the others with zeros to avoid possible collisions
  data.flatten.map { |i| next if i == nil or i < 1; largest = Math.log10(i).ceil if( Math.log10(i).ceil > largest ) }

  # Now smash our data together while making sure all the numbers are padded equal to the max
  c = data.map{ |p| p.map { |i| i.to_s.ljust largest } }.flatten.join "!"

  # And return a md5sum
  Digest::MD5.hexdigest c
end  
