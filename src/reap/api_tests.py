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

import unittest
import random
import string
import datetime
from reap.api import *

def random_string(length = 5):
    return ''.join(random.choice(string.ascii_lowercase) for x in xrange(length))

class TimesheetTest(unittest.TestCase):
    def setUp(self):
        # You need to have valid account info in an info.txt file to run tests.
        with open('info.txt') as info:
            self.base_uri = info.readline().strip()
            self.username = info.readline().strip()
            self.password = info.readline().strip()
        self.ts = Timesheet(self.base_uri, self.username, self.password)

class TestTimesheetLogin(TimesheetTest):
    def runTest(self):
        ts = Timesheet(self.base_uri, self.username, self.password)
        self.assertIsNotNone(ts)
        self.assertRaises(ValueError, Timesheet, random_string(), random_string(), random_string())

class TestProjectTask(TimesheetTest):
    def test_get_projects(self):
        projs = self.ts.projects()
        self.assertIsNotNone(projs)
        self.assertTrue(len(projs) > 0)
        for proj in projs:
            self.assertIsNotNone(proj.name)
            self.assertIsNotNone(proj.client)
            self.assertIsNotNone(proj.id)

    def test_get_tasks(self):
        projs = self.ts.projects()
        for proj in projs:
            tasks = proj.tasks()
            self.assertIsNotNone(tasks)
            self.assertTrue(len(tasks) > 0)
            for task in tasks:
                self.assertEqual(task.project.id, proj.id)
                self.assertIsNotNone(task.name)
                self.assertIsNotNone(task.id)
                self.assertIsNotNone(task.billable)

class TestEntry(TimesheetTest):
    def test_get(self):
        entries = self.ts.entries()
        self.assertIsNotNone(entries)
        for entry in entries:
            self.assertIsNotNone(entry.id)
            self.assertIsNotNone(entry.spent_at)
            self.assertIsNotNone(entry.user_id)
            self.assertIsNotNone(entry.client_name)
            self.assertIsNotNone(entry.project_id)
            self.assertIsNotNone(entry.project_name)
            self.assertIsNotNone(entry.task_id)
            self.assertIsNotNone(entry.task_name)
            self.assertIsNotNone(entry.hours)
            self.assertIsNotNone(entry.notes)
            if entry.started:
                self.assertIsNotNone(entry.timer_started)
                self.assertIsNotNone(entry.timer_created)
                self.assertIsNotNone(entry.timer_updated)

    def test_create(self):
        project = self.ts.projects()[0]
        task = project.tasks()[0]
        entry = self.ts.entries().create(task)
        self.assertIsNotNone(entry)
        self.assertTrue(entry.started)
        self.assertEqual(entry.project_id, project.id)
        self.assertTrue((entry.timer_created - datetime.datetime.utcnow()) < datetime.timedelta(minutes = 1))
        # clean up
        entry.delete()

    def test_delete(self):
        entries_count = len(self.ts.entries())
        entry = self.ts.entries().create(self.ts.projects()[0].tasks()[0])
        self.assertEqual(entries_count + 1, len(self.ts.entries()))
        entry.delete()
        self.assertEqual(entries_count, len(self.ts.entries()))

    def test_update_notes(self):
        project = self.ts.projects()[0]
        task = project.tasks()[0]
        entry = self.ts.entries().create(task)
        orig_notes = entry.notes
        new_note = random_string()
        entry.update(notes = new_note)
        self.assertEqual(new_note, entry.notes)
        # make sure it propagated to the server.
        new_entry = None
        for test_entry in self.ts.entries():
            if entry.id == test_entry.id:
                new_entry = test_entry
        self.assertIsNotNone(new_entry)
        self.assertEqual(new_entry.notes, new_note)
        entry.delete()

    def test_update_hours(self):
        project = self.ts.projects()[0]
        task = project.tasks()[0]
        entry = self.ts.entries().create(task)
        orig_hours = entry.hours
        new_hours = random.randint(0, 23)
        entry.update(hours = new_hours)
        self.assertEqual(new_hours, entry.hours)
        # make sure it propagated to the server.
        new_entry = None
        for test_entry in self.ts.entries():
            if entry.id == test_entry.id:
                new_entry = test_entry
        self.assertIsNotNone(new_entry)
        self.assertEqual(new_entry.hours, new_hours)
        entry.delete()

    def test_update_project(self):
        projects = self.ts.projects()
        project = projects[0]
        task = project.tasks()[0]
        new_proj = projects[1]
        new_task = new_proj.tasks()[0]
        entry = self.ts.entries().create(task)
        entry.update(project_id = new_proj.id, task_id = new_task.id)
        self.assertEqual(new_proj.id, entry.project_id)
        self.assertEqual(new_proj.name, entry.project_name)
        self.assertEqual(new_task.id, entry.task_id)
        self.assertEqual(new_task.name, entry.task_name)
        # make sure it propagated to the server.
        new_entry = None
        for test_entry in self.ts.entries():
            if entry.id == test_entry.id:
                new_entry = test_entry
        self.assertIsNotNone(new_entry)
        self.assertEqual(new_entry.project_id, new_proj.id)
        self.assertEqual(new_entry.task_id, new_task.id)
        entry.delete()

    def test_timer(self):
        project = self.ts.projects()[0]
        task = project.tasks()[0]
        entry = self.ts.entries().create(task)
        # it starts out running after creation.
        self.assertTrue(entry.started)
        entry.stop()
        self.assertFalse(entry.started)
        # make sure it propagated to the server.
        new_entry = None
        for test_entry in self.ts.entries():
            if entry.id == test_entry.id:
                new_entry = test_entry
        self.assertIsNotNone(new_entry)
        self.assertFalse(new_entry.started)
        # start it again.
        entry.start()
        self.assertTrue(entry.started)
        # make sure it propagated to the server.
        new_entry = None
        for test_entry in self.ts.entries():
            if entry.id == test_entry.id:
                new_entry = test_entry
        self.assertIsNotNone(new_entry)
        self.assertTrue(new_entry.started)
        entry.delete()

class HarvestTest(unittest.TestCase):
    def setUp(self):
        # You need to have valid account info in an info.txt file to run tests.
        with open('info.txt') as info:
            self.base_uri = info.readline().strip()
            self.username = info.readline().strip()
            self.password = info.readline().strip()
        self.hv = Harvest(self.base_uri, self.username, self.password)

class TestHarvestLogin(HarvestTest):
    def runTest(self):
        hv = Harvest(self.base_uri, self.username, self.password)
        self.assertIsNotNone(hv)
        self.assertRaises(ValueError, Harvest, random_string(), random_string(), random_string())

class TestPeople(HarvestTest):
    def test_get(self):
        people = self.hv.people()
        self.assertIsNotNone(people)
        for person in people:
            self.assertIsNotNone(person)
            self.assertIsNotNone(person.id)
            self.assertIsNotNone(person.email)
            self.assertIsNotNone(person.first_name)
            self.assertIsNotNone(person.last_name)
            self.assertIsNotNone(person.all_future)
            self.assertIsNotNone(person.active)
            self.assertIsNotNone(person.admin)
            self.assertIsNotNone(person.contractor)
            self.assertIsNotNone(person.telephone)
            self.assertIsNotNone(person.timezone)
            # optional ones
            # self.assertIsNotNone(person.department)
            # self.assertIsNotNone(person.default_rate)

    def test_create(self):
        fn = random_string()
        ln = random_string()
        email = random_string() + '@example.com'
        contractor = bool(random.getrandbits(1))
        admin = bool(random.getrandbits(1))
        department = random_string()
        default_rate = random.random() * 10
        person = self.hv.people().create(
            fn,
            ln,
            email,
            contractor = contractor,
            admin = admin,
            department = department,
            default_rate = default_rate,
        )
        self.assertIsNotNone(person)
        self.assertIsNotNone(person)
        self.assertIsNotNone(person.id)
        self.assertIsNotNone(person.email)
        self.assertEqual(person.email, email)
        self.assertIsNotNone(person.first_name)
        self.assertEqual(person.first_name, fn)
        self.assertIsNotNone(person.last_name)
        self.assertEqual(person.last_name, ln)
        self.assertIsNotNone(person.all_future)
        self.assertIsNotNone(person.active)
        self.assertIsNotNone(person.admin)
        self.assertEqual(person.admin, admin)
        self.assertIsNotNone(person.contractor)
        self.assertEqual(person.contractor, contractor)
        self.assertIsNotNone(person.telephone)
        self.assertIsNotNone(person.timezone)
        # clean up
        person.delete()

    def test_delete(self):
        person = self.hv.people().create(
            random_string(),
            random_string(),
            random_string() + '@example.com',
        )
        self.assertIsNotNone(person)
        id = person.id
        person.delete()
        # ensure it's no longer there.
        for p in self.hv.people():
            if p.id == id:
                self.fail()



if __name__ == '__main__':
    unittest.main()
