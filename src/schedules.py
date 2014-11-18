#!/usr/bin/env python
'''
Licensed under the Apache 2.0 License

Scheduler for the timer operation
The Schedule Class manages the schedule and uses the database to check when the next
scheduled event is to occur.
Created on Nov 16, 2014

@author: Gary O'Neall
'''
from threading import Thread, Event
from datetime import datetime, timedelta
from sys import argv
from os import path
import lightsinterface
import logging
import sqlite3

class Scheduler(Thread):
    '''
    Main class for managing the schedule for the lights
    '''
    
    FUDGE_MINUTES = timedelta(minutes=3)   # Number of minutes within the current time that we will go ahead and execute the action

    def __init__(self, db_path):
        '''
        Constructor for Scheduler
        db_path is the file path the the SQL database containing the schedule table
        '''
        Thread.__init__(self)
        self.setDaemon(True)
        self.db = db_path
        self.schedule_update_event = Event()
        
    def schedule_updated(self):
        '''
        Signals that the schedule has been updated
        '''
        self.schedule_update_event.set()
        
    def run(self):
        '''
        Main run method for the Thread.  Performs the next scheduled action at
        the designated time.
        '''
        print 'starting run'
        errors = 0
        max_errors = 10
        last_action = None
        while errors <= max_errors:
            print 'getting next action'
            next_action = self.__get_next_action(last_action)
            if self.__time_to_execute(next_action):
                if next_action != last_action:
                    try:
                        logging.info(self.get_action_description(next_action))
                        print self.get_action_description(next_action)
                        self.__execute_action(next_action)
                        last_action = next_action
                    except Exception as ex:
                        logging.exception(ex)
                        logging.error('Error executing scheduled event')
                        errors = errors + 1
                else:
                    print 'waiting fudge minutes'
                    self.schedule_update_event.wait(self.FUDGE_MINUTES.seconds)
                    self.schedule_update_event.clear()
            else:
                time_to_wait = self.__time_to_action(next_action)
                print 'waiting '+str(time_to_wait)
                self.schedule_update_event.wait(time_to_wait)
                self.schedule_update_event.clear()
 
    def __time_to_action(self, action):
        '''
        Calcuate the time in seconds before the next action is to be executed
        '''
        if action == None:
            return timedelta.max.seconds
        else:
            time_to_action = action['schedtime'] - datetime.now()
            if time_to_action.seconds < 0:
                return 0
            else:
                return time_to_action.seconds
        
    def __execute_action(self, action):
        '''
        Execute the action
        '''
        if action['turnon']:
            lightsinterface.lights_on()
        elif action['turnoff']:
            lightsinterface.lights_off()
        elif action['startplaylist']:
            lightsinterface.start_playlist()
        elif action['stopplaylist']:
            lightsinterface.stop_playlist()
           
    def get_action_description(self, action):
        if action['turnon']:
            return 'Turn On'
        elif action['turnoff']:
            return 'Turn Off'
        elif action['startplaylist']:
            return 'Start Playlist'
        elif action['stopplaylist']:
            return 'Stop Playlist'
        else:
            return 'Unknown'
                  
    def __time_to_execute(self, next_action):
        '''
        Returns True if it is time to exeucte the next action
        '''
        if next_action == None:
            return False
        return (datetime.now() + self.FUDGE_MINUTES) > next_action['schedtime']
        
        
    def __get_next_action(self, last_action):
        con = sqlite3.connect(self.db)
        try:
            cursor = con.execute('select id, day, hour, minute, turnon, turnoff, startplaylist, stopplaylist from schedule order by day,hour,minute')
            rows = cursor.fetchall()
            scheduled_actions = []
            now = datetime.now()
            for row in rows:
                scheduled_actions.append(dict(id=row[0], schedtime=self.__to_date(now, self.__day_to_num(row[1]), row[2], row[3]),
                                              turnon=row[4], turnoff=row[5], startplaylist=row[6], stopplaylist=row[7]))
            scheduled_actions = sorted(scheduled_actions, key=lambda sched: sched['schedtime'])

            i = 0
            while i < len(scheduled_actions) and (scheduled_actions[i] == last_action or scheduled_actions[i]['schedtime'] < now):
                i = i + 1
            if i < len(scheduled_actions):
                return scheduled_actions[i]
            else:
                return None
        finally:
            con.close()
     
    def __day_to_num(self, day_str):
        day_lower = day_str.strip().lower()
        if day_lower == 'monday':
            return 0
        elif day_lower == 'tuesday':
            return 1
        elif day_lower == 'wednesday':
            return 2
        elif day_lower == 'thursday':
            return 3
        elif day_lower == 'friday':
            return 4
        elif day_lower == 'saturday':
            return 5
        else:
            return 6
        
    def __to_date(self, start_date, daynum, hour, minute):  
        ''' Converts a day number (day of week 0 being Monday), hour and minute to a date time
         based on the start_date - ie: if the start day is day 3, then a daynum of 0 will be 5 days later
         '''
        start_day_of_week = start_date.weekday()
        if daynum < start_day_of_week:
            start_day_of_week = start_day_of_week - 7
        days_to_add = daynum - start_day_of_week
        retval = datetime(start_date.year, start_date.month, start_date.day, hour, minute) + timedelta(days_to_add)
        return retval
    
if __name__ == "__main__":
    '''
    Start up the scheduler
    '''
    if len(argv) != 2:
        print 'Invalid arguments'
        print 'Usage: schedule dbpath'
        exit(1)
    dbpath = path.expandvars(argv[1].strip())
    if not path.isfile(dbpath):
        print 'Database does not exist: '+dbpath
        exit(1)
    scheduler = Scheduler(dbpath)
    print 'Starting scheduler.  Press enter to have the notify the scheduler of any updates.  Enter STOP to exit'
    scheduler.start()
    cmd = raw_input("Enter to update scheduler or STOP to end:")
    while cmd.strip() != 'STOP':
        cmd = raw_input("Enter to update scheduler or STOP to end:")
    
