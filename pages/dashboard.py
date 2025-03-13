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

    # Get task progress data with more detailed query
    progress_data = db.execute_query("""
        SELECT 
            t.assigned_to, 
            t.status, 
            COUNT(*) as task_count,
            GROUP_CONCAT(t.name, ', ') as task_names
        FROM tasks t
        GROUP BY t.assigned_to, t.status
    """)

    # Initialize progress dictionary with all members
    progress = {}
    for member_id, name in all_members:
        progress[member_id] = {
            "name": name, 
            "total": 0, 
            "completed": 0,
            "tasks": {
                "not started": [],
                "started": [],
                "in progress": [],
                "blocked": [],
                "waiting": [],
                "completed": []
            }
        }

    # Add "Unassigned" category
    progress[None] = {
        "name": "Unassigned", 
        "total": 0, 
        "completed": 0,
        "tasks": {
            "not started": [],
            "started": [],
            "in progress": [],
            "blocked": [],
            "waiting": [],
            "completed": []
        }
    }

    # Fill in task data
    for member_id, status, count, task_names in progress_data:
        if member_id not in progress:
            # This shouldn't happen, but just in case
            progress[member_id] = {
                "name": member_map.get(member_id, "Unknown"), 
                "total": 0, 
                "completed": 0,
                "tasks": {
                    "not started": [],
                    "started": [],
                    "in progress": [],
                    "blocked": [],
                    "waiting": [],
                    "completed": []
                }
            }
        
        # Add to total count
        progress[member_id]["total"] += count
        
        # Add to completed count if status is completed
        if status == "completed":
            progress[member_id]["completed"] += count
        
        # Add task names to the appropriate status list
        if task_names:
            status_key = status.lower() if status else "not started"
            if status_key not in progress[member_id]["tasks"]:
                progress[member_id]["tasks"][status_key] = []
            
            progress[member_id]["tasks"][status_key].extend(task_names.split(", "))

    # Display progress for all members
    for member_id, data in progress.items():
        name = data["name"]
        total = data["total"]
        completed = data["completed"]
        
        # Create an expander for each team member
        with st.expander(f"**{name}** - {completed}/{total} tasks", expanded=False):
            if total > 0:
                # Calculate percentage
                pct = (completed / total) * 100
                
                # Show progress bar
                st.progress(int(pct))
                st.write(f"{pct:.1f}% completed")
                
                # Get all tasks for this member with more details
                member_tasks = db.execute_query("""
                    SELECT 
                        t.id, 
                        t.name, 
                        t.description, 
                        t.status,
                        p.name as project_name,
                        sp.name as subproject_name,
                        t.jira_ticket
                    FROM tasks t
                    LEFT JOIN projects p ON t.project_id = p.id
                    LEFT JOIN sub_projects sp ON t.sub_project_id = sp.id
                    WHERE t.assigned_to = ?
                    ORDER BY 
                        CASE 
                            WHEN t.status = 'completed' THEN 2
                            ELSE 1
                        END,
                        p.name, 
                        sp.name
                """, (member_id,))
                
                if member_tasks:
                    # Create a formatted HTML table
                    table_html = """
                    <table style="width:100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background-color: #f2f2f2;">
                                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Task</th>
                                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Project</th>
                                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Sub-Project</th>
                                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Status</th>
                                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Jira</th>
                            </tr>
                        </thead>
                        <tbody>
                    """
                    
                    for task in member_tasks:
                        task_id, task_name, task_desc, task_status, project_name, subproject_name, jira_ticket = task
                        
                        # Set row color based on status
                        row_color = "#e6ffe6" if task_status == "completed" else \
                                    "#ffcccc" if task_status == "blocked" else \
                                    "#ffe6cc" if task_status == "waiting" else \
                                    "#e6f7ff" if task_status == "in progress" else \
                                    "#f9f9f9"  # default
                        
                        # Format the task description (truncate if too long)
                        task_desc_short = (task_desc[:50] + '...') if task_desc and len(task_desc) > 50 else task_desc
                        
                        # Add tooltip with full description
                        tooltip = f'title="{task_desc}"' if task_desc else ''
                        
                        # Add row to table
                        table_html += f"""
                        <tr style="background-color: {row_color};">
                            <td style="padding: 8px; text-align: left; border: 1px solid #ddd;" {tooltip}>{task_name}</td>
                            <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{project_name or '-'}</td>
                            <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{subproject_name or '-'}</td>
                            <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{task_status or 'Not started'}</td>
                            <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{jira_ticket or '-'}</td>
                        </tr>
                        """
                    
                    table_html += """
                        </tbody>
                    </table>
                    """
                    
                    # Display the table
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.info("No detailed task information available.")
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