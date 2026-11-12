import os
import gpxpy
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("INTERVALS_API_KEY")
ATHLETE_ID = os.getenv("INTERVALS_ATHLETE_ID")
BASE_URL = "https://intervals.icu/api/v1"

st.title("Planificateur de Course Vélo")


@st.cache_data
def get_intervals_data():
  auth = ("API_KEY", API_KEY)
  default_ftp, default_weight, default_sv1 = 280, 68.0, 210
  power_curve = {}
  logs = []

  res_prof = requests.get(f"{BASE_URL}/athlete/{ATHLETE_ID}", auth=auth)
  if res_prof.status_code == 200:
    data = res_prof.json()
    default_weight = float(
        data.get("weight") or data.get("icu_weight") or default_weight
    )
    logs.append(f"✅ Poids récupéré : {default_weight} kg")
  else:
    logs.append("⚠️ Échec profil, utilisation de la valeur par défaut.")

  res_settings = requests.get(
      f"{BASE_URL}/athlete/{ATHLETE_ID}/settings", auth=auth
  )
  if res_settings.status_code == 200:
    settings = res_settings.json()
    sport_settings = settings.get("sportSettings", [])
    for sport in sport_settings:
      if sport.get("type") == "Ride":
        default_ftp = int(sport.get("icu_ftp") or default_ftp)
        logs.append(f"✅ FTP Cyclisme récupérée : {default_ftp} W")
        break
  else:
    logs.append("⚠️ Échec settings, utilisation de la valeur par défaut.")

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
  else:
    logs.append("⚠️ Échec zones, utilisation de la valeur par défaut.")

  res_curves = requests.get(
      f"{BASE_URL}/athlete/{ATHLETE_ID}/power-curves?curves=all&type=Ride",
      auth=auth,
  )
  if res_curves.status_code == 200:
    curves_data = res_curves.json()
    if curves_data and isinstance(curves_data, list):
      secs = curves_data[0].get("secs", [])
      watts = curves_data[0].get("watts", [])
      power_curve = dict(zip(secs, watts))
      logs.append(
          f"✅ Courbe de puissance chargée ({len(power_curve)} points)."
      )
  else:
    logs.append("⚠️ Échec courbe de puissance.")

  return default_ftp, default_weight, default_sv1, power_curve, logs


fetched_ftp, fetched_weight, fetched_sv1, power_curve, api_logs = (
    get_intervals_data()
)

with st.expander("Logs de validation Intervals.icu", expanded=False):
  for log in api_logs:
    st.write(log)

uploaded_file = st.file_uploader("Dépose ton fichier GPX (Komoot)", type=["gpx"])

distance_km, elevation_m, climbs_info = 100.0, 1500.0, []

if uploaded_file is not None:
  gpx = gpxpy.parse(uploaded_file)
  total_distance, elevation_gain = 0, 0
  prev_point = None

  for track in gpx.tracks:
    for segment in track.segments:
      for point in segment.points:
        if prev_point:
          total_distance += prev_point.distance_3d(point) or 0
          diff = point.elevation - prev_point.elevation
          if diff > 0:
            elevation_gain += diff
        prev_point = point

  distance_km = round(total_distance / 1000, 1)
  elevation_m = round(elevation_gain)

  for wpt in gpx.waypoints:
    if wpt.name:
      climbs_info.append(wpt.name)

st.sidebar.header("Paramètres physiologiques")
ftp = st.sidebar.number_input("FTP (W)", value=fetched_ftp, step=1)
weight = st.sidebar.number_input(
    "Poids (kg)", value=fetched_weight, step=0.1, format="%.1f"
)
sv1_power = st.sidebar.number_input("SV1 (W)", value=fetched_sv1, step=1)

st.sidebar.header("Paramètres de course")
distance = st.sidebar.number_input("Distance (km)", value=distance_km)
elevation = st.sidebar.number_input("Dénivelé positif (m D+)", value=elevation_m)
target_power = st.sidebar.slider(
    "Puissance cible (W)",
    min_value=100,
    max_value=int(ftp * 1.5),
    value=int(sv1_power),
)

w_kg = target_power / weight if weight and weight > 0 else 4.0
estimated_vam = int(w_kg * 140) + 350
time_on_flat = (distance - (elevation / 100)) / 30
time_on_climb = elevation / estimated_vam if estimated_vam > 0 else 0
total_hours = max(0.5, time_on_flat + time_on_climb)

carbs_per_hour = 80 if target_power > sv1_power else 60
total_carbs = int(total_hours * carbs_per_hour)
total_water_liters = round(total_hours * 0.7, 1)

col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      "Temps estimé",
      f"{int(total_hours)}h {int((total_hours % 1) * 60):02d}min",
  )
with col2:
  st.metric("Puissance Cible", f"{target_power} W", f"{w_kg:.1f} W/kg")
with col3:
  st.metric("VAM Estimée", f"{estimated_vam} m/h")
with col4:
  st.metric("Ravitaillement", f"{total_carbs} g", f"{total_water_liters} L")

if power_curve:
  st.subheader("Records de puissance (All-Time Intervals.icu)")
  p5s = power_curve.get(5, "N/A")
  p1m = power_curve.get(60, "N/A")
  p5m = power_curve.get(300, "N/A")
  p20m = power_curve.get(1200, "N/A")

  rc1, rc2, rc3, rc4 = st.columns(4)
  rc1.metric("Max 5s", f"{p5s} W" if isinstance(p5s, (int, float)) else p5s)
  rc2.Metric("Max 1min", f"{p1m} W" if isinstance(p1m, (int, float)) else p1m)
  rc3.metric("Max 5min", f"{p5m} W" if isinstance(p5m, (int, float)) else p5m)
  rc4.metric("Max 20min", f"{p20m} W" if isinstance(p20m, (int, float)) else p20m)

if climbs_info:
  st.subheader("Cols et côtes répertoriés (GPX)")
  for climb in climbs_info:
    st.markdown(f"— {climb}")
