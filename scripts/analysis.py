import os

import numpy as np
import psycopg
from dotenv import load_dotenv
from scipy import stats

load_dotenv()

QUERY = """
SELECT EXTRACT(ISODOW FROM shipped_at) >= 6 AS is_weekend,
       crew_id,
       EXTRACT(EPOCH FROM (delivered_at - promised_at)) / 60 AS delay_min
FROM shipments
WHERE delivered_at IS NOT NULL
"""

with psycopg.connect(
    host="localhost", port=5433, dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"], password=os.environ["POSTGRES_PASSWORD"],
) as conn:
    rows = conn.execute(QUERY).fetchall()

is_weekend = np.array([r[0] for r in rows])
crew_id = np.array([r[1] for r in rows])
delay = np.array([float(r[2]) for r in rows])


def welch(a, b):
    """Welch's t-test for the difference in means (a minus b)."""
    n1, n2 = len(a), len(b)
    v1, v2 = a.var(ddof=1), b.var(ddof=1)
    se = np.sqrt(v1 / n1 + v2 / n2)
    diff = a.mean() - b.mean()
    t = diff / se
    df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    p = 2 * stats.t.sf(abs(t), df)
    margin = stats.t.ppf(0.975, df) * se
    return diff, (diff - margin, diff + margin), t, df, p


def report(label, a, b):
    diff, ci, t, df, p = welch(a, b)
    print(f"{label}: weekend minus weekday = {diff:.2f} min, "
          f"95% CI ({ci[0]:.2f}, {ci[1]:.2f}), t = {t:.2f}, df = {df:.0f}, p = {p:.2g}")
    check = stats.ttest_ind(a, b, equal_var=False)
    print(f"   scipy check: t = {check.statistic:.2f}, p = {check.pvalue:.2g}")


# 1) Raw comparison (confounded by the bad crew)
report("All crews     ", delay[is_weekend], delay[~is_weekend])

# 2) Excluding crew 2
keep = crew_id != 2
report("Excluding crew 2", delay[keep & is_weekend], delay[keep & ~is_weekend])