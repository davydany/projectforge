import streamlit as st
from datetime import datetime
import utils.database as db

def app():
    st.header("Project Management")
    
    tabs = st.tabs(["Add Project", "Add Sub-Project", "View Projects"])
    
    with tabs[0]:
        st.subheader("Add New Project")
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        
        # Make assignment optional
        assign_to_member = st.checkbox("Assign to team member", value=False)
        assigned_to = None
        
        if assign_to_member:
            members = db.get_team_members()
            if members:
                member_dict = {name: id for id, name in members}
                member_name = st.selectbox("Assign To", list(member_dict.keys()))
                assigned_to = member_dict[member_name]
            else:
                st.warning("No team members available for assignment.")
        
        if st.button("Add Project"):
            db.execute_query(
                "INSERT INTO projects (name, description, start_date, end_date, assigned_to) VALUES (?, ?, ?, ?, ?)",
                (name, description, start_date.isoformat(), end_date.isoformat(), assigned_to)
            )
            st.success("Project added successfully!")
    
    with tabs[1]:
        st.subheader("Add New Sub-Project")
        projects = db.get_projects()
        
        if projects:
            proj_dict = {name: id for id, name in projects}
            parent_project = st.selectbox("Select Parent Project", list(proj_dict.keys()))
            
            name = st.text_input("Sub-Project Name", key="sub_name")
            description = st.text_area("Description", key="sub_desc")
            start_date = st.date_input("Start Date", key="sub_start")
            end_date = st.date_input("End Date", key="sub_end")
            
            # Make assignment optional for sub-projects too
            assign_to_member = st.checkbox("Assign to team member", value=False, key="sub_assign_check")
            assigned_to = None
            
            if assign_to_member:
                members = db.get_team_members()
                if members:
                    member_dict = {name: id for id, name in members}
                    member_name = st.selectbox("Assign To", list(member_dict.keys()), key="sub_assign")
                    assigned_to = member_dict[member_name]
                else:
                    st.warning("No team members available for assignment.")
            
            if st.button("Add Sub-Project"):
                db.execute_query(
                    """INSERT INTO sub_projects 
                       (project_id, name, description, start_date, end_date, assigned_to) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (proj_dict[parent_project], name, description, start_date.isoformat(), 
                     end_date.isoformat(), assigned_to)
                )
                st.success("Sub-Project added successfully!")
        else:
            st.warning("Please add a project first before adding sub-projects.")
    
    with tabs[2]:
        st.subheader("Project Overview")
        projects = db.execute_query("""
            SELECT p.id, p.name, p.description, p.start_date, p.end_date, 
                   CASE WHEN p.assigned_to IS NULL 
                        THEN 'Unassigned' 
                        ELSE tm.first_name || ' ' || tm.last_name 
                   END as assigned_to
            FROM projects p
            LEFT JOIN team_members tm ON p.assigned_to = tm.id
        """)
        
        if projects:
            for project in projects:
                with st.expander(f"{project[1]}"):
                    st.write(f"**Description:** {project[2]}")
                    st.write(f"**Timeline:** {project[3]} to {project[4]}")
                    st.write(f"**Assigned to:** {project[5]}")
                    
                    # Get sub-projects
                    sub_projects = db.execute_query(
                        """SELECT sp.name, sp.start_date, sp.end_date, 
                                  CASE WHEN sp.assigned_to IS NULL 
                                       THEN 'Unassigned' 
                                       ELSE tm.first_name || ' ' || tm.last_name 
                                  END as assigned_to
                           FROM sub_projects sp
                           LEFT JOIN team_members tm ON sp.assigned_to = tm.id
                           WHERE sp.project_id = ?""", 
                        (project[0],)
                    )
                    
                    if sub_projects:
                        st.write("**Sub-Projects:**")
                        for sub in sub_projects:
                            st.write(f"- {sub[0]} ({sub[1]} to {sub[2]}, assigned to {sub[3]})")
                    else:
                        st.write("No sub-projects yet.")
        else:
            st.info("No projects added yet.") 