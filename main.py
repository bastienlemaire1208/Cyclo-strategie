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
  ftp, weight, z2_upper = 250, 70, 180
  power_curve = {}

  res_prof = requests.get(f"{BASE_URL}/athlete/{ATHLETE_ID}", auth=auth)
  if res_prof.status_code == 200:
    data = res_prof.json()
    ftp = data.get("ftp", 250)
    weight = data.get("weight", 70)

  res_zones = requests.get(f"{BASE_URL}/athlete/{ATHLETE_ID}/zones", auth=auth)
  if res_zones.status_code == 200:
    for zone_set in res_zones.json():
      if zone_set.get("type") == "PWR":
        intervals = zone_set.get("value", [])
        if len(intervals) >= 2:
          z2_upper = intervals[1].get("max", int(ftp * 0.75))

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

  return ftp, weight, z2_upper, power_curve


ftp, weight, z2_upper, power_curve = get_intervals_data()

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

st.sidebar.header("Paramètres Intervals.icu")
st.sidebar.write(f"**FTP :** {ftp} W")
st.sidebar.write(f"**Poids :** {weight} kg")
st.sidebar.write(f"**Seuil Z2/Z3 :** {z2_upper} W")

st.sidebar.header("Paramètres de course")
distance = st.sidebar.number_input("Distance (km)", value=distance_km)
elevation = st.sidebar.number_input("Dénivelé positif (m D+)", value=elevation_m)
target_power = st.sidebar.slider(
    "Puissance cible (W)",
    min_value=100,
    max_value=int(ftp * 1.5),
    value=z2_upper,
)

w_kg = target_power / weight
estimated_vam = int(w_kg * 140) + 350
time_on_flat = (distance - (elevation / 100)) / 30
time_on_climb = elevation / estimated_vam if estimated_vam > 0 else 0
total_hours = max(0.5, time_on_flat + time_on_climb)

carbs_per_hour = 80 if target_power > z2_upper else 60
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
  rc2.metric("Max 1min", f"{p1m} W" if isinstance(p1m, (int, float)) else p1m)
  rc3.metric("Max 5min", f"{p5m} W" if isinstance(p5m, (int, float)) else p5m)
  rc4.metric("Max 20min", f"{p20m} W" if isinstance(p20m, (int, float)) else p20m)

if climbs_info:
  st.subheader("Cols et côtes répertoriés (GPX)")
  for climb in climbs_info:
    st.markdown(f"— {climb}")
