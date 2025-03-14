import streamlit as st
from datetime import datetime
import utils.database as db

def app():
    st.header("Task Notes")
    
    # Display notes by task
    st.subheader("Notes by Task")
    tasks = db.get_tasks()
    
    if tasks:
        task_dict = {name: id for id, name in tasks}
        selected_task = st.selectbox("Select Task", list(task_dict.keys()), key="view_task")
        
        notes = db.execute_query(
            "SELECT note, created_at FROM notes WHERE task_id = ? ORDER BY created_at DESC",
            (task_dict[selected_task],)
        )
        
        if notes:
            for note in notes:
                st.write(f"**{note[1]}**")
                st.write(note[0])
                st.markdown("---")
        else:
            st.info(f"No notes found for task: {selected_task}")
    else:
        st.info("No tasks available.")
    
    # Add note form in an expander
    with st.expander("➕ Add New Note", expanded=False):
        st.subheader("Add Note to Task")
        tasks = db.get_tasks()
        
        if tasks:
            task_dict = {name: id for id, name in tasks}
            task = st.selectbox("Select Task", list(task_dict.keys()))
            note = st.text_area("Note")
            
            if st.button("Add Note"):
                db.execute_query(
                    "INSERT INTO notes (task_id, note, created_at) VALUES (?, ?, ?)",
                    (task_dict[task], note, datetime.now().isoformat())
                )
                st.success("Note added successfully!")
                st.rerun()  # Refresh the page to show the new note
        else:
            st.warning("Please add tasks first before adding notes.") 