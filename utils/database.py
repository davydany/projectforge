import sqlite3
from datetime import datetime
import os
import streamlit as st
from typing import List, Dict, Any, Optional, Union, TypeVar, Type
from utils.models import Project, SubProject, Task, Team, TeamMember, Note, Reminder

# Type variable for generic model functions
T = TypeVar('T', Project, SubProject, Task, Team, TeamMember, Note, Reminder)

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

# Generic CRUD operations for models
def create_model(model: T) -> int:
    """Create a new record in the database from a model"""
    model_dict = model.to_dict()
    
    # Remove ID from the dictionary if it's None
    if model_dict.get('id') is None:
        del model_dict['id']
    
    # Get the table name from the model class name
    table_name = model.__class__.__name__.lower() + 's'
    if table_name == 'teams':
        table_name = 'teams'  # Special case for team (already plural)
    
    # Build the SQL query
    columns = ', '.join(model_dict.keys())
    placeholders = ', '.join(['?'] * len(model_dict))
    values = tuple(model_dict.values())
    
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    # Execute the query
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, values)
    
    # Get the ID of the new record
    cursor.execute("SELECT last_insert_rowid()")
    new_id = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    return new_id

def get_model_by_id(model_class: Type[T], id: int) -> Optional[T]:
    """Get a model by ID"""
    # Get the table name from the model class name
    table_name = model_class.__name__.lower() + 's'
    if table_name == 'teams':
        table_name = 'teams'  # Special case for team (already plural)
    
    query = f"SELECT * FROM {table_name} WHERE id = ?"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, (id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    # Get column names
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    conn.close()
    
    # Create a dictionary from the row
    data = {columns[i]: row[i] for i in range(len(columns))}
    
    # Create and return the model
    return model_class.from_dict(data)

def update_model(model: T) -> bool:
    """Update a model in the database"""
    if model.id is None:
        raise ValueError("Model must have an ID to be updated")
    
    model_dict = model.to_dict()
    
    # Get the table name from the model class name
    table_name = model.__class__.__name__.lower() + 's'
    if table_name == 'teams':
        table_name = 'teams'  # Special case for team (already plural)
    
    # Build the SQL query
    set_clause = ', '.join([f"{key} = ?" for key in model_dict.keys() if key != 'id'])
    values = tuple(value for key, value in model_dict.items() if key != 'id')
    values += (model.id,)  # Add ID for WHERE clause
    
    query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
    
    # Execute the query
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, values)
    
    # Check if the update was successful
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return success

def delete_model(model_class: Type[T], id: int) -> bool:
    """Delete a model from the database by ID"""
    # Get the table name from the model class name
    table_name = model_class.__name__.lower() + 's'
    if table_name == 'teams':
        table_name = 'teams'  # Special case for team (already plural)
    
    query = f"DELETE FROM {table_name} WHERE id = ?"
    
    # Execute the query
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, (id,))
    
    # Check if the delete was successful
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return success

def get_all_models(model_class: Type[T]) -> List[T]:
    """Get all models of a specific type"""
    # Get the table name from the model class name
    table_name = model_class.__name__.lower() + 's'
    if table_name == 'teams':
        table_name = 'teams'  # Special case for team (already plural)
    
    query = f"SELECT * FROM {table_name}"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query)
    
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    
    conn.close()
    
    # Create models from rows
    models = []
    for row in rows:
        data = {columns[i]: row[i] for i in range(len(columns))}
        models.append(model_class.from_dict(data))
    
    return models

# Keep the existing helper functions for backward compatibility
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