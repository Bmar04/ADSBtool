import csv
import xml.etree.ElementTree as ET
import pandas as pd

class Converter:
    def __init__(self):
        pass

    def convert_csv_to_xml(self, csv_file, xml_file):
        try:
            # Read the CSV file
            print(f"Reading CSV file: {csv_file}")
            df = pd.read_csv(csv_file)
            print(f"Found {len(df)} rows in CSV")

            # Write each row as a separate XML document on its own line
            print(f"Writing XML file: {xml_file}")
            
            with open(xml_file, 'w', encoding='utf-8') as f:
                for index, row in df.iterrows():
                    # Create XML for this single measurement with header and measurement sections
                    xml_content = f'<?xml version="1.0" encoding="utf-8"?><measurement><header><icao24>{str(row["icao24"])}</icao24><callsign>{str(row["callsign"])}</callsign></header><data><timestamp>{str(row["timestamp"])}</timestamp><latitude>{str(row["latitude"])}</latitude><longitude>{str(row["longitude"])}</longitude><baro_altitude>{str(row["baro_altitude"])}</baro_altitude><true_track>{str(row["true_track"])}</true_track><velocity>{str(row["velocity"])}</velocity></data></measurement>'
                    f.write(xml_content + '\n')
            
            print("Conversion completed successfully!")
            
        except Exception as e:
            print(f"Error during conversion: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    converter = Converter()
    converter.convert_csv_to_xml("aircraft_data.csv", "aircraft_data.xml") 