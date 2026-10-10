-- Q2: Are weekend shipments delayed more than weekday ones?
SELECT EXTRACT(ISODOW FROM shipped_at) >= 6 AS is_weekend,
       count(*)                                                               AS shipments,
       round(avg(EXTRACT(EPOCH FROM (delivered_at - promised_at)) / 60), 1)   AS avg_delay_min,
       round(stddev(EXTRACT(EPOCH FROM (delivered_at - promised_at)) / 60), 1) AS sd_delay_min
FROM shipments
WHERE delivered_at IS NOT NULL
GROUP BY is_weekend
ORDER BY is_weekend;