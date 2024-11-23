import csv
from typing import List, Dict

def load_devices_from_csv(filepath: str) -> List[Dict]:
    devices = []
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            devices.append(row)
    return devices