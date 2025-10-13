import requests
#import json
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
    """still fix this to collect all the stream data, even if something is missing"""

    all_streams_data = []

    for activity in activities:
        activity_id = activity["id"]
        streams_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        params = {"keys": "time,latlng,distance,altitude,velocity_smooth,heartrate,cadence,watts,moving,grade_smooth,temp", "key_by_type": "true"}
        headers = {"Authorization": f"Bearer {access_token}"}
        streams_res = requests.get(streams_url, headers=headers, params=params)
        #streams_res.raise_for_status()
        streams = streams_res.json()

        #if "latlng" in streams:
        #    coords = streams["latlng"]["data"]  # list of [lat, lng]
        #    coords_with_id = [[activity_id, "coordinates", [lat, lng]] for lat, lng in coords]
        #    #all_coords.extend(coords_with_id)
        #    all_streams_data.extend(coords_with_id)
        
        #if "distance" in streams:
        #    distances = streams["distance"]["data"]
        #    distance_with_id = [[activity_id, "distances", distance] for distance in distances]
        #    all_streams_data.extend(distance_with_id)

        # Check if we have the minimum required data (time and latlng)
        if "time" not in streams or "latlng" not in streams:
            print(f"Activity {activity_id} missing required stream data")
            continue

        num_points = len(streams["time"]["data"])
         
        #create df for streams data
        streams_df = pd.DataFrame({
            "activity_id": activity_id,
            "time": streams["time"]["data"],
            "latlng": streams["latlng"]["data"],
            "distance": streams.get("distance", {}).get("data", [None] * num_points),
            "altitude": streams.get("altitude", {}).get("data", [None] * num_points),
            "velocity_smooth": streams.get("velocity_smooth", {}).get("data", [None] * num_points),
            "heartrate": streams.get("heartrate", {}).get("data", [None] * num_points),
            "cadence": streams.get("cadence", {}).get("data", [None] * num_points),
            "watts": streams.get("watts", {}).get("data", [None] * num_points),
            "moving": streams.get("moving", {}).get("data", [None] * num_points),
            "grade_smooth": streams.get("grade_smooth", {}).get("data", [None] * num_points),
            "temp": streams.get("temp", {}).get("data", [None] * num_points)
        })
        
        all_streams_data.append(streams_df)


    print(f"Collected {len(all_streams_data)} GPS points.")

    if all_streams_data:
        final_df = pd.concat(all_streams_data, ignore_index=True)
        print(f"Collected {len(final_df)} GPS points.")
        return final_df
    else:
        print("No stream data collected.")
        return pd.DataFrame()

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
