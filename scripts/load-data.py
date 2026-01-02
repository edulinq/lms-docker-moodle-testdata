#!/usr/bin/env python3

import datetime
import http
import json
import os
import urllib.parse
import re
import subprocess
import sys
import time

import edq.util.pyimport
import requests

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(THIS_DIR, '..', 'lms-testdata', 'testdata')
LOAD_SCRIPT = os.path.join(THIS_DIR, '..', 'lms-testdata', 'load.py')

ASSIGNMENTS_FILE = os.path.join(DATA_DIR, 'assignments.json')
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
GROUPSETS_FILE = os.path.join(DATA_DIR, 'groupsets.json')
SUBMISSIONS_FILE = os.path.join(DATA_DIR, 'submissions.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

DATA_FILES = [
    USERS_FILE,
    COURSES_FILE,
    ASSIGNMENTS_FILE,
    GROUPSETS_FILE,
    SUBMISSIONS_FILE,
]

SERVER = 'http://127.0.0.1:4000'

USER_ATTRIBUTES = ["username", "firstname", "lastname", "email", "password"]
COURSE_ATTRIBUTES = ["shortname", "fullname", "idnumber", "category", "enrolment_1", "enrolment_2"]

ROLE_MAPPING = {
    "other": "student",  # HACK(JK): Want to use guest but Moodle is not allowing it
    "student": "student",
    "grader": "teacher",
    "admin": "editingteacher",
    "owner": "manager",
}

def run(command, capture_output = False):
    result = subprocess.run(command, shell = True, check = True, capture_output = capture_output)

    if (not capture_output):
        return result

    return result.stdout.decode('utf-8').splitlines()

def run_sql(sql, **kwargs):
    path = "/tmp/sqlcommand"
    with open(path, "w") as file:
        file.write(sql)

    return run(f'mysql moodle < {path}', **kwargs)

def add_users(users):
    path = "/tmp/users.csv" #!!!!!!!!!!!!!!!!! change to proper temp location
    for user in users.values():
        keys = USER_ATTRIBUTES.copy()

        row = [
            user["short-name"],
            user["name"], # Look at this later!
            user["name"], # Look at this later!
            user["email"],
            user["password"],
        ]

        for (i, (course_id, course_info)) in enumerate(user["course-info"].items()):
            keys.append(f"course{i + 1}")
            row.append(course_id)

            keys.append(f"role{i + 1}")
            row.append(ROLE_MAPPING[course_info["role"]])

        with open(path, "w") as file:
            file.write(",".join(keys) + "\n")
            file.write(",".join(row) + "\n")

        if (user["name"] != "server-owner"):
            run(f"php /var/www/html/admin/tool/uploaduser/cli/uploaduser.php --file={path} --mode=addnew")

        sql = f"""
            SELECT id
            FROM mdl_user
            WHERE username = '{user["name"]}'
            ;
        """
        output = run_sql(sql, capture_output = True)
        moodle_user_id = output[1]

        sql = f"""
            UPDATE mdl_user
            SET id = {user["id"]}
            WHERE id = {moodle_user_id}
            ;
        """
        run_sql(sql)

        tables = [
            'mdl_config_log',
            'mdl_files',
            'mdl_logstore_standard_log',
            'mdl_repository_instances',
            'mdl_user_preferences',
            'mdl_user_enrolments',
            'mdl_role_assignments',
        ]

        for table in tables:
            sql = f"""
                UPDATE {table}
                SET userid = {user["id"]}
                WHERE userid = {moodle_user_id}
                ;
            """
            run_sql(sql)


def add_courses(courses):
    path = "/tmp/courses.csv" #!!!!!!!!!!!!!!!!! change to proper temp location
    for course in courses.values():
        row = [
            course["short-name"],
            course["name"],
            course["id"],
            "1",
            "manual",
            "guest",
        ]

        with open(path, "w") as file:
            file.write(",".join(COURSE_ATTRIBUTES) + "\n")
            file.write(",".join(row) + "\n")

        result = run(f"php /var/www/html/admin/tool/uploadcourse/cli/uploadcourse.php --file={path} --mode=createnew", capture_output = True)

        moodle_course_id = None
        for line in result:
            if (str(course["id"]) in line):
                moodle_course_id = line.split("\t")[2]
                break

        if (moodle_course_id is None):
            raise ValueError("Course id not found.")

        sql = f"""
            UPDATE mdl_course
            SET id = {course["id"]}
            WHERE id = {moodle_course_id}
            ;
        """
        run_sql(sql)

        tables = [
            "mdl_enrol",
        ]

        for table in tables:
            sql = f"""
                UPDATE {table}
                SET courseid = {course["id"]}
                WHERE courseid = {moodle_course_id}
                ;
            """
            run_sql(sql)

def clean_up():
    sql = f"""
        DELETE FROM mdl_user_preferences;
    """
    run_sql(sql)

# Load the data from disk.
# All collections will be converted to a dict, keyed by the item's short name (`short-name`).
# The same short name is used to cross-reference items in this dataset.
# Returns (matches order of DATA_FILES): users, courses, assignments, groups, submissions.
def load_test_data():
    results = []

    for path in DATA_FILES:
        with open(path, 'r') as file:
            items = json.load(file)

        mapped_items = {}
        for item in items:
            key = item['short-name']
            if (key in mapped_items):
                raise ValueError(f"Found duplicate key ('{key}') in data file: '{path}'.")

            mapped_items[key] = item

        results.append(mapped_items)

    return tuple(results)

def main():
    dataset = edq.util.pyimport.import_path(LOAD_SCRIPT).load_test_data(DATA_DIR)
    (users, courses, assignments, groupsets, submissions) = dataset

    # HACK(JK): The server owner has hard-coded id in the code base.
    users["server-owner"]["id"] = 2

    # Add the courses.
    add_courses(courses)

    # Add the users.
    add_users(users)

    # Clean up.
    clean_up()

    return 0

if __name__ == '__main__':
    sys.exit(main())
