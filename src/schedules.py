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
    
    FUDGE_MINUTES = timedelta(minutes=1)   # Number of minutes within the current time that we will go ahead and execute the action
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
        errors = 0
        max_errors = 10
        while errors <= max_errors:
            next_action = self.__get_next_action()
            logging.debug('Next action='+str(next_action))
            if self.__time_to_execute(next_action):
                try:
                    logging.info(self.get_action_description(next_action))
                    self.__execute_action(next_action)
                except Exception as ex:
                    logging.error('Error executing scheduled event')
                    logging.exception(ex)
                    errors = errors + 1
            else:
                time_to_wait = self.__time_to_action(next_action)
                now = datetime.now()
                logging.debug('now=' +str(now))
                logging.debug('waiting '+str(time_to_wait))
                self.schedule_update_event.wait(time_to_wait)
                self.schedule_update_event.clear()
                logging.debug('waited='+str(datetime.now()-now))
 
    def __time_to_action(self, action):
        '''
        Calcuate the time in seconds before the next action is to be executed
        '''
        if action == None:            # Wait one day to roll over
            return timedelta(days=1).total_seconds()
        else:
            time_to_action = action['schedtime'] - datetime.now()
            if time_to_action.seconds < 0:
                logging.warn('Less than 0 seconds for action '+str(action))
                return 0
            else:
                return time_to_action.total_seconds()
        
    def __execute_action(self, action):
        '''
        Execute the action
        '''
        if action['action'] == 'turnon':
            lightsinterface.lights_on()
        elif action['action'] == 'turnoff':
            lightsinterface.lights_off()
        elif action['action'] == 'startplaylist':
            lightsinterface.start_playlist()
        elif action['action'] == 'stopplaylist':
            lightsinterface.stop_playlist()
        # Update database
        con = sqlite3.connect(self.db)
        try:
            id = action['id']
            now = datetime.now()
            logging.debug('Updating the set schedule for id '+str(id))
            con.execute('update schedule set lastaction=? where id=?', [now, id])
            con.commit()
            cursor = con.execute('select lastaction from schedule where id=?', [id])
            rows = cursor.fetchall()
            if len(rows) == 0:
                logging.error('Update of lastaction failed - no rows')
            else:
                logging.debug('Updated datetime = '+str(rows[0][0]))
        except Exception as ex:
            logging.error('Error updated last action')
            logging.exception(ex)
            con.rollback()
            con.commit()
        finally:
            con.close()
           
    def get_action_description(self, action):
        if action['action'] == 'turnon':
            return 'Turn On'
        elif action['action'] == 'turnoff':
            return 'Turn Off'
        elif action['action'] == 'startplaylist':
            return 'Start Playlist'
        elif action['action'] == 'stopplaylist':
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
        
        
    def __get_next_action(self):
        con = sqlite3.connect(self.db, detect_types=sqlite3.PARSE_DECLTYPES)
        try:
            cursor = con.execute('select id, day, hour, minute, action, lastaction as "[timestamp]" from schedule order by day,hour,minute')
            rows = cursor.fetchall()
            scheduled_actions = []
            now = datetime.now()
            for row in rows:
                scheduled_actions.append(dict(id=row[0], schedtime=self.__to_date(now, self.__day_to_num(row[1]), row[2], row[3]),
                                              action=row[4], lastaction=row[5]))
            scheduled_actions = sorted(scheduled_actions, key=lambda sched: sched['schedtime'])

            i = 0
            while i < len(scheduled_actions) and (self.__executed_today(scheduled_actions[i]) or (scheduled_actions[i]['schedtime'] + self.FUDGE_MINUTES) < now):
                i = i + 1
            if i < len(scheduled_actions):
                return scheduled_actions[i]
            else:
                logging.debug('returning none')
                if (i > 0):
                    logging.debug('last_record=' +str(scheduled_actions[i-1]))
                else:
                    logging.debug('Empty schedule')
                logging.debug('now=' +str(now))
                return None
        finally:
            con.close()
            
    def __executed_today(self, action):
        now_date = datetime.now()
        lastaction = action['lastaction']
        if lastaction == None:
            return False
        if not isinstance(lastaction, datetime):
            lastaction = datetime.strptime(lastaction, 'YYYY-MM-DDTHH.MM.SS.mmmmmm')
        return lastaction.year == now_date.year and lastaction.month == now_date.month and lastaction.day == now_date.day
     
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
    
