import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

# Page configuration
st.set_page_config(
    page_title="Nassau Candy Profitability Analytics",
    page_icon="🍬",
    layout="wide"
)

# Title
st.title("🍬 Nassau Candy Distributor - Profitability Analytics Dashboard")
st.markdown("---")

# Load data function
@st.cache_data
def load_data():
    # CORRECT FILE PATH
    file_path = r"D:\teja\Projects\unified project 1\Nassau Candy Distributor.csv"
    
    # Check if file exists
    if not os.path.exists(file_path):
        st.error(f"❌ File not found at: {file_path}")
        
        # Show all CSV files in the folder
        folder = r"D:\teja\Projects\unified project 1"
        if os.path.exists(folder):
            st.write("Files found in folder:")
            for file in os.listdir(folder):
                if file.endswith('.csv'):
                    st.write(f"  - {file}")
        return None
    
    # Load the CSV file
    df = pd.read_csv(file_path)
    st.success(f"✅ Data loaded successfully! Shape: {df.shape}")
    
    # Convert date columns - FIXED for day-month-year format
    if 'Order Date' in df.columns:
        # Try different date formats
        try:
            # Try day-first format (DD-MM-YYYY)
            df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
        except:
            # If that fails, let pandas infer (slower but works)
            df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True, errors='coerce')
    
    if 'Ship Date' in df.columns:
        try:
            df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y', errors='coerce')
        except:
            df['Ship Date'] = pd.to_datetime(df['Ship Date'], dayfirst=True, errors='coerce')
    
    # Calculate additional metrics
    if 'Gross Profit' in df.columns and 'Sales' in df.columns:
        df['Gross_Margin_Pct'] = (df['Gross Profit'] / df['Sales']) * 100
        if 'Units' in df.columns and df['Units'].sum() > 0:
            df['Profit_per_Unit'] = df['Gross Profit'] / df['Units']
        if 'Cost' in df.columns and 'Units' in df.columns:
            df['Cost_per_Unit'] = df['Cost'] / df['Units']
    
    return df

# Load data
df = load_data()

if df is None:
    st.stop()

# Show data preview
with st.expander("📊 View Raw Data Preview"):
    st.dataframe(df.head(10))
    st.write(f"Total Records: {len(df)}")
    st.write("**Column Names:**", df.columns.tolist())

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Date range filter (only if Order Date exists and has valid dates)
if 'Order Date' in df.columns and not df['Order Date'].isna().all():
    min_date = df['Order Date'].min()
    max_date = df['Order Date'].max()
    if pd.notna(min_date) and pd.notna(max_date):
        date_range = st.sidebar.date_input(
            "Date Range",
            [min_date.date(), max_date.date()],
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        # Apply date filter
        mask = (df['Order Date'].dt.date >= date_range[0]) & (df['Order Date'].dt.date <= date_range[1])
        filtered_df = df[mask].copy()
    else:
        filtered_df = df.copy()
else:
    filtered_df = df.copy()

# Division filter
if 'Division' in filtered_df.columns:
    divisions = ['All'] + sorted(filtered_df['Division'].unique().tolist())
    selected_division = st.sidebar.selectbox("Select Division", divisions)
    if selected_division != 'All':
        filtered_df = filtered_df[filtered_df['Division'] == selected_division]

# Margin threshold
if 'Gross_Margin_Pct' in filtered_df.columns:
    margin_threshold = st.sidebar.slider(
        "Minimum Gross Margin (%)",
        min_value=0.0,
        max_value=100.0,
        value=20.0,
        step=5.0
    )
    filtered_df = filtered_df[filtered_df['Gross_Margin_Pct'] >= margin_threshold]

# Product search
if 'Product Name' in filtered_df.columns:
    product_search = st.sidebar.text_input("Search Product", "")
    if product_search:
        filtered_df = filtered_df[
            filtered_df['Product Name'].str.contains(product_search, case=False, na=False)
        ]

# Display filter info
st.sidebar.markdown("---")
st.sidebar.info(f"Showing {len(filtered_df)} of {len(df)} records")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Product Profitability",
    "🏭 Division Performance", 
    "💰 Cost vs Margin Diagnostics",
    "🎯 Profit Concentration",
    "📈 Insights & Recommendations"
])

# Tab 1: Product Profitability
with tab1:
    st.header("Product-Level Profitability Analysis")
    
    if 'Product Name' in filtered_df.columns and 'Gross Profit' in filtered_df.columns:
        # Aggregate by product
        product_metrics = filtered_df.groupby(['Product Name', 'Division']).agg({
            'Sales': 'sum',
            'Gross Profit': 'sum',
            'Units': 'sum',
            'Gross_Margin_Pct': 'mean'
        }).reset_index()
        
        product_metrics = product_metrics.sort_values('Gross Profit', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 10 Products by Profit")
            top_profit = product_metrics.head(10)
            fig = px.bar(top_profit, x='Product Name', y='Gross Profit', 
                         color='Division', title="Top Profit Contributors")
            fig.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Top 10 Products by Margin %")
            top_margin = product_metrics.nlargest(10, 'Gross_Margin_Pct')
            fig = px.bar(top_margin, x='Product Name', y='Gross_Margin_Pct', 
                         color='Division', title="Highest Margin Products")
            fig.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # High sales low margin warning
        st.subheader("⚠️ Margin Risk Alert")
        high_sales = product_metrics[product_metrics['Sales'] > product_metrics['Sales'].quantile(0.75)]
        low_margin = high_sales[high_sales['Gross_Margin_Pct'] < product_metrics['Gross_Margin_Pct'].median()]
        
        if len(low_margin) > 0:
            st.warning(f"{len(low_margin)} products with high sales but below-average margins")
            st.dataframe(low_margin[['Product Name', 'Sales', 'Gross_Margin_Pct', 'Gross Profit']])
        else:
            st.success("✅ No high-risk margin products detected")
    else:
        st.warning("Product or profit columns not found")

# Tab 2: Division Performance
with tab2:
    st.header("Division Performance Analysis")
    
    if 'Division' in filtered_df.columns and 'Gross Profit' in filtered_df.columns:
        division_stats = filtered_df.groupby('Division').agg({
            'Sales': 'sum',
            'Gross Profit': 'sum',
            'Gross_Margin_Pct': 'mean',
            'Units': 'sum'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = make_subplots(rows=1, cols=2, 
                                subplot_titles=("Revenue by Division", "Profit by Division"))
            fig.add_trace(go.Bar(x=division_stats['Division'], y=division_stats['Sales'], 
                                name='Revenue', marker_color='blue'), row=1, col=1)
            fig.add_trace(go.Bar(x=division_stats['Division'], y=division_stats['Gross Profit'], 
                                name='Profit', marker_color='green'), row=1, col=2)
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(division_stats, values='Gross Profit', names='Division', 
                        title="Profit Distribution by Division")
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Division Performance Matrix")
        division_stats['Margin_vs_Avg'] = division_stats['Gross_Margin_Pct'] - division_stats['Gross_Margin_Pct'].mean()
        st.dataframe(division_stats.style.format({
            'Sales': '${:,.0f}',
            'Gross Profit': '${:,.0f}',
            'Gross_Margin_Pct': '{:.1f}%',
            'Margin_vs_Avg': '{:+.1f}%'
        }))
    else:
        st.warning("Division column not found")

# Tab 3: Cost vs Margin Diagnostics
with tab3:
    st.header("Cost Structure Analysis")
    
    if 'Cost' in filtered_df.columns and 'Sales' in filtered_df.columns and 'Gross_Margin_Pct' in filtered_df.columns:
        # Sample data for scatter plot (limit to 2000 points for performance)
        plot_df = filtered_df.sample(min(2000, len(filtered_df)))
        
        fig = px.scatter(plot_df, 
                        x='Cost', y='Sales', 
                        color='Division' if 'Division' in plot_df.columns else None,
                        size='Gross Profit' if 'Gross Profit' in plot_df.columns else None,
                        hover_data=['Product Name'] if 'Product Name' in plot_df.columns else None,
                        title="Cost vs Sales Analysis (Bubble size = Profit)")
        
        # Add break-even line
        max_val = max(plot_df['Cost'].max(), plot_df['Sales'].max())
        fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], 
                                mode='lines', name='Break-even Line', 
                                line=dict(dash='dash', color='red')))
        st.plotly_chart(fig, use_container_width=True)
        
        # Cost-heavy products needing review
        st.subheader("🔴 Products Needing Pricing Review")
        cost_heavy = filtered_df[
            (filtered_df['Cost'] > filtered_df['Cost'].quantile(0.75)) &
            (filtered_df['Gross_Margin_Pct'] < filtered_df['Gross_Margin_Pct'].quantile(0.25))
        ].groupby('Product Name').agg({
            'Cost': 'sum',
            'Gross_Margin_Pct': 'mean',
            'Sales': 'sum'
        }).reset_index().head(10)
        
        if len(cost_heavy) > 0:
            st.warning(f"{len(cost_heavy)} products with high cost and low margin")
            st.dataframe(cost_heavy)
        else:
            st.success("✅ No critical cost-heavy products found")
    else:
        st.warning("Cost, Sales, or Margin columns not found")

# Tab 4: Profit Concentration (Pareto)
with tab4:
    st.header("Pareto Analysis - 80/20 Rule")
    
    if 'Gross Profit' in filtered_df.columns and 'Product Name' in filtered_df.columns:
        product_profit = filtered_df.groupby('Product Name')['Gross Profit'].sum().sort_values(ascending=False)
        cumulative_pct = (product_profit.cumsum() / product_profit.sum() * 100).reset_index()
        cumulative_pct.columns = ['Product', 'Cumulative Profit %']
        cumulative_pct['Product %'] = (cumulative_pct.index + 1) / len(cumulative_pct) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cumulative_pct['Product %'], 
                                y=cumulative_pct['Cumulative Profit %'],
                                mode='lines+markers', 
                                name='Profit Concentration',
                                line=dict(color='green', width=3)))
        fig.add_hline(y=80, line_dash="dash", line_color="red", 
                     annotation_text="80% of Profit", annotation_position="top right")
        fig.add_vline(x=20, line_dash="dash", line_color="red",
                     annotation_text="20% of Products", annotation_position="top left")
        fig.update_layout(title="Pareto Chart: Profit Concentration",
                         xaxis_title="Percentage of Products (%)",
                         yaxis_title="Cumulative Profit (%)",
                         height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        products_for_80 = cumulative_pct[cumulative_pct['Cumulative Profit %'] <= 80].shape[0]
        pct_products = (products_for_80 / len(cumulative_pct)) * 100
        st.metric("Products generating 80% of profit", 
                 f"{products_for_80} products ({pct_products:.1f}%)")
        
        if pct_products < 20:
            st.success("✅ Healthy profit concentration (better than 80/20 rule)")
        else:
            st.warning("⚠️ Profit is spread across many products - consider focusing on top performers")
    else:
        st.warning("Required columns for Pareto analysis not found")

# Tab 5: Insights
with tab5:
    st.header("Key Insights & Recommendations")
    
    if 'Gross Profit' in filtered_df.columns and 'Sales' in filtered_df.columns:
        col1, col2, col3, col4 = st.columns(4)
        total_profit = filtered_df['Gross Profit'].sum()
        total_sales = filtered_df['Sales'].sum()
        
        with col1:
            st.metric("Total Profit", f"${total_profit:,.0f}")
        with col2:
            st.metric("Total Sales", f"${total_sales:,.0f}")
        with col3:
            margin = (total_profit/total_sales*100) if total_sales>0 else 0
            st.metric("Overall Margin", f"{margin:.1f}%")
        with col4:
            st.metric("Transactions", len(filtered_df))
        
        st.markdown("---")
        
        # Automated insights
        st.subheader("🤖 Automated Business Insights")
        
        # Best and worst products
        if 'Product Name' in filtered_df.columns:
            product_summary = filtered_df.groupby('Product Name')['Gross Profit'].sum()
            best_product = product_summary.idxmax() if len(product_summary) > 0 else "N/A"
            worst_product = product_summary.idxmin() if len(product_summary) > 0 else "N/A"
            
            st.markdown(f"""
            ### ✅ Top Opportunities:
            1. **Star Product:** {best_product} generates highest profit
            2. **Growth Potential:** Focus marketing on high-margin products
            
            ### ⚠️ Critical Issues:
            1. **Profit Drain:** {worst_product} needs review
            2. **Volume Trap:** Products with high sales but low margins need repricing
            """)
        
        st.markdown("---")
        
        # Recommendations
        st.subheader("💡 Strategic Recommendations")
        
        rec1, rec2, rec3 = st.columns(3)
        with rec1:
            st.info("**🎯 Product Strategy**\n\n• Focus marketing on top 20% profit products\n• Review bottom 10% for discontinuation\n• Bundle low-margin with high-margin products")
        
        with rec2:
            st.info("**💰 Pricing Actions**\n\n• Increase prices on low-margin items\n• Implement volume discounts for profitable products\n• Review cost structure for negative margin items")
        
        with rec3:
            st.info("**🏭 Operations**\n\n• Renegotiate supplier costs for margin-poor products\n• Optimize factory allocation using distance data\n• Improve shipping efficiency for high-volume products")
    else:
        st.warning("Required columns for insights not found")

st.markdown("---")
st.caption("📊 Nassau Candy Profitability Analytics | Data-Driven Decision Support System")
