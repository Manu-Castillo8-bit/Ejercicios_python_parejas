"""
Misión 05: Monitor Sismológico y Sismógrafo en Tiempo Real
Asignatura: Desarrollo de Software - INDEL 3DS
Tecnología: Python 3 + Tkinter (Librería nativa)
"""

import os
import csv
import math
import random
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# -------------------------------------------------------------
# PALETA DE COLORES (Estilo Neón / INDEL Dark Mode)
# -------------------------------------------------------------
COLOR_BG = "#06060C"          # Fondo de ventana principal
COLOR_SURFACE = "#10101C"     # Contenedores y paneles
COLOR_SURFACE2 = "#161626"    # Inputs y tarjetas internas
COLOR_LINE = "#242438"        # Líneas de cuadrícula y bordes
COLOR_TEXT = "#E9E9F6"        # Texto primario
COLOR_DIM = "#8B8BA9"         # Texto secundario / leyendas

# Colores de Alerta Sísmica
COLOR_VERDE = "#39FF88"       # Reposo / Sismo Micro (< 3.0)
COLOR_AMBAR = "#FFB300"       # Sismo Leve (3.0 - 4.9)
COLOR_NARANJA = "#FF7700"     # Sismo Moderado (5.0 - 6.9)
COLOR_ROJO = "#FF2E97"        # Sismo Fuerte / Severo (>= 7.0)
COLOR_CIAN = "#00F0FF"        # Trazo del sismógrafo


class SismografoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Misión 05: Monitor Sismológico en Tiempo Real · INDEL 3DS")
        self.root.geometry("1000x720")
        self.root.minsize(850, 600)
        self.root.configure(bg=COLOR_BG)

        # Archivo de persistencia de datos
        self.csv_filename = "registro_sismos.csv"

        # Variables de simulación de onda física
        self.canvas_width = 960
        self.canvas_height = 180
        self.wave_points = [self.canvas_height // 2] * (self.canvas_width // 2)
        
        # Parámetros de perturbación sísmica
        self.current_amplitude = 1.5  # Amplitud base (microtremores ambientales)
        self.decay_factor = 0.985      # Amortiguamiento físico de la onda
        self.wave_frequency = 0.35
        self.time_step = 0

        # Lista interna de sismos cargados
        self.sismos_registrados = []

        self.setup_styles()
        self.build_ui()
        self.load_csv_data()
        self.update_statistics()

        # Iniciar ciclo de animación continua (30 ms ~ 33 FPS)
        self.animate_seismograph()

    def setup_styles(self):
        """Configuración de estilos para ttk (Treeview, Scrollbars, Combobox)."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=COLOR_SURFACE,
            foreground=COLOR_TEXT,
            fieldbackground=COLOR_SURFACE,
            bordercolor=COLOR_LINE,
            font=("Consolas", 10),
            rowheight=26
        )
        style.configure(
            "Treeview.Heading",
            background=COLOR_SURFACE2,
            foreground=COLOR_CIAN,
            font=("Consolas", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview", background=[("selected", COLOR_SURFACE2)], foreground=[("selected", COLOR_VERDE)])

        style.configure(
            "TCombobox",
            fieldbackground=COLOR_SURFACE2,
            background=COLOR_SURFACE2,
            foreground=COLOR_TEXT,
            arrowcolor=COLOR_CIAN
        )

    def build_ui(self):
        # 1. ENCABEZADO SUPERIOR
        header = tk.Frame(self.root, bg=COLOR_SURFACE, height=55, padx=20)
        header.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(
            header,
            text="ESTACIÓN SISMOLÓGICA DIGITAL",
            font=("Consolas", 15, "bold"),
            fg=COLOR_CIAN,
            bg=COLOR_SURFACE
        )
        title_lbl.pack(side=tk.LEFT, pady=12)

        self.lbl_status_banner = tk.Label(
            header,
            text="ESTADO: REPOSO",
            font=("Consolas", 11, "bold"),
            fg=COLOR_VERDE,
            bg=COLOR_SURFACE,
            padx=12,
            pady=4
        )
        self.lbl_status_banner.pack(side=tk.RIGHT, pady=10)

        # Separador visual
        tk.Frame(self.root, bg=COLOR_LINE, height=1).pack(fill=tk.X)

        # 2. CONTENEDOR PRINCIPAL
        main_container = tk.Frame(self.root, bg=COLOR_BG, padx=16, pady=12)
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- ÁREA DEL SISMÓGRAFO (Canvas de oscilaciones) ---
        canvas_frame = tk.Frame(main_container, bg=COLOR_SURFACE, bd=1, relief=tk.SOLID)
        canvas_frame.pack(fill=tk.X, pady=(0, 10))

        canvas_header = tk.Frame(canvas_frame, bg=COLOR_SURFACE, padx=10, pady=4)
        canvas_header.pack(fill=tk.X)
        tk.Label(
            canvas_header,
            text="TRAZA SISMOGRÁFICA EN VIVO (EJE VERTICAL Z)",
            font=("Consolas", 9, "bold"),
            fg=COLOR_DIM,
            bg=COLOR_SURFACE
        ).pack(side=tk.LEFT)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg=COLOR_BG,
            height=self.canvas_height,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.X, padx=2, pady=(0, 2))

        # --- PANEL MEDIO: FORMULARIO + TARJETAS DE ESTADÍSTICAS ---
        middle_frame = tk.Frame(main_container, bg=COLOR_BG)
        middle_frame.pack(fill=tk.X, pady=(0, 10))

        # Formulario de Registro / Simulación
        form_frame = tk.LabelFrame(
            middle_frame,
            text=" Simulación y Registro de Eventos ",
            font=("Consolas", 10, "bold"),
            fg=COLOR_CIAN,
            bg=COLOR_SURFACE,
            padx=14,
            pady=10,
            bd=1
        )
        form_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Fila 1 de inputs: Magnitud y Profundidad
        row1 = tk.Frame(form_frame, bg=COLOR_SURFACE)
        row1.pack(fill=tk.X, pady=3)

        tk.Label(row1, text="Magnitud (Richter):", font=("Consolas", 10), fg=COLOR_TEXT, bg=COLOR_SURFACE).pack(side=tk.LEFT)
        self.entry_magnitud = tk.Entry(row1, width=7, font=("Consolas", 10), bg=COLOR_SURFACE2, fg=COLOR_CIAN, insertbackground=COLOR_CIAN, bd=2)
        self.entry_magnitud.pack(side=tk.LEFT, padx=(6, 16))
        self.entry_magnitud.insert(0, "4.5")

        tk.Label(row1, text="Profundidad (km):", font=("Consolas", 10), fg=COLOR_TEXT, bg=COLOR_SURFACE).pack(side=tk.LEFT)
        self.entry_profundidad = tk.Entry(row1, width=7, font=("Consolas", 10), bg=COLOR_SURFACE2, fg=COLOR_CIAN, insertbackground=COLOR_CIAN, bd=2)
        self.entry_profundidad.pack(side=tk.LEFT, padx=6)
        self.entry_profundidad.insert(0, "25")

        # Fila 2 de inputs: Epicentro
        row2 = tk.Frame(form_frame, bg=COLOR_SURFACE)
        row2.pack(fill=tk.X, pady=6)

        tk.Label(row2, text="Epicentro / Zona:", font=("Consolas", 10), fg=COLOR_TEXT, bg=COLOR_SURFACE).pack(side=tk.LEFT)
        self.combo_epicentro = ttk.Combobox(
            row2,
            values=[
                "Costa de La Libertad",
                "San Salvador (Falla Local)",
                "Golfo de Fonseca",
                "Ahuachapán",
                "Costa de Sonsonate",
                "San Miguel / Volcán Chaparrastique"
            ],
            width=28,
            font=("Consolas", 10)
        )
        self.combo_epicentro.current(0)
        self.combo_epicentro.pack(side=tk.LEFT, padx=(6, 0))

        # Botones de Acción
        btn_frame = tk.Frame(form_frame, bg=COLOR_SURFACE)
        btn_frame.pack(fill=tk.X, pady=(6, 0))

        btn_simular = tk.Button(
            btn_frame,
            text="⚡ REGISTRAR SISMO",
            font=("Consolas", 10, "bold"),
            bg=COLOR_ROJO,
            fg="#FFFFFF",
            activebackground="#FF55A0",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.handle_manual_event
        )
        btn_simular.pack(side=tk.LEFT, padx=(0, 6))

        btn_random = tk.Button(
            btn_frame,
            text="🎲 SISMO ALEATORIO",
            font=("Consolas", 10, "bold"),
            bg=COLOR_SURFACE2,
            fg=COLOR_VERDE,
            activebackground=COLOR_LINE,
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.simulate_random_event
        )
        btn_random.pack(side=tk.LEFT)

        # Panel de Métricas / Tarjetas Rápidas
        stats_frame = tk.LabelFrame(
            middle_frame,
            text=" Estadísticas de Estación ",
            font=("Consolas", 10, "bold"),
            fg=COLOR_AMBAR,
            bg=COLOR_SURFACE,
            padx=14,
            pady=8,
            bd=1
        )
        stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))

        self.lbl_total_sismos = tk.Label(stats_frame, text="Total Eventos: 0", font=("Consolas", 10), fg=COLOR_TEXT, bg=COLOR_SURFACE)
        self.lbl_total_sismos.pack(anchor="w", pady=2)

        self.lbl_max_mag = tk.Label(stats_frame, text="Magnitud Máx: 0.0 Richter", font=("Consolas", 10), fg=COLOR_ROJO, bg=COLOR_SURFACE)
        self.lbl_max_mag.pack(anchor="w", pady=2)

        self.lbl_avg_mag = tk.Label(stats_frame, text="Promedio: 0.0 Richter", font=("Consolas", 10), fg=COLOR_AMBAR, bg=COLOR_SURFACE)
        self.lbl_avg_mag.pack(anchor="w", pady=2)

        # --- PANEL INFERIOR: HISTORIAL DE REGISTROS (Treeview) ---
        table_frame = tk.Frame(main_container, bg=COLOR_SURFACE)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("fecha", "magnitud", "profundidad", "epicentro", "alerta")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("fecha", text="FECHA Y HORA")
        self.tree.heading("magnitud", text="MAGNITUD")
        self.tree.heading("profundidad", text="PROFUNDIDAD")
        self.tree.heading("epicentro", text="EPICENTRO / UBICACIÓN")
        self.tree.heading("alerta", text="NIVEL DE ALERTA")

        self.tree.column("fecha", width=160, anchor="center")
        self.tree.column("magnitud", width=110, anchor="center")
        self.tree.column("profundidad", width=120, anchor="center")
        self.tree.column("epicentro", width=260, anchor="w")
        self.tree.column("alerta", width=150, anchor="center")

        tree_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def trigger_wave(self, magnitude: float):
        """Dispara la simulación física de la perturbación en el sismógrafo."""
        # Escala visual proporcional a la magnitud
        self.current_amplitude = min(120, (magnitude ** 2.2) * 2.2)

        # Actualizar banner de estado según la escala Richter
        if magnitude < 3.0:
            alerta = "MICRO (SIN PELIGRO)"
            color = COLOR_VERDE
        elif magnitude < 5.0:
            alerta = "LEVE (PERCEPTIBLE)"
            color = COLOR_AMBAR
        elif magnitude < 7.0:
            alerta = "MODERADO (ALERTA)"
            color = COLOR_NARANJA
        else:
            alerta = "¡PELIGRO! SISMO MAYOR"
            color = COLOR_ROJO

        self.lbl_status_banner.config(text=f"ESTADO: {alerta} - {magnitude} M", fg=color)

    def animate_seismograph(self):
        """Bucle continuo para graficar la onda sísmica con física senoidal amortiguada."""
        self.time_step += 0.25
        center_y = self.canvas_height // 2

        # Ruido de micro-tremores normales
        noise = random.uniform(-1.5, 1.5)

        # Onda armónica si hay energía activa
        if self.current_amplitude > 1.8:
            wave_val = math.sin(self.time_step * self.wave_frequency) * self.current_amplitude
            wave_val += math.cos(self.time_step * 1.5) * (self.current_amplitude * 0.3)
            self.current_amplitude *= self.decay_factor
        else:
            wave_val = 0
            self.current_amplitude = 1.5
            if "REPOSO" not in self.lbl_status_banner.cget("text"):
                self.lbl_status_banner.config(text="ESTADO: REPOSO (MONITOREANDO)", fg=COLOR_VERDE)

        new_y = center_y + wave_val + noise
        self.wave_points.pop(0)
        self.wave_points.append(new_y)

        # Redibujar canvas
        self.canvas.delete("all")

        # Dibujar cuadrícula de fondo
        for y in range(0, self.canvas_height, 30):
            self.canvas.create_line(0, y, self.canvas_width, y, fill=COLOR_LINE, dash=(2, 4))
        self.canvas.create_line(0, center_y, self.canvas_width, center_y, fill=COLOR_LINE, width=1)

        # Trazar línea continua de la onda sísmica
        step_x = self.canvas_width / len(self.wave_points)
        coords = []
        for i, pt in enumerate(self.wave_points):
            coords.extend([i * step_x, pt])

        # Color del trazo: cian en reposo, rojo neón si la amplitud es alta
        line_color = COLOR_ROJO if self.current_amplitude > 15 else COLOR_CIAN
        self.canvas.create_line(coords, fill=line_color, width=1.8, smooth=True)

        # Reprogramar siguiente frame (30 milisegundos)
        self.root.after(30, self.animate_seismograph)

    def register_event(self, magnitude: float, depth: float, epicenter: str):
        """Almacena el evento, lo persiste en CSV y actualiza la interfaz."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Clasificación por nivel de alerta
        if magnitude < 3.0:
            nivel = "Micro (<3.0)"
        elif magnitude < 5.0:
            nivel = "Leve (3.0-4.9)"
        elif magnitude < 7.0:
            nivel = "Moderado (5.0-6.9)"
        else:
            nivel = "Severo (>=7.0)"

        record = {
            "fecha": timestamp,
            "magnitud": f"{magnitude:.1f}",
            "profundidad": f"{depth:.1f} km",
            "epicentro": epicenter,
            "alerta": nivel
        }

        # Guardar en memoria y en la tabla (arriba de primero)
        self.sismos_registrados.insert(0, record)
        self.tree.insert("", 0, values=(record["fecha"], f"{record['magnitud']} Richter", record["profundidad"], record["epicentro"], record["alerta"]))

        # Guardar en archivo CSV
        self.save_record_to_csv(record)

        # Disparar oscilación en el gráfico
        self.trigger_wave(magnitude)
        self.update_statistics()

    def handle_manual_event(self):
        """Valida y procesa los datos ingresados en el formulario."""
        try:
            mag = float(self.entry_magnitud.get().strip())
            prof = float(self.entry_profundidad.get().strip())
            epicentro = self.combo_epicentro.get().strip()

            if not (0.1 <= mag <= 10.0):
                messagebox.showerror("Error de Rango", "La magnitud debe estar entre 0.1 y 10.0 en escala Richter.")
                return

            if prof < 0:
                messagebox.showerror("Error de Valor", "La profundidad no puede ser negativa.")
                return

            if not epicentro:
                messagebox.showerror("Campo Vacío", "Por favor selecciona o escribe una ubicación.")
                return

            self.register_event(mag, prof, epicentro)

        except ValueError:
            messagebox.showerror("Entrada Inválida", "Ingresa valores numéricos válidos para Magnitud y Profundidad.")

    def simulate_random_event(self):
        """Genera un sismo aleatorio con valores verosímiles."""
        # Distribución ponderada: los sismos pequeños son más frecuentes
        mag = round(random.choices(
            [random.uniform(1.5, 3.2), random.uniform(3.3, 5.2), random.uniform(5.3, 7.8)],
            weights=[0.60, 0.30, 0.10]
        )[0], 1)

        prof = round(random.uniform(5.0, 110.0), 1)
        epicentro = random.choice(self.combo_epicentro["values"])

        self.entry_magnitud.delete(0, tk.END)
        self.entry_magnitud.insert(0, str(mag))

        self.entry_profundidad.delete(0, tk.END)
        self.entry_profundidad.insert(0, str(prof))

        self.combo_epicentro.set(epicentro)

        self.register_event(mag, prof, epicentro)

    def save_record_to_csv(self, record: dict):
        """Persiste una fila en el archivo CSV."""
        file_exists = os.path.exists(self.csv_filename)
        try:
            with open(self.csv_filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["fecha", "magnitud", "profundidad", "epicentro", "alerta"])
                if not file_exists:
                    writer.writeheader()
                writer.writerow(record)
        except Exception as e:
            print(f"[ERROR] No se pudo guardar en CSV: {e}")

    def load_csv_data(self):
        """Carga el historial previo almacenado en el archivo CSV al iniciar."""
        if not os.path.exists(self.csv_filename):
            return

        try:
            with open(self.csv_filename, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.sismos_registrados.append(row)
                    self.tree.insert("", 0, values=(
                        row["fecha"],
                        f"{row['magnitud']} Richter",
                        row["profundidad"],
                        row["epicentro"],
                        row["alerta"]
                    ))
        except Exception as e:
            print(f"[ERROR] No se pudo leer el archivo CSV: {e}")

    def update_statistics(self):
        """Calcula el total, sismo máximo y promedio de magnitudes."""
        total = len(self.sismos_registrados)
        self.lbl_total_sismos.config(text=f"Total Eventos: {total}")

        if total > 0:
            mags = [float(item["magnitud"].replace("Richter", "").strip()) for item in self.sismos_registrados]
            max_mag = max(mags)
            avg_mag = sum(mags) / total

            self.lbl_max_mag.config(text=f"Magnitud Máx: {max_mag:.1f} Richter")
            self.lbl_avg_mag.config(text=f"Promedio: {avg_mag:.1f} Richter")
        else:
            self.lbl_max_mag.config(text="Magnitud Máx: 0.0 Richter")
            self.lbl_avg_mag.config(text="Promedio: 0.0 Richter")


if __name__ == "__main__":
    root_window = tk.Tk()
    app = SismografoApp(root_window)
    root_window.mainloop()