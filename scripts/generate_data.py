import os
from datetime import datetime, timedelta, timezone

import numpy as np
import psycopg
from dotenv import load_dotenv

load_dotenv()
rng = np.random.default_rng(42) # seeded: same data every run

N_ROUTES, N_CREWS, N_SHIPMENTS = 12, 6, 20_000
START = datetime(2026, 1, 1, tzinfo=timezone.utc)

# Ground truth: what is REALLY causing delays in this company
baseline = -5.0        # minutes: shipments run slightly early on a short, easy route
min_per_km = 0.06      # extray delay minutes per km of route distance
weekend_effect = 3.0   # extra minutes when shipped on a weekend
bad_crew_id = 2        # one weekday crew that struggles
bad_crew_effect = 15.0 # extra minutes for that crew
noise_sd = 25.0        # random variation (std. dev., minutes)

def simulate_delay_minutes(distance_km, is_weekend, crew_id):
    delay = baseline + min_per_km * distance_km
    if is_weekend:
        delay += weekend_effect
    if crew_id == bad_crew_id:
        delay += bad_crew_effect
    return delay + rng.normal(0, noise_sd)

def main():
    routes = [
    (f"Depot-{i}", f"Depot-{i+100}", round(float(rng.uniform(50, 1200)), 1))
     for i in range(1, N_ROUTES + 1)
    ]
    # First half of crews work weekdays, second half weekends
    crews = [
    (f"Crew {i}", "weekday" if i <= N_CREWS // 2 else "weekend")
    for i in range (1, N_CREWS + 1)
    ]
    shipments = []
    for _ in range(N_SHIPMENTS):
        route_id = int(rng.integers(1, N_ROUTES + 1))
        distance = routes[route_id - 1][2]

        shipped = START + timedelta(minutes=int(rng.integers(0, 60 * 24 * 180)))
        is_weekend = shipped.weekday() >= 5

        # pick a crew whose shift matches the shipping day
        eligible = [ i + 1 for i, c in enumerate(crews)
                     if c[1] == ("weekend" if is_weekend else "weekday")]
        crew_id = int(rng.choice(eligible))

        promised = shipped + timedelta(hours=distance / 60 + 4) # 60 km/h + buffer
        delay = simulate_delay_minutes(distance, is_weekend, crew_id)
        delivered = max(promised + timedelta(minutes=float(delay)), 
                        shipped + timedelta(minutes = 30))

        if rng.random() < 0.02: # ~2% still in transit
            delivered = None

        weight = round(float(rng.uniform(0.5, 500)), 2)
        shipments.append((route_id, crew_id, shipped, promised, delivered, weight))
    
    with psycopg.connect(
        host="localhost", port=5433, dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"], password=os.environ["POSTGRES_PASSWORD"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE shipments, routes, crews RESTART IDENTITY CASCADE")
            cur.executemany(
                "INSERT INTO routes (origin, destination, distance_km) VALUES (%s, %s, %s)", routes)
            cur.executemany(
                "INSERT INTO crews (name, shift) VALUES (%s, %s)", crews)
            cur.executemany(
                "INSERT INTO shipments (route_id, crew_id, shipped_at, promised_at, delivered_at, weight_kg) "
                "VALUES (%s, %s, %s, %s, %s, %s)", shipments)

if __name__ == "__main__":
    main()