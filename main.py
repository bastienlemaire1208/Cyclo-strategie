import os
import gpxpy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("INTERVALS_API_KEY")
ATHLETE_ID = os.getenv("INTERVALS_ATHLETE_ID")
BASE_URL = "https://intervals.icu/api/v1"

CACHE_RECORDS_PATH = "saved_power_records.csv"

st.title("Planificateur de Course Vélo")


@st.cache_data
def get_intervals_data():
  auth = ("API_KEY", API_KEY)
  default_ftp, default_weight, default_sv1 = 280, 68.0, 210
  logs = []

  res_prof = requests.get(f"{BASE_URL}/athlete/{ATHLETE_ID}", auth=auth)
  if res_prof.status_code == 200:
    data = res_prof.json()
    default_weight = float(
        data.get("weight") or data.get("icu_weight") or default_weight
    )
    default_ftp = int(data.get("ftp") or default_ftp)
    logs.append(
        f"✅ Profil récupéré — Poids : {default_weight} kg | FTP : {default_ftp}"
        " W"
    )
  else:
    logs.append("⚠️ Échec profil, valeurs par défaut.")

  res_zones = requests.get(f"{BASE_URL}/athlete/{ATHLETE_ID}/zones", auth=auth)
  if res_zones.status_code == 200:
    for zone_set in res_zones.json():
      if zone_set.get("type") == "PWR":
        intervals = zone_set.get("value", [])
        if len(intervals) >= 2:
          default_sv1 = int(
              intervals[1].get("max") or int(default_ftp * 0.75)
          )
          logs.append(f"✅ SV1 récupéré : {default_sv1} W")
        break
  else:
    default_sv1 = int(default_ftp * 0.75)
    logs.append("⚠️ Échec zones, SV1 estimé à 75 % FTP.")

  return default_ftp, default_weight, default_sv1, logs


fetched_ftp, fetched_weight, fetched_sv1, api_logs = get_intervals_data()

with st.expander("Logs de validation Intervals.icu", expanded=False):
  for log in api_logs:
    st.write(log)

if "power_records" not in st.session_state:
  st.session_state.power_records = {
      "5s": 1099,
      "1min": 614,
      "5min": 374,
      "20min": 301,
  }
  if os.path.exists(CACHE_RECORDS_PATH):
    try:
      df_saved = pd.read_csv(CACHE_RECORDS_PATH, sep=None, engine="python")
      df_saved.columns = [str(col).strip().lower() for col in df_saved.columns]
      if "secs" in df_saved.columns and "watts" in df_saved.columns:
        for _, row in df_saved.iterrows():
          secs = row["secs"]
          watts = row["watts"]
          if secs == 5:
            st.session_state.power_records["5s"] = int(watts)
          elif secs == 60:
            st.session_state.power_records["1min"] = int(watts)
          elif secs == 300:
            st.session_state.power_records["5min"] = int(watts)
          elif secs == 1200:
            st.session_state.power_records["20min"] = int(watts)
    except Exception:
      pass

st.sidebar.header("Records de puissance (CSV)")
csv_file = st.sidebar.file_uploader(
    "Dépose ton CSV « Meilleurs efforts » (optionnel)"
)

if csv_file is not None:
  try:
    with open(CACHE_RECORDS_PATH, "wb") as f:
      f.write(csv_file.getbuffer())

    df_csv = pd.read_csv(CACHE_RECORDS_PATH, sep=None, engine="python")
    df_csv.columns = [str(col).strip().lower() for col in df_csv.columns]

    if "secs" in df_csv.columns and "watts" in df_csv.columns:
      for _, row in df_csv.iterrows():
        secs = row["secs"]
        watts = row["watts"]
        if secs == 5:
          st.session_state.power_records["5s"] = int(watts)
        elif secs == 60:
          st.session_state.power_records["1min"] = int(watts)
        elif secs == 300:
          st.session_state.power_records["5min"] = int(watts)
        elif secs == 1200:
          st.session_state.power_records["20min"] = int(watts)
      st.sidebar.success("✅ Nouveaux records enregistrés et mémorisés sur disque")
  except Exception as e:
    st.sidebar.error(f"Erreur de lecture du fichier : {e}")
elif os.path.exists(CACHE_RECORDS_PATH):
  st.sidebar.info("📁 Records chargés depuis la sauvegarde locale.")

uploaded_file = st.file_uploader("Dépose ton fichier GPX (Komoot)", type=["gpx"])

distance_km, elevation_m, detected_climbs, flat_sections = (
    100.0,
    1500.0,
