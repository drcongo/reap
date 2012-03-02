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
import reap.api.admin
import datetime
from reap.commands.support import *

PERSON_FORMAT = '''Name:           {person.first_name} {person.last_name}
ID:             {person.id}
Department:     {person.department}
Admin:          {person.admin}
Contractor:     {person.contractor}
Rate:           {person.default_rate}
'''

CLIENT_FORMAT = '''Name:           {client.name}
ID:             {client.id}
Details:        {client.details}
'''

PROJECT_FORMAT = '''Name:       {project.name}
ID:         {project.id}
ClientID:   {project.client_id}
Billable:   {project.billable}
Bill-By:    {project.bill_by}
Rate:       {project.hourly_rate}
Budget:     {project.budget}
Notes:      {project.notes}
'''

HOURS_REPORT_FORMAT = '''Name:           {person.first_name} {person.last_name}
ID:             {person.id}
Total Hours:    {total}
Billable:       {billable}
Non-billable:   {unbillable}
Ratio:          {ratio}
'''

def get_harvest():
    info = load_info()
    if info:
        base_uri = info[0]
        username = info[1]
        passwd = keyring.get_password(base_uri, username)
        return reap.api.admin.Harvest(base_uri, username, passwd)

def list_people(args):
    hv = get_harvest()
    if hv:
        contractors = []
        employees = []
        for person in hv.people():
            if person.contractor:
                contractors += [person]
            else:
                employees += [person]
        if len(employees) > 0:
            print '# Employees'
            for emp in employees:
                print str.format(PERSON_FORMAT, person = emp)
        if len(contractors) > 0:
            print '# Contractors'
            for contractor in contractors:
                print str.format(PERSON_FORMAT, person = contractor)

def create_person(args):
    hv = get_harvest()
    if hv:
        person = hv.create_person(
            args.firstname,
            args.lastname,
            args.email,
            admin = args.admin or False,
            contractor = args.contractor or False,
            department = args.department,
            default_rate = float(args.rate) if args.rate else None,
        )
        if person:
            print '# Created person:'
            print str.format(
                PERSON_FORMAT,
                person = person,
            )
        else:
            print 'Could not create person.'

def delete_person(args):
    hv = get_harvest()
    if hv:
        id = int(args.personid)
        for person in hv.people():
            if person.id == int(id):
                person.delete()
                print 'Person deleted.'
                break

def list_clients(args):
    hv = get_harvest()
    if hv:
        active = []
        inactive = []
        for client in hv.clients():
            if client.active:
                active += [client]
            else:
                inactive += [client]
        if len(active) > 0:
            print '# Active Clients'
            for act in active:
                print str.format(CLIENT_FORMAT, client = act)
        if len(inactive) > 0:
            print '# Inactive Clients'
            for inact in inactive:
                print str.format(CLIENT_FORMAT, client = inact)

def list_projects(args):
    hv = get_harvest()
    if hv:
        active = []
        inactive = []
        for proj in hv.projects():
            if proj.active:
                active += [proj]
            else:
                inactive += [proj]
        if len(active) > 0:
            print '# Active Projects'
            for act in active:
                print str.format(PROJECT_FORMAT, project = act)
        if len(inactive) > 0:
            print '# Inactive Projects'
            for inact in inactive:
                print str.format(PROJECT_FORMAT, project = inact)

def create_project(args):
    hv = get_harvest()
    if hv:
        project = hv.create_project(
            args.name,
            args.clientid,
            budget = args.budget if hasattr(args, 'budget') else None,
            notes = args.notes if hasattr(args, 'notes') else None,
            budget_by = args.budgetby if hasattr(args, 'budgetby') else 'none',
            bill_by = args.billby if hasattr(args, 'billby') else 'none',
        )
        if project:
            print '# Created Person:'
            print str.format(PROJECT_FORMAT, project = project)

def delete_project(args):
    hv = get_harvest()
    if hv:
        for project in hv.projects():
            if project.id == args.projectid:
                project.delete()
                print 'Project Deleted.'
                break

def hours_report(args):
    hv = get_harvest()
    if hv:
        people = []
        for pid in set(args.personids):
            id = int(pid)
            for p in hv.people():
                if p.id == id:
                    people += [p]
                    break
        if len(people) > 0:
            if args.start:
                start = datetime.datetime.strptime(args.start, '%Y%m%d')
            else:
                start = datetime.datetime.today()
            if args.end:
                end = datetime.datetime.strptime(args.end, '%Y%m%d')
            else:
                end = datetime.datetime.today()
            entries_collection = [
                (person, person.entries(start = start, end = end))
                for person in people
            ]
            if len(entries_collection) > 0:
                print str.format(
                    '# Hours Report for {} - {}',
                    start.strftime('%Y%m%d'),
                    end.strftime('%Y%m%d'),
                )
                projects = hv.projects()
                for person, entries in entries_collection:
                    map = {p: [] for p in projects}
                    for entry in entries:
                        for proj in map.keys():
                            if proj.id == entry.project_id:
                                map[proj] += [entry]
                                break;
                    total = 0.0
                    billable = 0.0
                    unbillable = 0.0
                    for proj in map.keys():
                        proj_total = 0.0
                        for entry in map[proj]:
                            proj_total += entry.hours
                        if proj.billable:
                            billable += proj_total
                        else:
                            unbillable += proj_total
                        total += proj_total
                    ratio = billable / unbillable if unbillable > 0.0 else 'Undef.'
                    print str.format(
                        HOURS_REPORT_FORMAT,
                        total = total,
                        billable = billable,
                        unbillable = unbillable,
                        ratio = ratio,
                        person = person,
                    )
            else:
                print 'No entries for that time period.'
        else:
            print 'No such person ID.'
