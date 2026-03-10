import streamlit as st
import pandas as pd
import requests
import json

# Setup Page Configuration
st.set_page_config(
    page_title="Assessment Admin Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Replace with your actual deployed Google Apps Script URL
GAS_URL = "https://script.google.com/macros/s/AKfycbz9BCuH-G7BCgGbviCDRO4ir7J8OdXKUNOV0uyq5LQmaLHfzaOddBehM9t9Auu5QsVM/exec"

# Admin Authentication
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets.get("admin_password", "admin123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("## 🔐 Admin Login Required")
        st.text_input("Please enter the administrator password:", type="password", on_change=password_entered, key="password")
        return False
    
    elif not st.session_state["password_correct"]:
        st.markdown("## 🔐 Admin Login Required")
        st.text_input("Please enter the administrator password:", type="password", on_change=password_entered, key="password")
        st.error("Incorrect Password")
        return False
    
    return True

# Data Fetching
@st.cache_data(ttl=60) # Cache the data for up to 60 seconds
def fetch_data():
    try:
        response = requests.get(GAS_URL)
        data = response.json()
        if data.get("status") == "success":
            return pd.DataFrame(data["data"])
        else:
            st.error(f"Error fetching data: {data.get('message')}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to connect to Google Sheet API: {str(e)}")
        return pd.DataFrame()

# Main App Logic
if check_password():
    st.title("📊 Candidate Assessment Results")
    st.markdown("Welcome to the secure administrator terminal.")

    # Refresh Button
    if st.button("🔄 Refresh Data"):
        fetch_data.clear()
        st.rerun()
        
    df = fetch_data()

    if not df.empty:
        # Pre-process elements
        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.strftime('%Y-%m-%d %H:%M')
        
        # Make sure Score is numeric for calculations
        if "Score" in df.columns:
            df["Score"] = pd.to_numeric(df["Score"], errors='coerce')
        
        # Display Key Metrics
        col1, col2, col3 = st.columns(3)
        total_responses = len(df)
        avg_score = df["Score"].mean() if "Score" in df.columns else 0
        
        col1.metric("Total Candidates", total_responses)
        col2.metric("Average Score", f"{avg_score:.1f} / 12")
        
        # Main Data Table
        st.markdown("### 📋 Recent Submissions")
        
        # We might not want to show the huge JSON block in the table, let's hide it from the preview
        display_columns = [col for col in df.columns if col != "Answers JSON"]
        st.dataframe(df[display_columns], use_container_width=True)
        
        # Detailed Candidate View
        st.markdown("### 🔍 Detailed Score Lookup")
        candidates = df["Name"].tolist() if "Name" in df.columns else []
        selected_candidate = st.selectbox("Select a Candidate to view their exact answers:", [""] + candidates)
        
        if selected_candidate:
            candidate_row = df[df["Name"] == selected_candidate].iloc[0]
            st.success(f"**Score:** {candidate_row.get('Score', 'N/A')} / 12")
            st.info(f"**Email:** {candidate_row.get('Email', 'N/A')} | **Phone:** {candidate_row.get('Phone Number', 'N/A')}")
            
            try:
                answers_json = json.loads(candidate_row.get("Answers JSON", "{}"))
                st.json(answers_json)
            except:
                st.warning("Could not parse detailed answers.")
            
    else:
        st.info("No assessment results have been submitted yet.")

