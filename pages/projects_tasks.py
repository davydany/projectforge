import streamlit as st
import pandas as pd
from datetime import datetime
import utils.database as db

def app():
    st.header("Project & Task Management")
    
    # Add buttons at the top for adding projects and tasks
    col1, col2, col3 = st.columns(3)
    with col1:
        add_project_button = st.button("➕ Add New Project", use_container_width=True)
    with col2:
        add_subproject_button = st.button("➕ Add New Sub-Project", use_container_width=True)
    with col3:
        add_task_button = st.button("➕ Add New Task", use_container_width=True)
    
    # Get team members for dropdown
    members = db.get_team_members()
    member_dict = {id: name for id, name in members}
    member_options = ["Unassigned"] + [name for _, name in members]
    
    # Add Project Dialog
    if add_project_button:
        with st.form(key="add_project_form"):
            st.subheader("Add New Project")
            name = st.text_input("Project Name")
            description = st.text_area("Description")
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            
            assign_to_member = st.checkbox("Assign to team member", value=False)
            assigned_to = None
            
            if assign_to_member and members:
                member_name = st.selectbox("Assign To", member_options)
                if member_name != "Unassigned":
                    assigned_to = next((id for id, name in member_dict.items() if name == member_name), None)
            
            submit_button = st.form_submit_button("Add Project")
            if submit_button and name:  # Ensure name is not empty
                db.execute_query(
                    """INSERT INTO projects 
                       (name, description, start_date, end_date, assigned_to) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (name, description, start_date.isoformat(), end_date.isoformat(), assigned_to)
                )
                st.success("Project added successfully!")
                st.rerun()
    
    # Add Sub-Project Dialog
    if add_subproject_button:
        with st.form(key="add_subproject_form"):
            st.subheader("Add New Sub-Project")
            
            # Get projects for parent selection
            projects = db.get_projects()
            if projects:
                project_options = [name for _, name in projects]
                parent_project = st.selectbox("Parent Project", project_options)
                project_id = next((id for id, name in projects if name == parent_project), None)
                
                name = st.text_input("Sub-Project Name")
                description = st.text_area("Description")
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
                
                assign_to_member = st.checkbox("Assign to team member", value=False)
                assigned_to = None
                
                if assign_to_member and members:
                    member_name = st.selectbox("Assign To", member_options)
                    if member_name != "Unassigned":
                        assigned_to = next((id for id, name in member_dict.items() if name == member_name), None)
                
                submit_button = st.form_submit_button("Add Sub-Project")
                if submit_button and name:  # Ensure name is not empty
                    db.execute_query(
                        """INSERT INTO sub_projects 
                           (project_id, name, description, start_date, end_date, assigned_to) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (project_id, name, description, start_date.isoformat(), end_date.isoformat(), assigned_to)
                    )
                    st.success("Sub-Project added successfully!")
                    st.rerun()
            else:
                st.warning("Please add a project first before adding sub-projects.")
                st.form_submit_button("Add Sub-Project", disabled=True)
    
    # Add Task Dialog
    if add_task_button:
        with st.form(key="add_task_form"):
            st.subheader("Add New Task")
            
            task_type = st.radio("Task Type", ["Project Task", "Sub-Project Task"])
            
            if task_type == "Project Task":
                projects = db.get_projects()
                if projects:
                    project_options = [name for _, name in projects]
                    parent = st.selectbox("Select Project", project_options)
                    project_id = next((id for id, name in projects if name == parent), None)
                    sub_project_id = None
                else:
                    st.warning("Please add a project first.")
                    st.form_submit_button("Add Task", disabled=True)
                    return
            else:
                sub_projects = db.get_sub_projects()
                if sub_projects:
                    subproj_options = [name for _, name in sub_projects]
                    parent = st.selectbox("Select Sub-Project", subproj_options)
                    sub_project_id = next((id for id, name in sub_projects if name == parent), None)
                    project_id = None
                else:
                    st.warning("Please add a sub-project first.")
                    st.form_submit_button("Add Task", disabled=True)
                    return
            
            name = st.text_input("Task Name")
            description = st.text_area("Description")
            jira_ticket = st.text_input("Jira Ticket (optional)")
            status = st.selectbox("Status", ["not started", "started", "blocked", "waiting", "in progress", "completed"])
            
            if members:
                member_name = st.selectbox("Assign To", member_options)
                if member_name != "Unassigned":
                    assigned_to = next((id for id, name in member_dict.items() if name == member_name), None)
                else:
                    assigned_to = None
                
                submit_button = st.form_submit_button("Add Task")
                if submit_button and name:  # Ensure name is not empty
                    db.execute_query(
                        """INSERT INTO tasks 
                           (project_id, sub_project_id, name, description, jira_ticket, status, assigned_to)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (project_id, sub_project_id, name, description, jira_ticket, status, assigned_to)
                    )
                    st.success("Task added successfully!")
                    st.rerun()
            else:
                st.warning("Please add team members first.")
                st.form_submit_button("Add Task", disabled=True)
    
    # Display projects and their tasks
    projects_data = db.execute_query("""
        SELECT p.id, p.name, p.description, p.start_date, p.end_date, p.assigned_to
        FROM projects p
        ORDER BY p.start_date DESC
    """)
    
    if projects_data:
        for project_id, project_name, project_desc, start_date, end_date, assigned_to in projects_data:
            # Format dates
            start_date = start_date.split('T')[0] if 'T' in start_date else start_date
            end_date = end_date.split('T')[0] if 'T' in end_date else end_date
            
            # Get assigned person name
            assigned_name = member_dict.get(assigned_to, "Unassigned") if assigned_to else "Unassigned"
            
            # Project header with details
            st.markdown(f"""
            ## Project: {project_name}
            **Timeline:** {start_date} to {end_date} | **Assigned to:** {assigned_name}
            
            {project_desc}
            """)
            
            # Project tasks
            project_tasks = db.execute_query("""
                SELECT t.id, t.name, t.description, t.jira_ticket, t.status, t.assigned_to
                FROM tasks t
                WHERE t.project_id = ? AND t.sub_project_id IS NULL
            """, (project_id,))
            
            if project_tasks:
                st.subheader("Tasks")
                
                # Convert to DataFrame for the editable table
                tasks_df = pd.DataFrame(project_tasks, 
                                       columns=["ID", "Name", "Description", "Jira Ticket", "Status", "Assigned To"])
                
                # Add assigned person name
                tasks_df["Assigned To Name"] = tasks_df["Assigned To"].apply(
                    lambda x: member_dict.get(x, "Unassigned") if x else "Unassigned"
                )
                
                # Add action buttons
                tasks_df["Delete"] = False
                tasks_df["Change Status"] = tasks_df["Status"]
                
                # Create an editable dataframe for tasks
                edited_tasks_df = st.data_editor(
                    tasks_df,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", disabled=True),
                        "Name": st.column_config.TextColumn("Name"),
                        "Description": st.column_config.TextColumn("Description"),
                        "Jira Ticket": st.column_config.TextColumn("Jira Ticket"),
                        "Status": st.column_config.TextColumn("Current Status", disabled=True),
                        "Change Status": st.column_config.SelectboxColumn(
                            "Change Status",
                            options=["not started", "started", "blocked", "waiting", "in progress", "completed"],
                            required=True
                        ),
                        "Assigned To": st.column_config.NumberColumn("Assigned To ID", disabled=True),
                        "Assigned To Name": st.column_config.SelectboxColumn(
                            "Assigned To",
                            options=member_options,
                            required=True
                        ),
                        "Delete": st.column_config.CheckboxColumn("Delete?", help="Select to delete this task")
                    },
                    hide_index=True,
                    num_rows="dynamic",
                    key=f"tasks_df_{project_id}"
                )
                
                # Handle task deletions
                for index, row in edited_tasks_df.iterrows():
                    if row["Delete"] and index < len(tasks_df):
                        # Check if task has notes or reminders
                        note_count = db.execute_query(
                            "SELECT COUNT(*) FROM notes WHERE task_id = ?", 
                            (row["ID"],)
                        )[0][0]
                        
                        reminder_count = db.execute_query(
                            "SELECT COUNT(*) FROM reminders WHERE task_id = ?", 
                            (row["ID"],)
                        )[0][0]
                        
                        if note_count > 0 or reminder_count > 0:
                            st.error(f"Cannot delete task '{row['Name']}' with notes or reminders. Please delete them first.")
                        else:
                            db.execute_query("DELETE FROM tasks WHERE id = ?", (row["ID"],))
                            st.success(f"Task '{row['Name']}' deleted successfully!")
                            st.rerun()
                
                # Handle task updates
                for index, row in edited_tasks_df.iterrows():
                    if index < len(tasks_df):  # This is an edit to existing row
                        # Check for status changes
                        if row["Status"] != row["Change Status"]:
                            db.execute_query(
                                "UPDATE tasks SET status = ? WHERE id = ?",
                                (row["Change Status"], row["ID"])
                            )
                            st.success(f"Updated status for task '{row['Name']}' to {row['Change Status']}")
                            st.rerun()
                        
                        # Check for assigned person changes
                        current_assigned = tasks_df.iloc[index]["Assigned To Name"]
                        if row["Assigned To Name"] != current_assigned:
                            # Find member_id from name
                            assigned_to = None
                            if row["Assigned To Name"] != "Unassigned":
                                assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                            
                            db.execute_query(
                                "UPDATE tasks SET assigned_to = ? WHERE id = ?",
                                (assigned_to, row["ID"])
                            )
                            st.success(f"Reassigned task '{row['Name']}' to {row['Assigned To Name']}")
                            st.rerun()
                        
                        # Check for other changes
                        if not tasks_df.iloc[index][["Name", "Description", "Jira Ticket"]].equals(
                            row[["Name", "Description", "Jira Ticket"]]
                        ):
                            db.execute_query(
                                """UPDATE tasks 
                                   SET name = ?, description = ?, jira_ticket = ?
                                   WHERE id = ?""",
                                (row["Name"], row["Description"], row["Jira Ticket"], row["ID"])
                            )
                            st.success(f"Updated task: {row['Name']}")
                            st.rerun()
                    else:  # This is a new row
                        if not pd.isna(row["Name"]):
                            # Find member_id from name
                            assigned_to = None
                            if not pd.isna(row["Assigned To Name"]) and row["Assigned To Name"] != "Unassigned":
                                assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                            
                            db.execute_query(
                                """INSERT INTO tasks 
                                   (project_id, sub_project_id, name, description, jira_ticket, status, assigned_to)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (project_id, None, row["Name"], row["Description"] or "", row["Jira Ticket"] or "", 
                                 row["Change Status"], assigned_to)
                            )
                            st.success(f"Added new task: {row['Name']}")
                            st.rerun()
            else:
                st.info(f"No tasks for project {project_name} yet.")
                
                # Show an empty table with structure for adding new tasks
                empty_tasks_df = pd.DataFrame(columns=["Name", "Description", "Jira Ticket", "Change Status", "Assigned To Name"])
                edited_empty_df = st.data_editor(
                    empty_tasks_df,
                    column_config={
                        "Name": st.column_config.TextColumn("Name"),
                        "Description": st.column_config.TextColumn("Description"),
                        "Jira Ticket": st.column_config.TextColumn("Jira Ticket"),
                        "Change Status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["not started", "started", "blocked", "waiting", "in progress", "completed"],
                            required=True
                        ),
                        "Assigned To Name": st.column_config.SelectboxColumn(
                            "Assigned To",
                            options=member_options,
                            required=True
                        )
                    },
                    num_rows="dynamic",
                    hide_index=True,
                    key=f"empty_tasks_df_{project_id}"
                )
                
                # Handle new task additions
                for _, row in edited_empty_df.iterrows():
                    if not pd.isna(row["Name"]):
                        # Find member_id from name
                        assigned_to = None
                        if not pd.isna(row["Assigned To Name"]) and row["Assigned To Name"] != "Unassigned":
                            assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                        
                        db.execute_query(
                            """INSERT INTO tasks 
                               (project_id, sub_project_id, name, description, jira_ticket, status, assigned_to)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (project_id, None, row["Name"], row["Description"] or "", row["Jira Ticket"] or "", 
                             row["Change Status"], assigned_to)
                        )
                        st.success(f"Added new task: {row['Name']}")
                        st.rerun()
            
            # Sub-projects and their tasks
            sub_projects = db.execute_query("""
                SELECT sp.id, sp.name, sp.description, sp.start_date, sp.end_date, sp.assigned_to
                FROM sub_projects sp
                WHERE sp.project_id = ?
            """, (project_id,))
            
            if sub_projects:
                st.markdown("### Sub-Projects")
                
                for sub_id, sub_name, sub_desc, sub_start, sub_end, sub_assigned in sub_projects:
                    # Format dates
                    sub_start = sub_start.split('T')[0] if 'T' in sub_start else sub_start
                    sub_end = sub_end.split('T')[0] if 'T' in sub_end else sub_end
                    
                    # Get assigned person name
                    sub_assigned_name = member_dict.get(sub_assigned, "Unassigned") if sub_assigned else "Unassigned"
                    
                    # Sub-project header with details
                    with st.expander(f"Sub-Project: {sub_name}", expanded=True):
                        st.markdown(f"""
                        **Timeline:** {sub_start} to {sub_end} | **Assigned to:** {sub_assigned_name}
                        
                        {sub_desc}
                        """)
                        
                        # Sub-project tasks
                        sub_tasks = db.execute_query("""
                            SELECT t.id, t.name, t.description, t.jira_ticket, t.status, t.assigned_to
                            FROM tasks t
                            WHERE t.sub_project_id = ?
                        """, (sub_id,))
                        
                        if sub_tasks:
                            st.subheader("Tasks")
                            
                            # Convert to DataFrame for the editable table
                            sub_tasks_df = pd.DataFrame(sub_tasks, 
                                                      columns=["ID", "Name", "Description", "Jira Ticket", "Status", "Assigned To"])
                            
                            # Add assigned person name
                            sub_tasks_df["Assigned To Name"] = sub_tasks_df["Assigned To"].apply(
                                lambda x: member_dict.get(x, "Unassigned") if x else "Unassigned"
                            )
                            
                            # Add action buttons
                            sub_tasks_df["Delete"] = False
                            sub_tasks_df["Change Status"] = sub_tasks_df["Status"]
                            
                            # Create an editable dataframe for tasks
                            edited_sub_tasks_df = st.data_editor(
                                sub_tasks_df,
                                column_config={
                                    "ID": st.column_config.NumberColumn("ID", disabled=True),
                                    "Name": st.column_config.TextColumn("Name"),
                                    "Description": st.column_config.TextColumn("Description"),
                                    "Jira Ticket": st.column_config.TextColumn("Jira Ticket"),
                                    "Status": st.column_config.TextColumn("Current Status", disabled=True),
                                    "Change Status": st.column_config.SelectboxColumn(
                                        "Change Status",
                                        options=["not started", "started", "blocked", "waiting", "in progress", "completed"],
                                        required=True
                                    ),
                                    "Assigned To": st.column_config.NumberColumn("Assigned To ID", disabled=True),
                                    "Assigned To Name": st.column_config.SelectboxColumn(
                                        "Assigned To",
                                        options=member_options,
                                        required=True
                                    ),
                                    "Delete": st.column_config.CheckboxColumn("Delete?", help="Select to delete this task")
                                },
                                hide_index=True,
                                num_rows="dynamic",
                                key=f"sub_tasks_df_{sub_id}"
                            )
                            
                            # Handle task deletions and updates (similar to project tasks)
                            # ... (similar code as for project tasks)
                        else:
                            st.info(f"No tasks for sub-project {sub_name} yet.")
                            
                            # Show an empty table with structure for adding new tasks
                            # ... (similar code as for project tasks)
            
            st.markdown("---")  # Separator between projects
    else:
        st.info("No projects added yet. Use the 'Add New Project' button to create a project.") 