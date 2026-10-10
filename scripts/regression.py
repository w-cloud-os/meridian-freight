import os

import numpy as np
import psycopg
from dotenv import load_dotenv

load_dotenv()

QUERY = """
SELECT r.distance_km,
       EXTRACT(EPOCH FROM (s.delivered_at - s.promised_at)) / 60
FROM shipments s
JOIN routes r ON r.id = s.route_id
WHERE s.delivered_at IS NOT NULL
"""

with psycopg.connect(
    host="localhost", port=5433, dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"], password=os.environ["POSTGRES_PASSWORD"],
) as conn:
    rows = conn.execute(QUERY).fetchall()

x = np.array([float(r[0]) for r in rows])   # distance in km
y = np.array([float(r[1]) for r in rows])   # delay in minutes


def gradient_descent(x, y, lr, steps):
    """Minimize mean squared error for y ~ w*x + b."""
    w = b = 0.0
    with np.errstate(all="ignore"):          # let divergence show up as nan, not crash
        for _ in range(steps):
            err = w * x + b - y
            w -= lr * 2 * np.mean(err * x)
            b -= lr * 2 * np.mean(err)
    return w, b


def mse(w, b, x, y):
    with np.errstate(all="ignore"):
        return np.mean((w * x + b - y) ** 2)


# 1) Exact answer (least squares)
w_cf, b_cf = np.linalg.lstsq(np.column_stack([x, np.ones_like(x)]), y, rcond=None)[0]
print(f"Closed form:  slope = {w_cf:.5f} min/km, intercept = {b_cf:.2f} min")

# 2) Raw distances: the learning rate that worked in project 1 blows up
w, b = gradient_descent(x, y, lr=0.05, steps=200)
print(f"Raw, lr=0.05:  slope = {w}, intercept = {b}, MSE = {mse(w, b, x, y)}")

# 3) Raw distances with a tiny learning rate: stable, but how close is it?
w, b = gradient_descent(x, y, lr=1e-7, steps=5000)
print(f"Raw, lr=1e-7:  slope = {w:.5f}, intercept = {b:.4f}, MSE = {mse(w, b, x, y):.2f}")

# 4) Standardize distance, then fit
mu, sd = x.mean(), x.std()
z = (x - mu) / sd
w_z, b_z = gradient_descent(z, y, lr=0.1, steps=500)
slope = w_z / sd                      # convert back to minutes per km
intercept = b_z - w_z * mu / sd
print(f"Standardized: slope = {slope:.5f} min/km, intercept = {intercept:.2f} min")

# 5) Interpretation
pred = slope * x + intercept
r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
print(f"Per 100 km: {slope * 100:.2f} minutes of extra delay")
print(f"R^2 = {r2:.3f}, residual std = {np.std(y - pred):.1f} min")