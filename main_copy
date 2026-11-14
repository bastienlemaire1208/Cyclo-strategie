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
      "5min": 374,
      "12min": 325,
      "20min": 301,
      "ftp": fetched_ftp,
  }
if "vam_records" not in st.session_state:
  st.session_state.vam_records = {
      "5min": 1150,
      "12min": 1050,
      "20min": 980,
      "ftp": 900,
  }

if os.path.exists(CACHE_RECORDS_PATH):
  try:
    df_saved = pd.read_csv(CACHE_RECORDS_PATH, sep=None, engine="python")
    df_saved.columns = [str(col).strip().lower() for col in df_saved.columns]
    if "secs" in df_saved.columns and "watts" in df_saved.columns:
      for _, row in df_saved.iterrows():
        secs = row["secs"]
        watts = row["watts"]
        if pd.notna(watts):
          if secs == 300:
            st.session_state.power_records["5min"] = int(watts)
          elif secs == 720:
            st.session_state.power_records["12min"] = int(watts)
          elif secs == 1200:
            st.session_state.power_records["20min"] = int(watts)
        if "vam" in df_saved.columns and pd.notna(row["vam"]):
          if secs == 300:
            st.session_state.vam_records["5min"] = float(row["vam"])
          elif secs == 720:
            st.session_state.vam_records["12min"] = float(row["vam"])
          elif secs == 1200:
            st.session_state.vam_records["20min"] = float(row["vam"])
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
          if secs == 300:
            st.session_state.power_records["5min"] = int(watts)
          elif secs == 720:
            st.session_state.power_records["12min"] = int(watts)
          elif secs == 1200:
            st.session_state.power_records["20min"] = int(watts)
        if "vam" in df_csv.columns and pd.notna(row["vam"]):
          if secs == 300:
            st.session_state.vam_records["5min"] = float(row["vam"])
          elif secs == 720:
            st.session_state.vam_records["12min"] = float(row["vam"])
          elif secs == 1200:
            st.session_state.vam_records["20min"] = float(row["vam"])
      st.sidebar.success(
          "✅ Nouveaux records (5m, 12m, 20m, FTP) enregistrés sur disque"
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
    "Poids du corps (kg)", value=69.0, step=0.1, format="%.1f"
)
sv1_power = st.sidebar.number_input("SV1 (W)", value=fetched_sv1, step=1)

st.sidebar.header("Paramètres matériels & Équipement")
bike_weight = st.sidebar.number_input(
    "Poids du vélo (kg)", value=9.5, step=0.1, format="%.1f"
)
gear_weight = st.sidebar.number_input(
    "Équipement, vêtements & bidons (kg)", value=4.0, step=0.1, format="%.1f"
)

total_system_weight = weight + bike_weight + gear_weight

st.sidebar.header("Météo & Environnement")
ambient_temp = st.sidebar.slider(
    "Température extérieure estimée (°C)", min_value=0, max_value=40, value=20
)

st.sidebar.header("Paramètres de course")
distance = st.sidebar.number_input("Distance (km)", value=distance_km)
elevation = st.sidebar.number_input("Dénivelé positif (m D+)", value=elevation_m)

# Paramètres physiques pour l'algorithme de mouvement
cr = 0.004
rho = 1.225
sc = 0.35
g = 9.81

target_intensity = 0.80
target_power_base = int(ftp * target_intensity)

total_seconds = 0
segment_powers = []
segment_times = []

if points_data:
  for pt in points_data:
    d_m = pt["d_dist"] * 1000.0
    if d_m <= 0:
      continue
    d_elev = pt["d_elev"]
    theta = np.arctan(d_elev / d_m) if d_m > 0 else 0.0

    seg_power = target_power_base * (1.0 + max(0.0, np.sin(theta)) * 0.5)

    v = 8.0
    for _ in range(5):
      power_res = (
          total_system_weight * g * np.sin(theta)
          + cr * total_system_weight * g * np.cos(theta)
      ) * v + 0.5 * rho * sc * v**3
      if power_res > 0:
        v = v * (seg_power / power_res) ** (1 / 3)
    v = max(1.5, min(v, 25.0))

    seg_time = d_m / v
    total_seconds += seg_time
    segment_powers.append(seg_power)
    segment_times.append(seg_time)

  total_hours = total_seconds / 3600.0

  if segment_powers and total_seconds > 0:
    num = sum([(p**4) * t for p, t in zip(segment_powers, segment_times)])
    target_power = int((num / total_seconds) ** 0.25)
  else:
    target_power = target_power_base
else:
  p5 = st.session_state.power_records["5min"]
  p20 = st.session_state.power_records["20min"]
  cp = (p20 * 1200 - p5 * 300) / (1200 - 300)

  estimated_vam = int(st.session_state.vam_records.get("20min", 980) * 0.9)
  time_on_flat = (distance - (elevation / 100)) / 31.0
  time_on_climb = elevation / estimated_vam if estimated_vam > 0 else 0
  total_hours = max(1.0, time_on_flat + time_on_climb)
  target_power = int(ftp * 0.80)

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

    min_elev = min([p["elev"] for p in pts_sub]) - 15
    start_d = pts_sub[0]["dist"]
    end_d = pts_sub[-1]["dist"]

    total_d = end_d - start_d
    target_chunk_d = max(0.2, total_d / 10)

    chunks = []
    c_start_d = pts_sub[0]["dist"]
    c_start_e = pts_sub[0]["elev"]
    curr_d = 0.0
    curr_e_gain = 0.0
    last_pt = pts_sub[0]

    for pt in pts_sub[1:]:
      seg_d = pt["dist"] - last_pt["dist"]
      seg_e = pt["d_elev"]
      curr_d += seg_d
      if seg_e > 0:
        curr_e_gain += seg_e
      last_pt = pt

      if curr_d >= target_chunk_d:
        c_end_d = pt["dist"]
        c_end_e = pt["elev"]
        g_chunk = (curr_e_gain / (curr_d * 1000)) * 100 if curr_d > 0 else 0
        chunks.append(
            {
                "x0": c_start_d,
                "x1": c_end_d,
                "y0": c_start_e,
                "y1": c_end_e,
                "grad": g_chunk,
            }
        )
        c_start_d = c_end_d
        c_start_e = c_end_e
        curr_d = 0.0
        curr_e_gain = 0.0

    if (
        chunks
        and pts_sub[-1]["dist"] > chunks[-1]["x1"]
        or not chunks
        and len(pts_sub) > 1
    ):
      c_end_d = pts_sub[-1]["dist"]
      c_end_e = pts_sub[-1]["elev"]
      tot_d_rem = c_end_d - c_start_d
      if tot_d_rem > 0:
        tot_e_rem = max(0, c_end_e - c_start_e)
        g_chunk = (tot_e_rem / (tot_d_rem * 1000)) * 100
        chunks.append(
            {
                "x0": c_start_d,
                "x1": c_end_d,
                "y0": c_start_e,
                "y1": c_end_e,
                "grad": g_chunk,
            }
        )

    from matplotlib.patches import Polygon

    for ch in chunks:
      x0, x1 = ch["x0"], ch["x1"]
      y0, y1 = ch["y0"], ch["y1"]
      g_seg = ch["grad"]
      bar_color = get_gradient_color(g_seg)

      polygon = Polygon(
          [[x0, min_elev], [x0, y0], [x1, y1], [x1, min_elev]],
          facecolor=bar_color,
          edgecolor=bar_color,
          linewidth=0,
          antialiased=False,
      )
      ax.add_patch(polygon)

      if (x1 - x0) >= 0.08:
        mid_x = (x0 + x1) / 2
        mid_y = min_elev + (min(y0, y1) - min_elev) * 0.5
        ax.text(
            mid_x,
            mid_y,
            f"{g_seg:.1f}%",
            color="#111111",
            fontsize=9,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor="white",
                alpha=0.75,
                edgecolor="none",
            ),
        )

    all_dists = [p["dist"] for p in pts_sub]
    all_elevs = [p["elev"] for p in pts_sub]
    ax.plot(all_dists, all_elevs, color="#111111", linewidth=1.5)

    ax.set_xlim(start_d, end_d)
    ax.set_ylim(min_elev, max(all_elevs) + 20)
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

    v_5 = st.session_state.vam_records.get("5min", 1150)
    v_12 = st.session_state.vam_records.get("12min", 1050)
    v_20 = st.session_state.vam_records.get("20min", 980)
    v_ftp = st.session_state.vam_records.get("ftp", 900)

    progress_ratio = (
        climb.get("start_km", 0) / distance if distance > 0 else 0.5
    )
    vam_factor = 0.90 - 0.05 * (
        (climb["dist"] / 5.0) * 0.5 + progress_ratio * 0.5
    )
    vam_factor = max(0.80, min(0.90, vam_factor))

    if est_duration_rough < 300:
      raw_vam = v_5
    elif est_duration_rough <= 720:
      ratio = (est_duration_rough - 300) / (720 - 300)
      raw_vam = v_5 * (1 - ratio) + v_12 * ratio
    elif est_duration_rough <= 1200:
      ratio = (est_duration_rough - 720) / (1200 - 720)
      raw_vam = v_12 * (1 - ratio) + v_20 * ratio
    else:
      ratio = min(1.0, (est_duration_rough - 1200) / 2400)
      raw_vam = v_20 * (1 - ratio) + v_ftp * ratio

    mass_ratio_factor = (
        weight / total_system_weight if total_system_weight > 0 else 1.0
    )
    climb_vam = int(raw_vam * vam_factor * mass_ratio_factor)

    climb_duration_sec = (
        int((climb["elev"] / climb_vam) * 3600) if climb_vam > 0 else 900
    )
    climb_duration_min = climb_duration_sec // 60
    climb_duration_sec_rem = climb_duration_sec % 60

    p_5 = st.session_state.power_records.get("5min", 374)
    p_12 = st.session_state.power_records.get("12min", 325)
    p_20 = st.session_state.power_records.get("20min", 301)
    p_ftp = ftp

    power_factor = 0.90 - 0.05 * (
        (climb["dist"] / 5.0) * 0.5 + progress_ratio * 0.5
    )
    power_factor = max(0.80, min(0.90, power_factor))

    if est_duration_rough < 300:
      raw_power = p_5
    elif est_duration_rough <= 720:
      ratio = (est_duration_rough - 300) / (720 - 300)
      raw_power = p_5 * (1 - ratio) + p_12 * ratio
    elif est_duration_rough <= 1200:
      ratio = (est_duration_rough - 720) / (1200 - 720)
      raw_power = p_12 * (1 - ratio) + p_20 * ratio
    else:
      ratio = min(1.0, (est_duration_rough - 1200) / 2400)
      raw_power = p_20 * (1 - ratio) + p_ftp * ratio

    climb_target_w = int(raw_power * power_factor)

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
