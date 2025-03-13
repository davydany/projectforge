import streamlit as st
import utils.database as db

def app():
    st.header("Task Management")
    
    tabs = st.tabs(["Add Task", "View Tasks"])
    
    with tabs[0]:
        st.subheader("Add New Task")
        task_type = st.radio("Task Type", ["Project Task", "Sub-Project Task"])
        
        if task_type == "Project Task":
            projects = db.get_projects()
            if projects:
                proj_dict = {name: id for id, name in projects}
                parent = st.selectbox("Select Project", list(proj_dict.keys()))
                project_id = proj_dict[parent]
                sub_project_id = None
            else:
                st.warning("Please add a project first.")
                return
        else:
            sub_projects = db.get_sub_projects()
            if sub_projects:
                subproj_dict = {name: id for id, name in sub_projects}
                parent = st.selectbox("Select Sub-Project", list(subproj_dict.keys()))
                sub_project_id = subproj_dict[parent]
                project_id = None
            else:
                st.warning("Please add a sub-project first.")
                return
        
        name = st.text_input("Task Name")
        description = st.text_area("Description")
        jira_ticket = st.text_input("Jira Ticket (optional)")
        status = st.selectbox("Status", ["not started", "started", "blocked", "in progress", "completed"])
        
        members = db.get_team_members()
        if members:
            member_dict = {name: id for id, name in members}
            assigned_to = st.selectbox("Assign To", list(member_dict.keys()))
            
            if st.button("Add Task"):
                db.execute_query(
                    """INSERT INTO tasks 
                       (project_id, sub_project_id, name, description, jira_ticket, status, assigned_to)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (project_id, sub_project_id, name, description, jira_ticket, 
                     status, member_dict[assigned_to])
                )
                st.success("Task added successfully!")
        else:
            st.warning("Please add team members first.")
    
    with tabs[1]:
        st.subheader("Task Overview")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status", 
                ["not started", "started", "blocked", "in progress", "completed"],
                default=[]
            )
        with col2:
            members = db.get_team_members()
            member_dict = {name: id for id, name in members}
            member_filter = st.multiselect("Filter by Team Member", list(member_dict.keys()), default=[])
        
        # Build query based on filters
        query = """
            SELECT t.id, t.name, t.description, t.jira_ticket, t.status,
                   tm.first_name || ' ' || tm.last_name as assigned_to,
                   CASE 
                       WHEN t.project_id IS NOT NULL THEN p.name
                       ELSE sp.name
                   END as parent_name
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN sub_projects sp ON t.sub_project_id = sp.id
            JOIN team_members tm ON t.assigned_to = tm.id
        """
        
        conditions = []
        params = []
        
        if status_filter:
            placeholders = ", ".join(["?"] * len(status_filter))
            conditions.append(f"t.status IN ({placeholders})")
            params.extend(status_filter)
        
        if member_filter:
            member_ids = [member_dict[name] for name in member_filter]
            placeholders = ", ".join(["?"] * len(member_ids))
            conditions.append(f"t.assigned_to IN ({placeholders})")
            params.extend(member_ids)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        tasks = db.execute_query(query, params)
        
        if tasks:
            for task in tasks:
                with st.expander(f"{task[1]} ({task[6]})"):
                    st.write(f"**Description:** {task[2]}")
                    if task[3]:  # Jira ticket
                        st.write(f"**Jira Ticket:** {task[3]}")
                    st.write(f"**Status:** {task[4]}")
                    st.write(f"**Assigned to:** {task[5]}")
                    
                    # Get notes for this task
                    notes = db.execute_query(
                        "SELECT note, created_at FROM notes WHERE task_id = ? ORDER BY created_at DESC", 
                        (task[0],)
                    )
                    
                    if notes:
                        st.write("**Notes:**")
                        for note in notes:
                            st.write(f"- {note[0]} _(added on {note[1]})_")
        else:
            st.info("No tasks found with the selected filters.") 