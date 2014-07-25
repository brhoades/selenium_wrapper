####################################################################################################
# Child Queue Results
#   Used to communicate via pool's childQueue in the first array slot.
FAILED         = 0
DONE           = 1
READY          = 2 
####################################################################################################

####################################################################################################
# Pool Data Indicies
#   These are stored in pool.data and per child. Failures/Successes store number of each,
#   while times is another array that stores all the time taken for each child.
FAILURES       = 0
SUCCESSES      = 1
TIMES          = 2
####################################################################################################

####################################################################################################
# Child Queue Indicies
#   For a child queue result, which is an array, you have the child number, the result (see the 
#   "Child Queue Results" for types), the time taken, and then the error message if there is one.
NUMBER         = 0
RESULT         = 1 
TIME           = 2
ERROR          = 3
####################################################################################################

####################################################################################################
# Error Log Levels
#   Error log levels are used to mark a message as a certain category, then output it if that level
#   of detail is requested.
NOTICE         = 0
WARNING        = 1
ERROR          = 2
CRITICAL       = 3
NONE           = 5
####################################################################################################
