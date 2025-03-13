import streamlit as st
import utils.database as db

def app():
    st.header("Team Member Management")
    
    # Display existing team members first
    st.subheader("Team Members")
    members = db.execute_query("""
        SELECT tm.id, tm.first_name, tm.last_name, tm.email, t.name 
        FROM team_members tm
        JOIN teams t ON tm.team_id = t.id
    """)
    
    if members:
        for member in members:
            with st.expander(f"{member[1]} {member[2]}"):
                st.write(f"**Email:** {member[3]}")
                st.write(f"**Team:** {member[4]}")
                
                # Get assigned tasks
                tasks = db.execute_query(
                    "SELECT name FROM tasks WHERE assigned_to = ?", 
                    (member[0],)
                )
                
                if tasks:
                    st.write("**Assigned Tasks:**")
                    for task in tasks:
                        st.write(f"- {task[0]}")
                else:
                    st.write("No tasks assigned yet.")
    else:
        st.info("No team members added yet.")
    
    # Add team member form in an expander
    with st.expander("➕ Add New Team Member", expanded=False):
        st.subheader("Add New Team Member")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        
        teams = db.get_teams()
        team_dict = {name: id for id, name in teams}
        
        if teams:
            team = st.selectbox("Select Team", list(team_dict.keys()))
            
            if st.button("Add Team Member"):
                db.execute_query(
                    "INSERT INTO team_members (first_name, last_name, email, team_id) VALUES (?, ?, ?, ?)",
                    (first_name, last_name, email, team_dict[team])
                )
                st.success("Team member added successfully!")
                st.rerun()  # Refresh the page to show the new member
        else:
            st.warning("Please add a team first before adding team members.") 