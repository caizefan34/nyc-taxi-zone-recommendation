#!/usr/bin/env python3
"""Download sample NYC TLC trip data for quick-start testing."""
import csv
from pathlib import Path
from urllib.request import urlopen

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"


def download_trip_sample():
    """Download a small sample of NYC TLC trip data from public source."""
    url = "https://raw.githubusercontent.com/fivethirtyeight/uber-tlc-foil-response/master/uber-trip-data/uber-raw-data-apr14.csv"
    output_path = SAMPLE_DIR / "sample_trip_data.csv"

    try:
        response = urlopen(url)
        content = response.read().decode("utf-8")
        lines = content.splitlines()
        header = lines[0]
        data = lines[1:501]

        SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="") as f:
            f.write(header + "\n")
            for line in data:
                f.write(line + "\n")

        print(f"Downloaded {len(data)} trip records to {output_path}")
        return len(data)
    except Exception as e:
        print(f"Warning: Could not download trip data: {e}")
        print("Creating synthetic sample data instead...")
        return _create_synthetic_trip_data(output_path)


def _create_synthetic_trip_data(output_path: Path) -> int:
    """Create synthetic trip sample data for testing."""
    import numpy as np
    np.random.seed(42)

    fields = ["hvfhs_license_num", "pickup_datetime", "dropoff_datetime",
              "PULocationID", "DOLocationID", "trip_miles", "trip_time",
              "base_passenger_fare", "tips"]

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for i in range(500):
            pickup_hour = np.random.randint(6, 22)
            pickup_min = np.random.randint(0, 59)
            duration = np.random.randint(10, 60)
            writer.writerow([
                "HV0001",
                f"2023-01-{np.random.randint(1,29):02d} {pickup_hour:02d}:{pickup_min:02d}:00",
                f"2023-01-{np.random.randint(1,29):02d} {pickup_hour:02d}:{(pickup_min + duration) % 60:02d}:00",
                np.random.choice([237, 236, 170, 161, 132, 142]),
                np.random.choice([237, 236, 170, 161, 132, 142]),
                round(np.random.uniform(0.5, 15.0), 2),
                duration,
                round(np.random.uniform(8, 45), 2),
                round(np.random.uniform(0, 8), 2),
            ])
    print(f"Created 500 synthetic trip records at {output_path}")
    return 500


def download_zone_sample():
    """Create sample zone data."""
    output_path = SAMPLE_DIR / "sample_zone_data.csv"
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    zones = [
        (237, "Upper East Side South", "Manhattan", 40.764, -73.960),
        (236, "Upper East Side North", "Manhattan", 40.780, -73.950),
        (170, "Central Harlem", "Manhattan", 40.812, -73.943),
        (161, "Midtown Center", "Manhattan", 40.758, -73.977),
        (132, "JFK Airport", "Queens", 40.642, -73.783),
        (142, "LaGuardia Airport", "Queens", 40.776, -73.874),
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["LocationID", "Zone", "Borough", "Latitude", "Longitude"])
        for z in zones:
            writer.writerow(z)
    print(f"Created {len(zones)} zone records at {output_path}")
    return len(zones)


def download_weather_sample():
    """Create sample weather data."""
    output_path = SAMPLE_DIR / "sample_weather_data.csv"
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    import numpy as np
    np.random.seed(42)

    fields = ["date", "hour", "temperature_c", "precipitation_mm", "wind_speed_kph", "condition"]

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for day in range(1, 8):
            for hour in range(0, 24, 3):
                temp = round(15 + np.random.normal(0, 5), 1)
                precip = round(max(0, np.random.exponential(0.3)), 2)
                wind = round(np.random.uniform(5, 25), 1)
                condition = "Clear" if precip < 0.1 else "Rain" if precip < 2 else "Heavy Rain"
                writer.writerow([f"2023-01-{day:02d}", hour, temp, precip, wind, condition])
    print(f"Created weather data at {output_path}")


def main():
    print("=== Download Sample Data ===")
    n_trips = download_trip_sample()
    n_zones = download_zone_sample()
    download_weather_sample()
    print(f"\nSample data ready in {SAMPLE_DIR}")
    print(f"  - {n_trips} trip records")
    print(f"  - {n_zones} zone records")
    print("  - Weather records (7 days, 3-hour intervals)")


if __name__ == "__main__":
    main()


