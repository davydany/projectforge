import streamlit as st
import pandas as pd
import utils.database as db

def app():
    st.header("Team Management")
    
    # Display existing teams in an editable table
    st.subheader("Teams")
    teams_data = db.execute_query("SELECT id, name, description, location FROM teams")
    
    if teams_data:
        # Convert to DataFrame for the editable table
        df = pd.DataFrame(teams_data, columns=["ID", "Name", "Description", "Location"])
        
        # Add a column for team members (for display only)
        team_members = {}
        for team_id, _, _, _ in teams_data:
            members = db.execute_query(
                "SELECT first_name, last_name FROM team_members WHERE team_id = ?", 
                (team_id,)
            )
            if members:
                team_members[team_id] = ", ".join([f"{m[0]} {m[1]}" for m in members])
            else:
                team_members[team_id] = "None"
        
        df["Members"] = df["ID"].apply(lambda x: team_members.get(x, "None"))
        
        # Add a delete button column
        df["Delete"] = False
        
        # Create an editable dataframe
        edited_df = st.data_editor(
            df,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "Name": st.column_config.TextColumn("Name"),
                "Description": st.column_config.TextColumn("Description"),
                "Location": st.column_config.TextColumn("Location"),
                "Members": st.column_config.TextColumn("Team Members", disabled=True),
                "Delete": st.column_config.CheckboxColumn("Delete?", help="Select to delete this team")
            },
            hide_index=True,
            num_rows="dynamic"
        )
        
        # Handle deletions first
        for index, row in edited_df.iterrows():
            if row["Delete"] and index < len(df):
                # Check if team has members
                member_count = db.execute_query(
                    "SELECT COUNT(*) FROM team_members WHERE team_id = ?", 
                    (row["ID"],)
                )[0][0]
                
                if member_count > 0:
                    st.error(f"Cannot delete team '{row['Name']}' with members. Please reassign or delete members first.")
                else:
                    db.execute_query("DELETE FROM teams WHERE id = ?", (row["ID"],))
                    st.success(f"Team '{row['Name']}' deleted successfully!")
                    st.rerun()
        
        # Check for changes and update database
        if not df[["ID", "Name", "Description", "Location"]].equals(
            edited_df[["ID", "Name", "Description", "Location"]]
        ):
            for index, row in edited_df.iterrows():
                if index < len(df):  # This is an edit to existing row
                    if not df.iloc[index][["Name", "Description", "Location"]].equals(
                        row[["Name", "Description", "Location"]]
                    ):
                        db.execute_query(
                            "UPDATE teams SET name = ?, description = ?, location = ? WHERE id = ?",
                            (row["Name"], row["Description"], row["Location"], row["ID"])
                        )
                        st.success(f"Updated team: {row['Name']}")
                else:  # This is a new row
                    if not pd.isna(row["Name"]):  # Only add if name is not empty
                        db.execute_query(
                            "INSERT INTO teams (name, description, location) VALUES (?, ?, ?)",
                            (row["Name"], row["Description"] or "", row["Location"] or "")
                        )
                        st.success(f"Added new team: {row['Name']}")
                        st.rerun()
    else:
        st.info("No teams added yet.")
        
        # Show an empty table with structure for adding new teams
        empty_df = pd.DataFrame(columns=["Name", "Description", "Location"])
        edited_df = st.data_editor(
            empty_df,
            num_rows="dynamic",
            hide_index=True
        )
        
        # Handle new team additions
        for _, row in edited_df.iterrows():
            if not pd.isna(row["Name"]):  # Only add if name is not empty
                db.execute_query(
                    "INSERT INTO teams (name, description, location) VALUES (?, ?, ?)",
                    (row["Name"], row["Description"] or "", row["Location"] or "")
                )
                st.success(f"Added new team: {row['Name']}")
                st.rerun()
    
    # Add team form in an expander (alternative method)
    with st.expander("➕ Add New Team", expanded=False):
        st.subheader("Add New Team")
        name = st.text_input("Team Name")
        description = st.text_area("Description")
        location = st.text_input("Location")
        
        if st.button("Add Team"):
            db.execute_query("INSERT INTO teams (name, description, location) VALUES (?, ?, ?)", 
                          (name, description, location))
            st.success("Team added successfully!")
            st.rerun()  # Refresh the page to show the new team 