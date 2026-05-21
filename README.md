
```markdown
# 📊 Financial Intelligence Text-to-SQL App

This repository contains a Streamlit-based web application that empowers users to query complex financial databases using natural language. 

By leveraging **Dataiku's external API**, **LLM Mesh**, and **secure SQL execution engines**, this application bridges the gap between non-technical business users and complex data infrastructure. The app dynamically fetches business logic (an ontology) to generate highly accurate, context-aware SQL queries, executing them securely without ever exposing database credentials to the frontend.

---

## ✨ Key Features

* **🧠 Natural Language to SQL:** Translates plain English questions into executable SQL using an LLM (e.g., OpenAI, Anthropic) routed through Dataiku's LLM Mesh.
* **📖 Dynamic Ontology Loading:** Automatically retrieves the latest `ontology.yaml` (data dictionary, schema rules, and business definitions) from a Dataiku Managed Folder via REST API. 
* **🛡️ Secure Remote Execution:** The Streamlit app does not connect directly to the database. Instead, it proxies the generated SQL query through Dataiku, leveraging Dataiku's pre-configured and governed database connections (e.g., Snowflake, PostgreSQL).
* **🧹 Smart SQL Sanitization:** Automatically detects and strips markdown formatting and conversational text from the LLM output to ensure clean, executable SQL.
* **⚡ Interactive UI:** Features a modern Streamlit interface with suggested one-click questions, a real-time query generation tracker, and dynamic dataframe rendering.

---

## 🏗️ Technical Architecture

This project decouples the frontend presentation layer from the backend data engineering and LLM orchestration layer.

1.  **Frontend (Streamlit Community Cloud):** Handles the user interface, session state, and API orchestration. Uses the external `dataiku-api-client` to communicate with the backend.
2.  **Backend & GenAI (Dataiku DSS):** Acts as the secure orchestrator. It hosts the business ontology, manages the LLM integration (LLM Mesh), and securely executes the SQL queries against the underlying data warehouse.
3.  **Data Warehouse (e.g., Snowflake):** The final destination where the SQL is executed, governed by Dataiku's connection security.

---

## 📋 Prerequisites

Before you begin, ensure you have the following:

* **Python:** Version 3.8 or higher.
* **Dataiku DSS Instance:** A running Dataiku instance with API access enabled.
* **Dataiku Personal API Key:** Generated from your Dataiku user profile (needs permissions to read the managed folder, use the LLM, and execute SQL queries).
* **LLM Mesh Configured:** An LLM connection (e.g., OpenAI) set up in your Dataiku instance.
* **Target Database:** A working database connection configured in Dataiku (e.g., Snowflake).
* **GitHub Account:** To host the repository for deployment.
* **Streamlit Cloud Account:** For hosting the application.

---
```
## 🛠️ Local Installation & Setup

Follow these steps to run the application locally on your machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies

Ensure your `requirements.txt` includes `streamlit`, `dataiku-api-client`, `pandas`, and `pyyaml`.

```bash
pip install -r requirements.txt
```

### 4. Configure Local Secrets

Streamlit uses a `.streamlit/secrets.toml` file to manage environment variables locally. **Never commit this file to version control.**

Create a `.streamlit` folder in the root of your project, and inside it, create `secrets.toml`:

```toml
# .streamlit/secrets.toml

# The URL of your Dataiku instance (e.g., [https://dss.yourcompany.com](https://dss.yourcompany.com))
DSS_HOST = "YOUR_DSS_HOST_URL"

# Your personal Dataiku API key
DSS_API_KEY = "YOUR_SECRET_API_KEY"

# The ID of the Dataiku Project containing the ontology and LLM
PROJECT_KEY = "YOUR_PROJECT_KEY"

# The ID of the Managed Folder containing 'ontology.yaml'
FOLDER_ID = "YOUR_FOLDER_ID"

# The internal Dataiku ID for the LLM you want to use (e.g., "openai:gpt-4")
LLM_ID = "YOUR_LLM_ID"

# The exact name of the database connection in Dataiku (e.g., "Snowflake_Prod")
CONNECTION_NAME = "YOUR_DB_CONNECTION"
```

### 5. Run the Application

Launch the Streamlit server:

```bash
streamlit run streamlit_git_app.py
```

The application will open in your default web browser at `http://localhost:8501`.

---

## 🚀 Deployment to Streamlit Community Cloud

Streamlit Community Cloud is the easiest way to deploy, manage, and share your app. Because this app uses the external `dataikuapi`, it can be hosted securely outside of your Dataiku environment.

1. **Push to GitHub:** Ensure your `streamlit_git_app.py` and `requirements.txt` are pushed to the `main` branch of your GitHub repository.
2. **Log in to Streamlit Cloud:** Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. **Create a New App:**
* Click **New app**.
* Select your repository, branch (`main`), and the main file path (`streamlit_git_app.py`).


4. **Configure Secrets (Crucial Step):**
* *Before* clicking deploy, click on **Advanced settings**.
* In the **Secrets** text area, paste the contents of your local `secrets.toml` file.
* Click **Save**.


5. **Deploy:** Click **Deploy!** Streamlit will provision a server, install your dependencies, inject the secure secrets, and launch your app.

---

## 📂 Project Structure

```text
├── .streamlit/
│   └── secrets.toml         # Local secrets (ignored by git)
├── streamlit_git_app.py     # Main Streamlit application code
├── requirements.txt         # Python package dependencies
├── .gitignore               # Git ignore rules (ensure .streamlit/ is here)
└── README.md                # Project documentation



---

## 🩺 Troubleshooting

* **Error: LLM Completion Failed:** Check if your `LLM_ID` in the secrets matches the exact ID in Dataiku. Ensure your Dataiku instance has active quotas for that specific LLM.
* **Error Loading Ontology:** Verify the `FOLDER_ID`. Check that `ontology.yaml` exists exactly with that naming convention in the root of the specified Dataiku Managed Folder. Ensure your API key has "Read" permissions for that folder.
* **SQL Execution Error:** This usually means the LLM hallucinated a column that doesn't exist, or the `CONNECTION_NAME` is incorrect. Check the generated SQL in the UI and verify it against your actual database schema.
* **Streamlit App Crashes on Boot:** Double-check your `requirements.txt`. Ensure `dataiku-api-client` is listed, *not* `dataiku` (the internal package).

---


```
