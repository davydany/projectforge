import sqlite3
from datetime import datetime

# Database connection
conn = sqlite3.connect('project_management.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            location TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            team_id INTEGER,
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            deviation INTEGER DEFAULT 0,
            assigned_to INTEGER,
            FOREIGN KEY (assigned_to) REFERENCES team_members(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sub_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            name TEXT,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            deviation INTEGER DEFAULT 0,
            assigned_to INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (assigned_to) REFERENCES team_members(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            sub_project_id INTEGER,
            name TEXT,
            description TEXT,
            jira_ticket TEXT,
            status TEXT,
            assigned_to INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (sub_project_id) REFERENCES sub_projects(id),
            FOREIGN KEY (assigned_to) REFERENCES team_members(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            note TEXT,
            created_at TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            reminder_date TEXT,
            note TEXT,
            followed_up INTEGER DEFAULT 0,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    ''')
    conn.commit()

# Helper Functions
def get_teams():
    c.execute("SELECT id, name FROM teams")
    return c.fetchall()

def get_team_members():
    c.execute("SELECT id, first_name || ' ' || last_name as name FROM team_members")
    return c.fetchall()

def get_projects():
    c.execute("SELECT id, name FROM projects")
    return c.fetchall()

def get_sub_projects():
    c.execute("SELECT id, name FROM sub_projects")
    return c.fetchall()

def get_tasks():
    c.execute("SELECT id, name FROM tasks")
    return c.fetchall()

def execute_query(query, params=None):
    if params:
        c.execute(query, params)
    else:
        c.execute(query)
    conn.commit()
    return c.fetchall() 