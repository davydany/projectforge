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
    
    # Get all team members
    all_members = db.execute_query("SELECT id, first_name || ' ' || last_name as name FROM team_members")
    member_map = {id: name for id, name in all_members}

    # Get task progress data
    progress_data = db.execute_query("SELECT assigned_to, status, COUNT(*) FROM tasks GROUP BY assigned_to, status")

    # Initialize progress dictionary with all members
    progress = {}
    for member_id, name in all_members:
        progress[member_id] = {"name": name, "total": 0, "completed": 0}

    # Add "Unassigned" category
    progress[None] = {"name": "Unassigned", "total": 0, "completed": 0}

    # Fill in task data
    for member_id, status, count in progress_data:
        if member_id not in progress:
            # This shouldn't happen, but just in case
            progress[member_id] = {"name": member_map.get(member_id, "Unknown"), "total": 0, "completed": 0}
        
        progress[member_id]["total"] += count
        if status == "completed":
            progress[member_id]["completed"] += count

    # Display progress for all members
    for member_id, data in progress.items():
        name = data["name"]
        total = data["total"]
        completed = data["completed"]
        
        st.write(f"**{name}**")
        
        if total > 0:
            pct = (completed / total) * 100
            st.progress(int(pct))
            st.write(f"{pct:.1f}% completed ({completed}/{total} tasks)")
        else:
            st.progress(0)
            st.write("No tasks assigned")
        
        st.write("---")
    
    # Recent Activity
    st.header("Recent Activity")
    
    # Get recent activity logs
    activity_logs = db.get_recent_activity_logs(limit=10)
    
    if activity_logs:
        # Create a container for scrollable activity log
        log_container = st.container()
        with log_container:
            for log_id, timestamp, action_type, entity_type, entity_id, entity_name, description, project_name in activity_logs:
                # Format timestamp
                timestamp = timestamp.split('T')[0] + " " + timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
                
                # Set icon based on action type
                icon = "✅" if action_type == "create" else "🔄" if action_type == "update" else "❌" if action_type == "delete" else "ℹ️"
                
                # Set color based on entity type
                color = "#e6f7ff" if entity_type == "project" else \
                        "#fff2e6" if entity_type == "subproject" else \
                        "#e6ffe6" if entity_type == "task" else \
                        "#f7e6ff" if entity_type == "note" else \
                        "#ffe6e6" if entity_type == "reminder" else "#f9f9f9"
                
                # Create a card-like display for each activity
                st.markdown(f"""
                <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px; background-color:{color};">
                    <p style="color:#555; font-size:0.8em;">{timestamp} | {icon} <b>{action_type.upper()}</b> {entity_type}: {entity_name}</p>
                    <p>{description}</p>
                    <p style="color:#888; font-size:0.8em;">Project: {project_name}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No recent activity logs yet.") 