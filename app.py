import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yaml
from pathlib import Path

# Import custom modules
from modules.data_loader import load_data, validate_excel
from modules.kpi_calculator import calculate_kpis, calculate_boutique_metrics
from modules.alerts import check_alerts, send_alert_summary
from modules.visualizations import create_revenue_chart, create_inventory_chart, create_conversion_funnel

# Page configuration
st.set_page_config(
    page_title="Luxury Retail BI Dashboard",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for luxury brand feel
st.markdown('''
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a1a;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-critical {
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .alert-warning {
        background-color: #ffaa00;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
</style>
''', unsafe_allow_html=True)

# Load configuration
@st.cache_resource
def load_config():
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.warning("Configuration file not found. Using default settings.")
        return {}

config = load_config()

# Title
st.markdown('<h1 class="main-header">💎 Luxury Retail Business Intelligence Dashboard</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=YOUR+LOGO", use_container_width=True)
    st.title("Dashboard Controls")

    # Data source selection
    data_source = st.radio("Data Source:", ["Upload Excel", "Demo Data"])

    if data_source == "Upload Excel":
        st.subheader("📊 Upload Data Files")

        sales_file = st.file_uploader("Daily Sales Report", type=['xlsx', 'xls', 'csv'], key="sales")
        inventory_file = st.file_uploader("Inventory Report", type=['xlsx', 'xls', 'csv'], key="inventory")

        if st.button("Process Uploaded Data", type="primary"):
            if sales_file and inventory_file:
                with st.spinner("Processing data..."):
                    sales_data, inventory_data, errors = load_data(sales_file, inventory_file)
                    if errors:
                        st.error("\n".join(errors))
                    else:
                        st.success("✓ Data loaded successfully!")
                        st.session_state['sales_data'] = sales_data
                        st.session_state['inventory_data'] = inventory_data
            else:
                st.warning("Please upload both files.")

    # Date range filter
    st.subheader("📅 Date Range")
    date_range = st.date_input(
        "Select Period:",
        value=(datetime.now() - timedelta(days=7), datetime.now()),
        max_value=datetime.now()
    )

    # Region/Boutique filter
    st.subheader("🏪 Filters")
    selected_region = st.multiselect("Region:", ["All", "Asia", "Europe", "Middle East", "Americas"])
    selected_boutique = st.multiselect("Boutique:", ["All"])

    # Refresh button
    if st.button("🔄 Refresh Data", type="secondary"):
        st.rerun()

# Main dashboard
if data_source == "Demo Data" or 'sales_data' in st.session_state:

    # Use demo data if selected
    if data_source == "Demo Data":
        from modules.data_loader import generate_demo_data
        sales_data, inventory_data = generate_demo_data()
    else:
        sales_data = st.session_state.get('sales_data')
        inventory_data = st.session_state.get('inventory_data')

    # Calculate KPIs
    kpis = calculate_kpis(sales_data, inventory_data)

    # Alert Section
    st.subheader("🚨 Critical Alerts")
    alerts = check_alerts(sales_data, inventory_data, config.get('thresholds', {}))

    if alerts['critical']:
        for alert in alerts['critical']:
            st.markdown(f'<div class="alert-critical">🔴 {alert}</div>', unsafe_allow_html=True)

    if alerts['warning']:
        for alert in alerts['warning']:
            st.markdown(f'<div class="alert-warning">⚠️ {alert}</div>', unsafe_allow_html=True)

    if not alerts['critical'] and not alerts['warning']:
        st.success("✓ All metrics within healthy ranges")

    st.divider()

    # Key Metrics Row
    st.subheader("📊 Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Daily Revenue",
            value=f"${kpis['daily_revenue']:,.0f}",
            delta=f"{kpis['revenue_growth']:.1f}%"
        )

    with col2:
        st.metric(
            label="Avg Transaction Value",
            value=f"${kpis['atv']:,.0f}",
            delta=f"{kpis['atv_change']:.1f}%"
        )

    with col3:
        st.metric(
            label="Conversion Rate",
            value=f"{kpis['conversion_rate']:.1f}%",
            delta=f"{kpis['conversion_change']:.1f}%"
        )

    with col4:
        st.metric(
            label="Inventory Turnover",
            value=f"{kpis['inventory_turnover']:.1f}x",
            delta="Healthy" if kpis['inventory_turnover'] > 2 else "Low"
        )

    with col5:
        st.metric(
            label="Stock Alerts",
            value=kpis['low_stock_items'],
            delta=f"{kpis['stockout_risk']} at risk"
        )

    st.divider()

    # Charts Row 1
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Revenue Trend (7 Days)")
        revenue_chart = create_revenue_chart(sales_data)
        st.plotly_chart(revenue_chart, use_container_width=True)

    with col2:
        st.subheader("🏪 Top 5 Boutiques by Revenue")
        boutique_metrics = calculate_boutique_metrics(sales_data)
        boutique_chart = px.bar(
            boutique_metrics.head(5),
            x='Boutique_Name',
            y='Revenue',
            color='Revenue',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(boutique_chart, use_container_width=True)

    # Charts Row 2
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 Inventory Status by Category")
        inventory_chart = create_inventory_chart(inventory_data)
        st.plotly_chart(inventory_chart, use_container_width=True)

    with col2:
        st.subheader("🎯 Conversion Funnel")
        funnel_chart = create_conversion_funnel(sales_data)
        st.plotly_chart(funnel_chart, use_container_width=True)

    st.divider()

    # Detailed Tables
    st.subheader("📋 Detailed Boutique Performance")

    # Display boutique metrics table
    st.dataframe(
        boutique_metrics,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Revenue": st.column_config.NumberColumn(
                "Revenue",
                format="$%d"
            ),
            "Units_Sold": st.column_config.NumberColumn(
                "Units Sold",
                format="%d"
            ),
            "Conversion_Rate": st.column_config.NumberColumn(
                "Conversion %",
                format="%.1f%%"
            )
        }
    )

    # Export section
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Export to Excel", type="primary"):
            # Create Excel export
            output_path = f"data/processed/dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                boutique_metrics.to_excel(writer, sheet_name='Boutique_Performance', index=False)
                pd.DataFrame([kpis]).to_excel(writer, sheet_name='KPIs', index=False)
            st.success(f"✓ Exported to {output_path}")

    with col2:
        if st.button("📧 Send Alert Summary", type="secondary"):
            send_alert_summary(alerts, config.get('email_settings', {}))
            st.success("✓ Alert summary sent to executives")

    with col3:
        st.download_button(
            label="📄 Download Report PDF",
            data="Sample PDF Report",
            file_name="dashboard_report.pdf",
            mime="application/pdf"
        )

else:
    st.info("👆 Please upload your data files using the sidebar to begin.")

    st.subheader("📋 Required Excel Headers")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Sales Report Headers:**")
        st.code('''Date
Boutique_ID
Boutique_Name
Region
SKU_Code
Product_Category
Brand
Units_Sold
Revenue_Local_Currency
Revenue_USD
Transaction_ID
Sales_Associate_ID
Customer_Type
Payment_Method''')

    with col2:
        st.markdown("**Inventory Report Headers:**")
        st.code('''Date
Boutique_ID
SKU_Code
Product_Name
Category
Brand
Current_Stock_Units
Min_Stock_Threshold
Max_Stock_Threshold
Unit_Cost
Retail_Price
Last_Restock_Date
Supplier_Lead_Time_Days''')

# Footer
st.divider()
st.markdown(
    f'''
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>💎 Luxury Retail BI Dashboard | Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
        <a href="https://github.com/yourusername/luxury-retail-dashboard" target="_blank">GitHub Repository</a></p>
    </div>
    ''',
    unsafe_allow_html=True
)
