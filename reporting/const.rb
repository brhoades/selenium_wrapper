# Reporting Constants
R_START             = 0
R_JOB_START         = 1
R_JOB_COMPLETE      = 2
R_JOB_FAIL          = 3
R_STOP              = 4
R_ALIVE             = 5
R_NEW_CHILD         = 6
R_END_CHILD         = 7

# Timeout for how long before an automatically generated run
# is not fair game to join. Also controls how long before a run
# with no recent jobs completed or clients used is terminated.
RUN_TIMEOUT         = 600

# Timeout for how long after we don't hear from a client, that they
# are deactivated.
CLIENT_TIMEOUT      = 180

# Whether we require a project prefix
PROJECT_PREFIX_REQ  = true

