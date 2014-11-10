####################################################################################################
# Child Queue Results
#   Used to communicate via pool's childQueue in the first array slot.
FAILED         = 0
DONE           = 1
READY          = 2
DISPLAY        = 3
STATUS         = 4
####################################################################################################



####################################################################################################
# Pool Data Indicies
#   These are stored in pool.data and per child. Failures/Successes store number of each,
#   while times is another array that stores all the time taken for each child.
FAILURES       = 0
SUCCESSES      = 1
DISPLAY        = 2
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
EXTRA1         = 4
####################################################################################################



####################################################################################################
# Error Log Levels
#   Error log levels are used to mark a message as a certain category, then output it if that level
#   of detail is requested.
INFO           = -1
DEBUG          = -1
NOTICE         = 0
WARNING        = 1
ERR            = 2
CRITICAL       = 3
NONE           = 5
####################################################################################################



####################################################################################################
# Universal Status Types
# Statuses used program wide to more easily determine statuses.
####################################################################################################
STARTING       = 0  # Is currently starting up, not quite running yet
RUNNING        = 1  # Running properly
PAUSED         = 2  # In a paused state but ready to continue.
STOPPED        = 3  # Shut down and will need to be fully restarted.
FINISHED       = 4  # Stopped but automatically due to lack of work.
ERRORED        = 5  # Stopped but due to a major error
####################################################################################################



####################################################################################################
# Display types
#   Display options for children which coordinate with colors.
DISP_LOAD      = 1
DISP_START     = 2
DISP_GOOD      = 3
DISP_ERROR     = 4
DISP_WAIT      = 5
DISP_DONE      = 6
DISP_FINISH    = 7 # Finished a job
#unused
DISP_DEAD      = 10
####################################################################################################



####################################################################################################
# Reporting Constants
R_START             = "POOL START"
R_JOB_START         = "JOB START"
R_JOB_COMPLETE      = "JOB FINISH"
R_JOB_FAIL          = "JOB ERROR"
R_STOP              = "POOL STOP"
R_NEW_CHILD         = "NEW CHILD"
R_END_CHILD         = "END CHILD"
####################################################################################################
