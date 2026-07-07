from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
import pandas as pd

app = FastAPI(
    title="API de Rastreo de Vuelos",
    description="Sistema Geoespacial de Rastreo de Vuelos en Tiempo Real",
    version="1.0.0"
)

DB_URL = "postgresql://admin:admin123@postgres:5432/vuelos_db"
engine = create_engine(DB_URL)


@app.get("/")
def root():
    return {"status": "ok", "mensaje": "API de Rastreo de Vuelos funcionando"}


@app.get("/vuelos")
def get_vuelos(limit: int = 100):
    query = text("""
        SELECT id, icao24, callsign, origin_country,
               longitude, latitude, baro_altitude,
               velocity, true_track, on_ground, timestamp
        FROM vuelos
        ORDER BY timestamp DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"limit": limit})
        rows = result.fetchall()
        columns = result.keys()

    data = [dict(zip(columns, row)) for row in rows]
    for row in data:
        row['timestamp'] = str(row['timestamp'])

    return {"total": len(data), "vuelos": data}


@app.get("/vuelos/pais/{pais}")
def get_vuelos_por_pais(pais: str):
    query = text("""
        SELECT icao24, callsign, origin_country,
               longitude, latitude, baro_altitude, velocity, timestamp
        FROM vuelos
        WHERE LOWER(origin_country) = LOWER(:pais)
        ORDER BY timestamp DESC
        LIMIT 100
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"pais": pais})
        rows = result.fetchall()
        columns = result.keys()

    data = [dict(zip(columns, row)) for row in rows]
    for row in data:
        row['timestamp'] = str(row['timestamp'])

    return {"pais": pais, "total": len(data), "vuelos": data}


@app.get("/vuelos/radio")
def get_vuelos_radio(
    lat: float = Query(..., description="Latitud del centro"),
    lon: float = Query(..., description="Longitud del centro"),
    km: float = Query(100, description="Radio en kilómetros")
):
    query = text("""
        SELECT icao24, callsign, origin_country,
               longitude, latitude, baro_altitude, velocity, timestamp,
               ROUND(
                   ST_Distance(
                       ubicacion::geography,
                       ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                   ) / 1000
               ) AS distancia_km
        FROM vuelos
        WHERE ST_DWithin(
            ubicacion::geography,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            :radio_metros
        )
        ORDER BY distancia_km ASC
        LIMIT 100
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {
            "lat": lat,
            "lon": lon,
            "radio_metros": km * 1000
        })
        rows = result.fetchall()
        columns = result.keys()

    data = [dict(zip(columns, row)) for row in rows]
    for row in data:
        row['timestamp'] = str(row['timestamp'])
        row['distancia_km'] = float(row['distancia_km'])

    return {
        "centro": {"lat": lat, "lon": lon},
        "radio_km": km,
        "total": len(data),
        "vuelos": data
    }


@app.get("/estadisticas")
def get_estadisticas():
    query = text("""
        SELECT 
            COUNT(*) as total_registros,
            COUNT(DISTINCT icao24) as vuelos_unicos,
            COUNT(DISTINCT origin_country) as paises,
            ROUND(AVG(baro_altitude)::numeric, 2) as altitud_promedio,
            ROUND(AVG(velocity)::numeric, 2) as velocidad_promedio,
            MAX(timestamp) as ultima_actualizacion
        FROM vuelos
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        row = result.fetchone()
        columns = result.keys()

    data = dict(zip(columns, row))
    data['ultima_actualizacion'] = str(data['ultima_actualizacion'])

    return data