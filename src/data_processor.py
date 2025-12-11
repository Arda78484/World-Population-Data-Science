import pandas as pd
import numpy as np

def calculate_missing_stats(df):
    """
    Calculates missing value statistics for the dataframe.
    """
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    missing_ratio = (missing_cells / total_cells) * 100
    
    # Missing by column
    missing_by_column = df.isnull().sum()
    missing_by_column = missing_by_column[missing_by_column > 0]
    
    return {
        'total_cells': total_cells,
        'missing_cells': missing_cells,
        'missing_ratio': missing_ratio,
        'missing_by_column': missing_by_column
    }

def clean_data(df, strategy='fill_mean'):
    """
    Cleans the data based on the selected strategy.
    """
    df_clean = df.copy()
    
    if strategy == 'drop':
        # Drop rows with missing data
        df_clean.dropna(inplace=True)
        
    elif strategy == 'fill_mean':
        # Fill with mean per country (Most logical approach)
        # Only fill numeric columns
        numeric_cols = ['population', 'surface_area', 'density']
        
        # Each country should use its own mean, not the global mean.
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean.groupby('country')[col].transform(lambda x: x.fillna(x.mean()))
            
        # If still empty (e.g., a country has no data at all), drop them
        existing_cols = [c for c in numeric_cols if c in df_clean.columns]
        if existing_cols:
            df_clean.dropna(subset=existing_cols, how='all', inplace=True)
        
    elif strategy == 'interpolate':
        # Interpolation is elegant for time series
        if 'date' in df_clean.columns:
            df_clean = df_clean.sort_values(by=['country', 'date'])
            
        numeric_cols = ['population', 'surface_area', 'density']
        
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean.groupby('country')[col].transform(lambda x: x.interpolate(method='linear', limit_direction='both'))
                
    return df_clean

def calculate_growth_rate(df):
    """
    Calculates the year-over-year population growth rate for each country.
    Adds a 'growth_rate' column to the dataframe.
    """
    # Ensure data is sorted by country and date
    df_sorted = df.sort_values(by=['country', 'date']).copy()
    
    # Calculate percentage change for population grouped by country
    # pct_change() calculates (current - previous) / previous
    df_sorted['growth_rate'] = df_sorted.groupby('country')['population'].pct_change() * 100
    
    return df_sorted

def get_top_n_countries(df, year, metric, n=10):
    """
    Returns the top N countries for a given metric in a specific year.
    Filters out aggregates to show only countries.
    """
    # Filter for the specific year and only countries (not aggregates)
    mask = (df['date'] == year) & (df['is_aggregate'] == False)
    df_year = df[mask]
    
    # Sort by the metric
    return df_year.sort_values(by=metric, ascending=False).head(n)
