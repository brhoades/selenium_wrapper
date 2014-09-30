# Takes in an Array of ranges. The ranges must be continuous and will be
# evaluated per integer. Returns a Hash where each key represents the # of
# ranges which include that key.
def tally_range( ranges )
  r = Hash.new

  ranges.each do |range|
    range.to_a.each do |i|
      if not r.has_key? i
        r[i] = 1
      else
        r[i] += 1
      end
    end
  end

  r
end

# Just an alias for taking the max of our sumed range values
def max_tallied_range( ranges )
  tally_range( ranges ).values.max
end

def avg_tallied_range( ranges )
  r = tally_range( ranges )
  r.values.reduce( :+ ).to_f / r.size
end
