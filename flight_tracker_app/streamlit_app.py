
import streamlit as st
import pandas as pd
import requests
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from datetime import datetime

USERNAME = st.secrets["opensky_username"]
PASSWORD = st.secrets["opensky_password"]

@st.cache_data
def load_schedule():
    df = pd.read_csv("COS all Timetable entries eff 07Jul2025.csv")
    df["Callsign"] = df["Carrier_Code"].astype(str) + df["Flight_No"].astype(str)
    return df

schedule_df = load_schedule()
callsigns = schedule_df["Callsign"].dropna().unique().tolist()

st.title("🛫 Real-Time Flight Tracker")
st.caption("Tracking active flights from your schedule using OpenSky Network")

st.sidebar.subheader("Options")
refresh_rate = st.sidebar.slider("Refresh rate (sec)", 15, 60, 30)

@st.cache_data(ttl=30)
def get_opensky_data():
    url = "https://opensky-network.org/api/states/all"
    response = requests.get(url, auth=(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from OpenSky")
        return None

data = get_opensky_data()

flights = []
if data and data.get("states"):
    for state in data["states"]:
        if state[1] and state[1].strip() in callsigns:
            flights.append({
                "icao24": state[0],
                "callsign": state[1].strip(),
                "origin_country": state[2],
                "longitude": state[5],
                "latitude": state[6],
                "altitude": state[7],
                "velocity": state[9],
                "heading": state[10],
                "vertical_rate": state[11],
                "last_contact": datetime.utcfromtimestamp(state[4]).strftime("%Y-%m-%d %H:%M:%S UTC")
            })

st.subheader(f"📍 Tracking {len(flights)} Active Flights")

if not flights:
    st.info("No active flights currently in air from your schedule.")
else:
    df_flights = pd.DataFrame(flights)
    st.dataframe(df_flights, use_container_width=True)

    m = folium.Map(location=[20, -30], zoom_start=2)
    marker_cluster = MarkerCluster().add_to(m)

    for flight in flights:
        if flight["latitude"] and flight["longitude"]:
            folium.Marker(
                location=[flight["latitude"], flight["longitude"]],
                popup=f"{flight['callsign']}\nAlt: {flight['altitude']}m\nSpeed: {flight['velocity']}m/s",
                tooltip=flight['callsign']
            ).add_to(marker_cluster)

    st_data = st_folium(m, width=700, height=500)

st.experimental_rerun()
