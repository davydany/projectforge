import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
import utils.database as db

def app():
    st.header("Project Dashboard")
    
    # Get date range of all projects and sub-projects
    date_range_data = db.execute_query("""
        SELECT MIN(start_date), MAX(end_date) FROM (
            SELECT start_date, end_date FROM projects
            UNION ALL
            SELECT start_date, end_date FROM sub_projects
        )
    """)
    
    # Set default date range based on data or fallback to current month
    if date_range_data and date_range_data[0][0] and date_range_data[0][1]:
        min_date = datetime.fromisoformat(date_range_data[0][0]).date()
        max_date = datetime.fromisoformat(date_range_data[0][1]).date()
    else:
        today = date.today()
        min_date = date(today.year, today.month, 1)  # First day of current month
        max_date = today + timedelta(days=30)  # 30 days from today
    
    # Gantt Chart Section
    st.subheader("Project Timeline")
    
    # Date range selector with slider
    date_range_container = st.container()
    with date_range_container:
        # Calculate total days for slider
        total_days = (max_date - min_date).days
        
        # Add some buffer days to the slider range
        slider_min_date = min_date - timedelta(days=14)
        slider_max_date = max_date + timedelta(days=14)
        slider_total_days = (slider_max_date - slider_min_date).days
        
        st.write("**Adjust Timeline Range:**")
        
        # Create a slider for date range selection
        col1, col2 = st.columns([3, 1])
        with col1:
            days_range = st.slider(
                "Date Range",
                min_value=0,
                max_value=slider_total_days,
                value=(14, 14 + total_days),  # Default to the actual data range
                step=1
            )
            
            # Convert slider values to dates
            filter_start = slider_min_date + timedelta(days=days_range[0])
            filter_end = slider_min_date + timedelta(days=days_range[1])
            
            st.write(f"Showing projects from **{filter_start}** to **{filter_end}**")
        
        with col2:
            # Add option for manual date input
            use_manual_dates = st.checkbox("Manual dates", value=False)
            
    # Manual date input if checkbox is selected
    if use_manual_dates:
        col1, col2 = st.columns(2)
        with col1:
            filter_start = st.date_input("Start Date", value=filter_start, key="manual_start")
        with col2:
            filter_end = st.date_input("End Date", value=filter_end, key="manual_end")
    
    # Projects & Sub-Projects within date range
    proj_data = db.execute_query("""
        SELECT name, start_date, end_date, assigned_to 
        FROM projects 
        WHERE (start_date >= ? AND start_date <= ?) 
           OR (end_date >= ? AND end_date <= ?)
           OR (start_date <= ? AND end_date >= ?)
    """, (filter_start.isoformat(), filter_end.isoformat(), 
          filter_start.isoformat(), filter_end.isoformat(),
          filter_start.isoformat(), filter_start.isoformat()))
    
    subproj_data = db.execute_query("""
        SELECT name, start_date, end_date, assigned_to 
        FROM sub_projects 
        WHERE (start_date >= ? AND start_date <= ?) 
           OR (end_date >= ? AND end_date <= ?)
           OR (start_date <= ? AND end_date >= ?)
    """, (filter_start.isoformat(), filter_end.isoformat(), 
          filter_start.isoformat(), filter_end.isoformat(),
          filter_start.isoformat(), filter_start.isoformat()))
    
    rows = []
    for rec in proj_data + subproj_data:
        rows.append({"Task": rec[0], "Start": rec[1], "Finish": rec[2], "Member_ID": rec[3]})
    
    member_map = dict(db.execute_query("SELECT id, first_name || ' ' || last_name FROM team_members"))
    
    for r in rows:
        r["Member"] = member_map.get(r["Member_ID"], "Unassigned") if r["Member_ID"] else "Unassigned"
    
    if rows:
        df = pd.DataFrame(rows)
        df['Start'] = pd.to_datetime(df['Start'])
        df['Finish'] = pd.to_datetime(df['Finish'])
        
        # Create Gantt chart
        fig = px.timeline(
            df, 
            x_start="Start", 
            x_end="Finish", 
            y="Member", 
            color="Task", 
            title="Project Timeline"
        )
        
        # Customize the chart
        fig.update_layout(
            xaxis=dict(
                title="Date",
                tickformat="%b %d\n%Y",
                tickangle=0,
            ),
            yaxis=dict(
                title="Team Member",
            ),
            height=400,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No projects/sub-projects in this date range.")
    
    # Team Progress Section
    st.subheader("Team Member Progress")
    
    progress_data = db.execute_query("SELECT assigned_to, status, COUNT(*) FROM tasks GROUP BY assigned_to, status")
    
    progress = {}
    for member_id, status, count in progress_data:
        if member_id not in progress:
            progress[member_id] = {"total": 0, "completed": 0}
        progress[member_id]["total"] += count
        if status == "completed":
            progress[member_id]["completed"] += count
    
    if progress:
        # Create progress bars
        for member_id, data in progress.items():
            name = member_map.get(member_id, "Unassigned") if member_id else "Unassigned"
            pct = (data["completed"] / data["total"]) * 100 if data["total"] else 0
            st.write(f"**{name}**")
            st.progress(int(pct))
            st.write(f"{pct:.1f}% completed ({data['completed']}/{data['total']} tasks)")
            st.write("---")
    else:
        st.info("No task data available yet.")
    
    # Recent Activity
    st.subheader("Recent Activity")
    
    recent_notes = db.execute_query("""
        SELECT n.created_at, t.name, n.note
        FROM notes n
        JOIN tasks t ON n.task_id = t.id
        ORDER BY n.created_at DESC
        LIMIT 5
    """)
    
    if recent_notes:
        for note in recent_notes:
            st.write(f"**{note[0]}** - Note added to task '{note[1]}': {note[2]}")
    else:
        st.info("No recent activity.") 