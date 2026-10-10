CREATE TABLE routes (
    id serial PRIMARY KEY,
    origin text NOT NULL,
    destination text NOT NULL,
    distance_km numeric NOT NULL,
    CHECK (distance_km > 0)
);

CREATE TABLE crews (
    id serial PRIMARY KEY,
    name text NOT NULL,
    shift text NOT NULL,
    CHECK (shift IN ('weekday', 'weekend'))
);

CREATE TABLE shipments (
    id serial PRIMARY KEY,
    route_id integer NOT NULL REFERENCES routes(id),
    crew_id integer NOT NULL REFERENCES crews(id),
    shipped_at timestamptz NOT NULL,
    promised_at timestamptz NOT NULL,
    delivered_at timestamptz,
    weight_kg numeric NOT NULL,
    CHECK (promised_at > shipped_at),
    CHECK (delivered_at IS NULL OR delivered_at >= shipped_at),
    CHECK (weight_kg > 0)
);

CREATE INDEX idx_shipments_route_id ON shipments(route_id);
CREATE INDEX idx_shipments_crew_id ON shipments(crew_id);
CREATE VIEW shipment_delays AS
SELECT id, route_id, crew_id,
       EXTRACT(EPOCH FROM (delivered_at - promised_at)) AS delay_minutes
FROM shipments
WHERE delivered_at IS NOT NULL