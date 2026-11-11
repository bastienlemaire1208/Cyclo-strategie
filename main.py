import os
from dotenv import load_dotenv
import pandas as pd
import requests
import streamlit as st

load_dotenv()

API_KEY = os.getenv("INTERVALS_API_KEY")
ATHLETE_ID = os.getenv("INTERVALS_ATHLETE_ID")
BASE_URL = "https://intervals.icu/api/v1"


@st.cache_data
def get_athlete_activities():
  url = f"{BASE_URL}/athlete/{ATHLETE_ID}/activities"
  auth = ("API_KEY", API_KEY)
  response = requests.get(url, auth=auth)
  if response.status_code == 200:
    return response.json()
  else:
    st.error(f"Erreur API : {response.status_code}")
    return []


@st.cache_data
def get_activity_streams(activity_id):
  # Récupère les données temporelles (watts, hr, cadence, distance, etc.)
  url = f"{BASE_URL}/activity/{activity_id}/streams?types=watts,heartrate,cadence,altitude,velocity_smooth"
  auth = ("API_KEY", API_KEY)
  response = requests.get(url, auth=auth)

  if response.status_code == 200:
    data = response.json()
    # L'API renvoie un format sous forme de dictionnaire de listes, on convertit en DataFrame pandas
    streams = {item["type"]: item["data"] for item in data}
    return pd.DataFrame(streams)
  return pd.DataFrame()


# Exemple d'intégration dans Streamlit
st.title("Analyseur Intervals.icu")

activities = get_athlete_activities()
if activities:
  # Création d'un selectbox pour choisir l'activité
  activity_options = {
      f"{act['start_date_local']} - {act.get('name', 'Sans nom')}": act['id']
      for act in activities
  }
  selected_name = st.selectbox(
      "Sélectionne une sortie", list(activity_options.keys())
  )
  selected_id = activity_options[selected_name]

  if st.button("Charger les données"):
    df_streams = get_activity_streams(selected_id)
    if not df_streams.empty:
      st.success("Données de puissance et cardio chargées avec succès !")
      st.line_chart(df_streams[['watts', 'heartrate']])
    else:
      st.warning("Aucune donnée détaillée trouvée pour cette activité.")
