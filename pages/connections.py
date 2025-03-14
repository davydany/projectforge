import streamlit as st
import utils.database as db
import json
import os

def app():
    st.header("Manage Connections")
    
    # Create tabs for different connection types
    tab1, tab2 = st.tabs(["Jira", "Bitbucket"])
    
    # Jira Connection Tab
    with tab1:
        st.subheader("Jira Connection Settings")
        
        # Get current Jira settings from database
        jira_settings = db.execute_query("SELECT settings FROM connections WHERE name = 'jira'")
        
        # Initialize default values
        jira_url = ""
        jira_username = ""
        jira_api_token = ""
        jira_project_key = ""
        jira_enabled = False
        
        # If settings exist, parse them
        if jira_settings and jira_settings[0][0]:
            try:
                settings = json.loads(jira_settings[0][0])
                jira_url = settings.get("url", "")
                jira_username = settings.get("username", "")
                jira_api_token = settings.get("api_token", "")
                jira_project_key = settings.get("project_key", "")
                jira_enabled = settings.get("enabled", False)
            except json.JSONDecodeError:
                st.error("Error parsing Jira settings. Using defaults.")
        
        # Create a form for Jira settings
        with st.form("jira_settings_form"):
            st.markdown("### Jira API Connection")
            st.markdown("""
            To connect to Jira, you'll need:
            1. Your Jira instance URL (e.g., https://yourcompany.atlassian.net)
            2. Your Jira username (email)
            3. An API token (create one at https://id.atlassian.com/manage-profile/security/api-tokens)
            4. Your Jira project key (optional)
            """)
            
            # Input fields
            jira_enabled = st.checkbox("Enable Jira Integration", value=jira_enabled)
            jira_url = st.text_input("Jira URL", value=jira_url, placeholder="https://yourcompany.atlassian.net")
            jira_username = st.text_input("Jira Username (Email)", value=jira_username, placeholder="your.email@example.com")
            jira_api_token = st.text_input("Jira API Token", value=jira_api_token, type="password", placeholder="••••••••••••••••")
            jira_project_key = st.text_input("Default Jira Project Key (Optional)", value=jira_project_key, placeholder="PROJ")
            
            # Submit button
            submitted = st.form_submit_button("Save Jira Settings")
            
            if submitted:
                # Create settings JSON
                settings = {
                    "url": jira_url,
                    "username": jira_username,
                    "api_token": jira_api_token,
                    "project_key": jira_project_key,
                    "enabled": jira_enabled
                }
                
                # Save to database
                if jira_settings:
                    # Update existing settings
                    db.execute_query(
                        "UPDATE connections SET settings = ? WHERE name = 'jira'",
                        (json.dumps(settings),)
                    )
                else:
                    # Insert new settings
                    db.execute_query(
                        "INSERT INTO connections (name, settings) VALUES (?, ?)",
                        ("jira", json.dumps(settings))
                    )
                
                st.success("Jira settings saved successfully!")
        
        # Test connection button
        if jira_url and jira_username and jira_api_token:
            if st.button("Test Jira Connection"):
                try:
                    # Import Jira library
                    from jira import JIRA
                    
                    # Try to connect
                    jira = JIRA(
                        server=jira_url,
                        basic_auth=(jira_username, jira_api_token)
                    )
                    
                    # Get current user to verify connection
                    current_user = jira.myself()
                    
                    st.success(f"✅ Connection successful! Connected as {current_user['displayName']}.")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
                    st.info("Please check your credentials and try again.")
        else:
            st.info("Please fill in all required fields to test the connection.")
    
    # Bitbucket Connection Tab
    with tab2:
        st.subheader("Bitbucket Connection Settings")
        
        # Get current Bitbucket settings from database
        bitbucket_settings = db.execute_query("SELECT settings FROM connections WHERE name = 'bitbucket'")
        
        # Initialize default values
        bitbucket_url = ""
        bitbucket_username = ""
        bitbucket_app_password = ""
        bitbucket_workspace = ""
        bitbucket_repository = ""
        bitbucket_enabled = False
        
        # If settings exist, parse them
        if bitbucket_settings and bitbucket_settings[0][0]:
            try:
                settings = json.loads(bitbucket_settings[0][0])
                bitbucket_url = settings.get("url", "")
                bitbucket_username = settings.get("username", "")
                bitbucket_app_password = settings.get("app_password", "")
                bitbucket_workspace = settings.get("workspace", "")
                bitbucket_repository = settings.get("repository", "")
                bitbucket_enabled = settings.get("enabled", False)
            except json.JSONDecodeError:
                st.error("Error parsing Bitbucket settings. Using defaults.")
        
        # Create a form for Bitbucket settings
        with st.form("bitbucket_settings_form"):
            st.markdown("### Bitbucket API Connection")
            st.markdown("""
            To connect to Bitbucket, you'll need:
            1. Your Bitbucket instance URL (e.g., https://bitbucket.org or your self-hosted URL)
            2. Your Bitbucket username
            3. An App Password (create one in Bitbucket account settings > App passwords)
            4. Your Workspace name
            5. Your Repository name (optional)
            """)
            
            # Input fields
            bitbucket_enabled = st.checkbox("Enable Bitbucket Integration", value=bitbucket_enabled)
            bitbucket_url = st.text_input("Bitbucket URL", value=bitbucket_url, placeholder="https://bitbucket.org")
            bitbucket_username = st.text_input("Bitbucket Username", value=bitbucket_username, placeholder="username")
            bitbucket_app_password = st.text_input("Bitbucket App Password", value=bitbucket_app_password, type="password", placeholder="••••••••••••••••")
            bitbucket_workspace = st.text_input("Workspace", value=bitbucket_workspace, placeholder="your-workspace")
            bitbucket_repository = st.text_input("Repository (Optional)", value=bitbucket_repository, placeholder="your-repo")
            
            # Submit button
            submitted = st.form_submit_button("Save Bitbucket Settings")
            
            if submitted:
                # Create settings JSON
                settings = {
                    "url": bitbucket_url,
                    "username": bitbucket_username,
                    "app_password": bitbucket_app_password,
                    "workspace": bitbucket_workspace,
                    "repository": bitbucket_repository,
                    "enabled": bitbucket_enabled
                }
                
                # Save to database
                if bitbucket_settings:
                    # Update existing settings
                    db.execute_query(
                        "UPDATE connections SET settings = ? WHERE name = 'bitbucket'",
                        (json.dumps(settings),)
                    )
                else:
                    # Insert new settings
                    db.execute_query(
                        "INSERT INTO connections (name, settings) VALUES (?, ?)",
                        ("bitbucket", json.dumps(settings))
                    )
                
                st.success("Bitbucket settings saved successfully!")
        
        # Test connection button
        if bitbucket_url and bitbucket_username and bitbucket_app_password and bitbucket_workspace:
            if st.button("Test Bitbucket Connection"):
                try:
                    # Import requests library for API calls
                    import requests
                    from requests.auth import HTTPBasicAuth
                    
                    # Construct API URL to get user info
                    api_url = f"{bitbucket_url.rstrip('/')}/api/2.0/user"
                    
                    # Make API request
                    response = requests.get(
                        api_url,
                        auth=HTTPBasicAuth(bitbucket_username, bitbucket_app_password)
                    )
                    
                    # Check response
                    if response.status_code == 200:
                        user_data = response.json()
                        st.success(f"✅ Connection successful! Connected as {user_data.get('display_name', user_data.get('username', 'Unknown'))}.")
                    else:
                        st.error(f"❌ Connection failed: HTTP {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
                    st.info("Please check your credentials and try again.")
        else:
            st.info("Please fill in all required fields to test the connection.") 