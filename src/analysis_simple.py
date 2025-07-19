import pandas as pd
import folium
import webbrowser
from datetime import datetime

class SimpleAircraftPlotter:
    def __init__(self, csv_file: str):
        """
        Simple aircraft plotter that shows points and connects them with lines
        
        Args:
            csv_file: Path to the CSV file containing aircraft data
        """
        self.csv_file = csv_file
        self.data = None
        self.load_data()
    
    def load_data(self):
        """Load aircraft data from CSV"""
        try:
            self.data = pd.read_csv(self.csv_file)
            
            # Convert timestamp to datetime
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            
            # Remove rows with missing coordinates
            self.data = self.data.dropna(subset=['latitude', 'longitude'])
            
            # Sort by aircraft and timestamp
            self.data = self.data.sort_values(['icao24', 'timestamp'])
            
            print(f"Loaded {len(self.data)} aircraft records")
            print(f"Unique aircraft: {self.data['icao24'].nunique()}")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = pd.DataFrame()
    
    def create_map(self, output_file: str = "aircraft_tracks.html"):
        """
        Create a simple map with aircraft points and tracks
        
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
        
        # Colors for different aircraft
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                  'lightred', 'darkblue', 'darkgreen', 'cadetblue', 
                  'darkpurple', 'pink', 'lightblue', 'lightgreen', 
                  'gray', 'black', 'brown']
        
        # Group by aircraft
        aircraft_groups = self.data.groupby('icao24')
        color_idx = 0
        
        print(f"Plotting {len(aircraft_groups)} aircraft...")
        
        for aircraft_id, group in aircraft_groups:
            # Sort by timestamp
            group = group.sort_values('timestamp').reset_index(drop=True)
            
            # Choose color for this aircraft
            color = colors[color_idx % len(colors)]
            color_idx += 1
            
            # If aircraft has multiple points, draw lines between them
            if len(group) > 1:
                # Create coordinates list for the line
                coordinates = []
                for _, row in group.iterrows():
                    coordinates.append([row['latitude'], row['longitude']])
                
                # Draw the flight path line
                folium.PolyLine(
                    coordinates,
                    color=color,
                    weight=3,
                    opacity=0.7,
                    popup=f"Aircraft: {aircraft_id}<br>Points: {len(coordinates)}"
                ).add_to(m)
            
            # Plot all points for this aircraft
            for i, (_, row) in enumerate(group.iterrows()):
                # Get altitude for color coding
                altitude = row.get('baro_altitude', 0) or row.get('geo_altitude', 0) or 0
                
                # Create popup info
                popup_text = f"""
                <b>Aircraft:</b> {aircraft_id}<br>
                <b>Callsign:</b> {row.get('callsign', 'N/A')}<br>
                <b>Point:</b> {i+1} of {len(group)}<br>
                <b>Time:</b> {row['timestamp']}<br>
                <b>Altitude:</b> {altitude} ft<br>
                <b>Speed:</b> {row.get('velocity', 'N/A')} knots
                """
                
                # Different marker for first and last points
                if i == 0 and len(group) > 1:
                    # First point - green marker
                    folium.Marker(
                        [row['latitude'], row['longitude']],
                        icon=folium.Icon(color='green', icon='play'),
                        popup=f"START<br>{popup_text}"
                    ).add_to(m)
                elif i == len(group) - 1 and len(group) > 1:
                    # Last point - red marker
                    folium.Marker(
                        [row['latitude'], row['longitude']],
                        icon=folium.Icon(color='red', icon='stop'),
                        popup=f"END<br>{popup_text}"
                    ).add_to(m)
                else:
                    # Middle points or single points - colored circles
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=5,
                        popup=popup_text,
                        color=color,
                        fillColor=color,
                        fillOpacity=0.7
                    ).add_to(m)
        
        # Add a simple legend
        legend_html = f'''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <b>Aircraft Tracks</b><br>
        <i class="fa fa-play" style="color:green"></i> Start Point<br>
        <i class="fa fa-stop" style="color:red"></i> End Point<br>
        <i class="fa fa-circle" style="color:blue"></i> Track Points<br>
        <hr>
        <b>Total Aircraft:</b> {len(aircraft_groups)}<br>
        <b>Total Points:</b> {len(self.data)}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        m.save(output_file)
        print(f"Map saved to {output_file}")
        
        # Try to open in browser
        try:
            webbrowser.open(output_file)
            print(f"Opened {output_file} in browser")
        except:
            print(f"Could not open browser. Open {output_file} manually")
        
        return m
    
    def print_summary(self):
        """Print a summary of the data"""
        if self.data.empty:
            print("No data loaded")
            return
        
        print("\n=== DATA SUMMARY ===")
        print(f"Total records: {len(self.data)}")
        print(f"Unique aircraft: {self.data['icao24'].nunique()}")
        print(f"Time range: {self.data['timestamp'].min()} to {self.data['timestamp'].max()}")
        
        # Count aircraft with multiple points
        aircraft_counts = self.data['icao24'].value_counts()
        multi_point = (aircraft_counts > 1).sum()
        print(f"Aircraft with tracks (>1 point): {multi_point}")
        print(f"Aircraft with single points: {len(aircraft_counts) - multi_point}")
        
        if multi_point > 0:
            print(f"Longest track: {aircraft_counts.max()} points")
            longest_aircraft = aircraft_counts.idxmax()
            print(f"Longest track aircraft: {longest_aircraft}")


# Simple usage
if __name__ == "__main__":
    # Create plotter
    plotter = SimpleAircraftPlotter("aircraft_data.csv")
    
    # Print summary
    plotter.print_summary()
    
    # Create and open map
    plotter.create_map()