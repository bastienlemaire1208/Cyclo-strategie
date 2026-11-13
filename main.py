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
      "10min": 335,
      "15min": 315,
      "20min": 301,
      "30min": 275,
      "45min": 255,
      "1h": 240,
      "1h30": 215,
  }
if "vam_records" not in st.session_state:
  st.session_state.vam_records = {}

if os.path.exists(CACHE_RECORDS_PATH):
  try:
    df_saved = pd.read_csv(CACHE_RECORDS_PATH, sep=None, engine="python")
    df_saved.columns = [str(col).strip().lower() for col in df_saved.columns]
    if "secs" in df_saved.columns and "watts" in df_saved.columns:
      for _, row in df_saved.iterrows():
        secs = row["secs"]
        watts = row["watts"]
        if pd.notna(watts):
          if secs == 5:
            st.session_state.power_records["5s"] = int(watts)
          elif secs == 60:
            st.session_state.power_records["1min"] = int(watts)
          elif secs == 300:
            st.session_state.power_records["5min"] = int(watts)
          elif secs == 600:
            st.session_state.power_records["10min"] = int(watts)
          elif secs == 900:
            st.session_state.power_records["15min"] = int(watts)
          elif secs == 1200:
            st.session_state.power_records["20min"] = int(watts)
          elif secs == 1800:
            st.session_state.power_records["30min"] = int(watts)
          elif secs == 2700:
            st.session_state.power_records["45min"] = int(watts)
          elif secs == 3600:
            st.session_state.power_records["1h"] = int(watts)
          elif secs == 5400:
            st.session_state.power_records["1h30"] = int(watts)
        if "vam" in df_saved.columns and pd.notna(row["vam"]):
          st.session_state.vam_records[int(secs)] = float(row["vam"])
  except Exception:
    pass

st.sidebar.header("Records de puissance & VAM (CSV)")
csv_file = st.sidebar.file_uploader(
    "Dépose ton CSV « Meilleurs efforts » (secs, watts, vam)"
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
        if pd.notna(watts):
          if secs == 5:
            st.session_state.power_records["5s"] = int(watts)
          elif secs == 60:
            st.session_state.power_records["1min"] = int(watts)
          elif secs == 300:
            st.session_state.power_records["5min"] = int(watts)
          elif secs == 600:
            st.session_state.power_records["10min"] = int(watts)
          elif secs == 900:
            st.session_state.power_records["15min"] = int(watts)
          elif secs == 1200:
            st.session_state.power_records["20min"] = int(watts)
          elif secs == 1800:
            st.session_state.power_records["30min"] = int(watts)
          elif secs == 2700:
            st.session_state.power_records["45min"] = int(watts)
          elif secs == 3600:
            st.session_state.power_records["1h"] = int(watts)
          elif secs == 5400:
            st.session_state.power_records["1h30"] = int(watts)
        if "vam" in df_csv.columns and pd.notna(row["vam"]):
          st.session_state.vam_records[int(secs)] = float(row["vam"])
      st.sidebar.success(
          "✅ Nouveaux records (Watts et VAM) enregistrés sur disque"
      )
  except Exception as e:
    st.sidebar.error(f"Erreur de lecture du fichier : {e}")
elif os.path.exists(CACHE_RECORDS_PATH):
  st.sidebar.info("📁 Records chargés depuis la sauvegarde locale.")

uploaded_file = st.file_uploader("Dépose ton fichier GPX (Komoot)", type=["gpx"])

distance_km, elevation_m, detected_climbs, flat_sections = (
    100.0,
    1500.0,
    [],
    [],
)
map_points = []
points_data = []

if uploaded_file is not None:
  gpx = gpxpy.parse(uploaded_file)
  total_distance, elevation_gain = 0, 0
  prev_point = None

  for track in gpx.tracks:
    for segment in track.segments:
      for point in segment.points:
        map_points.append({"lat": point.latitude, "lon": point.longitude})
        if prev_point:
          d = prev_point.distance_3d(point) or 0
          total_distance += d
          diff = point.elevation - prev_point.elevation
          if diff > 0:
            elevation_gain += diff
          points_data.append(
              {
                  "dist": total_distance / 1000.0,
                  "elev": point.elevation or 0.0,
                  "d_dist": d / 1000.0,
                  "d_elev": diff,
              }
          )
        prev_point = point

  distance_km = round(total_distance / 1000, 1)
  elevation_m = round(elevation_gain)

  if len(points_data) > 20:
    current_dist = 0
    current_elev = 0
    climb_start = 0
    in_climb = False
    climb_pts_indices = []

    flat_dist = 0
    flat_start = 0
    in_flat = False

    for idx, pt in enumerate(points_data):
      d_dist = pt["d_dist"]
      d_elev = pt["d_elev"]
      grad = (d_elev / max(d_dist, 0.0001)) * 100 if d_dist > 0 else 0

      is_ascending = d_elev > 0 or (d_dist > 0 and grad >= 0.5)
      if is_ascending:
        if not in_climb:
          in_climb = True
          climb_start = pt["dist"]
          current_dist = 0
          current_elev = 0
          climb_pts_indices = []
        current_dist += d_dist
        if d_elev > 0:
          current_elev += d_elev
        climb_pts_indices.append(idx)
      else:
        if in_climb:
          if current_dist >= 1.0:
            avg_grad = (current_elev / (current_dist * 1000)) * 100
            if avg_grad >= 3.0:
              detected_climbs.append(
                  {
                      "name": (
                          f"Côte {len(detected_climbs)+1} ({climb_start:.1f}"
                          " km)"
                      ),
                      "dist": round(current_dist, 2),
                      "elev": round(max(current_elev, 0)),
                      "grad": round(avg_grad, 1),
                      "start_km": round(climb_start, 1),
                      "indices": climb_pts_indices.copy(),
                  }
              )
          in_climb = False

      is_flat_or_rolling = grad >= -2.0
      if is_flat_or_rolling:
        if not in_flat:
          in_flat = True
          flat_start = pt["dist"]
          flat_dist = 0
        flat_dist += d_dist
      else:
        if in_flat:
          if flat_dist >= 1.0:
            flat_sections.append(
                {"start": round(flat_start, 1), "dist": round(flat_dist, 1)}
            )
          in_flat = False

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

p5 = st.session_state.power_records["5min"]
p20 = st.session_state.power_records["20min"]
cp = (p20 * 1200 - p5 * 300) / (1200 - 300)
w_prime = (p20 - cp) * 1200

w_kg = cp / weight if weight and weight > 0 else 4.0
estimated_vam = int(w_kg * 180) + 300
time_on_flat = (distance - (elevation / 100)) / 31.0
time_on_climb = elevation / estimated_vam if estimated_vam > 0 else 0
total_hours = max(1.0, time_on_flat + time_on_climb)

if total_hours > 4.0:
  target_power = int(sv1_power * 0.90)
elif total_hours > 2.5:
  target_power = int(sv1_power * 0.98)
elif total_hours > 1.5:
  target_power = int(sv1_power * 1.05)
else:
  target_power = int(cp * 0.95)

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

flat_target_w = int(sv1_power * 0.90)

st.subheader("Visualisation du parcours (GPS)")
if map_points:
  df_map = pd.DataFrame(map_points)
    st.map(df_map, zoom=10, use_container_width=True)
else:
  st.info("📁 Dépose un fichier GPX pour afficher la carte interactive.")

st.subheader("Stratégie sur les portions plates (> 1 km)")
st.markdown(
    f"Sur les sections planes et faux-plats (hors descentes prononcées), maintenir"
    f" une puissance stable de **{flat_target_w} W** (environ 90% du SV1) pour"
    " préserver l'intégrité musculaire tout en roulant dans le rythme du"
    " groupe."
)


def get_gradient_color(grad):
  if grad < 4:
    return "#b2df8a"
  elif grad < 6:
    return "#a6cee3"
  elif grad < 8:
    return "#fb9a99"
  elif grad < 10:
    return "#e31a1c"
  else:
    return "#6a3d9a"


@st.dialog("Profil altimétrique segmenté (Style Cols-cyclisme)", width="large")
def show_climb_popup(climb_name, climb_data, pts_sub):
  st.subheader(climb_name)
  dist_val = climb_data["dist"]
  elev_val = climb_data["elev"]
  grad_val = climb_data["grad"]
  st.markdown(
      f"**Longueur** : {dist_val} km | **Dénivelé** : +{elev_val} m |"
      f" **Pente moyenne** : {grad_val}%"
  )

  if pts_sub and len(pts_sub) > 1:
    fig, ax = plt.subplots(figsize=(11, 4.5))

    min_elev = min([p["elev"] for p in pts_sub]) - 10
    start_d = pts_sub[0]["dist"]
    end_d = pts_sub[-1]["dist"]

    from matplotlib.patches import Polygon

    for i in range(len(pts_sub) - 1):
      x0 = pts_sub[i]["dist"]
      x1 = pts_sub[i + 1]["dist"]
      y0 = pts_sub[i]["elev"]
      y1 = pts_sub[i + 1]["elev"]

      if x1 <= x0:
        continue

      d_seg = x1 - x0
      e_seg = y1 - y0
      g_seg = (e_seg / (d_seg * 1000)) * 100 if d_seg > 0 else 0
      bar_color = get_gradient_color(g_seg)

      polygon = Polygon(
          [[x0, min_elev], [x0, y0], [x1, y1], [x1, min_elev]],
          facecolor=bar_color,
          edgecolor=bar_color,
          linewidth=0,
          antialiased=False,
      )
      ax.add_patch(polygon)

    all_dists = [p["dist"] for p in pts_sub]
    all_elevs = [p["elev"] for p in pts_sub]
    ax.plot(all_dists, all_elevs, color="#111111", linewidth=1.5)

    ax.set_xlim(start_d, end_d)
    ax.set_ylim(min_elev, max(all_elevs) + 15)
    ax.set_title(
        f"Profil en colonnes continues — {climb_name}",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Distance sur la côte (km)")
    ax.set_ylabel("Altitude (m)")
    ax.grid(True, linestyle=":", alpha=0.4)
    st.pyplot(fig)
  else:
    st.info("Données altimétriques insuffisantes pour le profil détaillé.")

  if st.button("Fermer"):
    st.rerun()


if detected_climbs:
  st.subheader(
      "Cols et côtes répertoriés (Clique sur une côte pour l'analyse détaillée)"
  )

  max_dist = max([c["dist"] for c in detected_climbs]) if detected_climbs else 1
  max_grad = max([c["grad"] for c in detected_climbs]) if detected_climbs else 1

  for idx, climb in enumerate(detected_climbs):
    norm_dist = climb["dist"] / max_dist if max_dist > 0 else 0
    norm_grad = climb["grad"] / max_grad if max_grad > 0 else 0
    score = 0.5 * norm_dist + 0.5 * norm_grad

    if score > 0.7:
      color, diff_label = "🔴", "Difficile"
    elif score > 0.35:
      color, diff_label = "🟠", "Modérée"
    else:
      color, diff_label = "🟢", "Facile"

    est_duration_rough = int((climb["elev"] / 900) * 3600)
    if st.session_state.vam_records:
      closest_sec = min(
          st.session_state.vam_records.keys(),
          key=lambda x: abs(x - est_duration_rough),
      )
      climb_vam = int(st.session_state.vam_records[closest_sec])
    else:
      climb_vam = int((w_kg * 140) + (climb["grad"] * 15) + 420)
      climb_vam = max(550, min(1050, climb_vam))

    climb_duration_sec = (
        int((climb["elev"] / climb_vam) * 3600) if climb_vam > 0 else 900
    )
    climb_duration_min = climb_duration_sec // 60
    climb_duration_sec_rem = climb_duration_sec % 60

    progress_ratio = (
        climb.get("start_km", 0) / distance if distance > 0 else 0.5
    )
    factor = 0.90 - 0.05 * (
        (climb["dist"] / 5.0) * 0.5 + progress_ratio * 0.5
    )
    factor = max(0.85, min(0.90, factor))

    climb_target_w = int((cp + (w_prime / max(climb_duration_sec, 60))) * factor)

    col_btn, col_info = st.columns([0.4, 0.6])
    with col_btn:
      if st.button(
          f"{color} {climb['name']} ({diff_label})", key=f"climb_btn_{idx}"
      ):
        indices = climb.get("indices", [])
        sub_pts = [points_data[i] for i in indices] if indices else []
        show_climb_popup(climb["name"], climb, sub_pts)
    with col_info:
      st.markdown(
          f"📏 {climb['dist']} km | 📈 +{climb['elev']} m | 📐"
          f" {climb['grad']}% — VAM : **{climb_vam} m/h** | Temps : **{climb_duration_min} min {climb_duration_sec_rem:02d}s** | Cible :"
          f" **{climb_target_w} W**"
      )

st.subheader("Stratégie Nutritionnelle & Hydratation")
st.markdown(f"""
* **Hydratation** : Boire ~{water_per_hour_ml} ml/h.
* **Glucides Liquides (Bidons)** : 60 à 90 g/h de glucides.
* **Glucides Solides (Barres / Gels)** : À consommer prioritairement sur les **portions plates** et les faux-plats roulants, ou au sommet des cols juste avant la bascule en descente. Évitez de mâcher du solide dans les pourcentages raides (> 6%) où le débit cardiaque et ventilatoire est maximal.
""")
