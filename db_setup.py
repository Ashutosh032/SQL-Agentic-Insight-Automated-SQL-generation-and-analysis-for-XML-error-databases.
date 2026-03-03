"""
Database Setup Script
Loads the CSV file into a SQLite database.
"""
import sqlite3
import pandas as pd
from pathlib import Path


def create_database(csv_path: str = "server_xml_three_months_els.csv", db_path: str = "server_data.db"):
    """Load CSV data into SQLite database."""
    print(f"Loading CSV from: {csv_path}")
    
    # Read CSV file
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    # Clean column names (remove BOM and special characters)
    df.columns = [col.strip().replace('\ufeff', '').replace(' ', '_').replace('?', '').replace('/', '_') for col in df.columns]
    
    print(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    
    # Create SQLite connection
    conn = sqlite3.connect(db_path)
    
    # Write to SQLite
    df.to_sql('server_xml_errors', conn, if_exists='replace', index=False)
    
    # Verify
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM server_xml_errors")
    count = cursor.fetchone()[0]
    print(f"Successfully loaded {count} rows into SQLite database: {db_path}")
    
    conn.close()
    return db_path


def get_schema(db_path: str = "server_data.db") -> str:
    """Get database schema as a string."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("PRAGMA table_info(server_xml_errors)")
    columns = cursor.fetchall()
    
    schema = "Table: server_xml_errors\nColumns:\n"
    for col in columns:
        schema += f"  - {col[1]} ({col[2]})\n"
    
    # Get sample data
    cursor.execute("SELECT * FROM server_xml_errors LIMIT 3")
    samples = cursor.fetchall()
    
    schema += "\nSample Data (3 rows):\n"
    for sample in samples:
        schema += f"  {sample}\n"
    
    conn.close()
    return schema


if __name__ == "__main__":
    create_database()
    print("\n" + "="*50)
    print("Database Schema:")
    print("="*50)
    print(get_schema())
