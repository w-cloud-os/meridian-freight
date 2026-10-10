-- Solution for confounding error
SELECT EXTRACT(ISODOW FROM shipped_at) >= 6 AS is_weekend,
       count(*) AS shipments,
       round(avg(EXTRACT(EPOCH FROM (delivered_at - promised_at)) / 60), 1) AS avg_delay_min
FROM shipments
WHERE delivered_at IS NOT NULL
  AND crew_id <> 2
GROUP BY is_weekend
ORDER BY is_weekend;