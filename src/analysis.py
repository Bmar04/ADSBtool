import pandas as pd
import folium
from folium import plugins
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Optional, List, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import webbrowser

class AircraftMapAnalyzer:
    def __init__(self, csv_file: str):
        """
        Initialize the analyzer with aircraft data from CSV
        
        Args:
            csv_file: Path to the CSV file containing aircraft data
        """
        self.csv_file = csv_file
        self.data = None
        self.load_data()
    
    def load_data(self):
        """Load and preprocess the aircraft data from CSV"""
        try:
            self.data = pd.read_csv(self.csv_file)
            
            # Convert timestamp to datetime
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            
            # Remove rows with missing coordinates
            self.data = self.data.dropna(subset=['latitude', 'longitude'])
            
            # Sort by timestamp
            self.data = self.data.sort_values('timestamp')
            
            print(f"Loaded {len(self.data)} aircraft records")
            print(f"Time range: {self.data['timestamp'].min()} to {self.data['timestamp'].max()}")
            print(f"Unique aircraft: {self.data['icao24'].nunique()}")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = pd.DataFrame()
    
    def create_static_map(self, output_file: str = "aircraft_map.html"):
        """
        Create a static map showing all aircraft positions
        
        Args:
            output_file: Output HTML file name
        """
        if self.data.empty:
            print("No data to plot")
            return
        
        # Calculate map center
        center_lat = self.data['latitude'].mean()
        center_lon = self.data['longitude'].mean()
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # Add aircraft markers
        for _, row in self.data.iterrows():
            # Color based on altitude
            altitude = row.get('baro_altitude', 0) or row.get('geo_altitude', 0) or 0
            if altitude > 10000:
                color = 'red'
            elif altitude > 5000:
                color = 'orange'
            else:
                color = 'green'
            
            # Create popup info
            popup_text = f"""
            <b>Aircraft:</b> {row.get('icao24', 'Unknown')}<br>
            <b>Callsign:</b> {row.get('callsign', 'N/A')}<br>
            <b>Altitude:</b> {altitude} ft<br>
            <b>Speed:</b> {row.get('velocity', 'N/A')} knots<br>
            <b>Track:</b> {row.get('true_track', 'N/A')}°<br>
            <b>Time:</b> {row['timestamp']}<br>
            <b>On Ground:</b> {row.get('on_ground', 'N/A')}
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=5,
                popup=popup_text,
                color=color,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <b>Altitude Legend</b><br>
        <i class="fa fa-circle" style="color:red"></i> > 10,000 ft<br>
        <i class="fa fa-circle" style="color:orange"></i> 5,000-10,000 ft<br>
        <i class="fa fa-circle" style="color:green"></i> < 5,000 ft
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        m.save(output_file)
        print(f"Static map saved to {output_file}")
        return m
    
    def create_time_animation(self, output_file: str = "aircraft_animation.html"):
        """
        Create an animated map showing aircraft movement over time
        
        Args:
            output_file: Output HTML file name
        """
        if self.data.empty:
            print("No data to plot")
            return
        
        # Calculate map center
        center_lat = self.data['latitude'].mean()
        center_lon = self.data['longitude'].mean()
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # Calculate actual time intervals in the data
        time_diff = self.data['timestamp'].diff().dropna()
        if not time_diff.empty:
            avg_interval = time_diff.median().total_seconds()
            print(f"Average time interval in data: {avg_interval} seconds")
        else:
            avg_interval = 60  # Default to 1 minute
        
        # Group by aircraft and create features for each time point
        features = []
        
        # Sort data by timestamp first
        sorted_data = self.data.sort_values(['timestamp', 'icao24'])
        
        for _, row in sorted_data.iterrows():
            # Color based on altitude
            altitude = row.get('baro_altitude', 0) or row.get('geo_altitude', 0) or 0
            if altitude > 10000:
                color = 'red'
            elif altitude > 5000:
                color = 'orange'
            else:
                color = 'green'
            
            # Convert timestamp to string format that TimestampedGeoJson expects
            time_str = row['timestamp'].strftime('%Y-%m-%dT%H:%M:%S')
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['longitude'], row['latitude']]
                },
                "properties": {
                    "time": time_str,
                    "style": {"color": color, "fillColor": color, "radius": 6},
                    "icon": "circle",
                    "iconstyle": {
                        "fillColor": color,
                        "fillOpacity": 0.8,
                        "stroke": True,
                        "radius": 6
                    },
                    "popup": f"""
                    <b>Aircraft:</b> {row.get('icao24', 'Unknown')}<br>
                    <b>Callsign:</b> {row.get('callsign', 'N/A')}<br>
                    <b>Altitude:</b> {altitude} ft<br>
                    <b>Speed:</b> {row.get('velocity', 'N/A')} knots<br>
                    <b>Time:</b> {row['timestamp']}<br>
                    <b>Track:</b> {row.get('true_track', 'N/A')}°
                    """
                }
            }
            features.append(feature)
        
        print(f"Created {len(features)} time-based features for animation")
        
        # Use appropriate time period based on data intervals
        if avg_interval < 30:
            period = "PT10S"  # 10 second intervals for frequent data
        elif avg_interval < 120:
            period = "PT30S"  # 30 second intervals
        else:
            period = "PT1M"   # 1 minute intervals
        
        # Add TimestampedGeoJson layer
        plugins.TimestampedGeoJson(
            {
                "type": "FeatureCollection",
                "features": features
            },
            period=period,
            add_last_point=False,
            auto_play=False,
            loop=True,
            max_speed=5,
            loop_button=True,
            date_options="YYYY-MM-DDTHH:mm:ss",
            time_slider_drag_update=True,
            duration=period
        ).add_to(m)
        
        # Save map
        m.save(output_file)
        print(f"Animated map saved to {output_file}")
        return m
    
    def create_flight_paths(self, output_file: str = "flight_paths.html", min_points: int = 2):
        """
        Create a map showing flight paths for aircraft with multiple data points
        
        Args:
            output_file: Output HTML file name
            min_points: Minimum number of points required to draw a path
        """
        if self.data.empty:
            print("No data to plot")
            return
        
        # Calculate map center
        center_lat = self.data['latitude'].mean()
        center_lon = self.data['longitude'].mean()
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # Group by aircraft and sort by time
        aircraft_groups = self.data.groupby('icao24')
        
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                  'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
                  'darkpurple', 'pink', 'lightblue', 'lightgreen', 
                  'gray', 'black', 'lightgray']
        
        color_idx = 0
        paths_created = 0
        
        print(f"Processing {len(aircraft_groups)} aircraft for flight paths...")
        
        for aircraft_id, group in aircraft_groups:
            # Sort by timestamp
            group = group.sort_values('timestamp').reset_index(drop=True)
            
            if len(group) >= min_points:
                # Remove any duplicate positions (same lat/lon)
                group = group.drop_duplicates(subset=['latitude', 'longitude'], keep='first')
                
                if len(group) >= min_points:
                    # Create coordinates list [lat, lon] for folium
                    coordinates = []
                    times = []
                    
                    for _, row in group.iterrows():
                        coordinates.append([row['latitude'], row['longitude']])
                        times.append(row['timestamp'])
                    
                    if len(coordinates) >= min_points:
                        # Choose color
                        color = colors[color_idx % len(colors)]
                        color_idx += 1
                        
                        # Add flight path
                        folium.PolyLine(
                            coordinates,
                            color=color,
                            weight=3,
                            opacity=0.8,
                            popup=f"""
                            <b>Aircraft:</b> {aircraft_id}<br>
                            <b>Callsign:</b> {group.iloc[0].get('callsign', 'N/A')}<br>
                            <b>Points:</b> {len(coordinates)}<br>
                            <b>Duration:</b> {times[-1] - times[0]}<br>
                            <b>Start:</b> {times[0]}<br>
                            <b>End:</b> {times[-1]}
                            """
                        ).add_to(m)
                        
                        # Add start marker (green)
                        start_row = group.iloc[0]
                        folium.Marker(
                            [start_row['latitude'], start_row['longitude']],
                            icon=folium.Icon(color='green', icon='play'),
                            popup=f"""
                            <b>START</b><br>
                            Aircraft: {aircraft_id}<br>
                            Callsign: {start_row.get('callsign', 'N/A')}<br>
                            Time: {start_row['timestamp']}<br>
                            Altitude: {start_row.get('baro_altitude', 'N/A')} ft
                            """
                        ).add_to(m)
                        
                        # Add end marker (red)
                        end_row = group.iloc[-1]
                        folium.Marker(
                            [end_row['latitude'], end_row['longitude']],
                            icon=folium.Icon(color='red', icon='stop'),
                            popup=f"""
                            <b>END</b><br>
                            Aircraft: {aircraft_id}<br>
                            Callsign: {end_row.get('callsign', 'N/A')}<br>
                            Time: {end_row['timestamp']}<br>
                            Altitude: {end_row.get('baro_altitude', 'N/A')} ft
                            """
                        ).add_to(m)
                        
                        # Add intermediate points with timestamps
                        for i, (_, row) in enumerate(group.iterrows()):
                            if i > 0 and i < len(group) - 1:  # Skip start and end
                                folium.CircleMarker(
                                    [row['latitude'], row['longitude']],
                                    radius=3,
                                    popup=f"""
                                    <b>Point {i+1}</b><br>
                                    Aircraft: {aircraft_id}<br>
                                    Time: {row['timestamp']}<br>
                                    Altitude: {row.get('baro_altitude', 'N/A')} ft<br>
                                    Speed: {row.get('velocity', 'N/A')} knots
                                    """,
                                    color=color,
                                    fillColor=color,
                                    fillOpacity=0.7
                                ).add_to(m)
                        
                        paths_created += 1
        
        print(f"Created {paths_created} flight paths")
        
        # Add legend
        legend_html = f'''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <b>Flight Paths Legend</b><br>
        <i class="fa fa-play" style="color:green"></i> Start Point<br>
        <i class="fa fa-stop" style="color:red"></i> End Point<br>
        <i class="fa fa-circle" style="color:blue"></i> Intermediate Points<br>
        <b>Total Paths:</b> {paths_created}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        m.save(output_file)
        print(f"Flight paths map saved to {output_file}")
        return m
    
    def create_heatmap(self, output_file: str = "aircraft_heatmap.html"):
        """
        Create a heatmap showing aircraft density
        
        Args:
            output_file: Output HTML file name
        """
        if self.data.empty:
            print("No data to plot")
            return
        
        # Calculate map center
        center_lat = self.data['latitude'].mean()
        center_lon = self.data['longitude'].mean()
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # Prepare data for heatmap
        heat_data = [[row['latitude'], row['longitude']] for _, row in self.data.iterrows()]
        
        # Add heatmap
        plugins.HeatMap(heat_data).add_to(m)
        
        # Save map
        m.save(output_file)
        print(f"Heatmap saved to {output_file}")
        return m
    
    def generate_statistics(self):
        """Generate and display statistics about the aircraft data"""
        if self.data.empty:
            print("No data to analyze")
            return
        
        print("\n=== AIRCRAFT DATA STATISTICS ===")
        
        # Basic stats
        print(f"Total records: {len(self.data)}")
        print(f"Unique aircraft: {self.data['icao24'].nunique()}")
        print(f"Time span: {self.data['timestamp'].max() - self.data['timestamp'].min()}")
        
        # Time interval analysis
        time_diff = self.data['timestamp'].diff().dropna()
        if not time_diff.empty:
            avg_interval = time_diff.median().total_seconds()
            print(f"Median time interval: {avg_interval:.1f} seconds")
            print(f"Data collection frequency: Every ~{avg_interval/60:.1f} minutes")
        
        # Aircraft tracking analysis
        aircraft_counts = self.data['icao24'].value_counts()
        print(f"\nAircraft Tracking:")
        print(f"  Aircraft with >1 data point: {(aircraft_counts > 1).sum()}")
        print(f"  Aircraft with >5 data points: {(aircraft_counts > 5).sum()}")
        print(f"  Aircraft with >10 data points: {(aircraft_counts > 10).sum()}")
        print(f"  Max data points for one aircraft: {aircraft_counts.max()}")
        
        # Altitude stats
        altitudes = self.data['baro_altitude'].fillna(self.data['geo_altitude']).dropna()
        if not altitudes.empty:
            print(f"\nAltitude Statistics:")
            print(f"  Mean altitude: {altitudes.mean():.0f} ft")
            print(f"  Max altitude: {altitudes.max():.0f} ft")
            print(f"  Min altitude: {altitudes.min():.0f} ft")
            print(f"  Records with altitude data: {len(altitudes)}/{len(self.data)} ({len(altitudes)/len(self.data)*100:.1f}%)")
        
        # Speed stats
        speeds = self.data['velocity'].dropna()
        if not speeds.empty:
            print(f"\nSpeed Statistics:")
            print(f"  Mean speed: {speeds.mean():.0f} knots")
            print(f"  Max speed: {speeds.max():.0f} knots")
            print(f"  Min speed: {speeds.min():.0f} knots")
            print(f"  Records with speed data: {len(speeds)}/{len(self.data)} ({len(speeds)/len(self.data)*100:.1f}%)")
        
        # Geographic bounds
        print(f"\nGeographic Coverage:")
        print(f"  Latitude range: {self.data['latitude'].min():.4f} to {self.data['latitude'].max():.4f}")
        print(f"  Longitude range: {self.data['longitude'].min():.4f} to {self.data['longitude'].max():.4f}")
        
        # Top callsigns
        callsigns = self.data['callsign'].dropna().value_counts().head(10)
        if not callsigns.empty:
            print(f"\nTop 10 Most Tracked Callsigns:")
            for callsign, count in callsigns.items():
                print(f"  {callsign.strip()}: {count} records")
        
        # Data quality
        print(f"\nData Quality:")
        missing_callsign = self.data['callsign'].isna().sum()
        missing_altitude = self.data['baro_altitude'].isna().sum() + self.data['geo_altitude'].isna().sum()
        missing_speed = self.data['velocity'].isna().sum()
        
        print(f"  Missing callsigns: {missing_callsign}/{len(self.data)} ({missing_callsign/len(self.data)*100:.1f}%)")
        print(f"  Missing altitude: {missing_altitude}/{len(self.data)} ({missing_altitude/len(self.data)*100:.1f}%)")
        print(f"  Missing speed: {missing_speed}/{len(self.data)} ({missing_speed/len(self.data)*100:.1f}%)")
    
    def debug_data(self):
        """Debug the data to help troubleshoot visualization issues"""
        if self.data.empty:
            print("No data to debug")
            return
        
        print("\n=== DATA DEBUG INFO ===")
        
        # Show data structure
        print("Data columns:", list(self.data.columns))
        print("Data types:")
        for col in self.data.columns:
            print(f"  {col}: {self.data[col].dtype}")
        
        # Show sample data
        print(f"\nFirst 3 records:")
        for i, (_, row) in enumerate(self.data.head(3).iterrows()):
            print(f"  Record {i+1}:")
            print(f"    Timestamp: {row['timestamp']}")
            print(f"    Aircraft: {row.get('icao24', 'N/A')}")
            print(f"    Position: {row['latitude']}, {row['longitude']}")
            print(f"    Altitude: {row.get('baro_altitude', 'N/A')}")
            print()
        
        # Check for aircraft with multiple data points
        aircraft_counts = self.data['icao24'].value_counts()
        multi_point_aircraft = aircraft_counts[aircraft_counts > 1].head(5)
        
        if not multi_point_aircraft.empty:
            print("Sample aircraft with multiple data points:")
            for aircraft_id, count in multi_point_aircraft.items():
                aircraft_data = self.data[self.data['icao24'] == aircraft_id].sort_values('timestamp')
                print(f"  {aircraft_id} ({count} points):")
                print(f"    First: {aircraft_data.iloc[0]['timestamp']} at {aircraft_data.iloc[0]['latitude']:.4f}, {aircraft_data.iloc[0]['longitude']:.4f}")
                print(f"    Last:  {aircraft_data.iloc[-1]['timestamp']} at {aircraft_data.iloc[-1]['latitude']:.4f}, {aircraft_data.iloc[-1]['longitude']:.4f}")
                print()
        else:
            print("No aircraft have multiple data points - this is why animations/paths aren't working!")
            print("You need to run the scraper for longer to collect multiple points per aircraft.")
    
    def create_dashboard(self):
        """Create all visualizations and open them in browser"""
        print("Creating aircraft analysis dashboard...")
        
        # Debug data first
        self.debug_data()
        
        # Generate all maps
        self.create_static_map("aircraft_static_map.html")
        self.create_time_animation("aircraft_animation.html")
        self.create_flight_paths("aircraft_flight_paths.html")
        self.create_heatmap("aircraft_heatmap.html")
        
        # Generate statistics
        self.generate_statistics()
        
        # Create an index page
        self.create_index_page()
        
        print("\nDashboard created! Files generated:")
        print("  - index.html (main dashboard)")
        print("  - aircraft_static_map.html")
        print("  - aircraft_animation.html") 
        print("  - aircraft_flight_paths.html")
        print("  - aircraft_heatmap.html")
        
        # Open in browser
        try:
            webbrowser.open('index.html')
        except:
            print("Could not open browser automatically. Open index.html manually.")
    
    def create_index_page(self):
        """Create an index page linking to all visualizations"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aircraft Analysis Dashboard</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .card { 
                    border: 1px solid #ddd; 
                    border-radius: 8px; 
                    padding: 20px; 
                    margin: 20px 0; 
                    background-color: #f9f9f9;
                }
                .card h3 { margin-top: 0; color: #555; }
                .card a { 
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 10px;
                }
                .card a:hover { background-color: #0056b3; }
                .stats { background-color: #e9ecef; }
            </style>
        </head>
        <body>
            <h1>🛩️ Aircraft Analysis Dashboard</h1>
            <p>Generated from aircraft data collected over time</p>
            
            <div class="card">
                <h3>📍 Static Aircraft Map</h3>
                <p>View all aircraft positions on a single map with altitude-based color coding.</p>
                <a href="aircraft_static_map.html" target="_blank">Open Static Map</a>
            </div>
            
            <div class="card">
                <h3>⏰ Time Animation</h3>
                <p>Watch aircraft movement over time with an interactive time slider.</p>
                <a href="aircraft_animation.html" target="_blank">Open Animation</a>
            </div>
            
            <div class="card">
                <h3>✈️ Flight Paths</h3>
                <p>See the complete flight paths for aircraft with multiple data points.</p>
                <a href="aircraft_flight_paths.html" target="_blank">Open Flight Paths</a>
            </div>
            
            <div class="card">
                <h3>🔥 Aircraft Density Heatmap</h3>
                <p>Visualize areas with the highest aircraft traffic density.</p>
                <a href="aircraft_heatmap.html" target="_blank">Open Heatmap</a>
            </div>
            
            <div class="card stats">
                <h3>📊 Data Statistics</h3>
                <p>Check the console output or run the analyzer script to see detailed statistics about your aircraft data.</p>
            </div>
        </body>
        </html>
        """
        
        with open("index.html", "w", encoding='utf-8') as f:
            f.write(html_content)


# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = AircraftMapAnalyzer("aircraft_data.csv")
    
    # Create full dashboard
    analyzer.create_dashboard()