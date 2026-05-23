import pandas as pd
from sqlalchemy import create_engine, text
import config

def verify_etl_results():
    print("Connecting to PostgreSQL Docker container...")
    engine = create_engine(config.DATABASE_URL)
    
    # 1. Check all tables inside the database
    print("\nExisting tables in database:")
    query_tables = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_name NOT LIKE 'pg_%';
    """
    with engine.connect() as conn:
        tables = conn.execute(text(query_tables)).fetchall()
        for t in tables:
            print(f" - {t[0]}")
            
    # 2. Preview the final Combined Table Layer
    print("\nPreviewing top 3 rows of 'combined_master_sales':")
    try:
        df_combined = pd.read_sql("SELECT * FROM combined_master_sales LIMIT 3;", con=engine)
        print(df_combined.to_string(index=False))
        print(f"\nSuccess! Total rows in combined table: {pd.read_sql('SELECT COUNT(*) FROM combined_master_sales;', con=engine).iloc[0,0]}")
    except Exception as e:
        print(f"Error reading combined table: {e}")

if __name__ == "__main__":
    verify_etl_results()