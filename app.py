import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

# Page configuration
st.set_page_config(
    page_title="Afficionado Coffee Roasters - Product Optimization & Revenue Analysis",
    page_icon="☕",
    layout="wide"
)

# Title
st.title("☕ Afficionado Coffee Roasters - Product Optimization & Revenue Contribution Analysis")
st.markdown("---")

# Load data function
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try different file names
    possible_files = [
        "Afficionado Coffee Roasters.xlsx",
        "Afficionado Coffee Roasters.csv",
        "afficionado_coffee_roasters.xlsx",
        "afficionado_coffee_roasters.csv",
        "coffee_transactions.xlsx",
        "coffee_transactions.csv"
    ]
    
    for file_name in possible_files:
        file_path = os.path.join(current_dir, file_name)
        if os.path.exists(file_path):
            st.success(f"✅ Found file: {file_name}")
            
            # Load based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='latin1')
            else:
                df = pd.read_excel(file_path)
            
            return df
    
    st.error("❌ No data file found!")
    st.write("Files in current directory:")
    for file in os.listdir(current_dir):
        st.write(f"  - {file}")
    return None

# Load data
df = load_data()

if df is None:
    st.stop()

# Calculate Revenue
if 'transaction_qty' in df.columns and 'unit_price' in df.columns:
    df['revenue'] = df['transaction_qty'] * df['unit_price']
elif 'transaction_qty' in df.columns and 'Unit Price' in df.columns:
    df['revenue'] = df['transaction_qty'] * df['Unit Price']
elif 'Quantity' in df.columns and 'Price' in df.columns:
    df['revenue'] = df['Quantity'] * df['Price']

# Show data preview
with st.expander("📊 View Raw Data Preview"):
    st.dataframe(df.head(10))
    st.write(f"Total Records: {len(df)}")
    st.write("**Column Names:**", df.columns.tolist())

# Sidebar Filters
st.sidebar.header("🔍 Filters")

# Store location filter
if 'store_location' in df.columns:
    stores = ['All'] + sorted(df['store_location'].unique().tolist())
    selected_store = st.sidebar.selectbox("Select Store Location", stores)
else:
    selected_store = 'All'

# Category filter
if 'product_category' in df.columns:
    categories = ['All'] + sorted(df['product_category'].unique().tolist())
    selected_category = st.sidebar.selectbox("Select Product Category", categories)
else:
    selected_category = 'All'

# Product type filter
if 'product_type' in df.columns:
    product_types = ['All'] + sorted(df['product_type'].unique().tolist())
    selected_type = st.sidebar.selectbox("Select Product Type", product_types)
else:
    selected_type = 'All'

# Top N products slider
top_n = st.sidebar.slider("Number of Top Products to Display", min_value=5, max_value=30, value=10)

# Apply filters
filtered_df = df.copy()

if selected_store != 'All' and 'store_location' in df.columns:
    filtered_df = filtered_df[filtered_df['store_location'] == selected_store]

if selected_category != 'All' and 'product_category' in df.columns:
    filtered_df = filtered_df[filtered_df['product_category'] == selected_category]

if selected_type != 'All' and 'product_type' in df.columns:
    filtered_df = filtered_df[filtered_df['product_type'] == selected_type]

# Display filter info
st.sidebar.markdown("---")
st.sidebar.info(f"Showing {len(filtered_df)} of {len(df)} records")

# Calculate total revenue
total_revenue = filtered_df['revenue'].sum() if 'revenue' in filtered_df.columns else 0

# Key Metrics Row
st.subheader("📊 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue", f"${total_revenue:,.0f}")

with col2:
    unique_products = filtered_df['product_id'].nunique() if 'product_id' in filtered_df.columns else 0
    st.metric("Unique Products", unique_products)

with col3:
    total_quantity = filtered_df['transaction_qty'].sum() if 'transaction_qty' in filtered_df.columns else 0
    st.metric("Total Units Sold", f"{total_quantity:,}")

with col4:
    avg_transaction = filtered_df['revenue'].mean() if 'revenue' in filtered_df.columns else 0
    st.metric("Avg Transaction Value", f"${avg_transaction:.2f}")

st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Product Popularity & Revenue",
    "🏷️ Category & Product-Type Performance",
    "🎯 Revenue Concentration (Pareto)",
    "📈 Product Efficiency Analysis",
    "💡 Insights & Recommendations"
])

# ==================== TAB 1: Product Popularity & Revenue ====================
with tab1:
    st.header("Product Popularity vs Revenue Contribution")
    
    if 'product_id' in filtered_df.columns and 'revenue' in filtered_df.columns:
        # Aggregate by product
        product_metrics = filtered_df.groupby(['product_id', 'product_detail', 'product_category', 'product_type']).agg({
            'transaction_qty': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        product_metrics = product_metrics.sort_values('revenue', ascending=False)
        product_metrics['revenue_share'] = (product_metrics['revenue'] / product_metrics['revenue'].sum()) * 100
        product_metrics['volume_share'] = (product_metrics['transaction_qty'] / product_metrics['transaction_qty'].sum()) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"🏆 Top {top_n} Products by Revenue")
            top_revenue = product_metrics.head(top_n)
            fig = px.bar(top_revenue, x='product_detail', y='revenue', 
                         color='product_category', title=f"Top {top_n} Revenue Generators",
                         text_auto='.0f')
            fig.update_layout(xaxis_tickangle=-45, height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader(f"📈 Top {top_n} Products by Sales Volume")
            top_volume = product_metrics.nlargest(top_n, 'transaction_qty')
            fig = px.bar(top_volume, x='product_detail', y='transaction_qty', 
                         color='product_category', title=f"Top {top_n} Best Sellers",
                         text_auto=True)
            fig.update_layout(xaxis_tickangle=-45, height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Scatter plot: Revenue vs Volume
        st.subheader("📊 Revenue vs Sales Volume Analysis")
        fig = px.scatter(product_metrics, 
                        x='transaction_qty', y='revenue', 
                        size='revenue_share', color='product_category',
                        hover_data=['product_detail', 'product_type'],
                        title="Product Positioning Map (Size = Revenue Share)",
                        labels={'transaction_qty': 'Units Sold', 'revenue': 'Total Revenue ($)'})
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Bottom performers
        st.subheader("⚠️ Low-Performing Products (Need Review)")
        bottom_products = product_metrics.nsmallest(10, 'revenue')[['product_detail', 'product_category', 'product_type', 'transaction_qty', 'revenue', 'revenue_share']]
        st.dataframe(bottom_products.style.format({
            'revenue': '${:,.0f}',
            'revenue_share': '{:.2f}%',
            'transaction_qty': '{:,.0f}'
        }))
    else:
        st.warning("Product or revenue columns not found")

# ==================== TAB 2: Category & Product-Type Performance ====================
with tab2:
    st.header("Category & Product-Type Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'product_category' in filtered_df.columns and 'revenue' in filtered_df.columns:
            st.subheader("Revenue by Category")
            category_revenue = filtered_df.groupby('product_category')['revenue'].sum().reset_index()
            fig = px.pie(category_revenue, values='revenue', names='product_category', 
                        title="Revenue Distribution by Category", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            # Category metrics table
            category_metrics = filtered_df.groupby('product_category').agg({
                'revenue': 'sum',
                'transaction_qty': 'sum',
                'product_id': 'nunique'
            }).reset_index()
            category_metrics.columns = ['Category', 'Revenue', 'Units Sold', 'Unique Products']
            category_metrics['Revenue Share'] = (category_metrics['Revenue'] / category_metrics['Revenue'].sum()) * 100
            st.subheader("Category Performance Metrics")
            st.dataframe(category_metrics.style.format({
                'Revenue': '${:,.0f}',
                'Revenue Share': '{:.1f}%',
                'Units Sold': '{:,.0f}'
            }))
    
    with col2:
        if 'product_type' in filtered_df.columns and 'revenue' in filtered_df.columns:
            st.subheader(f"Top {top_n} Product Types by Revenue")
            type_revenue = filtered_df.groupby('product_type')['revenue'].sum().sort_values(ascending=False).head(top_n).reset_index()
            fig = px.bar(type_revenue, x='product_type', y='revenue', 
                        title=f"Top {top_n} Product Types", color='revenue')
            fig.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Product type within selected category
            if selected_category != 'All' and 'product_category' in filtered_df.columns:
                st.subheader(f"Product Types in {selected_category}")
                cat_filtered = filtered_df[filtered_df['product_category'] == selected_category]
                type_details = cat_filtered.groupby('product_type').agg({
                    'revenue': 'sum',
                    'transaction_qty': 'sum'
                }).reset_index().sort_values('revenue', ascending=False)
                st.dataframe(type_details.style.format({
                    'revenue': '${:,.0f}',
                    'transaction_qty': '{:,.0f}'
                }))

# ==================== TAB 3: Revenue Concentration (Pareto) ====================
with tab3:
    st.header("Revenue Concentration Analysis (Pareto / 80/20 Rule)")
    
    if 'product_id' in filtered_df.columns and 'revenue' in filtered_df.columns:
        # Sort products by revenue
        product_revenue = filtered_df.groupby(['product_id', 'product_detail', 'product_category'])['revenue'].sum().sort_values(ascending=False).reset_index()
        product_revenue['cumulative_revenue'] = product_revenue['revenue'].cumsum()
        product_revenue['cumulative_percent'] = (product_revenue['cumulative_revenue'] / product_revenue['revenue'].sum()) * 100
        product_revenue['product_percent'] = (product_revenue.index + 1) / len(product_revenue) * 100
        
        # Pareto chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=product_revenue['product_percent'], 
                                y=product_revenue['cumulative_percent'],
                                mode='lines+markers', 
                                name='Cumulative Revenue',
                                line=dict(color='#2E7D32', width=3),
                                fill='tozeroy', fillcolor='rgba(46,125,50,0.2)'))
        fig.add_hline(y=80, line_dash="dash", line_color="red", 
                     annotation_text="80% of Revenue", annotation_position="top right")
        fig.add_vline(x=20, line_dash="dash", line_color="red",
                     annotation_text="20% of Products", annotation_position="top left")
        fig.update_layout(title="Pareto Chart: Revenue Concentration",
                         xaxis_title="Percentage of Products (%)",
                         yaxis_title="Cumulative Revenue (%)",
                         height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate concentration
        products_for_80 = product_revenue[product_revenue['cumulative_percent'] <= 80].shape[0]
        pct_products = (products_for_80 / len(product_revenue)) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Products generating 80% of Revenue", 
                     f"{products_for_80} products ({pct_products:.1f}%)")
        
        with col2:
            # Revenue anchor products (top 20%)
            top_20_count = int(len(product_revenue) * 0.2)
            top_20_revenue = product_revenue.head(top_20_count)['revenue'].sum()
            top_20_percent = (top_20_revenue / product_revenue['revenue'].sum()) * 100
            st.metric("Top 20% Products Revenue Contribution", f"{top_20_percent:.1f}%")
        
        with col3:
            # Long tail products (bottom 50%)
            bottom_50_count = int(len(product_revenue) * 0.5)
            bottom_50_revenue = product_revenue.tail(bottom_50_count)['revenue'].sum()
            bottom_50_percent = (bottom_50_revenue / product_revenue['revenue'].sum()) * 100
            st.metric("Bottom 50% Products Revenue Contribution", f"{bottom_50_percent:.1f}%")
        
        # Revenue anchors (hero products)
        st.subheader("🌟 Revenue Anchor Products (Hero Products)")
        hero_products = product_revenue.head(5)[['product_detail', 'product_category', 'revenue']]
        hero_products['revenue_share'] = (hero_products['revenue'] / product_revenue['revenue'].sum()) * 100
        st.dataframe(hero_products.style.format({
            'revenue': '${:,.0f}',
            'revenue_share': '{:.1f}%'
        }))
        
        # Long tail products (candidates for removal)
        st.subheader("📋 Long-Tail Products (Candidates for Menu Review)")
        long_tail = product_revenue.tail(10)[['product_detail', 'product_category', 'revenue']]
        long_tail['revenue_share'] = (long_tail['revenue'] / product_revenue['revenue'].sum()) * 100
        st.dataframe(long_tail.style.format({
            'revenue': '${:,.0f}',
            'revenue_share': '{:.3f}%'
        }))
        
        # Risk assessment
        st.subheader("⚠️ Menu Diversification Risk Assessment")
        if pct_products < 20:
            st.success(f"✅ Healthy revenue concentration ({pct_products:.1f}% products drive 80% revenue). Menu is efficient.")
        elif pct_products < 30:
            st.warning(f"⚠️ Moderate concentration ({pct_products:.1f}% products drive 80% revenue). Consider menu optimization.")
        else:
            st.error(f"🔴 High diversification risk ({pct_products:.1f}% products drive 80% revenue). Menu may be overcrowded.")
    else:
        st.warning("Required columns not found")

# ==================== TAB 4: Product Efficiency Analysis ====================
with tab4:
    st.header("Product Efficiency Score Analysis")
    
    if 'product_id' in filtered_df.columns and 'revenue' in filtered_df.columns:
        # Calculate efficiency metrics
        product_efficiency = filtered_df.groupby(['product_id', 'product_detail', 'product_category']).agg({
            'revenue': 'sum',
            'transaction_qty': 'sum'
        }).reset_index()
        
        product_efficiency['revenue_per_unit'] = product_efficiency['revenue'] / product_efficiency['transaction_qty']
        product_efficiency['revenue_per_unit_rank'] = product_efficiency['revenue_per_unit'].rank(ascending=False)
        
        # Efficiency score (normalized 0-100)
        max_revenue_per_unit = product_efficiency['revenue_per_unit'].max()
        product_efficiency['efficiency_score'] = (product_efficiency['revenue_per_unit'] / max_revenue_per_unit) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Highest Revenue Per Unit (Premium Products)")
            high_efficiency = product_efficiency.nlargest(10, 'revenue_per_unit')[['product_detail', 'product_category', 'revenue_per_unit', 'efficiency_score']]
            fig = px.bar(high_efficiency, x='product_detail', y='revenue_per_unit', 
                        color='product_category', title="Top 10 Products by Revenue Per Unit")
            fig.update_layout(xaxis_tickangle=-45, height=450)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Product Efficiency Matrix")
            # Create efficiency categories
            product_efficiency['efficiency_category'] = pd.cut(
                product_efficiency['efficiency_score'], 
                bins=[0, 25, 50, 75, 101], 
                labels=['Low', 'Medium', 'High', 'Premium']
            )
            efficiency_counts = product_efficiency['efficiency_category'].value_counts().reset_index()
            efficiency_counts.columns = ['Efficiency Level', 'Count']
            fig = px.pie(efficiency_counts, values='Count', names='Efficiency Level',
                        title="Product Efficiency Distribution", hole=0.3,
                        color_discrete_map={'Premium': '#2E7D32', 'High': '#4CAF50', 
                                           'Medium': '#FFC107', 'Low': '#F44336'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Efficiency vs Volume scatter
        st.subheader("📈 Efficiency vs Popularity Matrix")
        fig = px.scatter(product_efficiency, 
                        x='transaction_qty', y='revenue_per_unit',
                        size='revenue', color='efficiency_category',
                        hover_data=['product_detail', 'product_category'],
                        title="Product Positioning: Efficiency (Price) vs Popularity (Volume)",
                        labels={'transaction_qty': 'Units Sold (Popularity)', 
                               'revenue_per_unit': 'Revenue Per Unit ($) - Efficiency'})
        fig.add_hline(y=product_efficiency['revenue_per_unit'].median(), 
                     line_dash="dash", line_color="gray", 
                     annotation_text="Median Efficiency")
        fig.add_vline(x=product_efficiency['transaction_qty'].median(), 
                     line_dash="dash", line_color="gray",
                     annotation_text="Median Popularity")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations based on quadrant
        st.subheader("🎯 Product Strategy Recommendations by Quadrant")
        
        # Define quadrants
        median_volume = product_efficiency['transaction_qty'].median()
        median_price = product_efficiency['revenue_per_unit'].median()
        
        stars = product_efficiency[(product_efficiency['transaction_qty'] > median_volume) & 
                                  (product_efficiency['revenue_per_unit'] > median_price)]
        workhorses = product_efficiency[(product_efficiency['transaction_qty'] > median_volume) & 
                                        (product_efficiency['revenue_per_unit'] <= median_price)]
        niche = product_efficiency[(product_efficiency['transaction_qty'] <= median_volume) & 
                                   (product_efficiency['revenue_per_unit'] > median_price)]
        underperformers = product_efficiency[(product_efficiency['transaction_qty'] <= median_volume) & 
                                            (product_efficiency['revenue_per_unit'] <= median_price)]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.info(f"⭐ **Stars**\n{len(stars)} products\nHigh volume, High price")
        with col2:
            st.info(f"🔄 **Workhorses**\n{len(workhorses)} products\nHigh volume, Low price")
        with col3:
            st.info(f"💎 **Niche**\n{len(niche)} products\nLow volume, High price")
        with col4:
            st.warning(f"⚠️ **Underperformers**\n{len(underperformers)} products\nLow volume, Low price")
    else:
        st.warning("Required columns not found")

# ==================== TAB 5: Insights & Recommendations ====================
with tab5:
    st.header("Key Insights & Strategic Recommendations")
    
    if 'revenue' in filtered_df.columns:
        total_rev = filtered_df['revenue'].sum()
        unique_prods = filtered_df['product_id'].nunique() if 'product_id' in filtered_df.columns else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Revenue", f"${total_rev:,.0f}")
        with col2:
            st.metric("Unique Products", unique_prods)
        with col3:
            revenue_per_product = total_rev / unique_prods if unique_prods > 0 else 0
            st.metric("Revenue Per Product", f"${revenue_per_product:,.0f}")
        
        st.markdown("---")
        
        # Automated insights
        st.subheader("🤖 Automated Business Insights")
        
        if 'product_id' in filtered_df.columns:
            product_rev = filtered_df.groupby('product_id')['revenue'].sum().sort_values(ascending=False)
            top_product = product_rev.idxmax() if len(product_rev) > 0 else "N/A"
            top_product_rev = product_rev.max() if len(product_rev) > 0 else 0
            
            st.markdown(f"""
            ### 📊 Revenue Distribution Insights:
            - **Top Product** contributes **${top_product_rev:,.0f}** ({top_product_rev/total_rev*100:.1f}% of total)
            - **Bottom 20% of products** contribute only **{(product_rev.tail(int(len(product_rev)*0.2)).sum()/total_rev*100):.1f}%** of revenue
            - **Revenue per product** averages **${revenue_per_product:,.0f}**
            """)
        
        # Recommendations
        st.subheader("💡 Strategic Recommendations for Menu Optimization")
        
        rec1, rec2, rec3 = st.columns(3)
        
        with rec1:
            st.markdown("""
            ### 🎯 Menu Simplification
            - **Remove or Redesign:** Bottom 10% of products by revenue
            - **Consolidate:** Similar low-performing variants
            - **Test:** Seasonal rotation for niche products
            """)
        
        with rec2:
            st.markdown("""
            ### 💰 Pricing Strategy
            - **Increase prices** on workhorse products (high volume, low price)
            - **Premium positioning** for star products
            - **Bundle** underperformers with popular items
            """)
        
        with rec3:
            st.markdown("""
            ### 🏆 Hero Product Strategy
            - **Feature** top 5 revenue anchors in marketing
            - **Cross-sell** with complementary products
            - **Ensure availability** of hero products at all stores
            """)
        
        st.markdown("---")
        
        # Specific action items
        st.subheader("📋 Specific Action Items")
        
        action_items = pd.DataFrame({
            'Priority': ['🔴 High', '🔴 High', '🟡 Medium', '🟡 Medium', '🟢 Low'],
            'Action': [
                'Review bottom 5 products for potential removal',
                'Increase prices on top 5 workhorse products by 5-10%',
                'Create combo deals featuring hero products + underperformers',
                'Test premium versions of top 3 revenue anchors',
                'Seasonal rotation for long-tail products'
            ],
            'Expected Impact': [
                'Reduce menu complexity',
                '+3-5% revenue from these products',
                'Increase underperformer sales by 15%',
                'Higher average transaction value',
                'Menu freshness, customer interest'
            ]
        })
        st.dataframe(action_items, use_container_width=True)
        
        # Efficiency summary
        st.subheader("📊 Product Efficiency Summary")
        st.info("""
        **Key Metrics to Track Monthly:**
        - Revenue Concentration Ratio (% of products generating 80% revenue)
        - Number of products with <0.5% revenue share
        - Average revenue per product
        - Top 5 products revenue contribution %
        """)
    else:
        st.warning("Revenue column not found")

# Footer
st.markdown("---")
st.caption("☕ Afficionado Coffee Roasters - Product Optimization & Revenue Contribution Analysis | Data-Driven Menu Intelligence")
