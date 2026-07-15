# data-analyist-agent
## Setup Instructions

Follow these steps to set up the project locally:

### Build the sales database

The analyst queries `database/sales.db`, not the CSV directly. Create or refresh
the database from the e-commerce dataset with:

```bash
python3 database/create_db.py
```

This imports all dataset records into the `sales` table using SQLite-friendly
snake_case column names.

### 1. Create a Virtual Environment
Create a isolated Python virtual environment named `.venv`:

**On Linux/macOS:**
```bash
python3 -m venv .venv
