import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def check_alerts(sales_data, inventory_data, thresholds):
    """Check for critical alerts based on thresholds"""

    alerts = {
        'critical': [],
        'warning': []
    }

    # Default thresholds
    default_thresholds = {
        'revenue_drop_pct': 15,
        'sales_target_miss_pct': 20,
        'low_stock_threshold': 5,
        'conversion_drop_pct': 25,
        'inventory_turnover_min': 2,
        'shrinkage_rate_max': 1.5
    }

    # Merge with provided thresholds
    thresholds = {**default_thresholds, **thresholds}

    # Get today's and last week's data
    today = datetime.now().date()
    if len(sales_data) > 0:
        latest_date = sales_data['Date'].max().date()
        today_data = sales_data[sales_data['Date'].dt.date == latest_date]
        week_ago = latest_date - timedelta(days=7)
        week_ago_data = sales_data[sales_data['Date'].dt.date == week_ago]

        # Revenue Drop Alert
        today_revenue = today_data['Revenue_USD'].sum()
        week_ago_revenue = week_ago_data['Revenue_USD'].sum()

        if week_ago_revenue > 0:
            revenue_change = ((today_revenue - week_ago_revenue) / week_ago_revenue * 100)
            if revenue_change < -thresholds['revenue_drop_pct']:
                alerts['critical'].append(
                    f"Revenue dropped {abs(revenue_change):.1f}% vs. same day last week"
                )

        # Boutique Performance Alerts
        boutique_revenue = today_data.groupby('Boutique_Name')['Revenue_USD'].sum()
        avg_boutique_revenue = boutique_revenue.mean()

        for boutique, revenue in boutique_revenue.items():
            if revenue < avg_boutique_revenue * 0.5:  # 50% below average
                alerts['warning'].append(
                    f"{boutique} revenue significantly below network average"
                )

        # Zero Transaction Alert (after 2 PM)
        current_hour = datetime.now().hour
        if current_hour >= 14:
            boutiques_with_sales = set(today_data['Boutique_Name'].unique())
            all_boutiques = set(sales_data['Boutique_Name'].unique())
            no_sales_boutiques = all_boutiques - boutiques_with_sales

            for boutique in no_sales_boutiques:
                alerts['critical'].append(
                    f"{boutique} has ZERO transactions today"
                )

    # Inventory Alerts
    if len(inventory_data) > 0:
        # Low Stock Alert
        low_stock = inventory_data[
            inventory_data['Current_Stock_Units'] <= inventory_data['Min_Stock_Threshold']
        ]

        if len(low_stock) > 0:
            alerts['warning'].append(
                f"{len(low_stock)} SKUs below minimum stock threshold"
            )

        # Stockout Alert
        stockout = inventory_data[inventory_data['Current_Stock_Units'] == 0]

        if len(stockout) > 0:
            for _, item in stockout.head(5).iterrows():  # Show top 5
                alerts['critical'].append(
                    f"STOCKOUT: {item['Product_Name']} at {item.get('Boutique_ID', 'Unknown')}"
                )

        # Dead Stock Alert (over 180 days)
        if 'Last_Restock_Date' in inventory_data.columns:
            inventory_data['Days_Since_Restock'] = (
                datetime.now() - pd.to_datetime(inventory_data['Last_Restock_Date'])
            ).dt.days

            dead_stock = inventory_data[
                (inventory_data['Days_Since_Restock'] > 180) & 
                (inventory_data['Current_Stock_Units'] > 0)
            ]

            if len(dead_stock) > 0:
                dead_stock_value = (dead_stock['Current_Stock_Units'] * 
                                   dead_stock['Unit_Cost']).sum()
                total_inventory_value = (inventory_data['Current_Stock_Units'] * 
                                        inventory_data['Unit_Cost']).sum()
                dead_stock_pct = (dead_stock_value / total_inventory_value * 100) if total_inventory_value > 0 else 0

                if dead_stock_pct > 10:
                    alerts['warning'].append(
                        f"Dead stock (>180 days) represents {dead_stock_pct:.1f}% of inventory value"
                    )

    return alerts

def send_alert_summary(alerts, email_settings):
    """Send alert summary via email"""

    if not email_settings:
        print("Email settings not configured. Skipping email send.")
        return

    try:
        # Create email
        msg = MIMEMultipart()
        msg['From'] = email_settings.get('from_email', 'dashboard@company.com')
        msg['To'] = ', '.join(email_settings.get('to_emails', []))
        msg['Subject'] = f"Luxury Retail Dashboard - Alert Summary {datetime.now().strftime('%Y-%m-%d')}"

        # Email body
        body = f"""
        <html>
        <body>
        <h2>Daily Alert Summary</h2>
        <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h3 style="color: red;">Critical Alerts ({len(alerts['critical'])})</h3>
        <ul>
        {''.join([f'<li>{alert}</li>' for alert in alerts['critical']])}
        </ul>

        <h3 style="color: orange;">Warnings ({len(alerts['warning'])})</h3>
        <ul>
        {''.join([f'<li>{alert}</li>' for alert in alerts['warning']])}
        </ul>

        <p><a href="{email_settings.get('dashboard_url', '#')}">View Full Dashboard</a></p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # Send email (requires SMTP configuration)
        # Uncomment and configure when deploying
        # with smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port']) as server:
        #     server.starttls()
        #     server.login(email_settings['smtp_username'], email_settings['smtp_password'])
        #     server.send_message(msg)

        print("Alert summary prepared (email sending disabled in demo)")

    except Exception as e:
        print(f"Error sending alert email: {str(e)}")
