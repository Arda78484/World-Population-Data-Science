import wbdata
import pandas as pd
import datetime

def fetch_and_process_data():
    """
    Fetches data from the World Bank API, tags countries and groups,
    and saves it to disk.
    """
    # 1. Indicators
    indicators = {
        'SP.POP.TOTL': 'population',
        'AG.LND.TOTL.K2': 'surface_area'
    }

    # 2. Date Range (Kept wide)
    data_date = (datetime.datetime(1960, 1, 1), datetime.datetime(2023, 12, 31))

    # 3. Fetch Data (Worldwide)
    # cache=True keeps it in memory, avoids repeated queries (during runtime)
    df = wbdata.get_dataframe(indicators, country='all', date=data_date)
    
    # Get rid of MultiIndex (country, date) -> columns
    df.reset_index(inplace=True)
    df['date'] = df['date'].astype(int)
    
    # 4. Metadata Integration (To distinguish between Country and Group)
    # Fetching metadata for all countries/regions
    countries = wbdata.get_countries()
    country_meta = pd.DataFrame(countries)
    
    # Columns of interest: id (iso code), name, region, incomeLevel
    # Those with Region value "Aggregates" are not countries (EU, World, OECD etc.)
    country_meta = country_meta[['name', 'region', 'incomeLevel', 'id']]
    
    # Region column returns a dict, let's extract the value
    country_meta['region_name'] = country_meta['region'].apply(lambda x: x['value'] if isinstance(x, dict) else None)
    
    # Mark those labeled "Aggregates"
    country_meta['is_aggregate'] = country_meta['region_name'] == 'Aggregates'
    
    # Merge metadata with the main DataFrame (Merge on Country Name)
    # Note: 'country' column in wbdata dataframe is the country name.
    # We also include 'id' which is the ISO code, useful for maps
    df_final = pd.merge(df, country_meta[['name', 'region_name', 'is_aggregate', 'id']], left_on='country', right_on='name', how='left')
    
    # Rename id to iso_code for clarity
    df_final.rename(columns={'id': 'iso_code'}, inplace=True)
    
    # Cleanup unnecessary columns
    df_final.drop(columns=['name'], inplace=True)
    
    # Density Calculation (Feature Engineering)
    df_final['density'] = df_final['population'] / df_final['surface_area']
    
    # Save to disk
    import os
    os.makedirs('data', exist_ok=True)
    df_final.to_csv('data/population_data.csv', index=False)
    
    return df_final

if __name__ == "__main__":
    print("Script manuel çalıştırıldı...")
    data = fetch_and_process_data()
    print(data.sample(5))