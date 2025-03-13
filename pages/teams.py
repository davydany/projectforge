import streamlit as st
import utils.database as db

def app():
    st.header("Team Management")
    
    tab1, tab2 = st.tabs(["Add Team", "View Teams"])
    
    with tab1:
        st.subheader("Add New Team")
        name = st.text_input("Team Name")
        description = st.text_area("Description")
        location = st.text_input("Location")
        
        if st.button("Add Team"):
            db.execute_query("INSERT INTO teams (name, description, location) VALUES (?, ?, ?)", 
                          (name, description, location))
            st.success("Team added successfully!")
    
    with tab2:
        st.subheader("Existing Teams")
        teams = db.execute_query("SELECT id, name, description, location FROM teams")
        
        if teams:
            for team in teams:
                with st.expander(f"{team[1]}"):
                    st.write(f"**Description:** {team[2]}")
                    st.write(f"**Location:** {team[3]}")
                    
                    # Get team members
                    members = db.execute_query(
                        "SELECT first_name, last_name FROM team_members WHERE team_id = ?", 
                        (team[0],)
                    )
                    
                    if members:
                        st.write("**Team Members:**")
                        for member in members:
                            st.write(f"- {member[0]} {member[1]}")
                    else:
                        st.write("No team members yet.")
        else:
            st.info("No teams added yet.") 