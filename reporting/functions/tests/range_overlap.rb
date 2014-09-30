require_relative '../range_overlap.rb'
require 'test/unit'

class RangeOverlapTest < Test::Unit::TestCase
  def setup
    @smallRanges = [ ]
    @largeRanges = [ ]

    100.times do 
      lower = rand(-100..100)
      upper = rand(1000..10000)
      @smallRanges << Range.new( lower, upper )
    end

    100.times do 
      lower = rand(-1000..1000)
      upper = rand(10000..100000)
      @largeRanges << Range.new( lower, upper )
    end
  end

  def test_smallRanges
    r = tally_range @smallRanges 
    
    r.keys.each do |k|
      i = r[k]
      assert( i <= r.size )
      assert( i >= 0 )
      c = 0
      @smallRanges.each do |range|
        c += 1 if( range.member? k )
      end

      assert_equal c, i, "Brute force check for number in range failed to match (this is very bad)."
    end
  end

  def test_largeRanges
    r = tally_range @largeRanges 
    
    r.keys.each do |k|
      i = r[k]
      assert( i <= r.size )
      assert( i >= 0 )
      c = 0
      @largeRanges.each do |range|
        c += 1 if( range.member? k )
      end

      assert_equal c, i, "Brute force check for number in range failed to match (this is very bad)."
    end
  end

end
