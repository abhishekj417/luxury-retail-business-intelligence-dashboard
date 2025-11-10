import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_revenue_chart(sales_data):
    """Create 7-day revenue trend chart"""
    daily_revenue = sales_data.groupby(sales_data['Date'].dt.date)['Revenue_USD'].sum().reset_index()
    daily_revenue.columns = ['Date', 'Revenue']

    fig = px.line(daily_revenue, x='Date', y='Revenue', 
                  title='Daily Revenue Trend',
                  markers=True)
    fig.update_traces(line_color='#667eea', line_width=3)
    fig.update_layout(hovermode='x unified')
    return fig

def create_inventory_chart(inventory_data):
    """Create inventory status by category"""
    category_stock = inventory_data.groupby('Category').agg({
        'Current_Stock_Units': 'sum',
        'Min_Stock_Threshold': 'sum'
    }).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Current Stock', x=category_stock['Category'], 
                         y=category_stock['Current_Stock_Units']))
    fig.add_trace(go.Bar(name='Min Threshold', x=category_stock['Category'], 
                         y=category_stock['Min_Stock_Threshold']))

    fig.update_layout(barmode='group', title='Inventory Levels by Category')
    return fig

def create_conversion_funnel(sales_data):
    """Create conversion funnel visualization"""
    total_visitors = len(sales_data['Boutique_ID'].unique()) * 100
    unique_customers = len(sales_data['Transaction_ID'].unique())
    total_transactions = len(sales_data)

    fig = go.Figure(go.Funnel(
        y=['Store Visitors', 'Engaged Customers', 'Completed Purchases'],
        x=[total_visitors, unique_customers, total_transactions],
        textinfo="value+percent initial"
    ))

    fig.update_layout(title='Customer Conversion Funnel')
    return fig
