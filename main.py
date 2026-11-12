import os
from dotenv import load_dotenv
import requests
import streamlit as st

load_dotenv()

API_KEY = os.getenv("INTERVALS_API_KEY")
ATHLETE_ID = os.getenv("INTERVALS_ATHLETE_ID")
BASE_URL = "https://intervals.icu/api/v1"

st.title("Planificateur de Course Vélo")


@st.cache_data
def get_athlete_profile():
  url = f"{BASE_URL}/athlete/{ATHLETE_ID}"
  response = requests.get(url, auth=("API_KEY", API_KEY))
  if response.status_code == 200:
    return response.json()
  return {}


# Récupération des données athlète (FTP, Poids) si dispo sur Intervals
athlete_data = get_athlete_profile()
default_ftp = athlete_data.get("ftp", 250)
default_weight = athlete_data.get("weight", 70)

st.sidebar.header("Paramètres de la course")
distance = st.sidebar.number_input(
    "Distance (km)", min_value=10, max_value=400, value=100
)
elevation = st.sidebar.number_input(
    "Dénivelé positif (m D+)", min_value=0, max_value=10000, value=1500
)

st.sidebar.header("Paramètres physiologiques")
ftp = st.sidebar.number_input("FTP (Watts)", value=default_ftp)
weight = st.sidebar.number_input("Poids (kg)", value=default_weight)

# Objectifs de la sortie
target_intensity = st.sidebar.slider(
    "Intensité visée (% de la FTP)", min_value=55, max_value=95, value=75
)
target_power = int(ftp * (target_intensity / 100))

# Estimation de la vitesse et de la VAM selon la puissance et le poids (W/kg)
w_kg = target_power / weight
# Estimation empirique de la VAM basée sur le ratio W/kg
estimated_vam = int(w_kg * 150) + 400
# Temps estimé basé sur le plat et la montée
time_on_flat = (distance - (elevation / 100)) / (
    25 + (w_kg * 2)
)  # Vitesse estimée
time_on_climb = elevation / estimated_vam
total_hours = time_on_flat + time_on_climb

# Calculs nutritionnels et hydriques
# Glucides : 60 à 90g par heure selon l'intensité
carbs_per_hour = 75 if target_intensity > 75 else 60
total_carbs = int(total_hours * carbs_per_hour)

# Hydratation : 500ml à 800ml par heure selon l'effort
water_per_hour = 650
total_water_liters = round((total_hours * water_per_hour) / 1000, 1)

# Affichage du plan
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric("Temps estimé", f"{int(total_hours)}h {int((total_hours % 1) * 60)}min")
with col2:
  st.metric("Puissance Cible", f"{target_power} W", f"{w_kg:.1f} W/kg")
with col3:
  st.metric("VAM Estimée", f"{estimated_vam} m/h")
with col4:
  st.metric("Intensité", f"{target_intensity}% FTP")

st.subheader("Stratégie de Ravitaillement")
col_nut1, col_nut2 = st.columns(2)
with col_nut1:
  st.markdown(f"**Glucides totaux :** {total_carbs} g")
  st.markdown(
      f"— Soit environ **{carbs_per_hour} g/h** (gels, barres ou boissons"
      " énergétiques)."
  )
with col_nut2:
  st.markdown(f"**Eau totale :** {total_water_liters} L")
  st.markdown(
      f"— Soit environ **{water_per_hour} ml/h** (à adapter selon la"
      " température)."
  )
