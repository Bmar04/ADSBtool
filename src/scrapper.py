import requests
import time
import csv
import pandas as pd
import numpy as np
from datetime import datetime

from opensky_api import OpenSkyApi

class Scrapper:
    def __init__(self):
        print("Using OpenSky API without authentication")
        self.api = OpenSkyApi(username="", password="")

    def get_aircraft_data(self, lat_min, lat_max, lon_min, lon_max):
        try:
            bounds = (lat_min, lat_max, lon_min, lon_max)
            print(f"Requesting data for bounds: {bounds}")
            
            states = self.api.get_states(bbox=bounds)
            aircraft_data = []
            timestamp = datetime.now().isoformat()
            
            if states and states.states:
                print(f"Found {len(states.states)} aircraft")
                for state in states.states:
                    aircraft_data.append({
                        "timestamp": timestamp,
                        "icao24": state.icao24,
                        "callsign": state.callsign,
                        "latitude": state.latitude,
                        "longitude": state.longitude,
                        "baro_altitude": state.baro_altitude,
                        "true_track": state.true_track,
                        "velocity": state.velocity,
                        "vertical_rate": state.vertical_rate,
                        "squawk": state.squawk,
                        "geo_altitude": state.geo_altitude,
                        "on_ground": state.on_ground,
                        "last_contact": state.last_contact,
                        "spi": state.spi,
                        "position_source": state.position_source,
                    })
            else:
                print("No states returned from API for these bounds")
            return aircraft_data
        except Exception as e:
            print(f"Error getting aircraft data: {e}")
            return []

    def save_to_csv(self, aircraft_data, filename):
        try:
            if not aircraft_data:
                print("No aircraft data to save")
                return
            
            # Check if file exists and has content
            file_exists = False
            try:
                with open(filename, 'r') as f:
                    # Check if file has content (more than just header)
                    lines = f.readlines()
                    file_exists = len(lines) > 0
            except FileNotFoundError:
                file_exists = False
            
            # Open in append mode if file exists, write mode if new
            mode = 'a' if file_exists else 'w'
            
            with open(filename, mode, newline='', encoding='utf-8') as file:
                fieldnames = aircraft_data[0].keys()
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                # Only write header if it's a new file
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(aircraft_data)
                
            print(f"{'Appended' if file_exists else 'Created'} {len(aircraft_data)} records to {filename}")
                
        except Exception as e:
            print(f"Error saving to CSV: {e}")

if __name__ == "__main__":
    scrapper = Scrapper()

    try:
        while True:
            # Default bounds for Colorado
            aircraft_data = scrapper.get_aircraft_data(37.0, 41.0, -109.0, -102.0)
            scrapper.save_to_csv(aircraft_data, "aircraft_data.csv")
            print(f"Total records now: {len(aircraft_data)} this batch")
            time.sleep(12)
    except KeyboardInterrupt:
        print("Program terminated by user")