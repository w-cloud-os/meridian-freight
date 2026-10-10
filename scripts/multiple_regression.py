import os

import numpy as np
import psycopg
from dotenv import load_dotenv

load_dotenv()

QUERY = """
SELECT r.distance_km,
       EXTRACT(ISODOW FROM s.shipped_at) >= 6,
       s.crew_id,
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

distance = np.array([float(r[0]) for r in rows])
weekend = np.array([float(r[1]) for r in rows])
crew2 = np.array([float(r[2] == 2) for r in rows])   # 1 if crew 2, else 0
y = np.array([float(r[3]) for r in rows])

# Design matrix: intercept, distance, weekend, crew 2
X = np.column_stack([np.ones(len(y)), distance, weekend, crew2])
names = ["intercept", "distance (min/km)", "weekend (min)", "crew 2 (min)"]

# Solve the normal equations (solve is more stable than inverting XtX)
beta = np.linalg.solve(X.T @ X, X.T @ y)

# Uncertainty: sigma^2 * (XtX)^-1 gives the covariance of the estimates
resid = y - X @ beta
n, k = X.shape
sigma2 = resid @ resid / (n - k)
se = np.sqrt(np.diag(sigma2 * np.linalg.inv(X.T @ X)))

print(f"{'term':<20}{'estimate':>10}{'std err':>10}{'95% CI':>22}")
for name, b, s in zip(names, beta, se):
    print(f"{name:<20}{b:>10.4f}{s:>10.4f}   ({b - 1.96 * s:8.4f}, {b + 1.96 * s:8.4f})")

r2 = 1 - (resid @ resid) / np.sum((y - y.mean()) ** 2)
print(f"\nResidual std = {np.sqrt(sigma2):.1f} min, R^2 = {r2:.3f}")