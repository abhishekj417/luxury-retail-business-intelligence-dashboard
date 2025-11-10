import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_kpis(sales_data, inventory_data):
    """Calculate key performance indicators"""

    # Today's data
    today = datetime.now().date()
    today_data = sales_data[sales_data['Date'].dt.date == today]
    yesterday_data = sales_data[sales_data['Date'].dt.date == (today - timedelta(days=1))]

    # If no data for today, use latest available date
    if len(today_data) == 0:
        latest_date = sales_data['Date'].max()
        today_data = sales_data[sales_data['Date'].dt.date == latest_date.date()]
        prev_date = latest_date - timedelta(days=1)
        yesterday_data = sales_data[sales_data['Date'].dt.date == prev_date.date()]

    # Daily Revenue
    daily_revenue = today_data['Revenue_USD'].sum()
    prev_revenue = yesterday_data['Revenue_USD'].sum()
    revenue_growth = ((daily_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0

    # Average Transaction Value
    atv = today_data.groupby('Transaction_ID')['Revenue_USD'].sum().mean()
    prev_atv = yesterday_data.groupby('Transaction_ID')['Revenue_USD'].sum().mean()
    atv_change = ((atv - prev_atv) / prev_atv * 100) if prev_atv > 0 else 0

    # Conversion Rate (assuming 100 visitors per boutique per day as baseline)
    total_transactions = len(today_data['Transaction_ID'].unique())
    total_boutiques = len(today_data['Boutique_ID'].unique())
    estimated_visitors = total_boutiques * 100
    conversion_rate = (total_transactions / estimated_visitors * 100) if estimated_visitors > 0 else 0

    prev_transactions = len(yesterday_data['Transaction_ID'].unique())
    prev_visitors = len(yesterday_data['Boutique_ID'].unique()) * 100
    prev_conversion = (prev_transactions / prev_visitors * 100) if prev_visitors > 0 else 0
    conversion_change = conversion_rate - prev_conversion

    # Inventory Turnover (annual basis)
    total_inventory_value = (inventory_data['Current_Stock_Units'] * inventory_data['Unit_Cost']).sum()
    last_30_days = sales_data[sales_data['Date'] >= (datetime.now() - timedelta(days=30))]
    cogs_30_days = last_30_days['Units_Sold'].sum() * inventory_data['Unit_Cost'].mean()
    annual_cogs = cogs_30_days * 12
    inventory_turnover = (annual_cogs / total_inventory_value) if total_inventory_value > 0 else 0

    # Low Stock Items
    low_stock_items = len(inventory_data[
        inventory_data['Current_Stock_Units'] <= inventory_data['Min_Stock_Threshold']
    ])

    stockout_risk = len(inventory_data[inventory_data['Current_Stock_Units'] == 0])

    return {
        'daily_revenue': daily_revenue,
        'revenue_growth': revenue_growth,
        'atv': atv if not np.isnan(atv) else 0,
        'atv_change': atv_change if not np.isnan(atv_change) else 0,
        'conversion_rate': conversion_rate,
        'conversion_change': conversion_change,
        'inventory_turnover': inventory_turnover,
        'low_stock_items': low_stock_items,
        'stockout_risk': stockout_risk
    }

def calculate_boutique_metrics(sales_data):
    """Calculate performance metrics by boutique"""

    # Latest 7 days
    latest_date = sales_data['Date'].max()
    last_7_days = sales_data[sales_data['Date'] >= (latest_date - timedelta(days=7))]

    boutique_metrics = last_7_days.groupby(['Boutique_Name', 'Region']).agg({
        'Revenue_USD': 'sum',
        'Units_Sold': 'sum',
        'Transaction_ID': 'nunique'
    }).reset_index()

    boutique_metrics.columns = ['Boutique_Name', 'Region', 'Revenue', 'Units_Sold', 'Transactions']

    # Calculate conversion rate (estimated)
    boutique_metrics['Estimated_Visitors'] = 700  # 100 per day * 7 days
    boutique_metrics['Conversion_Rate'] = (boutique_metrics['Transactions'] / 
                                           boutique_metrics['Estimated_Visitors'] * 100)

    boutique_metrics['ATV'] = boutique_metrics['Revenue'] / boutique_metrics['Transactions']

    # Sort by revenue
    boutique_metrics = boutique_metrics.sort_values('Revenue', ascending=False)

    return boutique_metrics

def calculate_category_performance(sales_data):
    """Calculate performance by product category"""

    category_metrics = sales_data.groupby('Product_Category').agg({
        'Revenue_USD': 'sum',
        'Units_Sold': 'sum',
        'Transaction_ID': 'nunique'
    }).reset_index()

    category_metrics.columns = ['Category', 'Revenue', 'Units_Sold', 'Transactions']
    category_metrics['Revenue_Share'] = (category_metrics['Revenue'] / 
                                         category_metrics['Revenue'].sum() * 100)

    return category_metrics.sort_values('Revenue', ascending=False)
