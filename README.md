# ✈️ Sistema Geoespacial de Rastreo de Vuelos en Tiempo Real

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+PostGIS-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B)

Sistema end-to-end que ingesta, almacena y visualiza datos de vuelos en tiempo real sobre Estados Unidos utilizando la API de OpenSky Network.

## 🏗️ Arquitectura

OpenSky API → Mage AI → PostgreSQL/PostGIS → FastAPI → Streamlit

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Orquestación | Mage AI |
| Base de datos | PostgreSQL 15 + PostGIS |
| Procesamiento | Python, Pandas, GeoPandas |
| Backend | FastAPI + Uvicorn |
| Dashboard | Streamlit + Folium |
| Infraestructura | Docker + Docker Compose |

## 🚀 Cómo correrlo

**Requisitos:** Docker Desktop instalado y corriendo

**Pasos:**

1. Clona el repositorio y entra a la carpeta
2. Ejecuta: `docker compose up --build -d`
3. Accede a los servicios:

| Servicio | URL |
|---|---|
| Dashboard Streamlit | http://localhost:8501 |
| FastAPI Docs | http://localhost:8000/docs |
| Mage AI | http://localhost:6790 |

## 📡 API Endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/` | Health check |
| GET | `/vuelos` | Todos los vuelos recientes |
| GET | `/vuelos/pais/{pais}` | Vuelos por país de origen |
| GET | `/vuelos/radio` | Vuelos en radio específico |
| GET | `/estadisticas` | Estadísticas generales |

## 📊 Features del Dashboard

- 🗺️ Mapa interactivo en tiempo real con posición de aviones
- ✈️ Iconos de aviones rotados según dirección de vuelo
- 📈 Gráficas de países de origen y distribución de altitudes
- 🔍 Búsqueda espacial por radio con PostGIS
- 🔄 Auto-refresh configurable
