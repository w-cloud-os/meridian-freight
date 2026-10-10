-- Q3: Which crews run late?
SELECT c.name,
       c.shift,
       count(*)                     AS shipments,
       roung(avg(delay_minutes), 1) AS avg_delay_min
FROM shipment_delays d
JOIN crews c ON c.id = d.crew_id
GROUP BY c.id, c.name, c.shift
ORDER BY avg_delay_min DESC;