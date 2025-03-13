import streamlit as st
import pandas as pd
from datetime import datetime
import utils.database as db

def app():
    st.header("Project & Task Management")
    
    # Initialize session state for navigation
    if "view" not in st.session_state:
        st.session_state.view = "list"
    if "selected_project_id" not in st.session_state:
        st.session_state.selected_project_id = None
    if "selected_project_name" not in st.session_state:
        st.session_state.selected_project_name = None
    
    # Functions to handle navigation
    def view_project_details(project_id, project_name):
        st.session_state.view = "detail"
        st.session_state.selected_project_id = project_id
        st.session_state.selected_project_name = project_name
        st.rerun()
    
    def back_to_list():
        st.session_state.view = "list"
        st.session_state.selected_project_id = None
        st.session_state.selected_project_name = None
        st.rerun()
    
    # Dialog functions for notes and reminders
    @st.dialog("Add Note to Task")
    def open_note_modal(task_id, task_name):
        note_modal = st.container()
        with note_modal:
            st.subheader(f"Add Note to: {task_name}")
            note_text = st.text_area("Note", height=150)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Cancel", use_container_width=True):
                    close_modals()
            with col2:
                if st.button("Add Note", use_container_width=True):
                    if note_text:
                        db.execute_query(
                            "INSERT INTO notes (task_id, note, created_at) VALUES (?, ?, ?)",
                            (task_id, note_text, datetime.now().isoformat())
                        )
                        st.success("Note added successfully!")
                        close_modals()
    
    @st.dialog("Add Reminder for Task")
    def open_reminder_modal(task_id, task_name):
        reminder_modal = st.container()
        with reminder_modal:
            st.subheader(f"Add Reminder for: {task_name}")
            reminder_date = st.date_input("Reminder Date")
            reminder_note = st.text_area("Reminder Note", height=100)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Cancel", use_container_width=True):
                    close_modals()
            with col2:
                if st.button("Add Reminder", use_container_width=True):
                    if reminder_note:
                        db.execute_query(
                            "INSERT INTO reminders (task_id, reminder_date, note) VALUES (?, ?, ?)",
                            (task_id, reminder_date.isoformat(), reminder_note)
                        )
                        st.success("Reminder added successfully!")
                        close_modals()
    
    def close_modals():
        st.rerun()
    
    # Get team members for dropdown
    members = db.get_team_members()
    member_dict = {id: name for id, name in members}
    member_options = ["Unassigned"] + [name for _, name in members]
    
    # LIST VIEW
    if st.session_state.view == "list":
        # Add buttons at the top for adding projects and tasks
        col1, col2, col3 = st.columns(3)
        with col1:
            add_project_button = st.button("➕ Add New Project", use_container_width=True)
        with col2:
            add_subproject_button = st.button("➕ Add New Sub-Project", use_container_width=True)
        with col3:
            add_task_button = st.button("➕ Add New Task", use_container_width=True)
        
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
        
        # Display projects list
        st.subheader("Projects")
        
        # Get projects data
        projects_data = db.execute_query("""
            SELECT p.id, p.name, p.description, p.start_date, p.end_date, p.assigned_to
            FROM projects p
            ORDER BY p.start_date DESC
        """)
        
        if projects_data:
            # Display projects as cards
            for project_id, name, description, start_date, end_date, assigned_to in projects_data:
                # Format dates
                start_date = start_date.split('T')[0] if 'T' in start_date else start_date
                end_date = end_date.split('T')[0] if 'T' in end_date else end_date
                
                # Get assigned person name
                assigned_name = member_dict.get(assigned_to, "Unassigned") if assigned_to else "Unassigned"
                
                # Get task count
                task_count = db.execute_query(
                    "SELECT COUNT(*) FROM tasks WHERE project_id = ? AND sub_project_id IS NULL", 
                    (project_id,)
                )[0][0]
                
                # Get sub-project count
                subproject_count = db.execute_query(
                    "SELECT COUNT(*) FROM sub_projects WHERE project_id = ?", 
                    (project_id,)
                )[0][0]
                
                # Create a card-like display for each project
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {name}")
                        st.markdown(f"**Timeline:** {start_date} to {end_date} | **Assigned to:** {assigned_name}")
                        st.markdown(f"**Tasks:** {task_count} | **Sub-Projects:** {subproject_count}")
                        if description:
                            st.markdown(f"{description[:100]}..." if len(description) > 100 else description)
                    with col2:
                        st.button("View Details", key=f"view_{project_id}", 
                                 on_click=view_project_details, args=(project_id, name),
                                 use_container_width=True)
                    st.markdown("---")
        else:
            st.info("No projects added yet. Use the 'Add New Project' button to create a project.")
    
    # DETAIL VIEW
    else:  # st.session_state.view == "detail"
        project_id = st.session_state.selected_project_id
        project_name = st.session_state.selected_project_name
        
        # Back button
        st.button("← Back to Projects List", on_click=back_to_list)
        
        # Project header
        st.header(f"Project: {project_name}")
        
        # Get project details
        project_details = db.execute_query("""
            SELECT p.description, p.start_date, p.end_date, p.assigned_to
            FROM projects p
            WHERE p.id = ?
        """, (project_id,))[0]
        
        description, start_date, end_date, assigned_to = project_details
        
        # Format dates
        start_date = start_date.split('T')[0] if 'T' in start_date else start_date
        end_date = end_date.split('T')[0] if 'T' in end_date else end_date
        
        # Get assigned person name
        assigned_name = member_dict.get(assigned_to, "Unassigned") if assigned_to else "Unassigned"
        
        # Display project details
        st.markdown(f"**Timeline:** {start_date} to {end_date} | **Assigned to:** {assigned_name}")
        st.markdown(f"**Description:** {description}")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["Tasks", "Sub-Projects", "Notes & Reminders", "Activity Log"])
        
        # Tasks Tab
        with tab1:
            st.subheader("Project Tasks")
            
            # Get tasks for this project
            tasks = db.execute_query("""
                SELECT t.id, t.name, t.description, t.jira_ticket, t.status, t.assigned_to
                FROM tasks t
                WHERE t.project_id = ? AND t.sub_project_id IS NULL
            """, (project_id,))
            
            if tasks:
                # Convert to DataFrame for the editable table
                tasks_df = pd.DataFrame(tasks, 
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
                
                # Add action buttons for each task
                for index, row in tasks_df.iterrows():
                    task_id = row["ID"]
                    task_name = row["Name"]
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.container(border=True):
                            st.markdown(f"**{task_name}**")
                            st.markdown(f"**{row['Description'][:100]}...**")
                    with col2:
                        if st.button("📝 Add Note", key=f"note_btn_{task_id}", use_container_width=True):
                            open_note_modal(task_id, task_name)
                        if st.button("🔔 Add Reminder", key=f"reminder_btn_{task_id}", use_container_width=True):
                            open_reminder_modal(task_id, task_name)
                    st.markdown("---")
                
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
        
        # Sub-Projects Tab
        with tab2:
            st.subheader("Sub-Projects")
            
            # Get sub-projects for this project
            sub_projects = db.execute_query("""
                SELECT sp.id, sp.name, sp.description, sp.start_date, sp.end_date, sp.assigned_to
                FROM sub_projects sp
                WHERE sp.project_id = ?
            """, (project_id,))
            
            if sub_projects:
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
                            
                            # Add action buttons for each sub-task
                            for index, row in sub_tasks_df.iterrows():
                                sub_task_id = row["ID"]
                                sub_task_name = row["Name"]
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("📝 Add Note", key=f"note_btn_sub_{sub_task_id}", use_container_width=True):
                                        open_note_modal(sub_task_id, sub_task_name)
                                with col2:
                                    if st.button("🔔 Add Reminder", key=f"reminder_btn_sub_{sub_task_id}", use_container_width=True):
                                        open_reminder_modal(sub_task_id, sub_task_name)
                            
                            # Handle sub-task deletions and updates (similar to project tasks)
                            for index, row in edited_sub_tasks_df.iterrows():
                                if row["Delete"] and index < len(sub_tasks_df):
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
                                
                                if index < len(sub_tasks_df):  # This is an edit to existing row
                                    # Check for status changes
                                    if row["Status"] != row["Change Status"]:
                                        db.execute_query(
                                            "UPDATE tasks SET status = ? WHERE id = ?",
                                            (row["Change Status"], row["ID"])
                                        )
                                        st.success(f"Updated status for task '{row['Name']}' to {row['Change Status']}")
                                        st.rerun()
                                    
                                    # Check for assigned person changes
                                    current_assigned = sub_tasks_df.iloc[index]["Assigned To Name"]
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
                                    if not sub_tasks_df.iloc[index][["Name", "Description", "Jira Ticket"]].equals(
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
                                            (project_id, sub_project_id, row["Name"], row["Description"] or "", row["Jira Ticket"] or "", 
                                             row["Change Status"], assigned_to)
                                        )
                                        st.success(f"Added new task: {row['Name']}")
                                        st.rerun()
                        else:
                            st.info(f"No tasks for sub-project {sub_name} yet.")
                            
                            # Show an empty table with structure for adding new tasks
                            empty_sub_tasks_df = pd.DataFrame(columns=["Name", "Description", "Jira Ticket", "Change Status", "Assigned To Name"])
                            edited_empty_sub_tasks_df = st.data_editor(
                                empty_sub_tasks_df,
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
                                key=f"empty_sub_tasks_df_{sub_id}"
                            )
                            
                            # Handle new sub-task additions
                            for _, row in edited_empty_sub_tasks_df.iterrows():
                                if not pd.isna(row["Name"]):
                                    # Find member_id from name
                                    assigned_to = None
                                    if not pd.isna(row["Assigned To Name"]) and row["Assigned To Name"] != "Unassigned":
                                        assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                                    
                                    db.execute_query(
                                        """INSERT INTO tasks 
                                           (project_id, sub_project_id, name, description, jira_ticket, status, assigned_to)
                                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                        (project_id, sub_project_id, row["Name"], row["Description"] or "", row["Jira Ticket"] or "", 
                                         row["Change Status"], assigned_to)
                                    )
                                    st.success(f"Added new task: {row['Name']}")
                                    st.rerun()
            else:
                st.info(f"No sub-projects for {project_name} yet.")
        
        # Notes & Reminders Tab
        with tab3:
            # Get all tasks for this project (including sub-project tasks)
            all_tasks = db.execute_query("""
                SELECT t.id, t.name
                FROM tasks t
                WHERE t.project_id = ? OR t.sub_project_id IN (
                    SELECT sp.id FROM sub_projects sp WHERE sp.project_id = ?
                )
            """, (project_id, project_id))
            
            if all_tasks:
                task_ids = [t[0] for t in all_tasks]
                task_names = {t[0]: t[1] for t in all_tasks}
                
                # Create two columns for notes and reminders
                notes_col, reminders_col = st.columns(2)
                
                # Notes section in left column
                with notes_col:
                    st.subheader("Notes")
                    
                    notes = db.execute_query("""
                        SELECT n.id, n.task_id, n.note, n.created_at
                        FROM notes n
                        WHERE n.task_id IN ({})
                        ORDER BY n.created_at DESC
                    """.format(','.join(['?'] * len(task_ids))), task_ids)
                    
                    if notes:
                        # Create a container for scrollable notes list
                        notes_container = st.container()
                        with notes_container:
                            for note_id, task_id, note_text, created_at in notes:
                                # Format date
                                created_at = created_at.split('T')[0] + " " + created_at.split('T')[1][:8] if 'T' in created_at else created_at
                                
                                # Create a card-like display for each note
                                st.markdown(f"""
                                <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px;">
                                    <p style="color:#888; font-size:0.8em;">{created_at} | Task: <b>{task_names[task_id]}</b></p>
                                    <p>{note_text}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Add delete button below each note
                                if st.button("Delete Note", key=f"del_note_{note_id}", use_container_width=True):
                                    db.execute_query("DELETE FROM notes WHERE id = ?", (note_id,))
                                    st.success("Note deleted successfully!")
                                    st.rerun()
                    else:
                        st.info("No notes for this project yet.")
                
                # Reminders section in right column
                with reminders_col:
                    st.subheader("Reminders")
                    
                    # Get today's date for highlighting
                    today = datetime.now().date().isoformat()
                    
                    reminders = db.execute_query("""
                        SELECT r.id, r.task_id, r.reminder_date, r.note, r.followed_up
                        FROM reminders r
                        WHERE r.task_id IN ({})
                        ORDER BY 
                            r.followed_up ASC,  -- Pending reminders first
                            CASE 
                                WHEN r.reminder_date = ? THEN 0  -- Today's reminders
                                WHEN r.reminder_date < ? THEN 1  -- Overdue reminders
                                ELSE 2  -- Future reminders
                            END,
                            r.reminder_date ASC  -- Chronological order
                    """.format(','.join(['?'] * len(task_ids))), task_ids + [today, today])
                    
                    if reminders:
                        # Create a container for scrollable reminders list
                        reminders_container = st.container()
                        with reminders_container:
                            for reminder_id, task_id, reminder_date, reminder_note, followed_up in reminders:
                                # Format date
                                reminder_date = reminder_date.split('T')[0] if 'T' in reminder_date else reminder_date
                                
                                # Determine if this is today's reminder
                                is_today = reminder_date == today
                                is_overdue = reminder_date < today
                                
                                # Set background color based on status
                                bg_color = "#ffcccc" if is_today and not followed_up else \
                                          "#ffe6cc" if is_overdue and not followed_up else \
                                          "#e6ffe6" if followed_up else "#f9f9f9"
                                
                                status = "✅ Followed up" if followed_up else \
                                        "⚠️ Overdue" if is_overdue else \
                                        "🔔 Today" if is_today else "⏰ Upcoming"
                                
                                # Create a card-like display for each reminder with appropriate highlighting
                                st.markdown(f"""
                                <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px; background-color:{bg_color};">
                                    <p style="color:#555; font-size:0.8em;">{reminder_date} | Task: <b>{task_names[task_id]}</b> | <span style="font-weight:bold;">{status}</span></p>
                                    <p>{reminder_note}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Add action buttons below each reminder
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Delete", key=f"del_reminder_{reminder_id}", use_container_width=True):
                                        db.execute_query("DELETE FROM reminders WHERE id = ?", (reminder_id,))
                                        st.success("Reminder deleted successfully!")
                                        st.rerun()
                                with col2:
                                    if not followed_up:
                                        if st.button("Mark Complete", key=f"followup_{reminder_id}", use_container_width=True):
                                            db.execute_query("UPDATE reminders SET followed_up = 1 WHERE id = ?", (reminder_id,))
                                            st.success("Reminder marked as followed up!")
                                            st.rerun()
                                    else:
                                        if st.button("Mark Pending", key=f"pending_{reminder_id}", use_container_width=True):
                                            db.execute_query("UPDATE reminders SET followed_up = 0 WHERE id = ?", (reminder_id,))
                                            st.success("Reminder marked as pending!")
                                            st.rerun()
                    else:
                        st.info("No reminders for this project yet.")
            else:
                st.info("No tasks in this project yet. Add tasks to create notes and reminders.")
        
        # Activity Log Tab
        with tab4:
            st.subheader("Activity Log")
            
            # Get activity logs for this project
            activity_logs = db.get_project_activity_logs(project_id)
            
            if activity_logs:
                # Create a container for scrollable activity log
                log_container = st.container()
                with log_container:
                    for log_id, timestamp, action_type, entity_type, entity_id, entity_name, description in activity_logs:
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
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No activity logs for this project yet.") 