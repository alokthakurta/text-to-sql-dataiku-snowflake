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
        columns = [col['name'] for col in schema['columns']]
        
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
st.title("External Text-to-SQL Demo 🔍")
st.write("This demo fetches your latest `ontology.yaml` and executes queries via the Dataiku API.")

user_question = st.text_input("Ask a question about your data:")

if st.button("Generate SQL"):
    if user_question:
        with st.spinner("Fetching latest ontology and generating SQL..."):
            current_ontology = load_latest_ontology()
            
            if current_ontology:
                sql_query = generate_sql(user_question, current_ontology)
                
                st.subheader("Generated SQL Query:")
                st.code(sql_query, language="sql")
                
                if not sql_query.startswith("Error"):
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
