import requests
from datetime import date, timedelta

CITIES = {
    "Kochi":     (9.9312, 76.2673),
    "Mumbai":    (19.0760, 72.8777),
    "Delhi":     (28.6139, 77.2090),
    "Chennai":   (13.0827, 80.2707),
    "Bengaluru": (12.9716, 77.5946),
}

URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"

target_day = date.today() - timedelta(days=1)  # yesterday


def fetch_city(city, lat, lon, day):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": HOURLY_FIELDS,
        "timezone": "Asia/Kolkata",
        "start_date": day.isoformat(),
        "end_date": day.isoformat(),
    }
    response = requests.get(URL, params=params, timeout=30)
    response.raise_for_status()   # stops with an error if the API failed
    return response.json()


data = fetch_city("Kochi", *CITIES["Kochi"], target_day)

hourly = data["hourly"]
print(f"Rows returned: {len(hourly['time'])}")

for i in range(len(hourly["time"])):
    print(
        hourly["time"][i],
        "| temp:", hourly["temperature_2m"][i],
        "| humidity:", hourly["relative_humidity_2m"][i],
        "| rain:", hourly["precipitation"][i],
        "| wind:", hourly["wind_speed_10m"][i],
    )