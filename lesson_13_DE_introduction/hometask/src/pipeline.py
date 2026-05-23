import pandas as pd
from sqlalchemy import create_engine, text
import config
import cleaning

def run_pipeline():
    print("Starting local ETL Pipeline...")
    engine = create_engine(config.DATABASE_URL)
    
    # Ensure clean database schemas/tables before running
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS combined_master_sales;"))
        conn.commit()

    # --- PHASE 1: LOAD CSV TO POSTGRES (raw_data layer) ---
    print("\n--- Phase 1: Loading Raw Data to PostgreSQL ---")
    raw_dfs = {}
    for table_name, path in config.RAW_FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        print(f"Reading and loading raw {table_name}...")
        
        # Read file exactly as it is
        df_raw = pd.read_csv(path)
        raw_dfs[table_name] = df_raw
        
        # Save to database as raw table
        df_raw.to_sql(f"raw_{table_name}", con=engine, if_exists="replace", index=False)
    
    # --- PHASE 2: TRANFORM & NORMALIZE (processed_tables layer) ---
    print("\n--- Phase 2: Cleaning and Normalizing Tables ---")
    processed_dfs = {
        "customers": cleaning.clean_customers(raw_dfs["customers"]),
        "products": cleaning.clean_products(raw_dfs["products"]),
        "orders": cleaning.clean_orders(raw_dfs["orders"]),
        "order_items": cleaning.clean_order_items(raw_dfs["order_items"]),
    }
    
    # Remove orphan rows (Foreign Key verification)
    processed_dfs = cleaning.enforce_foreign_keys(processed_dfs)
    
    # Save cleaned normalized tables to database
    for table_name, df_clean in processed_dfs.items():
        print(f"Saving normalized table: processed_{table_name}...")
        df_clean.to_sql(f"processed_{table_name}", con=engine, if_exists="replace", index=False)

    # --- PHASE 3: COMBINE DATA (combined_table layer) ---
    print("\n--- Phase 3: Creating Combined Analytical Master Table ---")
    
    # Dynamic column name discovery for safety
    prod_df = processed_dfs["products"]
    prod_name_col = next((col for col in prod_df.columns if 'name' in col or 'title' in col), prod_df.columns[1])
    
    # Merge all normalized data into one single denormalized master table
    df_items_prod = pd.merge(processed_dfs["order_items"], prod_df, on="product_id", how="inner")
    df_combined = pd.merge(df_items_prod, processed_dfs["orders"], on="order_id", how="inner")
    df_combined = pd.merge(df_combined, processed_dfs["customers"], on="customer_id", how="left")
    
    # Calculate analytical financial metric
    df_combined["item_total_revenue"] = df_combined["quantity"] * df_combined["price"]
    
    # Standardize specific column name for the output
    if prod_name_col != "product_name":
        df_combined = df_combined.rename(columns={prod_name_col: "product_name"})
        
    print("Saving analytical flat table: combined_master_sales...")
    df_combined.to_sql("combined_master_sales", con=engine, if_exists="replace", index=False)
    
    print("\nETL Pipeline executed successfully!")

if __name__ == "__main__":
    run_pipeline()