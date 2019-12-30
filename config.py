#################################
## MyBanker Configuration File ##
#################################

# Whether initial installation wizard ran and configured the application
# done - Initial setup is completed and the app is ready to use
# pending - Initial setup not completed and application will lauch setup wizard 
#           next time the site is accessed
## IMPORTANT: DON'T EDIT THIS OPTION. IT WILL BE HANDLED BY THE APP ##
INITIAL_SETUP = 'pending'

# ---------------- #
# DATABASE DETAILS
# ---------------- #
MYSQL_DATABASE_USER = 'mybanker'
MYSQL_DATABASE_PASSWORD = 'mybanker'
MYSQL_DATABASE_HOST = 'mysql'
MYSQL_DATABASE_DB = 'mybanker'

# ------------ #
# MF NAV Stuff #
# ------------ #
MFNAV_LINK = 'http://portal.amfiindia.com/spages/NAVALL.txt'
MFNAV_FILE = '/tmp/mybanker_mfnav'
