import requests
import json
import pandas as pd
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Replace these with your own Strava API credentials
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET") 
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN") 

# Validate that all credentials are loaded
if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    raise ValueError("Missing Strava credentials! Please check your .env file.")

# Step 1: Get a new access token using your refresh token
def get_access_token():
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    response = requests.post(auth_url, data=payload)
    response.raise_for_status()
    access_token = response.json()["access_token"]
    return access_token

def get_all_activities(access_token, per_page=200):
    """Retrieve *all* user activities, not just the first page."""
    activities = []
    page = 1
    while True:
        print(f"Fetching page {page}...")
        url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"per_page": per_page, "page": page}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break

        data = response.json()
        if not data:
            print("No more activities found — all data retrieved.")
            break

        activities.extend(data)
        page += 1
        time.sleep(0.2)  # be gentle to Strava's API limits

    return activities

def get_coordinates_of_activities(access_token, activities):
    all_coords = []

    for activity in activities:
        activity_id = activity["id"]
        streams_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        params = {"keys": "latlng", "key_by_type": "true"}
        headers = {"Authorization": f"Bearer {access_token}"}
        streams_res = requests.get(streams_url, headers=headers, params=params)
        streams_res.raise_for_status()
        streams = streams_res.json()

        if "latlng" in streams:
            coords = streams["latlng"]["data"]  # list of [lat, lng]
            all_coords.extend(coords)

    print(f"Collected {len(all_coords)} GPS points.")

    return all_coords

def write_data_to_csv(df, filename):
    folder_path = 'data'
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)
    df.to_csv(file_path, index=False)
    print(f"✅ DataFrame saved at: {file_path}")


if __name__ == "__main__":
    #get token
    access_token = get_access_token()
    
    #get raw api data
    activities_data = get_all_activities(access_token)#, per_page=200, page=1)

    coordinates_data = get_coordinates_of_activities(access_token, activities_data)

    # Convert to DataFrame
    activities_df = pd.DataFrame(activities_data)
    coordinates_df = pd.DataFrame(coordinates_data)#, columns=["lat", "lng"])

    # Save locally in the repo
    write_data_to_csv(activities_df, "activities_data.csv")
    write_data_to_csv(coordinates_df, "coordinates_data.csv")

    print("Finished")
