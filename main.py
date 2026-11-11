import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd

st.title("Analyseur de Trace GPX")

uploaded_file = st.file_uploader("Dépose ton fichier GPX ici", type=["gpx"])

def parse_gpx(file_obj):
    tree = ET.parse(file_obj)
    root = tree.getroot()
    
    # Extraction dynamique du namespace du fichier GPX
    ns = {'gpx': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
    tag_path = './/{http://www.topografix.com/GPX/1/1}trkpt' if ns else './/trkpt'
    
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
    try:
        df_gpx = parse_gpx(uploaded_file)
        st.success(f"Fichier chargé avec succès ! {len(df_gpx)} points détectés.")
        st.write(df_gpx.head())
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
else:
    st.info("Envoie un fichier GPX pour commencer l'analyse.")
