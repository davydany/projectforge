import streamlit as st
import pandas as pd
from datetime import datetime
import utils.database as db

def app():
    st.header("Project Management")
    
    # Display existing projects in an editable table
    st.subheader("Projects")
    
    # Get team members for dropdown
    members = db.get_team_members()
    member_dict = {id: f"{first} {last}" for id, first, last in members}
    member_options = ["Unassigned"] + [f"{first} {last}" for _, first, last in members]
    
    # Get projects data
    projects_data = db.execute_query("""
        SELECT p.id, p.name, p.description, p.start_date, p.end_date, p.assigned_to
        FROM projects p
    """)
    
    if projects_data:
        # Convert to DataFrame for the editable table
        df = pd.DataFrame(projects_data, columns=["ID", "Name", "Description", "Start Date", "End Date", "Assigned To"])
        
        # Format dates and assigned_to
        df["Start Date"] = df["Start Date"].apply(lambda x: x.split('T')[0] if 'T' in x else x)
        df["End Date"] = df["End Date"].apply(lambda x: x.split('T')[0] if 'T' in x else x)
        df["Assigned To Name"] = df["Assigned To"].apply(lambda x: member_dict.get(x, "Unassigned") if x else "Unassigned")
        
        # Add a column for sub-projects (for display only)
        sub_projects = {}
        for project_id, _, _, _, _, _ in projects_data:
            subs = db.execute_query(
                """SELECT sp.name FROM sub_projects sp WHERE sp.project_id = ?""", 
                (project_id,)
            )
            if subs:
                sub_projects[project_id] = ", ".join([sub[0] for sub in subs])
            else:
                sub_projects[project_id] = "None"
        
        df["Sub-Projects"] = df["ID"].apply(lambda x: sub_projects.get(x, "None"))
        
        # Add a delete button column
        df["Delete"] = False
        
        # Create an editable dataframe
        edited_df = st.data_editor(
            df,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "Name": st.column_config.TextColumn("Name"),
                "Description": st.column_config.TextColumn("Description"),
                "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                "End Date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD"),
                "Assigned To": st.column_config.NumberColumn("Assigned To ID", disabled=True, visible=False),
                "Assigned To Name": st.column_config.SelectboxColumn(
                    "Assigned To",
                    options=member_options,
                    required=True
                ),
                "Sub-Projects": st.column_config.TextColumn("Sub-Projects", disabled=True),
                "Delete": st.column_config.CheckboxColumn("Delete?", help="Select to delete this project")
            },
            hide_index=True,
            num_rows="dynamic"
        )
        
        # Handle deletions first
        for index, row in edited_df.iterrows():
            if row["Delete"] and index < len(df):
                # Check if project has sub-projects
                sub_count = db.execute_query(
                    "SELECT COUNT(*) FROM sub_projects WHERE project_id = ?", 
                    (row["ID"],)
                )[0][0]
                
                # Check if project has tasks
                task_count = db.execute_query(
                    "SELECT COUNT(*) FROM tasks WHERE project_id = ?", 
                    (row["ID"],)
                )[0][0]
                
                if sub_count > 0 or task_count > 0:
                    st.error(f"Cannot delete project '{row['Name']}' with sub-projects or tasks. Please delete them first.")
                else:
                    db.execute_query("DELETE FROM projects WHERE id = ?", (row["ID"],))
                    st.success(f"Project '{row['Name']}' deleted successfully!")
                    st.rerun()
        
        # Check for changes and update database
        if not df[["ID", "Name", "Description", "Start Date", "End Date", "Assigned To Name"]].equals(
            edited_df[["ID", "Name", "Description", "Start Date", "End Date", "Assigned To Name"]]
        ):
            for index, row in edited_df.iterrows():
                if index < len(df):  # This is an edit to existing row
                    if not df.iloc[index][["Name", "Description", "Start Date", "End Date", "Assigned To Name"]].equals(
                        row[["Name", "Description", "Start Date", "End Date", "Assigned To Name"]]
                    ):
                        # Find member_id from name
                        assigned_to = None
                        if row["Assigned To Name"] != "Unassigned":
                            assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                        
                        # Format dates for database
                        start_date = row["Start Date"]
                        end_date = row["End Date"]
                        if isinstance(start_date, pd.Timestamp):
                            start_date = start_date.strftime("%Y-%m-%d")
                        if isinstance(end_date, pd.Timestamp):
                            end_date = end_date.strftime("%Y-%m-%d")
                        
                        db.execute_query(
                            """UPDATE projects 
                               SET name = ?, description = ?, start_date = ?, end_date = ?, assigned_to = ? 
                               WHERE id = ?""",
                            (row["Name"], row["Description"], start_date, end_date, assigned_to, row["ID"])
                        )
                        st.success(f"Updated project: {row['Name']}")
                else:  # This is a new row
                    if not pd.isna(row["Name"]) and not pd.isna(row["Start Date"]) and not pd.isna(row["End Date"]):
                        # Find member_id from name
                        assigned_to = None
                        if not pd.isna(row["Assigned To Name"]) and row["Assigned To Name"] != "Unassigned":
                            assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                        
                        # Format dates for database
                        start_date = row["Start Date"]
                        end_date = row["End Date"]
                        if isinstance(start_date, pd.Timestamp):
                            start_date = start_date.strftime("%Y-%m-%d")
                        if isinstance(end_date, pd.Timestamp):
                            end_date = end_date.strftime("%Y-%m-%d")
                        
                        db.execute_query(
                            """INSERT INTO projects 
                               (name, description, start_date, end_date, assigned_to) 
                               VALUES (?, ?, ?, ?, ?)""",
                            (row["Name"], row["Description"] or "", start_date, end_date, assigned_to)
                        )
                        st.success(f"Added new project: {row['Name']}")
                        st.rerun()
    else:
        st.info("No projects added yet.")
        
        # Show an empty table with structure for adding new projects
        empty_df = pd.DataFrame(columns=["Name", "Description", "Start Date", "End Date", "Assigned To Name"])
        edited_df = st.data_editor(
            empty_df,
            column_config={
                "Name": st.column_config.TextColumn("Name"),
                "Description": st.column_config.TextColumn("Description"),
                "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                "End Date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD"),
                "Assigned To Name": st.column_config.SelectboxColumn(
                    "Assigned To",
                    options=member_options,
                    required=True
                )
            },
            num_rows="dynamic",
            hide_index=True
        )
        
        # Handle new project additions
        for _, row in edited_df.iterrows():
            if not pd.isna(row["Name"]) and not pd.isna(row["Start Date"]) and not pd.isna(row["End Date"]):
                # Find member_id from name
                assigned_to = None
                if not pd.isna(row["Assigned To Name"]) and row["Assigned To Name"] != "Unassigned":
                    assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                
                # Format dates for database
                start_date = row["Start Date"]
                end_date = row["End Date"]
                if isinstance(start_date, pd.Timestamp):
                    start_date = start_date.strftime("%Y-%m-%d")
                if isinstance(end_date, pd.Timestamp):
                    end_date = end_date.strftime("%Y-%m-%d")
                
                db.execute_query(
                    """INSERT INTO projects 
                       (name, description, start_date, end_date, assigned_to) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (row["Name"], row["Description"] or "", start_date, end_date, assigned_to)
                )
                st.success(f"Added new project: {row['Name']}")
                st.rerun()
    
    # Sub-Projects Table
    st.subheader("Sub-Projects")
    
    # Get projects for dropdown
    projects = db.get_projects()
    project_dict = {id: name for id, name in projects}
    project_options = [name for _, name in projects]
    
    # Get sub-projects data
    if projects:
        sub_projects_data = db.execute_query("""
            SELECT sp.id, sp.project_id, sp.name, sp.description, sp.start_date, sp.end_date, sp.assigned_to
            FROM sub_projects sp
        """)
        
        if sub_projects_data:
            # Convert to DataFrame for the editable table
            sub_df = pd.DataFrame(sub_projects_data, 
                                 columns=["ID", "Project ID", "Name", "Description", "Start Date", "End Date", "Assigned To"])
            
            # Format dates and add parent project and assigned_to names
            sub_df["Start Date"] = sub_df["Start Date"].apply(lambda x: x.split('T')[0] if 'T' in x else x)
            sub_df["End Date"] = sub_df["End Date"].apply(lambda x: x.split('T')[0] if 'T' in x else x)
            sub_df["Project"] = sub_df["Project ID"].apply(lambda x: project_dict.get(x, "Unknown"))
            sub_df["Assigned To Name"] = sub_df["Assigned To"].apply(lambda x: member_dict.get(x, "Unassigned") if x else "Unassigned")
            
            # Add a delete button column
            sub_df["Delete"] = False
            
            # Create an editable dataframe for sub-projects
            edited_sub_df = st.data_editor(
                sub_df,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", disabled=True),
                    "Project ID": st.column_config.NumberColumn("Project ID", disabled=True, visible=False),
                    "Project": st.column_config.SelectboxColumn(
                        "Parent Project",
                        options=project_options,
                        required=True
                    ),
                    "Name": st.column_config.TextColumn("Name"),
                    "Description": st.column_config.TextColumn("Description"),
                    "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                    "End Date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD"),
                    "Assigned To": st.column_config.NumberColumn("Assigned To ID", disabled=True, visible=False),
                    "Assigned To Name": st.column_config.SelectboxColumn(
                        "Assigned To",
                        options=member_options,
                        required=True
                    ),
                    "Delete": st.column_config.CheckboxColumn("Delete?", help="Select to delete this sub-project")
                },
                hide_index=True,
                num_rows="dynamic"
            )
            
            # Handle deletions first
            for index, row in edited_sub_df.iterrows():
                if row["Delete"] and index < len(sub_df):
                    # Check if sub-project has tasks
                    task_count = db.execute_query(
                        "SELECT COUNT(*) FROM tasks WHERE sub_project_id = ?", 
                        (row["ID"],)
                    )[0][0]
                    
                    if task_count > 0:
                        st.error(f"Cannot delete sub-project '{row['Name']}' with tasks. Please delete tasks first.")
                    else:
                        db.execute_query("DELETE FROM sub_projects WHERE id = ?", (row["ID"],))
                        st.success(f"Sub-project '{row['Name']}' deleted successfully!")
                        st.rerun()
            
            # Check for changes and update database
            if not sub_df[["ID", "Project", "Name", "Description", "Start Date", "End Date", "Assigned To Name"]].equals(
                edited_sub_df[["ID", "Project", "Name", "Description", "Start Date", "End Date", "Assigned To Name"]]
            ):
                for index, row in edited_sub_df.iterrows():
                    if index < len(sub_df):  # This is an edit to existing row
                        if not sub_df.iloc[index][["Project", "Name", "Description", "Start Date", "End Date", "Assigned To Name"]].equals(
                            row[["Project", "Name", "Description", "Start Date", "End Date", "Assigned To Name"]]
                        ):
                            # Find project_id from name
                            project_id = next((id for id, name in projects if name == row["Project"]), None)
                            
                            # Find member_id from name
                            assigned_to = None
                            if row["Assigned To Name"] != "Unassigned":
                                assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                            
                            # Format dates for database
                            start_date = row["Start Date"]
                            end_date = row["End Date"]
                            if isinstance(start_date, pd.Timestamp):
                                start_date = start_date.strftime("%Y-%m-%d")
                            if isinstance(end_date, pd.Timestamp):
                                end_date = end_date.strftime("%Y-%m-%d")
                            
                            db.execute_query(
                                """UPDATE sub_projects 
                                   SET project_id = ?, name = ?, description = ?, start_date = ?, end_date = ?, assigned_to = ? 
                                   WHERE id = ?""",
                                (project_id, row["Name"], row["Description"], start_date, end_date, assigned_to, row["ID"])
                            )
                            st.success(f"Updated sub-project: {row['Name']}")
                    else:  # This is a new row
                        if not pd.isna(row["Name"]) and not pd.isna(row["Project"]) and not pd.isna(row["Start Date"]) and not pd.isna(row["End Date"]):
                            # Find project_id from name
                            project_id = next((id for id, name in projects if name == row["Project"]), None)
                            
                            # Find member_id from name
                            assigned_to = None
                            if not pd.isna(row["Assigned To Name"]) and row["Assigned To Name"] != "Unassigned":
                                assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                            
                            # Format dates for database
                            start_date = row["Start Date"]
                            end_date = row["End Date"]
                            if isinstance(start_date, pd.Timestamp):
                                start_date = start_date.strftime("%Y-%m-%d")
                            if isinstance(end_date, pd.Timestamp):
                                end_date = end_date.strftime("%Y-%m-%d")
                            
                            db.execute_query(
                                """INSERT INTO sub_projects 
                                   (project_id, name, description, start_date, end_date, assigned_to) 
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (project_id, row["Name"], row["Description"] or "", start_date, end_date, assigned_to)
                            )
                            st.success(f"Added new sub-project: {row['Name']}")
                            st.rerun()
        else:
            st.info("No sub-projects added yet.")
            
            # Show an empty table with structure for adding new sub-projects
            empty_sub_df = pd.DataFrame(columns=["Project", "Name", "Description", "Start Date", "End Date", "Assigned To Name"])
            edited_sub_df = st.data_editor(
                empty_sub_df,
                column_config={
                    "Project": st.column_config.SelectboxColumn(
                        "Parent Project",
                        options=project_options,
                        required=True
                    ),
                    "Name": st.column_config.TextColumn("Name"),
                    "Description": st.column_config.TextColumn("Description"),
                    "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                    "End Date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD"),
                    "Assigned To Name": st.column_config.SelectboxColumn(
                        "Assigned To",
                        options=member_options,
                        required=True
                    )
                },
                num_rows="dynamic",
                hide_index=True
            )
            
            # Handle new sub-project additions
            for _, row in edited_sub_df.iterrows():
                if not pd.isna(row["Name"]) and not pd.isna(row["Project"]) and not pd.isna(row["Start Date"]) and not pd.isna(row["End Date"]):
                    # Find project_id from name
                    project_id = next((id for id, name in projects if name == row["Project"]), None)
                    
                    # Find member_id from name
                    assigned_to = None
                    if not pd.isna(row["Assigned To Name"]) and row["Assigned To Name"] != "Unassigned":
                        assigned_to = next((id for id, name in member_dict.items() if name == row["Assigned To Name"]), None)
                    
                    # Format dates for database
                    start_date = row["Start Date"]
                    end_date = row["End Date"]
                    if isinstance(start_date, pd.Timestamp):
                        start_date = start_date.strftime("%Y-%m-%d")
                    if isinstance(end_date, pd.Timestamp):
                        end_date = end_date.strftime("%Y-%m-%d")
                    
                    db.execute_query(
                        """INSERT INTO sub_projects 
                           (project_id, name, description, start_date, end_date, assigned_to) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (project_id, row["Name"], row["Description"] or "", start_date, end_date, assigned_to)
                    )
                    st.success(f"Added new sub-project: {row['Name']}")
                    st.rerun()
    else:
        st.info("Please add a project first before adding sub-projects.") 