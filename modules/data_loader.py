import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def validate_excel(df, required_columns, file_type):
    """Validate uploaded Excel file has required columns"""
    errors = []
    missing_cols = set(required_columns) - set(df.columns)

    if missing_cols:
        errors.append(f"{file_type} is missing columns: {', '.join(missing_cols)}")

    return errors

def load_data(sales_file, inventory_file):
    """Load and validate uploaded Excel files"""
    errors = []

    # Required columns
    sales_columns = ['Date', 'Boutique_ID', 'Boutique_Name', 'Region', 'SKU_Code', 
                    'Product_Category', 'Brand', 'Units_Sold', 'Revenue_USD', 
                    'Transaction_ID', 'Customer_Type']

    inventory_columns = ['Date', 'Boutique_ID', 'SKU_Code', 'Product_Name', 'Category',
                        'Brand', 'Current_Stock_Units', 'Min_Stock_Threshold', 
                        'Retail_Price']

    try:
        # Load sales data
        if sales_file.name.endswith('.csv'):
            sales_data = pd.read_csv(sales_file)
        else:
            sales_data = pd.read_excel(sales_file)

        # Validate sales data
        errors.extend(validate_excel(sales_data, sales_columns, "Sales Report"))

        # Convert date column
        sales_data['Date'] = pd.to_datetime(sales_data['Date'])

    except Exception as e:
        errors.append(f"Error loading sales file: {str(e)}")
        sales_data = None

    try:
        # Load inventory data
        if inventory_file.name.endswith('.csv'):
            inventory_data = pd.read_csv(inventory_file)
        else:
            inventory_data = pd.read_excel(inventory_file)

        # Validate inventory data
        errors.extend(validate_excel(inventory_data, inventory_columns, "Inventory Report"))

        # Convert date column
        inventory_data['Date'] = pd.to_datetime(inventory_data['Date'])

    except Exception as e:
        errors.append(f"Error loading inventory file: {str(e)}")
        inventory_data = None

    return sales_data, inventory_data, errors

def generate_demo_data():
    """Generate demo data for testing"""

    # Demo sales data
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    boutiques = ['Dubai Mall', 'Paris Champs-Élysées', 'London Bond Street', 
                'NYC Fifth Avenue', 'Tokyo Ginza', 'Hong Kong Central']
    regions = ['Middle East', 'Europe', 'Europe', 'Americas', 'Asia', 'Asia']
    categories = ['Watches', 'Jewelry', 'Accessories']
    brands = ['Rolex', 'Cartier', 'Patek Philippe', 'Van Cleef & Arpels']

    sales_records = []
    for date in dates:
        for boutique, region in zip(boutiques, regions):
            # Generate 5-15 transactions per boutique per day
            num_transactions = np.random.randint(5, 16)
            for i in range(num_transactions):
                sales_records.append({
                    'Date': date,
                    'Boutique_ID': f"BTQ{boutiques.index(boutique)+1:03d}",
                    'Boutique_Name': boutique,
                    'Region': region,
                    'SKU_Code': f"SKU{np.random.randint(1000, 9999)}",
                    'Product_Category': np.random.choice(categories),
                    'Brand': np.random.choice(brands),
                    'Units_Sold': np.random.randint(1, 4),
                    'Revenue_Local_Currency': np.random.randint(5000, 50000),
                    'Revenue_USD': np.random.randint(5000, 50000),
                    'Transaction_ID': f"TXN{date.strftime('%Y%m%d')}{i:04d}",
                    'Sales_Associate_ID': f"SA{np.random.randint(100, 999)}",
                    'Customer_Type': np.random.choice(['New', 'Returning', 'VIP'], p=[0.3, 0.5, 0.2]),
                    'Payment_Method': np.random.choice(['Credit Card', 'Cash', 'Wire Transfer'])
                })

    sales_data = pd.DataFrame(sales_records)

    # Demo inventory data
    inventory_records = []
    for boutique in boutiques:
        for i in range(50):  # 50 SKUs per boutique
            current_stock = np.random.randint(0, 20)
            min_threshold = 5
            inventory_records.append({
                'Date': datetime.now(),
                'Boutique_ID': f"BTQ{boutiques.index(boutique)+1:03d}",
                'SKU_Code': f"SKU{1000+i}",
                'Product_Name': f"Luxury Item {i}",
                'Category': np.random.choice(categories),
                'Brand': np.random.choice(brands),
                'Current_Stock_Units': current_stock,
                'Min_Stock_Threshold': min_threshold,
                'Max_Stock_Threshold': 20,
                'Unit_Cost': np.random.randint(2000, 20000),
                'Retail_Price': np.random.randint(5000, 50000),
                'Last_Restock_Date': datetime.now() - timedelta(days=np.random.randint(1, 60)),
                'Supplier_Lead_Time_Days': np.random.randint(7, 30)
            })

    inventory_data = pd.DataFrame(inventory_records)

    return sales_data, inventory_data
