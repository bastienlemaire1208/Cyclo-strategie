import os
import numpy as np
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("INTERVALS_API_KEY")
ATHLETE_ID = os.getenv("INTERVALS_ATHLETE_ID")
BASE_URL = "https://intervals.icu/api/v1"

st.title("Analyseur Intervals.icu — VAM & Puissance")


@st.cache_data
def get_athlete_activities():
  url = f"{BASE_URL}/athlete/{ATHLETE_ID}/activities"
  response = requests.get(url, auth=("API_KEY", API_KEY))
  if response.status_code == 200:
    return response.json()
  return []


@st.cache_data
def get_activity_streams(activity_id):
  url = f"{BASE_URL}/activity/{activity_id}/streams?types=watts,heartrate,cadence,altitude,time"
  response = requests.get(url, auth=("API_KEY", API_KEY))
  if response.status_code == 200:
    data = response.json()
    streams = {item["type"]: item["data"] for item in data}
    return pd.DataFrame(streams)
  return pd.DataFrame()


def calculate_vam(df):
  if "altitude" not in df.columns or "time" not in df.columns:
    return 0

  # Calcul du dénivelé positif cumulé
  df["ele_diff"] = df["altitude"].diff()
  positive_gain = df.loc[df["ele_diff"] > 0, "ele_diff"].sum()

  # Temps total en heures
  total_time_hours = (df["time"].iloc[-1] - df["time"].iloc[0]) / 3600

  if total_time_hours > 0:
    return positive_gain / total_time_hours
  return 0


activities = get_athlete_activities()
if activities:
  activity_options = {
      f"{act['start_date_local']} — {act.get('name', 'Sortie')}": act["id"]
      for act in activities
  }
  selected_name = st.selectbox(
      "Sélectionne une sortie", list(activity_options.keys())
  )
  selected_id = activity_options[selected_name]

  if st.button("Analyser la sortie"):
    df_streams = get_activity_streams(selected_id)

    if not df_streams.empty:
      vam = calculate_vam(df_streams)

      col1, col2 = st.columns(2)
      with col1:
        st.metric("VAM Globale", f"{int(vam)} m/h")
      with col2:
        if "watts" in df_streams.columns:
          avg_power = int(df_streams["watts"].mean())
          st.metric("Puissance Moyenne", f"{avg_power} W")

      st.subheader("Courbes Puissance et Fréquence Cardiaque")
      chart_data = df_streams[["watts", "heartrate"]].copy()
      st.line_chart(chart_data)
    else:
      st.warning("Aucun flux de données disponible pour cette activité.")
