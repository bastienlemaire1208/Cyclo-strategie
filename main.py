import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd

st.title("Analyseur de Trace GPX")

uploaded_file = st.file_uploader("Dépose ton fichier GPX ici", type=["gpx"])

def parse_gpx(file_obj):
    tree = ET.parse(file_obj)
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

if uploaded_file is not None:
    df_gpx = parse_gpx(uploaded_file)
    st.success("Fichier GPX chargé avec succès !")
    st.write(df_gpx.head())
else:
    st.info("Envoie un fichier GPX pour commencer l'analyse.")
