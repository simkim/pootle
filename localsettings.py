from pootle.install_dirs import *

# This file contains the configuration settings for the Pootle server.

#Example for google as an external smtp server
#DEFAULT_FROM_EMAIL = 'DEFAULT_USER@YOUR_DOMAIN.com'
#EMAIL_HOST_USER = 'USER@YOUR_DOMAIN.com'
#EMAIL_HOST_PASSWORD = 'YOUR_PASSWORD'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True

DATABASE_ENGINE = 'sqlite3'                 # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = working_path('dbs/pootle.db') # Or path to database file if using sqlite3.
DATABASE_USER = ''                          # Not used with sqlite3.
DATABASE_PASSWORD = ''                      # Not used with sqlite3.
DATABASE_HOST = ''                          # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''                          # Set to empty string for default. Not used with sqlite3.

STATS_DB_PATH = working_path(os.path.join('dbs', 'stats.db')) # None means the default path

PODIRECTORY = working_path('po')

# Cache Backend settings
#
# By default we use django's in memory cache which is only suitable
# for small deployments. memcached is prefered. for more info check
# http://docs.djangoproject.com/en/1.0/topics/cache/
CACHE_BACKEND = 'locmem:///?max_entries=4096&cull_frequency=5'

# Uncomment to use memcached for caching
# CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

# set this to False, DEBUG mode is only needed when testing beta's or
# hacking pootle
DEBUG = True


# Use the commented definition to authenticate first with Mozilla's LDAP system and then to fall back
# to Django's authentication system.
#AUTHENTICATION_BACKENDS = ('pootle.auth.ldap_backend.LdapBackend', 'django.contrib.auth.backends.ModelBackend',)
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

# LDAP Setup
# The LDAP server.  Format:  protocol://hostname:port
AUTH_LDAP_SERVER = ''
# Anonymous Credentials
AUTH_LDAP_ANON_DN = ''
AUTH_LDAP_ANON_PASS = ''
# Base DN to search
AUTH_LDAP_BASE_DN = ''
# What are we filtering on?  %s will be the username (must be in the string)
AUTH_LDAP_FILTER = ''
# This is a mapping of pootle field names to LDAP fields.  The key is pootle's name, the value should be your LDAP field name.  If you don't use the field
# or don't want to automatically retrieve these fields from LDAP comment them out.  The only required field is 'dn'.
AUTH_LDAP_FIELDS = {
        'dn':'dn',
        #'first_name':'',
        #'last_name':'',
        #'email':''
        }
