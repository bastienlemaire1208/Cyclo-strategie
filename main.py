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

st.sidebar.header("Records de puissance (CSV)")
csv_file = st.sidebar.file_uploader("Dépose ton CSV « Meilleurs efforts »")

if csv_file is not None:
  try:
    df_csv = pd.read_csv(csv_file, sep=None, engine="python")
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
      st.sidebar.success("✅ Records mis à jour et mémorisés")
    else:
      st.sidebar.warning(
          "⚠️ Format non reconnu : colonnes 'Secs' et 'Watts' attendues."
      )
  except Exception as e:
    st.sidebar.error(f"Erreur de lecture du fichier : {e}")

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

st.sidebar.header("Météo & Environnement")
ambient_temp = st.sidebar.slider(
    "Température extérieure estimée (°C)", min_value=0, max_value=40, value=20
)

st.sidebar.header("Paramètres de course")
distance = st.sidebar.number_input("Distance (km)", value=distance_km)
elevation = st.sidebar.number_input("Dénivelé positif (m D+)", value=elevation_m)

# Calcul de la Puissance Critique (CP) et de W' à partir des records 5 min et 20 min
p5 = st.session_state.power_records["5min"]
p20 = st.session_state.power_records["20min"]
cp = (p20 * 1200 - p5 * 300) / (1200 - 300)
w_prime = (p20 - cp) * 1200

estimated_duration_hours_rough = (distance / 27) + (elevation / 1000 * 0.4)
if estimated_duration_hours_rough > 4:
  target_power = int(cp * 0.90)
elif estimated_duration_hours_rough > 2:
  target_power = int(cp * 0.95)
else:
  target_power = int(cp)

w_kg = target_power / weight if weight and weight > 0 else 4.0
estimated_vam = int(w_kg * 140) + 350
time_on_flat = (distance - (elevation / 100)) / 30
time_on_climb = elevation / estimated_vam if estimated_vam > 0 else 0
total_hours = max(0.5, time_on_flat + time_on_climb)

water_per_hour_ml = int(550 + (ambient_temp - 20) * 25)
water_per_hour_ml = max(300, water_per_hour_ml)
total_water_liters = round((total_hours * water_per_hour_ml) / 1000, 1)

base_carbs_h = 90 if target_power >= sv1_power else 60
carbs_per_hour = (
    int(base_carbs_h * 0.85) if ambient_temp > 28 else base_carbs_h
)
total_carbs = int(total_hours * carbs_per_hour)

col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(
      "Temps estimé",
      f"{int(total_hours)}h {int((total_hours % 1) * 60):02d}min",
  )
with col2:
  st.metric("Puissance Cible (PN)", f"{target_power} W")
with col3:
  st.metric(
      "Glucides",
      f"{total_carbs} g",
      help=f"~{carbs_per_hour} g/h (Jeukendrup)",
  )
with col4:
  st.metric(
      "Hydratation",
      f"{total_water_liters} L",
      help=f"~{water_per_hour_ml} ml/h ({ambient_temp}°C)",
  )

if climbs_info:
  st.subheader("Cols et côtes répertoriés (Modèle CP / W')")
  for climb in climbs_info:
    # Estimation d'un effort type de 15 minutes (900s) par col, pondéré à 92% pour la course
    t_climb_sec = 900
    climb_target_w = int((cp + (w_prime / t_climb_sec)) * 0.92)
    st.markdown(
        f"— **{climb}** : cible optimale modélisée ~{climb_target_w} W"
    )
