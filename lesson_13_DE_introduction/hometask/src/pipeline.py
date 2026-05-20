import pandas as pd
from sqlalchemy import create_engine
import config
import cleaning

def run_pipeline():
    print("Запуск ETL пайплайну...")
    engine = create_engine(config.DATABASE_URL)
    
    raw_data = {}
    for table_name, path in config.RAW_FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Файл не знайдено: {path}. Будь ласка, завантаж його.")
        print(f"Зчитування {table_name}...")
        raw_data[table_name] = pd.read_csv(path)
        
    print("Очищення та валідація даних...")
    cleaned_data = {
        "customers": cleaning.clean_customers(raw_data["customers"]),
        "products": cleaning.clean_products(raw_data["products"]),
        "orders": cleaning.clean_orders(raw_data["orders"]),
        "order_items": cleaning.clean_order_items(raw_data["order_items"]),
    }
    
    cleaned_data = cleaning.enforce_foreign_keys(cleaned_data)
    
    print("Створення аналітичних вітрин даних...")
    
    prod_df = cleaned_data["products"]
    prod_df.columns = prod_df.columns.str.strip()
    
    prod_name_col = None
    for col in prod_df.columns:
        if 'name' in col.lower() or 'title' in col.lower():
            prod_name_col = col
            break
            
    if prod_name_col is None:
        prod_name_col = prod_df.columns[1] if len(prod_df.columns) > 1 else 'product_id'

    df_items_prod = pd.merge(cleaned_data["order_items"], prod_df, on="product_id", how="inner")
    df_full = pd.merge(df_items_prod, cleaned_data["orders"], on="order_id", how="inner")
    
    df_full["total_item_revenue"] = df_full["quantity"] * df_full["price"]
    
    mart_customer_sales = df_full.groupby("customer_id").agg(
        total_orders=("order_id", "nunique"),
        total_spent=("total_item_revenue", "sum")
    ).reset_index()
    
    cust_df = cleaned_data["customers"]
    email_col = 'email' if 'email' in cust_df.columns else cust_df.columns[1]
    mart_customer_sales = pd.merge(mart_customer_sales, cust_df[["customer_id", email_col]], on="customer_id", how="left")
    
    mart_product_performance = df_full.groupby("product_id").agg(
        units_sold=("quantity", "sum"),
        total_revenue=("total_item_revenue", "sum")
    ).reset_index()
    
    mart_product_performance = pd.merge(
        mart_product_performance, 
        prod_df[["product_id", prod_name_col]], 
        on="product_id", 
        how="left"
    )
    mart_product_performance = mart_product_performance.rename(columns={prod_name_col: "product_name"})

    print(f"Запис даних у базу SQLite ({config.DB_PATH.name})...")
    
    for table_name, df in cleaned_data.items():
        df.to_sql(f"dim_{table_name}", con=engine, if_exists="replace", index=False)
        
    mart_customer_sales.to_sql("mart_customer_sales", con=engine, if_exists="replace", index=False)
    mart_product_performance.to_sql("mart_product_performance", con=engine, if_exists="replace", index=False)
    
    print("ETL Пайплайн успішно виконано!")

if __name__ == "__main__":
    run_pipeline()