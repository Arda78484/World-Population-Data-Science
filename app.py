import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from src.data_fetcher import fetch_and_process_data
from src.data_processor import calculate_missing_stats, clean_data, calculate_growth_rate, get_top_n_countries
import os

# Page Settings
st.set_page_config(page_title="World Pop Insights", layout="wide")

st.title("🌍 World Population Insights")
st.markdown("Historical Population Analysis")

# Data Loading (Cache mechanism)
@st.cache_data
def load_data():
    if os.path.exists('data/population_data.csv'):
        return pd.read_csv('data/population_data.csv')
    return None

# Sidebar - Control Panel
with st.sidebar:
    st.header("Data Management")
    
    # API Fetch
    if st.button("Fetch / Update Data from API"):
        with st.spinner('Communicating with World Bank API...'):
            try:
                load_data.clear()
                new_df = fetch_and_process_data()
                st.success(f"Data fetched successfully! Total Rows: {len(new_df)}")
                if 'cleaned_df' in st.session_state:
                    del st.session_state.cleaned_df
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Reload Local Data
    if st.button("Reload Local Data"):
        load_data.clear()
        if 'cleaned_df' in st.session_state:
            del st.session_state.cleaned_df
        st.success("Cache cleared and data reloaded from disk.")
        st.rerun()

df = load_data()

if df is not None:
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Data Health & Cleaning", "📊 Overview", "🏆 Rankings & Growth", "📈 Time Series Analysis", "📂 Raw Data"])

    # --- TAB 1: DATA HEALTH & CLEANING ---
    with tab1:
        st.header("Data Quality Analysis")
        
        # Session State usage: To keep cleaned data in memory
        if 'cleaned_df' not in st.session_state:
            st.session_state.cleaned_df = df

        current_df = st.session_state.cleaned_df
        stats = calculate_missing_stats(current_df)

        # 1. Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cells", f"{stats['total_cells']:,}")
        col2.metric("Missing Cells", f"{stats['missing_cells']:,}", delta_color="inverse")
        col3.metric("Missing Ratio", f"%{stats['missing_ratio']:.2f}")

        # 2. Visualization (Pie Chart and Heatmap)
        col_viz1, col_viz2 = st.columns(2)
        
        with col_viz1:
            st.subheader("Fill Rate (Pie Chart)")
            # Pie chart data
            labels = ['Filled Data', 'Missing Data']
            sizes = [stats['total_cells'] - stats['missing_cells'], stats['missing_cells']]
            explode = (0, 0.1)  # Separate the missing slice slightly

            fig_pie, ax_pie = plt.subplots()
            ax_pie.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                    shadow=True, startangle=90, colors=['#66b3ff','#ff9999'])
            ax_pie.axis('equal') 
            st.pyplot(fig_pie)

        with col_viz2:
            st.subheader("Missing Data Map (Heatmap)")
            st.markdown("Yellow lines indicate missing data locations.")
            # Seaborn Heatmap - For professional look
            fig_heat, ax_heat = plt.subplots(figsize=(8, 5))
            # If data is too large, heatmap slows down, so we can sample or just show nulls
            sns.heatmap(current_df.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax_heat)
            st.pyplot(fig_heat)

        # 3. Action: Cleaning Options
        st.divider()
        st.subheader("🛠️ Cleaning Operations")
        
        clean_method = st.selectbox(
            "Select Cleaning Method:",
            ("Select...", "drop (Delete missing rows)", "fill_mean (Fill with country mean)", "interpolate (Time series completion)")
        )
        
        if st.button("Apply"):
            if clean_method != "Select...":
                method_key = clean_method.split()[0] # take before parenthesis
                st.session_state.cleaned_df = clean_data(df, strategy=method_key)
                st.success(f"Data cleaned with '{method_key}' method! Charts updated.")
                st.rerun() # Rerun to update charts with new data
            else:
                st.warning("Please select a method.")

    # Use current_df for other tabs
    if 'cleaned_df' not in st.session_state:
        st.session_state.cleaned_df = df
    current_df = st.session_state.cleaned_df

    with tab2:
        st.subheader("Country and Group Distinction")
        
        # Filtering Option
        filter_option = st.radio("Analysis Scope:", ["Countries Only", "Groups Only (Aggregates)", "All"], horizontal=True)
        
        if filter_option == "Countries Only":
            filtered_df = current_df[current_df['is_aggregate'] == False]
        elif filter_option == "Groups Only (Aggregates)":
            filtered_df = current_df[current_df['is_aggregate'] == True]
        else:
            filtered_df = current_df

        # Year Selection
        min_year = int(filtered_df['date'].min())
        max_year = int(filtered_df['date'].max())
        
        selected_year = st.slider("Select Year", min_year, max_year, max_year, key="overview_year_slider")

        # Data for Selected Year
        year_data = filtered_df[filtered_df['date'] == selected_year].copy()
        
        # Fill NaN density for visualization to avoid Plotly errors
        year_data['density'] = year_data['density'].fillna(0)
        
        col1, col2 = st.columns(2)
        col1.metric("Number of Entities in Dataset", len(year_data))
        col1.markdown(f"*Selected Year: {selected_year}*")
        
        # --- CHOROPLETH MAP ---
        st.markdown(f"### 🗺️ Global Population Map ({selected_year})")
        if 'iso_code' in year_data.columns:
            fig_map = px.choropleth(
                year_data,
                locations="iso_code",
                color="population",
                hover_name="country",
                color_continuous_scale=px.colors.sequential.Plasma,
                title=f"World Population Map ({selected_year})",
                labels={'population': 'Population'}
            )
            fig_map.update_layout(geo=dict(showframe=False, showcoastlines=False, projection_type='equirectangular'))
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("ISO codes not found in data. Please click 'Fetch / Update Data from API' to update the dataset with ISO codes.")

        # Simple Scatter Plot (Density vs Population)
        st.markdown(f"### Population vs Surface Area Distribution ({selected_year})")
        
        # Interactive Plotly Chart
        fig = px.scatter(
            year_data,
            x="surface_area",
            y="population",
            color="region_name",
            size="density",
            hover_name="country",
            log_x=True,
            log_y=True,
            title=f"{selected_year} Distribution (Logarithmic)",
            labels={
                "surface_area": "Surface Area (km²)",
                "population": "Population",
                "region_name": "Region",
                "density": "Density (pop/km²)"
            },
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: RANKINGS & GROWTH ---
    with tab3:
        st.header("🏆 Rankings & Growth Analysis")
        
        # Calculate Growth Rate if not present
        if 'growth_rate' not in current_df.columns:
            current_df = calculate_growth_rate(current_df)
            st.session_state.cleaned_df = current_df # Update session state
        
        col_rank1, col_rank2 = st.columns([1, 2])
        
        with col_rank1:
            st.subheader("Top N Analysis")
            target_year = st.slider("Select Year", int(current_df['date'].min()), int(current_df['date'].max()), int(current_df['date'].max()), key="rankings_year_slider")
            metric = st.selectbox("Select Metric", ["population", "density", "growth_rate", "surface_area"])
            top_n = st.slider("Number of Countries", 5, 20, 10)
            
            top_countries = get_top_n_countries(current_df, target_year, metric, n=top_n)
            st.dataframe(top_countries[['country', metric, 'region_name']].reset_index(drop=True))
            
        with col_rank2:
            st.subheader(f"Top {top_n} Countries by {metric.capitalize()} ({target_year})")
            fig_bar, ax_bar = plt.subplots(figsize=(10, 6))
            sns.barplot(data=top_countries, x=metric, y='country', palette='viridis', ax=ax_bar)
            ax_bar.set_title(f"Top {top_n} by {metric}")
            st.pyplot(fig_bar)
            
        st.divider()
        
        st.subheader("Growth Rate Distribution")
        # Histogram of growth rates for the selected year
        year_data = current_df[(current_df['date'] == target_year) & (current_df['is_aggregate'] == False)]
        
        fig_hist, ax_hist = plt.subplots(figsize=(10, 4))
        sns.histplot(data=year_data, x='growth_rate', bins=30, kde=True, ax=ax_hist)
        ax_hist.set_title(f"Distribution of Population Growth Rates in {target_year}")
        ax_hist.set_xlabel("Growth Rate (%)")
        st.pyplot(fig_hist)

    with tab4:
        st.subheader("Comparative Growth")
        # Country selection with Multiselect
        all_entities = current_df['country'].unique().tolist()
        selected_entities = st.multiselect("Select Countries/Groups to Compare:", all_entities, default=["Turkiye", "Germany"])
        
        if selected_entities:
            subset = current_df[current_df['country'].isin(selected_entities)]
            
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            sns.lineplot(data=subset, x='date', y='population', hue='country', ax=ax2)
            ax2.set_title("Population Change by Year")
            ax2.grid(True, linestyle='--', alpha=0.7)
            st.pyplot(fig2)

    with tab5:
        st.dataframe(current_df)

else:
    st.info("No data available yet. Please click the 'Fetch / Update Data from API' button in the sidebar.")