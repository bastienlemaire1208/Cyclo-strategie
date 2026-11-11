import xml.etree.ElementTree as ET
import pandas as pd

def parse_gpx(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    data = []
    for trkpt in root.iter('{http://www.topografix.com/GPX/1/1}trkpt'):
        lat = float(trkpt.attrib['lat'])
        lon = float(trkpt.attrib['lon'])
        
        ele_elem = trkpt.find('{http://www.topografix.com/GPX/1/1}ele')
        ele = float(ele_elem.text) if ele_elem is not None else 0.0
        
        time_elem = trkpt.find('{http://www.topografix.com/GPX/1/1}time')
        time = time_elem.text if time_elem is not None else None
        
        data.append({
            'time': pd.to_datetime(time) if time else None, 
            'lat': lat, 
            'lon': lon, 
            'ele': ele
        })
        
    df = pd.DataFrame(data)
    if 'time' in df.columns and df['time'].notna().any():
        df.set_index('time', inplace=True)
    return df

if __name__ == '__main__':
    # Exemple d'utilisation : remplacez 'sortie.gpx' par le chemin de votre fichier
    file_path = 'sortie.gpx'
    try:
        df_gpx = parse_gpx(file_path)
        print(df_gpx.head())
    except FileNotFoundError:
        print(f"Fichier {file_path} introuvable.")

