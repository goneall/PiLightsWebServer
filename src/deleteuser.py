#!/usr/bin/env python
# Licensed under the Apache 2.0 License
'''
Deletes a user from the database
Usage: deleteuser username
The environment variable LIGHTS_WEB_DATABASE must be set to the path of the database

Created on Nov 13, 2014

@author: Gary O'Neall
'''
import sys
import sqlite3
from hashlib import sha256
from os import path

DB_PATH = path.expandvars('$LIGHTS_WEB_DATABASE')

def usage():
    ''' Prints the usage to the console
    '''
    print "Usage:"
    print "deleteuser username"
    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
        sys.exit(1)
    username = sys.argv[1].strip()
    if not path.isfile(DB_PATH):
        print "Database is not initialized"
        sys.exit(1)
    con = sqlite3.connect(DB_PATH)

    try:
        cursor = con.execute('select id from users where username=?', [username])
        row = cursor.fetchone()
        if not row:
            print "User does not exist"
            sys.exit(1)
        con.execute('delete from users where username=?', [username])
        print 'user deleted'
    except Exception as ex:
        print "Error updating database: "+str(ex)
    finally:
        con.commit()
        con.close()
