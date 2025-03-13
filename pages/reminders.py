import streamlit as st
from datetime import datetime, date
import utils.database as db

def app():
    st.header("Task Reminders")
    
    tabs = st.tabs(["Add Reminder", "View Reminders"])
    
    with tabs[0]:
        st.subheader("Add Reminder to Task")
        tasks = db.get_tasks()
        
        if tasks:
            task_dict = {name: id for id, name in tasks}
            task = st.selectbox("Select Task", list(task_dict.keys()))
            reminder_date = st.date_input("Reminder Date")
            note = st.text_area("Reminder Note")
            
            if st.button("Add Reminder"):
                db.execute_query(
                    "INSERT INTO reminders (task_id, reminder_date, note) VALUES (?, ?, ?)",
                    (task_dict[task], reminder_date.isoformat(), note)
                )
                st.success("Reminder added successfully!")
        else:
            st.warning("Please add tasks first before adding reminders.")
    
    with tabs[1]:
        st.subheader("Reminders Overview")
        
        # Filter options
        show_all = st.checkbox("Show all reminders (including followed up)")
        
        if show_all:
            query = """
                SELECT r.id, t.name, r.reminder_date, r.note, r.followed_up
                FROM reminders r
                JOIN tasks t ON r.task_id = t.id
                ORDER BY r.reminder_date
            """
            reminders = db.execute_query(query)
        else:
            today = date.today().isoformat()
            query = """
                SELECT r.id, t.name, r.reminder_date, r.note, r.followed_up
                FROM reminders r
                JOIN tasks t ON r.task_id = t.id
                WHERE r.reminder_date <= ? AND r.followed_up = 0
                ORDER BY r.reminder_date
            """
            reminders = db.execute_query(query, (today,))
        
        if reminders:
            for rem in reminders:
                with st.expander(f"{rem[1]} - Due: {rem[2]}"):
                    st.write(f"**Note:** {rem[3]}")
                    st.write(f"**Status:** {'Followed up' if rem[4] else 'Needs attention'}")
                    
                    if not rem[4]:  # If not followed up
                        if st.button(f"Mark as Followed Up", key=f"followup_{rem[0]}"):
                            db.execute_query(
                                "UPDATE reminders SET followed_up = 1 WHERE id = ?", 
                                (rem[0],)
                            )
                            st.success("Marked as followed up!")
                            st.rerun()
        else:
            st.info("No reminders found.") 