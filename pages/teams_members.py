import streamlit as st
import pandas as pd
import utils.database as db

def app():
    st.header("Team Management")
    
    # Add buttons at the top for adding teams and members
    col1, col2 = st.columns(2)
    with col1:
        add_team_button = st.button("➕ Add New Team", use_container_width=True)
    with col2:
        add_member_button = st.button("➕ Add New Team Member", use_container_width=True)
    
    # Add Team Dialog
    if add_team_button:
        with st.form(key="add_team_form"):
            st.subheader("Add New Team")
            name = st.text_input("Team Name")
            description = st.text_area("Description")
            location = st.text_input("Location")
            
            submit_button = st.form_submit_button("Add Team")
            if submit_button and name:  # Ensure name is not empty
                db.execute_query("INSERT INTO teams (name, description, location) VALUES (?, ?, ?)", 
                              (name, description, location))
                st.success("Team added successfully!")
                st.rerun()  # Refresh the page to show the new team
    
    # Add Team Member Dialog
    if add_member_button:
        with st.form(key="add_member_form"):
            st.subheader("Add New Team Member")
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email")
            
            teams = db.get_teams()
            if teams:
                team_options = [name for _, name in teams]
                team = st.selectbox("Select Team", team_options)
                team_id = next((id for id, name in teams if name == team), None)
                
                submit_button = st.form_submit_button("Add Team Member")
                if submit_button and first_name and last_name:  # Ensure required fields are not empty
                    db.execute_query(
                        "INSERT INTO team_members (first_name, last_name, email, team_id) VALUES (?, ?, ?, ?)",
                        (first_name, last_name, email, team_id)
                    )
                    st.success("Team member added successfully!")
                    st.rerun()  # Refresh the page to show the new member
            else:
                st.warning("Please add a team first before adding team members.")
                st.form_submit_button("Add Team Member", disabled=True)
    
    # Display teams and their members
    teams_data = db.execute_query("SELECT id, name, description, location FROM teams")
    
    if teams_data:
        for team_id, team_name, description, location in teams_data:
            st.subheader(f"Team: {team_name}")
            
            # Team details in an expander
            with st.expander("Team Details", expanded=False):
                # Create a dataframe for the team details
                team_df = pd.DataFrame({
                    "ID": [team_id],
                    "Name": [team_name],
                    "Description": [description],
                    "Location": [location],
                    "Delete": [False]
                })
                
                # Create an editable dataframe for team details
                edited_team_df = st.data_editor(
                    team_df,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", disabled=True),
                        "Name": st.column_config.TextColumn("Name"),
                        "Description": st.column_config.TextColumn("Description"),
                        "Location": st.column_config.TextColumn("Location"),
                        "Delete": st.column_config.CheckboxColumn("Delete?", help="Select to delete this team")
                    },
                    hide_index=True,
                    disabled=["ID"]
                )
                
                # Handle team deletion
                if edited_team_df.iloc[0]["Delete"]:
                    # Check if team has members
                    member_count = db.execute_query(
                        "SELECT COUNT(*) FROM team_members WHERE team_id = ?", 
                        (team_id,)
                    )[0][0]
                    
                    if member_count > 0:
                        st.error(f"Cannot delete team '{team_name}' with members. Please delete members first.")
                    else:
                        db.execute_query("DELETE FROM teams WHERE id = ?", (team_id,))
                        st.success(f"Team '{team_name}' deleted successfully!")
                        st.rerun()
                
                # Handle team updates
                if not team_df[["Name", "Description", "Location"]].equals(
                    edited_team_df[["Name", "Description", "Location"]]
                ):
                    row = edited_team_df.iloc[0]
                    db.execute_query(
                        "UPDATE teams SET name = ?, description = ?, location = ? WHERE id = ?",
                        (row["Name"], row["Description"], row["Location"], team_id)
                    )
                    st.success(f"Updated team: {row['Name']}")
                    st.rerun()
            
            # Get team members
            members = db.execute_query("""
                SELECT tm.id, tm.first_name, tm.last_name, tm.email, tm.team_id 
                FROM team_members tm
                WHERE tm.team_id = ?
            """, (team_id,))
            
            if members:
                # Convert to DataFrame for the editable table
                members_df = pd.DataFrame(members, columns=["ID", "First Name", "Last Name", "Email", "Team ID"])
                
                # Add a column for assigned tasks (for display only)
                assigned_tasks = {}
                for member_id, _, _, _, _ in members:
                    tasks = db.execute_query(
                        "SELECT name FROM tasks WHERE assigned_to = ?", 
                        (member_id,)
                    )
                    if tasks:
                        assigned_tasks[member_id] = ", ".join([task[0] for task in tasks])
                    else:
                        assigned_tasks[member_id] = "None"
                
                members_df["Tasks"] = members_df["ID"].apply(lambda x: assigned_tasks.get(x, "None"))
                
                # Add a delete button column
                members_df["Delete"] = False
                
                # Create an editable dataframe
                edited_members_df = st.data_editor(
                    members_df,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", disabled=True),
                        "First Name": st.column_config.TextColumn("First Name"),
                        "Last Name": st.column_config.TextColumn("Last Name"),
                        "Email": st.column_config.TextColumn("Email"),
                        "Team ID": st.column_config.NumberColumn("Team ID", disabled=True),
                        "Tasks": st.column_config.TextColumn("Assigned Tasks", disabled=True),
                        "Delete": st.column_config.CheckboxColumn("Delete?", help="Select to delete this member")
                    },
                    hide_index=True,
                    num_rows="dynamic"
                )
                
                # Handle member deletions
                for index, row in edited_members_df.iterrows():
                    if row["Delete"] and index < len(members_df):
                        # Check if member has tasks
                        task_count = db.execute_query(
                            "SELECT COUNT(*) FROM tasks WHERE assigned_to = ?", 
                            (row["ID"],)
                        )[0][0]
                        
                        if task_count > 0:
                            st.error(f"Cannot delete member '{row['First Name']} {row['Last Name']}' with assigned tasks. Please reassign tasks first.")
                        else:
                            db.execute_query("DELETE FROM team_members WHERE id = ?", (row["ID"],))
                            st.success(f"Team member '{row['First Name']} {row['Last Name']}' deleted successfully!")
                            st.rerun()
                
                # Check for changes and update database
                if not members_df[["ID", "First Name", "Last Name", "Email"]].equals(
                    edited_members_df[["ID", "First Name", "Last Name", "Email"]]
                ):
                    for index, row in edited_members_df.iterrows():
                        if index < len(members_df):  # This is an edit to existing row
                            if not members_df.iloc[index][["First Name", "Last Name", "Email"]].equals(
                                row[["First Name", "Last Name", "Email"]]
                            ):
                                db.execute_query(
                                    """UPDATE team_members 
                                       SET first_name = ?, last_name = ?, email = ? 
                                       WHERE id = ?""",
                                    (row["First Name"], row["Last Name"], row["Email"], row["ID"])
                                )
                                st.success(f"Updated team member: {row['First Name']} {row['Last Name']}")
                        else:  # This is a new row
                            if not pd.isna(row["First Name"]) and not pd.isna(row["Last Name"]):
                                db.execute_query(
                                    """INSERT INTO team_members 
                                       (first_name, last_name, email, team_id) 
                                       VALUES (?, ?, ?, ?)""",
                                    (row["First Name"], row["Last Name"], row["Email"] or "", team_id)
                                )
                                st.success(f"Added new team member: {row['First Name']} {row['Last Name']}")
                                st.rerun()
            else:
                st.info(f"No members in team {team_name} yet.")
                
                # Show an empty table with structure for adding new members
                empty_members_df = pd.DataFrame(columns=["First Name", "Last Name", "Email"])
                edited_empty_df = st.data_editor(
                    empty_members_df,
                    num_rows="dynamic",
                    hide_index=True
                )
                
                # Handle new member additions
                for _, row in edited_empty_df.iterrows():
                    if not pd.isna(row["First Name"]) and not pd.isna(row["Last Name"]):
                        db.execute_query(
                            """INSERT INTO team_members 
                               (first_name, last_name, email, team_id) 
                               VALUES (?, ?, ?, ?)""",
                            (row["First Name"], row["Last Name"], row["Email"] or "", team_id)
                        )
                        st.success(f"Added new team member: {row['First Name']} {row['Last Name']}")
                        st.rerun()
    else:
        st.info("No teams added yet. Use the 'Add New Team' button to create a team.") 