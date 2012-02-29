# Copyright 2012 Jake Basile
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import keyring
import getpass
import urllib2
import reap.api.timesheet
from reap.commands.support import *

STATUS_TASK_FORMAT = '''Project:    {entry.project_name}
Task:       {entry.task_name}
ID:         {entry.id}
Notes:      {entry.notes}
Time:       {hours}:{minutes:02d}
'''

# def save_bookmarks(bookmarks):
#     with open(expanduser('~/.reapbkmrks'), 'w') as file:
#         dump(bookmarks, file)
#
# def load_bookmarks():
#     path = expanduser('~/.reapbkmrks')
#     if exists(path):
#         with open(path, 'r') as file:
#             return load(file)
#     else:
#         return {}

def get_timesheet():
    info = load_info()
    if info:
        base_uri = info[0]
        username = info[1]
        passwd = keyring.get_password(base_uri, username)
        return reap.api.timesheet.Timesheet(base_uri, username, passwd)

def login(args):
    password = getpass.getpass()
    try:
        ts = reap.api.timesheet.Timesheet(args.baseuri, args.username, password)
    except ValueError:
        print 'Invalid Credentials.'
        return
    except urllib2.URLError:
        print 'Unable to communicate. Check information and try again.'
        return
    keyring.set_password(args.baseuri, args.username, password)
    save_info(args.baseuri, args.username)
    print 'You are now logged in.'

def status(args):
    ts = get_timesheet()
    if ts:
        total = 0
        running_entry = None
        stopped_entries = []
        for entry in ts.entries():
            if entry.started:
                running_entry = entry
            else:
                stopped_entries += [entry]
            total += entry.hours
        if running_entry:
            print '# Currently Running Timer:'
            print str.format(
                STATUS_TASK_FORMAT,
                entry = running_entry,
                hours = int(running_entry.hours),
                minutes = int(running_entry.hours % 1 * 60),
            )
        if len(stopped_entries) > 0:
            print '# Stopped Entries:'
            for entry in stopped_entries:
                print str.format(
                    STATUS_TASK_FORMAT,
                    entry = entry,
                    hours = int(entry.hours),
                    minutes = int(entry.hours % 1 * 60),
                )
        if total:
            total_hours = int(total)
            total_minutes = int(total % 1 * 60)
            print str.format('# Total Daily Hours: {}:{:02d}\n', total_hours, total_minutes)

# def bookmark(args):
#     ts = get_timesheet()
#     if ts:
#         bookmark_entry = None
#         for entry in ts.entries():
#             if entry.id == int(args.entryid):
#                 bookmark_entry = entry
#         if bookmark_entry:
#             bookmarks = load_bookmarks()
#             bookmarks[args.name] = (args.entryid, bookmark_entry.project_name, bookmark_entry.task_name)
#             save_bookmarks(bookmarks)
#             print 'Bookmark added.'
#         else:
#             print 'No such task on your timesheet.'
#
# def bookmarks(args):
#     bookmarks = load_bookmarks()
#     if len(bookmarks) > 0:
#         for key in bookmarks.keys():
#             bkmk = bookmarks[key]
#             print str.format('{}: {bkmk[0]} ({bkmk[1]} - {bkmk[2]})', key, bkmk = bkmk)

def start(args):
    ts = get_timesheet()
    if ts:
        found = None
        id = int(args.entryid)
        for entry in ts.entries():
            if entry.id == id:
                found = entry
                break
        if found:
            if found.started:
                print 'Entry timer already started.'
            else:
                entry.start()
                print 'Entry timer started.'
        else:
            print 'No entry with that ID.'

def stop(args):
    ts = get_timesheet()
    if ts:
        found = None
        for entry in ts.entries():
            if entry.started:
                found = entry
                break
        if found:
            found.stop()
            print 'Entry timer stopped.'
        else:
            print 'No timers to stop.'

def list(args):
    ts = get_timesheet()
    if ts:
        print '# Projects and Tasks:'
        for proj in ts.projects():
            print proj.name
            for task in proj.tasks():
                print str.format('|----{} ({} {})', task.name, proj.id, task.id)
            print ''

def create(args):
    ts = get_timesheet()
    if ts:
        dec_time = 0.0
        if args.time:
            split = args.time.split(':')
            hours = float(split[0])
            minutes = float(split[1])
            dec_time = hours + minutes / 60
        notes = args.notes or ''
        for proj in ts.projects():
            if proj.id == int(args.projectid):
                for task in proj.tasks():
                    if task.id == int(args.taskid):
                        entry = ts.entries().create(task, hours = dec_time, notes = notes)
                        print '# Added entry:'
                        print str.format(
                            STATUS_TASK_FORMAT,
                            entry = entry,
                            hours = int(entry.hours),
                            minutes = int(entry.hours % 1 * 60),
                        )
                        return
        print 'No project/task found with those IDs.'

def delete(args):
    ts = get_timesheet()
    if ts:
        found = None
        for entry in ts.entries():
            if entry.id == int(args.entryid):
                found = entry
                break
        if found:
            found.delete()
            print 'Entry deleted.'
        else:
            print 'No entry with that ID.'

def update(args):
    ts = get_timesheet()
    if ts:
        found = None
        for entry in ts.entries():
            if entry.id == int(args.entryid):
                found = entry
                break
        if found:
            time = entry.hours
            proj_id = entry.project_id
            task_id = entry.task_id
            notes = entry.notes
            # check for notes
            if args.notes:
                if args.append:
                    notes = entry.notes + args.notes
                else:
                    notes = args.notes
            # check for time
            if args.time:
                split = args.time.split(':')
                hours = float(split[0])
                minutes = float(split[1])
                time = hours + minutes / 60
                if args.append:
                    time = entry.hours + time
            # check for task.
            if args.task:
                found_task = None
                for proj in ts.projects():
                    if proj.id == int(args.task[0]):
                        for task in proj.tasks():
                            if task.id == int(args.task[1]):
                                found_task = task
                                break
                if found_task:
                    proj_id = args.task[0]
                    task_id = args.task[1]
                else:
                    print 'No such project and task ID. Abort.'
                    return
            entry.update(notes, time, proj_id, task_id)
            print '# Updated entry:'
            print str.format(
                STATUS_TASK_FORMAT,
                entry = entry,
                hours = int(entry.hours),
                minutes = int(entry.hours % 1 * 60),
            )
        else:
            print 'No entry with that ID.'
