"""
Sismógrafo SV - Monitor en Tiempo Real
--------------------------------------
Esta aplicación utiliza la librería Flet para crear una interfaz gráfica que 
monitorea sismos en tiempo real utilizando la API pública del USGS (United States 
Geological Survey). Está centrada en la región de Centroamérica y calcula la 
distancia de los epicentros a San Salvador.
"""

import os
import json
import math
import csv
import threading
import time
from datetime import datetime
import requests
import flet as ft
import flet.canvas as cv

# -------------------------------------------------------------
# CONFIGURACIÓN GENERAL Y CONSTANTES
# -------------------------------------------------------------
# URL de la API del USGS para obtener los sismos de las últimas 24 horas
API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
CACHE_FILE = "sismos_cache.json"

# Coordenadas de San Salvador (Referencia para cálculos de distancia)
SS_LAT = 13.69
SS_LON = -89.19
RADIO_TIERRA_KM = 6371

# Límites geográficos para el mapa (Filtro para Centroamérica)
LON_MIN, LON_MAX = -93.0, -82.0
LAT_MIN, LAT_MAX = 7.0, 19.0

# Paleta de colores para la interfaz y los sismos según su magnitud
COLOR_VERDE = "#39FF88"   # Sismos leves (< 3.0)
COLOR_AMBAR = "#FFB300"   # Sismos moderados (3.0 - 4.4)
COLOR_MAGENTA = "#FF2E97" # Sismos fuertes (>= 4.5)
COLOR_BG_MAP = "#0F172A"  # Fondo del mapa
COLOR_LINE = "#1E293B"    # Líneas de cuadrícula
COLOR_MAPA = "#475569"    # Silueta costera y fronteras

# Coordenadas geográficas simplificadas de la silueta de Centroamérica para dibujar el mapa
COASTLINES = [
    # Costa del Pacífico (Desde Guatemala hasta Panamá)
    [(-92.2, 14.6), (-90.8, 14.2), (-89.8, 13.5), (-88.8, 13.2), (-87.8, 13.1),
     (-87.3, 13.3), (-87.1, 12.9), (-86.2, 11.8), (-85.8, 11.1), (-84.8, 9.9),
     (-83.6, 8.5), (-82.9, 8.2), (-81.8, 7.2), (-80.0, 7.4), (-78.5, 7.5)],
    
    # Costa del Caribe (Desde Belice/Honduras hasta Panamá)
    [(-88.3, 18.2), (-88.2, 15.8), (-86.0, 15.9), (-85.0, 16.0), (-83.2, 15.0),
     (-83.1, 14.0), (-83.6, 11.5), (-83.6, 10.9), (-82.7, 9.6), (-80.0, 9.2),
     (-79.5, 9.5), (-77.5, 8.6)],

    # Límite territorial norte de El Salvador / Frontera con Guatemala y Honduras
    [(-90.1, 13.9), (-89.5, 14.4), (-89.1, 14.4), (-88.1, 14.1), (-87.7, 13.1)]
]


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia ortodrómica (distancia más corta en la superficie de una esfera)
    entre dos puntos geográficos dados sus latitudes y longitudes.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return RADIO_TIERRA_KM * c


def get_color_and_size(mag):
    """
    Asigna un color y un tamaño de radio (para el punto en el mapa) basándose
    en la magnitud del sismo.
    """
    if mag is None:
        mag = 0
    radius = 3 + (mag * 2.5)
    
    if mag < 3.0:
        color = COLOR_VERDE
    elif mag < 4.5:
        color = COLOR_AMBAR
    else:
        color = COLOR_MAGENTA
        
    return color, radius


def main(page: ft.Page):
    """
    Función principal que construye la interfaz gráfica y maneja la lógica de Flet.
    """
    # Configuración de la ventana principal
    page.title = "SISMÓGRAFO SV · Monitor en Tiempo Real"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 1200
    page.window_height = 800

    # Estado global de la aplicación
    state = {
        "sismos_data": [],      # Lista de sismos descargados/en caché
        "map_width": 700,       # Ancho dinámico del canvas del mapa
        "map_height": 600,      # Alto dinámico del canvas del mapa
        "selected_eq": None     # Sismo actualmente seleccionado por el usuario
    }

    def mostrar_notificacion(mensaje, color_bg="#334155"):
        """Muestra un mensaje tipo SnackBar (pop-up) en la parte inferior."""
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color="white", weight="bold"),
            bgcolor=color_bg,
            duration=4000
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # -------------------------------------------------------------
    # COMPONENTES DE LA INTERFAZ
    # -------------------------------------------------------------
    # Filtro desplegable por magnitud mínima
    mag_filter = ft.Dropdown(
        options=[ft.dropdown.Option(x) for x in ["0.0", "2.0", "3.0", "4.0", "4.5", "5.0"]],
        value="0.0",
        width=100,
        label="Mag Mín"
    )
    
    lbl_status = ft.Text("Estado: Listo", color="grey", size=13)
    
    # Etiquetas para la tarjeta de detalle del evento
    lbl_detail_mag = ft.Text("Magnitud: --", weight="bold", size=16)
    lbl_detail_place = ft.Text("Lugar: Selecciona un sismo de la lista", width=280)
    lbl_detail_depth = ft.Text("Profundidad: --")
    lbl_detail_dist = ft.Text("Distancia a SS: --")
    
    # Tarjeta que muestra los detalles del sismo seleccionado
    detail_card = ft.Container(
        content=ft.Column([
            ft.Text("DETALLE DEL EVENTO", weight="bold", color="cyan"),
            lbl_detail_mag,
            lbl_detail_place,
            lbl_detail_depth,
            lbl_detail_dist
        ]),
        bgcolor="#1E293B",
        padding=15,
        border_radius=10,
        width=320
    )
    
    # Lista scrolleable de sismos
    lista_sismos = ft.ListView(expand=True, spacing=5, auto_scroll=False)
    
    # Panel lateral izquierdo (Tarjeta de detalles + Lista)
    left_panel = ft.Column([
        detail_card,
        ft.Text("ÚLTIMAS 24 HORAS (Centroamérica)", weight="bold"),
        ft.Container(content=lista_sismos, expand=True)
    ], width=320)

    # Canvas donde se dibuja el mapa y los epicentros
    map_canvas = cv.Canvas(expand=True)
    map_container = ft.Container(
        content=map_canvas,
        bgcolor=COLOR_BG_MAP,
        border_radius=10,
        expand=True
    )

    # -------------------------------------------------------------
    # DIBUJO Y LÓGICA
    # -------------------------------------------------------------
    def coords_to_pixels(lon, lat):
        """Convierte coordenadas geográficas (lat, lon) a píxeles X, Y en el canvas."""
        x_prop = (lon - LON_MIN) / (LON_MAX - LON_MIN)
        x = x_prop * state["map_width"]
        y_prop = (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)
        y = state["map_height"] - (y_prop * state["map_height"])
        return x, y

    def draw_map():
        """Se encarga de renderizar la cuadrícula, el mapa, la capital y los sismos en el Canvas."""
        map_canvas.shapes.clear()
        w, h = state["map_width"], state["map_height"]
        
        # 1. Cuadrícula de coordenadas
        for i in range(1, 10):
            x = i * (w / 10)
            y = i * (h / 10)
            map_canvas.shapes.append(cv.Line(x, 0, x, h, paint=ft.Paint(color=COLOR_LINE, stroke_width=1)))
            map_canvas.shapes.append(cv.Line(0, y, w, y, paint=ft.Paint(color=COLOR_LINE, stroke_width=1)))
            
        # 2. Silueta del mapa de Centroamérica
        map_paint = ft.Paint(color=COLOR_MAPA, stroke_width=2)
        for path in COASTLINES:
            for k in range(len(path) - 1):
                lon1, lat1 = path[k]
                lon2, lat2 = path[k + 1]
                x1, y1 = coords_to_pixels(lon1, lat1)
                x2, y2 = coords_to_pixels(lon2, lat2)
                map_canvas.shapes.append(cv.Line(x1, y1, x2, y2, paint=map_paint))

        # 3. Ubicación de San Salvador (Marca con cruz blanca)
        ss_x, ss_y = coords_to_pixels(SS_LON, SS_LAT)
        map_canvas.shapes.extend([
            cv.Line(ss_x - 8, ss_y, ss_x + 8, ss_y, paint=ft.Paint(color="white", stroke_width=2)),
            cv.Line(ss_x, ss_y - 8, ss_x, ss_y + 8, paint=ft.Paint(color="white", stroke_width=2)),
            cv.Text(ss_x + 12, ss_y - 12, "San Salvador", ft.TextStyle(color="white", size=11, weight="bold"))
        ])
        
        # 4. Epicentros de los sismos
        try:
            min_mag = float(mag_filter.value) if mag_filter.value else 0.0
        except ValueError:
            min_mag = 0.0

        for s in state["sismos_data"]:
            props = s['properties']
            mag = props.get('mag')
            if mag is None or mag < min_mag:
                continue
                
            geom = s['geometry']['coordinates']
            x, y = coords_to_pixels(geom[0], geom[1])
            color, radius = get_color_and_size(mag)
            
            # Dibujar el círculo del sismo
            map_canvas.shapes.append(cv.Circle(x, y, radius, paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL)))
            
            # Resaltar si el sismo está seleccionado
            if state["selected_eq"] and state["selected_eq"]['id'] == s['id']:
                map_canvas.shapes.append(
                    cv.Circle(x, y, radius + 6, paint=ft.Paint(color="white", style=ft.PaintingStyle.STROKE, stroke_width=2))
                )
        
        map_canvas.update()

    def select_sismo(s):
        """Evento al hacer clic en un sismo de la lista: Actualiza los detalles y redibuja el mapa."""
        state["selected_eq"] = s
        props = s['properties']
        geom = s['geometry']['coordinates']
        mag = props.get('mag')
        place = props.get('place', 'Desconocido')
        depth = geom[2]
        
        # Calcular distancia respecto a San Salvador
        dist_km = haversine(SS_LAT, SS_LON, geom[1], geom[0])
        color, _ = get_color_and_size(mag)
        
        # Actualizar tarjeta de detalles
        lbl_detail_mag.value = f"Magnitud: {mag} Richter"
        lbl_detail_mag.color = color
        lbl_detail_place.value = f"Lugar: {place}"
        lbl_detail_depth.value = f"Profundidad: {depth:.1f} km"
        lbl_detail_dist.value = f"Distancia a SS: {dist_km:.1f} km"
        
        detail_card.update()
        draw_map()

    def refresh_ui(e=None):
        """Reconstruye la lista lateral basándose en el filtro de magnitud y redibuja el mapa."""
        lista_sismos.controls.clear()
        try:
            min_mag = float(mag_filter.value) if mag_filter.value else 0.0
        except ValueError:
            min_mag = 0.0
        
        for s in state["sismos_data"]:
            props = s['properties']
            mag = props.get('mag')
            
            if mag is None or mag < min_mag:
                continue
                
            color, _ = get_color_and_size(mag)
            place = props.get('place', 'Desconocido')
            time_dt = datetime.fromtimestamp(props.get('time', 0) / 1000.0)
            time_str = time_dt.strftime("%H:%M:%S")
            
            # Crear ítem para la lista
            item = ft.Container(
                content=ft.Column([
                    ft.Text(f"{mag}M - {time_str}", color=color, weight="bold"),
                    ft.Text(place, size=12)
                ], spacing=2),
                padding=10,
                bgcolor="#334155",
                border_radius=8,
                on_click=lambda e, eq=s: select_sismo(eq)
            )
            lista_sismos.controls.append(item)
            
        lista_sismos.update()
        draw_map()

    # Vincular evento de cambio en el filtro a la actualización de la UI
    mag_filter.on_change = refresh_ui

    # -------------------------------------------------------------
    # PULL DE DATOS Y EXPORTAR
    # -------------------------------------------------------------
    def fetch_data_task():
        """Función ejecutada en segundo plano (Threading) para obtener datos de la API sin bloquear la UI."""
        btn_refresh.disabled = True
        btn_refresh.text = "Cargando..."
        lbl_status.value = "⏳ Conectando con servidor del USGS..."
        lbl_status.color = "yellow"
        page.update()
        
        try:
            # Petición a la API del USGS
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Filtrar sismos que ocurrieron dentro de los límites de Centroamérica
            filtered = []
            for feature in data.get('features', []):
                coords = feature['geometry']['coordinates']
                lon, lat = coords[0], coords[1]
                if LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX:
                    filtered.append(feature)
                    
            # Guardar caché
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(filtered, f)
                
            # Actualizar estado e UI
            state["sismos_data"] = filtered
            now = datetime.now().strftime("%H:%M:%S")
            lbl_status.value = f"✅ Actualizado a las {now} ({len(filtered)} sismos)"
            lbl_status.color = COLOR_VERDE
            
            refresh_ui()
            mostrar_notificacion(f"✅ ¡Se descargaron {len(filtered)} sismos con éxito!", "#15803D")
            
        except Exception as err:
            # Fallback en caso de no haber internet
            lbl_status.value = "⚠️ Sin internet: Cargando caché local"
            lbl_status.color = COLOR_AMBAR
            load_cache()
            mostrar_notificacion("⚠️ No se pudo conectar a internet. Usando caché.", "#B45309")
        finally:
            # Restaurar el botón independientemente del resultado
            btn_refresh.disabled = False
            btn_refresh.text = "🔄 Actualizar"
            page.update()

    def trigger_fetch(e=None):
        """Inicia el hilo para la descarga de datos para evitar que la app se congele."""
        mostrar_notificacion("🔄 Solicitando datos a la API...", "#1E293B")
        threading.Thread(target=fetch_data_task, daemon=True).start()

    def load_cache():
        """Carga los sismos desde el archivo local en caso de que exista."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    sismos = json.load(f)
                    state["sismos_data"] = sismos
                refresh_ui()
            except Exception:
                pass

    def export_csv(e):
        """Exporta los sismos actualmente mostrados a un archivo CSV local."""
        if not state["sismos_data"]:
            mostrar_notificacion("❌ No hay sismos en la lista para exportar.", "#B91C1C")
            return
            
        filename = "sismos_filtrados.csv"
        try:
            min_mag = float(mag_filter.value) if mag_filter.value else 0.0
        except ValueError:
            min_mag = 0.0
        
        exportados = 0
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Encabezados
                writer.writerow(["ID", "Fecha/Hora", "Magnitud", "Lugar", "Profundidad (km)", "Distancia a SS (km)", "Latitud", "Longitud"])
                
                # Filas
                for s in state["sismos_data"]:
                    props = s['properties']
                    geom = s['geometry']['coordinates']
                    mag = props.get('mag')
                    
                    # Respetar el filtro de magnitud actual al exportar
                    if mag is None or mag < min_mag:
                        continue
                    
                    time_dt = datetime.fromtimestamp(props.get('time', 0) / 1000.0)
                    dist = haversine(SS_LAT, SS_LON, geom[1], geom[0])
                    
                    writer.writerow([
                        s['id'],
                        time_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        mag,
                        props.get('place', 'Desconocido'),
                        f"{geom[2]:.1f}",
                        f"{dist:.1f}",
                        geom[1],
                        geom[0]
                    ])
                    exportados += 1
                    
            ruta_completa = os.path.abspath(filename)
            lbl_status.value = f"💾 CSV Guardado ({exportados} filas)"
            lbl_status.color = COLOR_VERDE
            lbl_status.update()
            
            mostrar_notificacion(f"📁 Guardado ({exportados} sismos) en:\n{ruta_completa}", "#0D9488")
            
        except Exception as ex:
            mostrar_notificacion(f"❌ Error al guardar archivo: {ex}", "#B91C1C")

    def on_map_resize(e: cv.CanvasResizeEvent):
        """Actualiza las dimensiones del lienzo del mapa si la ventana cambia de tamaño."""
        state["map_width"] = e.width
        state["map_height"] = e.height
        draw_map()

    # Asignar evento de redimensionado al canvas
    map_canvas.on_resize = on_map_resize

    # -------------------------------------------------------------
    # MONTAJE DE LA INTERFAZ
    # -------------------------------------------------------------
    btn_refresh = ft.ElevatedButton("🔄 Actualizar", on_click=trigger_fetch)
    btn_export = ft.ElevatedButton("💾 Exportar CSV", on_click=export_csv, color="white", bgcolor="#334155")
    
    # Barra superior con título y controles
    top_bar = ft.Row([
        ft.Text("🌎 SISMÓGRAFO SV", size=20, weight="bold", color="cyan"),
        ft.Container(width=10),
        mag_filter,
        btn_refresh,
        btn_export,
        ft.Container(expand=True), # Spacer
        lbl_status
    ], alignment="start", vertical_alignment="center")
    
    # Layout principal que une el panel izquierdo y el mapa
    main_layout = ft.Row([left_panel, map_container], expand=True)
    
    # Agregar todo a la ventana principal
    page.add(top_bar, ft.Divider(), main_layout)
    
    # Ejecución inicial
    load_cache()
    trigger_fetch()


if __name__ == "__main__":
    # Inicia la aplicación de Flet
    ft.app(target=main)