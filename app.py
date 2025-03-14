import streamlit as st
import sqlite3
from datetime import datetime, date
import pandas as pd
import plotly.express as px

# Import pages
import pages.notes
import pages.reminders
import pages.dashboard
import pages.teams_members
import pages.projects_tasks
import pages.connections
import utils.database as db

# Initialize the database
db.init_db()

# Page configuration
st.set_page_config(
    page_title="ProjectForge",
    page_icon="🛠️",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("ProjectForge")
st.sidebar.image("https://img.icons8.com/color/96/000000/project-management.png", width=100)

# Main navigation
pages = {
    "Dashboard": pages.dashboard,
    "Teams & Members": pages.teams_members,
    "Projects & Tasks": pages.projects_tasks,
    "Notes": pages.notes,
    "Reminders": pages.reminders,
    "Manage Connections": pages.connections
}

selection = st.sidebar.radio("Navigate to", list(pages.keys()))

# Display the selected page
pages[selection].app()

# Footer
st.sidebar.markdown("---")
st.sidebar.info("ProjectForge v1.0") 