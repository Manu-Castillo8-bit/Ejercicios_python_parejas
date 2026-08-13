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
API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
CACHE_FILE = "sismos_cache.json"

SS_LAT = 13.69
SS_LON = -89.19
RADIO_TIERRA_KM = 6371

LON_MIN, LON_MAX = -93.0, -82.0
LAT_MIN, LAT_MAX = 7.0, 19.0

COLOR_VERDE = "#39FF88"
COLOR_AMBAR = "#FFB300"
COLOR_MAGENTA = "#FF2E97"
COLOR_BG_MAP = "#0F172A"
COLOR_LINE = "#1E293B"
COLOR_MAPA = "#475569"  # Color para las líneas de la silueta costera y fronteras

# Coordenadas geográficas simplificadas de la silueta de Centroamérica
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
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return RADIO_TIERRA_KM * c


def get_color_and_size(mag):
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
    page.title = "SISMÓGRAFO SV · Monitor en Tiempo Real"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 1200
    page.window_height = 800

    state = {
        "sismos_data": [],
        "map_width": 700,
        "map_height": 600,
        "selected_eq": None
    }

    def mostrar_notificacion(mensaje, color_bg="#334155"):
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
    mag_filter = ft.Dropdown(
        options=[ft.dropdown.Option(x) for x in ["0.0", "2.0", "3.0", "4.0", "4.5", "5.0"]],
        value="0.0",
        width=100,
        label="Mag Mín"
    )
    
    lbl_status = ft.Text("Estado: Listo", color="grey", size=13)
    
    lbl_detail_mag = ft.Text("Magnitud: --", weight="bold", size=16)
    lbl_detail_place = ft.Text("Lugar: Selecciona un sismo de la lista", width=280)
    lbl_detail_depth = ft.Text("Profundidad: --")
    lbl_detail_dist = ft.Text("Distancia a SS: --")
    
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
    
    lista_sismos = ft.ListView(expand=True, spacing=5, auto_scroll=False)
    
    left_panel = ft.Column([
        detail_card,
        ft.Text("ÚLTIMAS 24 HORAS (Centroamérica)", weight="bold"),
        ft.Container(content=lista_sismos, expand=True)
    ], width=320)

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
        x_prop = (lon - LON_MIN) / (LON_MAX - LON_MIN)
        x = x_prop * state["map_width"]
        y_prop = (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)
        y = state["map_height"] - (y_prop * state["map_height"])
        return x, y

    def draw_map():
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

        # 3. Ubicación de San Salvador
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
            
            map_canvas.shapes.append(cv.Circle(x, y, radius, paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL)))
            
            if state["selected_eq"] and state["selected_eq"]['id'] == s['id']:
                map_canvas.shapes.append(
                    cv.Circle(x, y, radius + 6, paint=ft.Paint(color="white", style=ft.PaintingStyle.STROKE, stroke_width=2))
                )
        
        map_canvas.update()

    def select_sismo(s):
        state["selected_eq"] = s
        props = s['properties']
        geom = s['geometry']['coordinates']
        mag = props.get('mag')
        place = props.get('place', 'Desconocido')
        depth = geom[2]
        
        dist_km = haversine(SS_LAT, SS_LON, geom[1], geom[0])
        color, _ = get_color_and_size(mag)
        
        lbl_detail_mag.value = f"Magnitud: {mag} Richter"
        lbl_detail_mag.color = color
        lbl_detail_place.value = f"Lugar: {place}"
        lbl_detail_depth.value = f"Profundidad: {depth:.1f} km"
        lbl_detail_dist.value = f"Distancia a SS: {dist_km:.1f} km"
        
        detail_card.update()
        draw_map()

    def refresh_ui(e=None):
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

    mag_filter.on_change = refresh_ui

    # -------------------------------------------------------------
    # PULL DE DATOS Y EXPORTAR
    # -------------------------------------------------------------
    def fetch_data_task():
        btn_refresh.disabled = True
        btn_refresh.text = "Cargando..."
        lbl_status.value = "⏳ Conectando con servidor del USGS..."
        lbl_status.color = "yellow"
        page.update()
        
        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            filtered = []
            for feature in data.get('features', []):
                coords = feature['geometry']['coordinates']
                lon, lat = coords[0], coords[1]
                if LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX:
                    filtered.append(feature)
                    
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(filtered, f)
                
            state["sismos_data"] = filtered
            now = datetime.now().strftime("%H:%M:%S")
            lbl_status.value = f"✅ Actualizado a las {now} ({len(filtered)} sismos)"
            lbl_status.color = COLOR_VERDE
            refresh_ui()
            mostrar_notificacion(f"✅ ¡Se descargaron {len(filtered)} sismos con éxito!", "#15803D")
            
        except Exception as err:
            lbl_status.value = "⚠️ Sin internet: Cargando caché local"
            lbl_status.color = COLOR_AMBAR
            load_cache()
            mostrar_notificacion("⚠️ No se pudo conectar a internet. Usando caché.", "#B45309")
        finally:
            btn_refresh.disabled = False
            btn_refresh.text = "🔄 Actualizar"
            page.update()

    def trigger_fetch(e=None):
        mostrar_notificacion("🔄 Solicitando datos a la API...", "#1E293B")
        threading.Thread(target=fetch_data_task, daemon=True).start()

    def load_cache():
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    sismos = json.load(f)
                    state["sismos_data"] = sismos
                refresh_ui()
            except Exception:
                pass

    def export_csv(e):
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
                writer.writerow(["ID", "Fecha/Hora", "Magnitud", "Lugar", "Profundidad (km)", "Distancia a SS (km)", "Latitud", "Longitud"])
                
                for s in state["sismos_data"]:
                    props = s['properties']
                    geom = s['geometry']['coordinates']
                    mag = props.get('mag')
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
        state["map_width"] = e.width
        state["map_height"] = e.height
        draw_map()

    map_canvas.on_resize = on_map_resize

    # -------------------------------------------------------------
    # MONTAJE DE LA INTERFAZ
    # -------------------------------------------------------------
    btn_refresh = ft.ElevatedButton("🔄 Actualizar", on_click=trigger_fetch)
    btn_export = ft.ElevatedButton("💾 Exportar CSV", on_click=export_csv, color="white", bgcolor="#334155")
    
    top_bar = ft.Row([
        ft.Text("🌎 SISMÓGRAFO SV", size=20, weight="bold", color="cyan"),
        ft.Container(width=10),
        mag_filter,
        btn_refresh,
        btn_export,
        ft.Container(expand=True),
        lbl_status
    ], alignment="start", vertical_alignment="center")
    
    main_layout = ft.Row([left_panel, map_container], expand=True)
    page.add(top_bar, ft.Divider(), main_layout)
    
    load_cache()
    trigger_fetch()


if __name__ == "__main__":
    ft.app(target=main)