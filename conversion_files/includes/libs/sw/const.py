####################################################################################################
# Child Queue Results
#   Used to communicate via pool's childQueue in the first array slot.
FAILED         = 0
DONE           = 1
READY          = 2
STATUS_UP      = 3
####################################################################################################



####################################################################################################
# Pool Data Indicies
#   These are stored in pool.data and per child. Failures/Successes store number of each,
#   while times is another array that stores all the time taken for each child.
FAILURES       = 0
SUCCESSES      = 1
STATUS         = 2
TIMES          = 3
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
INFO           = -1
NOTICE         = 0
WARNING        = 1
ERR            = 2
CRITICAL       = 3
NONE           = 5
####################################################################################################



####################################################################################################
# Status Types
#   Statuses for children which coordinate with colors.
STAT_LOAD      = 1
STAT_START     = 2
STAT_GOOD      = 3
STAT_ERROR     = 4
STAT_WAIT      = 5
STAT_DONE      = 6
STAT_FINISH    = 7 # Finished a job
#unused
STAT_DEAD      = 10
####################################################################################################
