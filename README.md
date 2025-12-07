## How To Run

### 0. API KEY
the api key used for LLM inference is available on config_template.toml. But if you want to use your own api key, you can use https://freeinference.org (it's free!)

### 1. Start the Database
```bash
docker compose up -d
```
*This starts Neo4j at `bolt://localhost:7687` (User: `neo4j`, Password: `password`).*

### 2. Configure the Application

```bash
# Windows (PowerShell)
copy config_template.toml config.toml

# Linux/macOS
cp config_template.toml config.toml
```

### 3. Install Dependencies
Set up your Python environment and install the required packages.

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv

# Activate the virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Populate the Database (First Time Only)
If you are running this for the first time and need to seed the database with initial data:

```bash
python seeder/populate_neo4j.py
```

### 5. Run the Application
Finally, run the main script to start the RAG system.

```bash
python main.py
```

## Additional Notes

- **Schema**: The graph schema is defined in `schema_example.txt`. Update this file if your data model changes.
