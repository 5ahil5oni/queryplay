import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="QueryPlay - Experiment, Query, Visualize",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. Session State Management (The "Brain" of the App)
# -----------------------------------------------------------------------------
# We use session_state so that every user gets their OWN temporary database.
# This prevents User A from seeing User B's data.

if 'db_conn' not in st.session_state:
    # Create an in-memory database connection for this specific user session
    st.session_state.db_conn = sqlite3.connect(":memory:", check_same_thread=False)

if 'uploaded_files_list' not in st.session_state:
    st.session_state.uploaded_files_list = []

# Shortcut variable for code readability
conn = st.session_state.db_conn

# -----------------------------------------------------------------------------
# 3. Helper Functions
# -----------------------------------------------------------------------------

def sanitize_column_names(df):
    """
    Cleans column names to make them SQL-compatible.
    Ex: "Order Date" -> "Order_Date"
    """
    df.columns = [
        str(c).strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        for c in df.columns
    ]
    return df

def load_data_to_db(uploaded_file):
    """
    Reads CSV and inserts into the user's private SQLite DB.
    """
    try:
        # Create a clean table name based on filename
        table_name = uploaded_file.name.split('.')[0]
        # Keep only alphanumeric characters for the table name
        table_name = "".join([c for c in table_name if c.isalnum() or c == '_'])
        
        # Read CSV
        df = pd.read_csv(uploaded_file)
        df = sanitize_column_names(df)
        
        # Write to SQL (replace if exists allows re-uploading to overwrite)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        return table_name, None
    except Exception as e:
        return None, str(e)

# -----------------------------------------------------------------------------
# 4. Sidebar: Inputs & Instructions
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📂 Data Upload")
    
    # Allow multiple CSV uploads
    uploaded_files = st.file_uploader(
        "Upload CSV files here", 
        type=["csv"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded.")
        
        # Process files
        for file in uploaded_files:
            if file.name not in st.session_state.uploaded_files_list:
                t_name, error = load_data_to_db(file)
                if t_name:
                    st.session_state.uploaded_files_list.append(file.name)
                    st.toast(f"Table '{t_name}' created!", icon="✅")
                else:
                    st.error(f"Error: {error}")

    st.markdown("---")
    
    # Database Schema Viewer
    st.subheader("🗄️ Database Schema")
    if st.button("Refresh Schema"):
        # Just reruns the script to update the view
        st.rerun()

    # Query sqlite_master to find all tables
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            for t in tables:
                table_name = t[0]
                with st.expander(f"Table: {table_name}"):
                    # Show columns and types
                    schema_df = pd.read_sql(f"PRAGMA table_info({table_name})", conn)
                    st.dataframe(schema_df[['name', 'type']], hide_index=True)
        else:
            st.info("No tables found. Upload a CSV to start.")
            
    except Exception as e:
        st.error(f"DB Error: {e}")

    st.markdown("---")
    if st.button("🧹 Clear Database"):
        st.session_state.db_conn.close()
        del st.session_state.db_conn
        st.session_state.uploaded_files_list = []
        st.rerun()

# -----------------------------------------------------------------------------
# 5. Main Area: SQL Editor
# -----------------------------------------------------------------------------
st.title("QueryPlay - Experiment, Query, Visualize")
st.markdown("""
Write SQL queries against your uploaded CSVs. 
The data is stored in **temporary memory** and vanishes when you leave.
""")

# Default query suggestion
default_query = "SELECT * FROM sqlite_master WHERE type='table';"
if len(st.session_state.uploaded_files_list) > 0:
    # Try to find the name of the first table uploaded to make a friendly default query
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
    res = cursor.fetchone()
    if res:
        default_query = f"SELECT * FROM {res[0]} LIMIT 10;"

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_area("SQL Query Editor", value=default_query, height=200)

with col2:
    st.markdown("<br><br>", unsafe_allow_html=True) # Spacing
    run_btn = st.button("▶️ Run Query", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# 6. Results & Visualization
# -----------------------------------------------------------------------------
if run_btn or query:
    try:
        # Run the query
        results_df = pd.read_sql_query(query, conn)
        
        st.divider()
        
        # Tabs for Data vs Visualization
        tab1, tab2 = st.tabs(["📄 Data Results", "📈 Visualization"])
        
        with tab1:
            st.markdown(f"**Results:** {results_df.shape[0]} rows, {results_df.shape[1]} columns")
            st.dataframe(results_df, use_container_width=True)
            
            # Export Buttons
            st.markdown("### 📥 Export")
            c1, c2 = st.columns(2)
            
            with c1:
                csv_data = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
            
            with c2:
                # Excel Export
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    results_df.to_excel(writer, index=False, sheet_name='Sheet1')
                excel_data = output.getvalue()
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name="query_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with tab2:
            if not results_df.empty:
                st.markdown("#### Quick Plotter")
                chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie", "Histogram"])
                
                columns = results_df.columns.tolist()
                
                c_x, c_y, c_color = st.columns(3)
                with c_x:
                    x_col = st.selectbox("X Axis", columns)
                with c_y:
                    # Auto-select second column for Y if available
                    y_idx = 1 if len(columns) > 1 else 0
                    y_col = st.selectbox("Y Axis (Values)", columns, index=y_idx)
                with c_color:
                    color_col = st.selectbox("Color Group (Optional)", ["None"] + columns)
                
                color_opt = None if color_col == "None" else color_col
                
                if chart_type == "Bar":
                    fig = px.bar(results_df, x=x_col, y=y_col, color=color_opt)
                elif chart_type == "Line":
                    fig = px.line(results_df, x=x_col, y=y_col, color=color_opt)
                elif chart_type == "Scatter":
                    fig = px.scatter(results_df, x=x_col, y=y_col, color=color_opt)
                elif chart_type == "Pie":
                    fig = px.pie(results_df, names=x_col, values=y_col)
                elif chart_type == "Histogram":
                    fig = px.histogram(results_df, x=x_col, color=color_opt)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Query returned no results, so no charts can be drawn.")

    except Exception as e:
        st.error(f"❌ SQL Error: {e}")