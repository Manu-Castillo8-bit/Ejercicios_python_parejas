import json
import os
import threading
import urllib.request
from datetime import datetime
import flet as ft

# 1. BASE DE DATOS DE MUNICIPIOS DE EL SALVADOR
MUNICIPIOS = {
    "San Salvador": {"lat": 13.6989, "lon": -89.2208},
    "Santa Ana": {"lat": 13.9942, "lon": -89.5597},
    "San Miguel": {"lat": 13.4833, "lon": -88.1833},
    "La Libertad": {"lat": 13.4883, "lon": -89.3222},
    "Sonsonate": {"lat": 13.7189, "lon": -89.7242},
    "Ahuachapán": {"lat": 13.9214, "lon": -89.8450},
    "Usulután": {"lat": 13.3500, "lon": -88.4500},
    "Cojutepeque": {"lat": 13.7211, "lon": -88.9322},
}

# 2. TRADUCCIÓN DE CÓDIGOS WMO
WMO_CODES = {
    0: ("Cielo despejado", "☀️"),
    1: ("Principalmente despejado", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Niebla", "🌫️"),
    48: ("Niebla con escarcha", "🌫️"),
    51: ("Llovizna ligera", "🌦️"),
    53: ("Llovizna moderada", "🌦️"),
    55: ("Llovizna densa", "🌧️"),
    61: ("Lluvia ligera", "🌧️"),
    63: ("Lluvia moderada", "🌧️"),
    65: ("Lluvia fuerte", "🌧️"),
    80: ("Chubascos ligeros", "🌦️"),
    81: ("Chubascos moderados", "🌧️"),
    82: ("Chubascos violentos", "⛈️"),
    95: ("Tormenta eléctrica", "🌩️"),
    96: ("Tormenta con granizo", "⛈️"),
}

CACHE_FILE = "clima_cache.json"

def main(page: ft.Page):
    page.title = "¿VOY O NO VOY?"
    page.theme_mode = "dark"
    page.padding = 20
    page.scroll = "auto"

    # Componentes UI
    dropdown_municipio = ft.Dropdown(
        label="Seleccioná tu municipio",
        options=[ft.dropdown.Option(m) for m in MUNICIPIOS.keys()],
        value="San Salvador",
        expand=True,
    )

    btn_actualizar = ft.ElevatedButton("🔄 Actualizar")

    # Contenedores de Estado
    loader = ft.ProgressRing(visible=False, width=30, height=30)
    lbl_estado = ft.Text("", size=12, italic=True)

    # Tarjeta del Veredicto
    txt_veredicto = ft.Text("CARGANDO...", size=26, weight="bold", color="white", text_align="center")
    txt_subveredicto = ft.Text("", size=14, color="white70", text_align="center")
    
    card_veredicto = ft.Container(
        content=ft.Column(
            [txt_veredicto, txt_subveredicto],
            horizontal_alignment="center",
            alignment="center",
        ),
        padding=25,
        border_radius=15,
        bgcolor="grey800",
        alignment=ft.Alignment(0, 0),
    )

    # Clima Actual
    lbl_temp_actual = ft.Text("--°C", size=40, weight="bold")
    lbl_clima_desc = ft.Text("--", size=18)

    # Barras de Próximas 12 Horas
    row_barras = ft.Row(scroll="always", spacing=12)

    # Campo donde se muestra el mensaje listo para copiar
    txt_mensaje_grupo = ft.TextField(
        label="Aviso listo para copiar y enviar",
        read_only=True,
        visible=False,
        multiline=True,
    )

    btn_copiar_mensaje = ft.ElevatedButton(
        "💬 Generar aviso para el grupo",
        visible=False,
    )

    def generar_aviso(e):
        muni = dropdown_municipio.value
        veredicto = txt_veredicto.value
        temp = lbl_temp_actual.value
        clima = lbl_clima_desc.value
        
        txt_mensaje_grupo.value = f"Clima en {muni}: {veredicto}. Temp: {temp} ({clima})."
        txt_mensaje_grupo.visible = True
        page.update()

    btn_copiar_mensaje.on_click = generar_aviso

    def guardar_cache(data, municipio):
        try:
            cache = {
                "municipio": municipio,
                "timestamp": datetime.now().strftime("%I:%M %p - %d/%m"),
                "data": data
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
        except Exception:
            pass

    def cargar_cache():
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def calcular_veredicto(probs_3h, temp_actual, es_cache=False, timestamp=""):
        if es_cache:
            return {
                "titulo": "NO SÉ TODAVÍA",
                "subtitulo": f"Sin datos frescos. Datos guardados a las {timestamp}.",
                "color": "grey700",
            }
        
        max_prob = max(probs_3h) if probs_3h else 0
        
        if max_prob >= 70:
            titulo = "NO SALGÁS SIN PARAGUAS"
            color = "#E91E63"
        elif max_prob >= 40:
            titulo = "LLEVALO POR SI ACASO"
            color = "#FFA000"
        else:
            titulo = "ANDÁ TRANQUILO"
            color = "#2E7D32"

        subtitulo = f"Probabilidad máxima en las próximas 3h: {max_prob}%"
        if temp_actual > 32.0:
            subtitulo += "\n☀️ ¡Pasa de 32°C! Llevá bloqueador y agua."

        return {"titulo": titulo, "subtitulo": subtitulo, "color": color}

    def actualizar_ui(data, municipio, es_cache=False, timestamp_cache=""):
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        probs = hourly.get("precipitation_probability", [])
        codes = hourly.get("weather_code", [])

        hora_actual_str = datetime.now().strftime("%Y-%m-%dT%H:00")
        try:
            idx = times.index(hora_actual_str)
        except ValueError:
            idx = 0

        probs_3h = probs[idx:idx+3]
        probs_12h = probs[idx:idx+12]
        times_12h = times[idx:idx+12]
        
        temp_actual = temps[idx] if idx < len(temps) else 0.0
        code_actual = codes[idx] if idx < len(codes) else 0

        ver = calcular_veredicto(probs_3h, temp_actual, es_cache, timestamp_cache)
        card_veredicto.bgcolor = ver["color"]
        txt_veredicto.value = ver["titulo"]
        txt_subveredicto.value = ver["subtitulo"]

        desc_clima, emoji = WMO_CODES.get(code_actual, ("Desconocido", "🌡️"))
        lbl_temp_actual.value = f"{temp_actual}°C"
        lbl_clima_desc.value = f"{emoji} {desc_clima}"

        row_barras.controls.clear()
        for i in range(len(probs_12h)):
            p = probs_12h[i]
            t_str = times_12h[i].split("T")[1][:5]
            altura_barra = max(float(p), 5.0)

            col = ft.Column(
                [
                    ft.Text(f"{p}%", size=10, weight="bold"),
                    ft.Container(
                        width=20,
                        height=altura_barra,
                        bgcolor="blue400" if p >= 40 else "blue200",
                        border_radius=4,
                    ),
                    ft.Text(t_str, size=10),
                ],
                horizontal_alignment="center",
                alignment="end",
            )
            row_barras.controls.append(col)

        btn_copiar_mensaje.visible = True
        txt_mensaje_grupo.visible = False

        lbl_estado.value = f"Última actualización: {datetime.now().strftime('%I:%M %p')}" if not es_cache else f"Modo Offline ({timestamp_cache})"
        loader.visible = False
        page.update()

    def consultar_api(e=None):
        muni_nombre = dropdown_municipio.value
        coords = MUNICIPIOS[muni_nombre]
        
        loader.visible = True
        lbl_estado.value = "Consultando satélites..."
        page.update()

        def peticion():
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={coords['lat']}&longitude={coords['lon']}"
                f"&hourly=temperature_2m,precipitation_probability,weather_code"
                f"&timezone=America%2FEl_Salvador"
            )
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=8) as response:
                    data = json.loads(response.read().decode())
                    guardar_cache(data, muni_nombre)
                    actualizar_ui(data, muni_nombre)
            except Exception:
                cache = cargar_cache()
                if cache and cache.get("municipio") == muni_nombre:
                    actualizar_ui(cache["data"], muni_nombre, es_cache=True, timestamp_cache=cache["timestamp"])
                else:
                    txt_veredicto.value = "ERROR DE CONEXIÓN"
                    txt_subveredicto.value = "No hay internet ni datos guardados para este municipio."
                    card_veredicto.bgcolor = "red900"
                    loader.visible = False
                    lbl_estado.value = "Error al obtener datos"
                    page.update()

        threading.Thread(target=peticion).start()

    dropdown_municipio.on_change = consultar_api
    btn_actualizar.on_click = consultar_api

    page.add(
        ft.Row([dropdown_municipio, btn_actualizar, loader]),
        lbl_estado,
        ft.Divider(height=10, color="transparent"),
        card_veredicto,
        ft.Divider(height=15, color="transparent"),
        ft.Row([lbl_temp_actual, lbl_clima_desc], alignment="center", spacing=15),
        ft.Divider(height=15),
        ft.Text(" Probabilidad de lluvia (próximas 12 horas):", weight="bold"),
        ft.Container(content=row_barras, padding=10),
        ft.Divider(height=10, color="transparent"),
        ft.Column(
            [btn_copiar_mensaje, txt_mensaje_grupo],
            horizontal_alignment="center",
        )
    )

    consultar_api()

ft.app(target=main)