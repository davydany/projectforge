import sqlite3
from datetime import datetime
import os
import streamlit as st
# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Use a path that will be mounted as a volume
DB_PATH = 'data/projectforge.db'

# Database connection
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            user_id INTEGER,
            action_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            entity_name TEXT,
            description TEXT,
            project_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            settings TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    # conn.close()

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

def execute_query(query, params=None, fetch_last_id=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    if fetch_last_id:
        cursor.execute("SELECT last_insert_rowid()")
        result = cursor.fetchone()[0]
    else:
        result = cursor.fetchall()
    
    conn.commit()
    conn.close()
    return result

# Add a function to log activities
def log_activity(action_type, entity_type, entity_id, entity_name, description, project_id=None, user_id=None):
    """
    Log an activity in the system
    
    Parameters:
    - action_type: 'create', 'update', 'delete'
    - entity_type: 'project', 'subproject', 'task', 'note', 'reminder'
    - entity_id: ID of the affected entity
    - entity_name: Name of the affected entity
    - description: Description of the activity
    - project_id: ID of the project this activity belongs to (can be None)
    - user_id: ID of the user who performed the action (can be None)
    """
    st.info(f"Logging activity: {action_type} for {entity_type} with ID {entity_id}")
    print(f"Logging activity: {action_type} for {entity_type} with ID {entity_id}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO activity_logs 
           (timestamp, user_id, action_type, entity_type, entity_id, entity_name, description, project_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now().isoformat(), user_id, action_type, entity_type, entity_id, entity_name, description, project_id)
    )
    
    conn.commit()
    conn.close()

# Function to get activity logs for a project
def get_project_activity_logs(project_id, limit=50):
    """Get recent activity logs for a specific project"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT id, timestamp, action_type, entity_type, entity_id, entity_name, description
           FROM activity_logs
           WHERE project_id = ?
           ORDER BY timestamp DESC
           LIMIT ?""",
        (project_id, limit)
    )
    
    logs = cursor.fetchall()
    conn.close()
    
    return logs

# Function to get all recent activity logs
def get_recent_activity_logs(limit=50):
    """Get recent activity logs across all projects"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT a.id, a.timestamp, a.action_type, a.entity_type, a.entity_id, a.entity_name, a.description, p.name
           FROM activity_logs a
           LEFT JOIN projects p ON a.project_id = p.id
           ORDER BY a.timestamp DESC
           LIMIT ?""",
        (limit,)
    )
    
    logs = cursor.fetchall()
    conn.close()
    
    return logs 