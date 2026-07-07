import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================
API_URL = "http://fastapi:8000"

CLIENT_ID     = "amy.him-api-client"
CLIENT_SECRET = "fcSze65WMPfF7FT1jpo15kkwgIodrMd1"

BBOX = {'lamin': 24.0, 'lomin': -125.0, 'lamax': 50.0, 'lomax': -66.0}

st.set_page_config(
    page_title="FlightTrack — Live Air Traffic",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500&display=swap');

.stApp {
    background: #000000;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(0, 100, 255, 0.07) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(0, 200, 255, 0.05) 0%, transparent 50%);
}

[data-testid="stSidebar"] {
    background: rgba(2, 15, 35, 0.95) !important;
    border-right: 1px solid rgba(0, 150, 255, 0.2) !important;
}

.main-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.6rem;
    font-weight: 900;
    background: linear-gradient(90deg, #00aaff, #00ffee, #0066ff);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s linear infinite;
    letter-spacing: 2px;
    margin-bottom: 0;
}

@keyframes shimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}

.main-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: rgba(0, 180, 255, 0.6);
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-top: 4px;
}

.metric-card {
    background: linear-gradient(135deg, rgba(0, 20, 50, 0.9), rgba(0, 10, 30, 0.95));
    border: 1px solid rgba(0, 150, 255, 0.25);
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, #00aaff, transparent);
    animation: scanLine 2s ease-in-out infinite;
}

@keyframes scanLine {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.metric-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: rgba(0, 180, 255, 0.6);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #00ddff;
    text-shadow: 0 0 20px rgba(0, 200, 255, 0.5);
}

.neon-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0, 150, 255, 0.5), transparent);
    margin: 24px 0;
}

.section-header {
    font-family: 'Orbitron', monospace;
    font-size: 0.85rem;
    color: #00aaff;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(0, 150, 255, 0.4), transparent);
}

.pulse-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #00ff88;
    border-radius: 50%;
    box-shadow: 0 0 10px #00ff88;
    animation: pulse 1.5s ease-in-out infinite;
    margin-right: 8px;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.4; transform: scale(0.8); }
}

.status-bar {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: rgba(0, 180, 255, 0.5);
    letter-spacing: 2px;
    padding: 8px 0;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNCIÓN PARA OBTENER VUELOS EN TIEMPO REAL DESDE OPENSKY
# ============================================================
@st.cache_data(ttl=30)  # Cache de 30 segundos
def obtener_vuelos_tiempo_real():
    try:
        # Token
        url_token = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
        resp = requests.post(url_token, data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }, timeout=15)
        token = resp.json()["access_token"]

        # Vuelos
        resp = requests.get(
            "https://opensky-network.org/api/states/all",
            params=BBOX,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        estados = resp.json().get("states", [])

        columnas = ["icao24","callsign","origin_country","time_position","last_contact",
                    "longitude","latitude","baro_altitude","on_ground","velocity",
                    "true_track","vertical_rate","sensors","geo_altitude","squawk","spi","position_source"]

        df = pd.DataFrame(estados, columns=columnas)
        df = df.dropna(subset=["latitude","longitude"])
        df = df[df["on_ground"] == False]
        df["callsign"] = df["callsign"].str.strip()
        return df, len(df), datetime.now().strftime("%H:%M:%S")

    except Exception as e:
        return pd.DataFrame(), 0, "Error"


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style='font-family: Orbitron, monospace; font-size: 1rem; color: #00aaff;
                letter-spacing: 3px; text-transform: uppercase; margin-bottom: 24px;
                padding-bottom: 12px; border-bottom: 1px solid rgba(0,150,255,0.2)'>
        ⚙ Control Panel
    </div>
    """, unsafe_allow_html=True)

    limite = st.slider("Vuelos a mostrar", 50, 500, 200, step=50)
    refresh_rate = st.selectbox("Actualizar cada:", ["30 segundos", "60 segundos", "2 minutos"], index=0)
    auto_refresh = st.checkbox("🔴 Live Mode", value=False)

    st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='font-family: Inter, sans-serif; font-size: 0.75rem;
                color: rgba(0,180,255,0.5); letter-spacing: 1px;'>
        <span class='pulse-dot'></span> SISTEMA ACTIVO<br><br>
        Fuente: OpenSky Network<br>
        Región: Estados Unidos<br>
        Protocolo: OAuth2<br>
        Modo: Tiempo Real
    </div>
    """, unsafe_allow_html=True)

    if st.button(" Actualizar ahora"):
        st.cache_data.clear()
        st.rerun()

    if auto_refresh:
        import time
        rates = {"30 segundos": 30, "60 segundos": 60, "2 minutos": 120}
        time.sleep(rates[refresh_rate])
        st.cache_data.clear()
        st.rerun()

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class='main-title'>✈ FLIGHTTRACK</div>
<div class='main-subtitle'>Sistema Geoespacial de Rastreo de Vuelos en Tiempo Real</div>
<div class='neon-divider'></div>
""", unsafe_allow_html=True)

# ============================================================
# OBTENER DATOS EN TIEMPO REAL
# ============================================================
df, total_vuelos, ultima_actualizacion = obtener_vuelos_tiempo_real()

# ============================================================
# MÉTRICAS
# ============================================================
st.markdown("<div class='section-header'>Telemetría en Vivo</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Vuelos Activos</div>
        <div class='metric-value'>{total_vuelos:,}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    paises = df['origin_country'].nunique() if len(df) > 0 else 0
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Países</div>
        <div class='metric-value'>{paises}</div>
    </div>""", unsafe_allow_html=True)

with col3:
    alt_prom = f"{df['baro_altitude'].mean():,.0f}" if len(df) > 0 else "N/A"
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Altitud Prom.</div>
        <div class='metric-value'>{alt_prom}m</div>
    </div>""", unsafe_allow_html=True)

with col4:
    vel_prom = f"{df['velocity'].mean():,.0f}" if len(df) > 0 else "N/A"
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Velocidad Prom.</div>
        <div class='metric-value'>{vel_prom}m/s</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)

# ============================================================
# MAPA EN TIEMPO REAL
# ============================================================
st.markdown("<div class='section-header'>Mapa de Tráfico Aéreo en Vivo</div>", unsafe_allow_html=True)

if len(df) > 0:
    df_mapa = df.head(limite)

    mapa = folium.Map(
        location=[39.5, -98.35],
        zoom_start=4,
        tiles='CartoDB dark_matter'
    )

    for _, row in df_mapa.iterrows():
        track = row.get('true_track') or 0
        icon_html = f"""
        <div style="
            font-size: 18px;
            transform: rotate({track}deg);
            filter: drop-shadow(0 0 6px #00ddff);
            line-height: 1;
            color: #00ddff;
        ">✈</div>
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            icon=folium.DivIcon(
                html=icon_html,
                icon_size=(24, 24),
                icon_anchor=(12, 12)
            ),
            popup=folium.Popup(
                f"""
                <div style='font-family: monospace; background: #020b18;
                            color: #00ddff; padding: 8px; border-radius: 4px;
                            border: 1px solid #00aaff; min-width: 160px;'>
                    <b>✈ {row.get('callsign', 'N/A')}</b><br>
                    <hr style='border-color: #00aaff33; margin: 4px 0'>
                       {row.get('origin_country', 'N/A')}<br>
                       Alt: {row.get('baro_altitude', 'N/A')} m<br>
                       Vel: {row.get('velocity', 'N/A')} m/s<br>
                       Track: {round(track)}°
                </div>
                """,
                max_width=200
            )
        ).add_to(mapa)

    st_folium(mapa, width=None, height=500, returned_objects=[])

    st.markdown(f"""
    <div class='status-bar'>
        <span class='pulse-dot'></span>
        {total_vuelos} VUELOS ACTIVOS EN TIEMPO REAL — ÚLTIMA ACTUALIZACIÓN: {ultima_actualizacion}
    </div>
    """, unsafe_allow_html=True)

else:
    st.info(" No hay vuelos disponibles en este momento.")

st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)

# ============================================================
# GRÁFICAS
# ============================================================
st.markdown("<div class='section-header'>Análisis de Tráfico</div>", unsafe_allow_html=True)

if len(df) > 0:
    col1, col2 = st.columns(2)

    with col1:
        top_paises = df['origin_country'].value_counts().head(10).reset_index()
        top_paises.columns = ['País', 'Vuelos']
        fig1 = go.Figure(go.Bar(
            x=top_paises['Vuelos'],
            y=top_paises['País'],
            orientation='h',
            marker=dict(
                color=top_paises['Vuelos'],
                colorscale=[[0, '#003366'], [0.5, '#0066cc'], [1, '#00ddff']],
                showscale=False,
                line=dict(color='rgba(0,170,255,0.3)', width=1)
            )
        ))
        fig1.update_layout(
            title=dict(text='Top 10 Países de Origen', font=dict(family='Orbitron', color='#00aaff', size=12)),
            plot_bgcolor='rgba(2,11,24,0.8)',
            paper_bgcolor='rgba(2,11,24,0)',
            font=dict(color='#aaccee', family='Inter'),
            xaxis=dict(gridcolor='rgba(0,100,255,0.1)', color='#aaccee'),
            yaxis=dict(gridcolor='rgba(0,100,255,0.1)', color='#aaccee'),
            margin=dict(l=10, r=10, t=40, b=10),
            height=320
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        altitudes = df['baro_altitude'].dropna()
        fig2 = go.Figure(go.Histogram(
            x=altitudes,
            nbinsx=20,
            marker=dict(
                color='rgba(0,170,255,0.7)',
                line=dict(color='rgba(0,220,255,0.8)', width=1)
            )
        ))
        fig2.update_layout(
            title=dict(text='Distribución de Altitudes', font=dict(family='Orbitron', color='#00aaff', size=12)),
            plot_bgcolor='rgba(2,11,24,0.8)',
            paper_bgcolor='rgba(2,11,24,0)',
            font=dict(color='#aaccee', family='Inter'),
            xaxis=dict(title='Altitud (m)', gridcolor='rgba(0,100,255,0.1)', color='#aaccee'),
            yaxis=dict(title='Vuelos', gridcolor='rgba(0,100,255,0.1)', color='#aaccee'),
            margin=dict(l=10, r=10, t=40, b=10),
            height=320
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)

# ============================================================
# TABLA
# ============================================================
st.markdown("<div class='section-header'>Registro de Vuelos</div>", unsafe_allow_html=True)

if len(df) > 0:
    df_tabla = df[['callsign', 'origin_country', 'latitude', 'longitude',
                   'baro_altitude', 'velocity', 'true_track']].copy()
    df_tabla.columns = ['Callsign', 'País', 'Latitud', 'Longitud',
                        'Altitud (m)', 'Velocidad (m/s)', 'Dirección (°)']
    st.dataframe(df_tabla, use_container_width=True, height=300)

st.markdown("<div class='neon-divider'></div>", unsafe_allow_html=True)

# ============================================================
# BÚSQUEDA POR RADIO
# ============================================================
st.markdown("<div class='section-header'>Búsqueda Espacial por Radio</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
lat = col1.number_input("Latitud", value=40.7128, format="%.4f")
lon = col2.number_input("Longitud", value=-74.0060, format="%.4f")
km = col3.number_input("Radio (km)", value=200, min_value=10, max_value=1000)

if st.button(" Ejecutar Búsqueda Espacial"):
    try:
        resp = requests.get(
            f"{API_URL}/vuelos/radio",
            params={"lat": lat, "lon": lon, "km": km},
            timeout=10
        )
        resultado = resp.json()
        st.success(f" {resultado['total']} vuelos encontrados en radio de {km} km")
        if resultado['total'] > 0:
            df_radio = pd.DataFrame(resultado['vuelos'])
            st.dataframe(df_radio[['callsign', 'origin_country', 'baro_altitude',
                                    'velocity', 'distancia_km']].rename(columns={
                'callsign': 'Callsign', 'origin_country': 'País',
                'baro_altitude': 'Altitud (m)', 'velocity': 'Velocidad (m/s)',
                'distancia_km': 'Distancia (km)'
            }), use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")