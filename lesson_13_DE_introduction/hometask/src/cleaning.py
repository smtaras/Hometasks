import pandas as pd
import re

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Очищення таблиці користувачів"""
    df = df.dropna(subset=['customer_id']).drop_duplicates(subset=['customer_id'])
    
    df['email'] = df['email'].fillna('unknown@example.com').astype(str).str.strip().str.lower()
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    df.loc[~df['email'].str.match(email_regex, na=False), 'email'] = 'invalid_format@example.com'
    
    return df

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Очищення таблиці товарів"""
    df = df.dropna(subset=['product_id']).drop_duplicates(subset=['product_id'])
    
    df['price'] = df['price'].abs()
    df.loc[df['price'] == 0, 'price'] = 9.99
    
    return df

def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Очищення таблиці замовлень (адаптовано під реальні колонки)"""
    df.columns = df.columns.str.strip()
    
    if 'order_id' not in df.columns:
        raise KeyError(f"Колонку 'order_id' не знайдено! Доступні: {list(df.columns)}")
        
    df = df.dropna(subset=['order_id']).drop_duplicates(subset=['order_id'])
    
    if 'created_at' in df.columns:
        df['order_date'] = pd.to_datetime(df['created_at'], errors='coerce')
        df = df.drop(columns=['created_at'])
    elif 'order_date' in df.columns:
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
    else:
        raise KeyError(f"Не знайдено колонку з датою. Доступні: {list(df.columns)}")
        
    df = df.dropna(subset=['order_date'])
    
    status_col = 'order_status' if 'order_status' in df.columns else 'status'
    
    if status_col in df.columns:
        df['status'] = df[status_col].fillna('UNKNOWN').astype(str).str.strip().str.upper()
        if status_col != 'status':
            df = df.drop(columns=[status_col])
    else:
        df['status'] = 'UNKNOWN'
    
    return df

def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """Очищення таблиці позицій в замовленні"""
    df = df.dropna(subset=['order_item_id']).drop_duplicates(subset=['order_item_id'])
    
    if 'quantity' in df.columns:
        df['quantity'] = df['quantity'].abs().fillna(1).astype(int)
        df.loc[df['quantity'] == 0, 'quantity'] = 1
        
    return df

def enforce_foreign_keys(dfs: dict) -> dict:
    """
    Видалення сирітських записів (Missing references).
    Наприклад, якщо в orders є customer_id, якого немає в customers.csv
    """
    dfs['orders'] = dfs['orders'][dfs['orders']['customer_id'].isin(dfs['customers']['customer_id'])]
    
    dfs['order_items'] = dfs['order_items'][dfs['order_items']['order_id'].isin(dfs['orders']['order_id'])]
    
    dfs['order_items'] = dfs['order_items'][dfs['order_items']['product_id'].isin(dfs['products']['product_id'])]
    
    return dfs