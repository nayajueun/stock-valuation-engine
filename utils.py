import pandas as pd
import os
import json

# Function to save data to CSV
def save_to_csv(data, filepath, mode='w'):
    df = pd.DataFrame(data)
    
    # Convert complex objects to JSON strings before saving
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
  
    if mode == 'w' or not os.path.isfile(filepath):
        df.to_csv(filepath, index=False, mode=mode, header=True)
    else:
        df.to_csv(filepath, index=False, mode=mode, header=False)


def load_csv(filepath):
    df = pd.read_csv(filepath)
    
    # Attempt to convert strings back to Python objects if they are JSON
    for column in df.columns:
        if df[column].dtype == object:
            print(column)
            df[column] = df[column].apply(lambda x: json.loads(x) if is_json(x) else x)
    
    return df

def is_json(myjson):
    if not isinstance(myjson, str):
        return False
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True


def load_and_filter_data(filepath, country=None, sector=None, min_cap=None, max_cap=None):
    df = pd.read_csv(filepath)
    if country:
        df = df[df['Country'] == country]
    if sector:
        df = df[df['Sector Key'] == sector]
    if min_cap:
        df = df[df['Market Cap'] >= float(min_cap)]
    if max_cap:
        df = df[df['Market Cap'] <= float(max_cap)]
    return df
