import streamlit as st
import sqlite3
from datetime import datetime, date
import pandas as pd
import plotly.express as px

# Import pages
import pages.teams
import pages.members
import pages.projects
import pages.tasks
import pages.notes
import pages.reminders
import pages.dashboard
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
    "Teams": pages.teams,
    "Team Members": pages.members,
    "Projects": pages.projects,
    "Tasks": pages.tasks,
    "Notes": pages.notes,
    "Reminders": pages.reminders
}

selection = st.sidebar.radio("Navigate to", list(pages.keys()))

# Display the selected page
pages[selection].app()

# Footer
st.sidebar.markdown("---")
st.sidebar.info("ProjectForge v1.0") 