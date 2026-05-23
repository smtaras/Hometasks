import pandas as pd
import re

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and normalizes the raw customers data."""
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Drop rows missing the primary key or with duplicate keys
    df = df.dropna(subset=['customer_id']).drop_duplicates(subset=['customer_id'])
    
    # Handle emails: fill missing, lowercase, and validate format
    df['email'] = df['email'].fillna('unknown@example.com').astype(str).str.strip().str.lower()
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    df.loc[~df['email'].str.match(email_regex, na=False), 'email'] = 'invalid_format@example.com'
    
    return df

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and normalizes the raw products data."""
    df.columns = df.columns.str.strip().str.lower()
    
    df = df.dropna(subset=['product_id']).drop_duplicates(subset=['product_id'])
    
    # Fix negative prices using absolute value, replace 0 with default fallback price
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').abs()
        df.loc[(df['price'] == 0) | (df['price'].isna()), 'price'] = 9.99
        
    return df

def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and normalizes the raw orders data dynamically handling column names."""
    df.columns = df.columns.str.strip().str.lower()
    
    df = df.dropna(subset=['order_id']).drop_duplicates(subset=['order_id'])
    
    # Handle date column (supports 'created_at' or 'order_date')
    date_col = 'created_at' if 'created_at' in df.columns else ('order_date' if 'order_date' in df.columns else None)
    if date_col:
        df['order_date'] = pd.to_datetime(df[date_col], errors='coerce')
        if date_col != 'order_date':
            df = df.drop(columns=[date_col])
    else:
        raise KeyError(f"Could not find a date column. Available columns: {list(df.columns)}")
        
    # Drop rows where the timestamp is completely invalid (NaT)
    df = df.dropna(subset=['order_date'])
    
    # Handle order status (supports 'order_status' or 'status')
    status_col = 'order_status' if 'order_status' in df.columns else 'status'
    if status_col in df.columns:
        df['status'] = df[status_col].fillna('UNKNOWN').astype(str).str.strip().str.upper()
        if status_col != 'status':
            df = df.drop(columns=[status_col])
    else:
        df['status'] = 'UNKNOWN'
        
    return df

def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and normalizes the raw order items data."""
    df.columns = df.columns.str.strip().str.lower()
    
    df = df.dropna(subset=['order_item_id']).drop_duplicates(subset=['order_item_id'])
    
    # Fix negative or zero quantities
    if 'quantity' in df.columns:
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').abs().fillna(1).astype(int)
        df.loc[df['quantity'] == 0, 'quantity'] = 1
        
    return df

def enforce_foreign_keys(dfs: dict) -> dict:
    """Removes orphan records to maintain relational integrity (Foreign Key emulation)."""
    # Orders must have a valid customer
    dfs['orders'] = dfs['orders'][dfs['orders']['customer_id'].isin(dfs['customers']['customer_id'])]
    
    # Order items must have a valid order and a valid product
    dfs['order_items'] = dfs['order_items'][dfs['order_items']['order_id'].isin(dfs['orders']['order_id'])]
    dfs['order_items'] = dfs['order_items'][dfs['order_items']['product_id'].isin(dfs['products']['product_id'])]
    
    return dfs