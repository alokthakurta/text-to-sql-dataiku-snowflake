import streamlit as st
import dataikuapi
import pandas as pd
import yaml
import json

# --- SECURE CONFIGURATION ---
# These will be populated by Streamlit Cloud's Secrets Manager
DSS_HOST = st.secrets["DSS_HOST"]
DSS_API_KEY = st.secrets["DSS_API_KEY"]
PROJECT_KEY = st.secrets["PROJECT_KEY"]
FOLDER_ID = st.secrets["FOLDER_ID"]
LLM_ID = st.secrets["LLM_ID"]
CONNECTION_NAME = st.secrets["CONNECTION_NAME"]

# Initialize External Client
client = dataikuapi.DSSClient(DSS_HOST, DSS_API_KEY)
project = client.get_project(PROJECT_KEY)

# --- DYNAMIC DATA LOADING (EXTERNAL) ---
def load_latest_ontology():
    try:
        folder = project.get_managed_folder(FOLDER_ID)
        # Download the file via REST API
        file_stream = folder.get_file("ontology.yaml")
        ontology_data = yaml.safe_load(file_stream.content)
        return ontology_data
    except Exception as e:
        st.error(f"Error loading ontology: {e}")
        return None

# --- LLM INTEGRATION (EXTERNAL) ---
def generate_sql(question, ontology):
    ontology_str = json.dumps(ontology, indent=2)
    prompt = f"""
    You are an expert SQL assistant. 
    Here is the current database ontology and schema rules:
    {ontology_str}
    
    Based ONLY on the provided ontology, write a SQL query to answer the following question. 
    Return ONLY the raw SQL query, no markdown, no explanations.
    
    Question: {question}
    """
    try:
        llm = project.get_llm(LLM_ID)
        completion = llm.new_completion()
        completion.with_message(prompt, role="user")
        response = completion.execute()
        
        if response.success:
            return response.text
        else:
            return "Error: LLM completion failed."
    except Exception as e:
        return f"Error generating SQL: {e}"
        
# --- SQL EXECUTION (EXTERNAL VIA API) ---
def execute_generated_sql(sql_query):
    try:
        # We proxy the query through Dataiku's REST API using the connection name
        query_runner = client.sql_query(sql_query, connection=CONNECTION_NAME)
        
        # Extract schema to build pandas columns
        schema = query_runner.get_schema()
        
        # FIX: Check if schema is a dictionary or directly a list
        if isinstance(schema, dict) and 'columns' in schema:
            columns = [col['name'] for col in schema['columns']]
        else:
            columns = [col['name'] for col in schema]
        
        # Fetch the data row by row
        data = []
        for row in query_runner.iter_rows():
            data.append(row)
            
        query_runner.verify() # Verifies stream completed successfully
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=columns)
        return df, None
    except Exception as e:
        return None, str(e)
# --- STREAMLIT UI ---
st.title("Financial Intelligence, Unleashed.")
st.write("Powered by Tiger’s advanced analytics to bring you institutional-grade market insights in real time.")

st.markdown("""
    <style>
    /* Target the text inside Streamlit buttons to make it smaller */
    div[data-testid="stButton"] button p {
        font-size: 10px !important; /* Change this number to make it bigger/smaller */
    }
    </style>
""", unsafe_allow_html=True)

# 1. Initialize session state to remember the question
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

# 2. Add Suggested Questions
st.write("**💡 Suggested Questions:**")

# Row 1
row1_col1, row1_col2, row1_col3 = st.columns(3)
if row1_col1.button("What is our Total Revenue?"):
    st.session_state.current_question = "What is our Total Revenue?"
if row1_col2.button("How many leads converted last month?"):
    st.session_state.current_question = "How many leads converted last month?"
if row1_col3.button("Who are our top 5 sales reps?"):
    st.session_state.current_question = "Who are our top 5 sales reps?"

# Row 2
row2_col1, row2_col2, row2_col3 = st.columns(3)
if row2_col1.button("What is the Cost Per Lead (CPL)?"):
    st.session_state.current_question = "What is the Cost Per Lead (CPL) for each campaign?"
if row2_col2.button("Calculate ROMI by Region"):
    st.session_state.current_question = "Calculate Return on Marketing Investment (ROMI) by Region"
if row2_col3.button("Identify CAC for converted leads"):
    st.session_state.current_question = "Identify Customer Acquisition Cost (CAC) for converted leads"

st.markdown("---")

# 3. Tie the text input directly to the session state using the 'key' parameter
user_question = st.text_input(
    "Ask a question about your data:", 
    key="current_question"
)

if st.button("Generate SQL"):
    if user_question:
        with st.spinner("Fetching latest ontology and generating SQL..."):
            current_ontology = load_latest_ontology()
            
            if current_ontology:
                # 1. Generate the raw response from the LLM
                raw_llm_output = generate_sql(user_question, current_ontology)
                
                # 2. Clean the output to remove Markdown backticks
                sql_query = raw_llm_output.strip()
                if sql_query.startswith("```sql"):
                    sql_query = sql_query[6:] # Strip the first 6 characters
                elif sql_query.startswith("```"):
                    sql_query = sql_query[3:] # Strip the first 3 characters
                
                if sql_query.endswith("```"):
                    sql_query = sql_query[:-3] # Strip the last 3 characters
                    
                sql_query = sql_query.strip() # Remove any leftover whitespace/newlines
                
                # 3. Display the cleaned SQL
                st.subheader("Generated SQL Query:")
                st.code(sql_query, language="sql")
                
                # 4. Execute the cleaned SQL
                if not raw_llm_output.startswith("Error"):
                    st.subheader("Query Results:")
                    with st.spinner("Executing query remotely..."):
                        results_df, error_msg = execute_generated_sql(sql_query)
                        
                        if error_msg:
                            st.error(f"SQL Execution Error: {error_msg}")
                        elif results_df is not None:
                            if results_df.empty:
                                st.info("Query executed successfully, but returned 0 rows.")
                            else:
                                st.dataframe(results_df) 
    else:
        st.warning("Please enter a question first.")
