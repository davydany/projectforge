import streamlit as st
import pandas as pd
import utils.database as db

def app():
    st.header("Team Member Management")
    
    # Display existing team members in an editable table
    st.subheader("Team Members")
    
    # Get team data for the dropdown
    teams = db.get_teams()
    team_dict = {id: name for id, name in teams}
    team_options = [""] + [name for _, name in teams]
    
    # Get member data
    members_data = db.execute_query("""
        SELECT tm.id, tm.first_name, tm.last_name, tm.email, tm.team_id 
        FROM team_members tm
    """)
    
    if members_data:
        # Convert to DataFrame for the editable table
        df = pd.DataFrame(members_data, columns=["ID", "First Name", "Last Name", "Email", "Team ID"])
        df["Team"] = df["Team ID"].apply(lambda x: team_dict.get(x, ""))
        
        # Add a column for assigned tasks (for display only)
        assigned_tasks = {}
        for member_id, _, _, _, _ in members_data:
            tasks = db.execute_query(
                "SELECT name FROM tasks WHERE assigned_to = ?", 
                (member_id,)
            )
            if tasks:
                assigned_tasks[member_id] = ", ".join([task[0] for task in tasks])
            else:
                assigned_tasks[member_id] = "None"
        
        df["Tasks"] = df["ID"].apply(lambda x: assigned_tasks.get(x, "None"))
        
        # Add a delete button column
        df["Delete"] = False
        
        # Create an editable dataframe
        edited_df = st.data_editor(
            df,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "First Name": st.column_config.TextColumn("First Name"),
                "Last Name": st.column_config.TextColumn("Last Name"),
                "Email": st.column_config.TextColumn("Email"),
                "Team": st.column_config.SelectboxColumn(
                    "Team",
                    options=team_options,
                    required=True
                ),
                "Team ID": st.column_config.NumberColumn("Team ID", disabled=True),
                "Tasks": st.column_config.TextColumn("Assigned Tasks", disabled=True),
                "Delete": st.column_config.CheckboxColumn("Delete?", help="Select to delete this member")
            },
            hide_index=True,
            num_rows="dynamic"
        )
        
        # Handle deletions first
        for index, row in edited_df.iterrows():
            if row["Delete"] and index < len(df):
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
        if not df[["ID", "First Name", "Last Name", "Email", "Team"]].equals(
            edited_df[["ID", "First Name", "Last Name", "Email", "Team"]]
        ):
            for index, row in edited_df.iterrows():
                if index < len(df):  # This is an edit to existing row
                    if not df.iloc[index][["First Name", "Last Name", "Email", "Team"]].equals(
                        row[["First Name", "Last Name", "Email", "Team"]]
                    ):
                        # Find team_id from team name
                        team_id = next((id for id, name in teams if name == row["Team"]), None)
                        
                        if team_id is not None:
                            db.execute_query(
                                """UPDATE team_members 
                                   SET first_name = ?, last_name = ?, email = ?, team_id = ? 
                                   WHERE id = ?""",
                                (row["First Name"], row["Last Name"], row["Email"], team_id, row["ID"])
                            )
                            st.success(f"Updated team member: {row['First Name']} {row['Last Name']}")
                else:  # This is a new row
                    if not pd.isna(row["First Name"]) and not pd.isna(row["Last Name"]) and not pd.isna(row["Team"]):
                        # Find team_id from team name
                        team_id = next((id for id, name in teams if name == row["Team"]), None)
                        
                        if team_id is not None:
                            db.execute_query(
                                """INSERT INTO team_members 
                                   (first_name, last_name, email, team_id) 
                                   VALUES (?, ?, ?, ?)""",
                                (row["First Name"], row["Last Name"], row["Email"] or "", team_id)
                            )
                            st.success(f"Added new team member: {row['First Name']} {row['Last Name']}")
                            st.rerun()
    else:
        st.info("No team members added yet.")
        
        # Show an empty table with structure for adding new members
        if teams:
            empty_df = pd.DataFrame(columns=["First Name", "Last Name", "Email", "Team"])
            edited_df = st.data_editor(
                empty_df,
                column_config={
                    "Team": st.column_config.SelectboxColumn(
                        "Team",
                        options=team_options,
                        required=True
                    )
                },
                num_rows="dynamic",
                hide_index=True
            )
            
            # Handle new member additions
            for _, row in edited_df.iterrows():
                if not pd.isna(row["First Name"]) and not pd.isna(row["Last Name"]) and not pd.isna(row["Team"]):
                    # Find team_id from team name
                    team_id = next((id for id, name in teams if name == row["Team"]), None)
                    
                    if team_id is not None:
                        db.execute_query(
                            """INSERT INTO team_members 
                               (first_name, last_name, email, team_id) 
                               VALUES (?, ?, ?, ?)""",
                            (row["First Name"], row["Last Name"], row["Email"] or "", team_id)
                        )
                        st.success(f"Added new team member: {row['First Name']} {row['Last Name']}")
                        st.rerun()
        else:
            st.warning("Please add a team first before adding team members.")
    
    # Add team member form in an expander (alternative method)
    with st.expander("➕ Add New Team Member", expanded=False):
        st.subheader("Add New Team Member")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        
        if teams:
            team = st.selectbox("Select Team", [name for _, name in teams])
            team_id = next((id for id, name in teams if name == team), None)
            
            if st.button("Add Team Member"):
                db.execute_query(
                    "INSERT INTO team_members (first_name, last_name, email, team_id) VALUES (?, ?, ?, ?)",
                    (first_name, last_name, email, team_id)
                )
                st.success("Team member added successfully!")
                st.rerun()  # Refresh the page to show the new member
        else:
            st.warning("Please add a team first before adding team members.") 