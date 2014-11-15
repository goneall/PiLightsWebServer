#!/usr/bin/env python
# Licensed under the Apache 2.0 License
'''
Add a user to the database
Usage: adduser username password
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
    ''' Pprints the usage to the console
    '''
    print "Usage:"
    print "adduser username password"
    
if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)
    username = sys.argv[1].strip()
    password = sys.argv[2].strip()
    password_hash = sha256(password)
    password_dig = password_hash.hexdigest()
    if not path.isfile(DB_PATH):
        print "Database is not initialized"
        sys.exit(1)
    con = sqlite3.connect(DB_PATH)

    try:
        cursor = con.execute('select id from users where username=?', [username])
        row = cursor.fetchone()
        if row:
            print "User already exists"
            sys.exit(1)
        con.execute('insert into users (username, password) values (?, ?)', [username, password_dig])
        print 'user added'
    except Exception as ex:
        print "Error updating database: "+str(ex)
    finally:
        con.commit()
        con.close()