-- Q1: Does average delay grow with route distance?
SELECT r.id,
       r.distance_km,
       count(*)                       AS shipments,
       round(avg(d.delay_minutes), 1) AS avg_delay_min
FROM shipment_delays d
JOIN routes r ON r.id = d.route_id
GROUP BY r.id, r.distance_km
ORDER BY r.distance_km;