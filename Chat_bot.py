"""
Misión 04: ChatBot Asistente con Detección de Intenciones
Asignatura: Desarrollo de Software - INDEL 3DS
Tecnología: Python 3 + Tkinter (Sin librerías externas)
"""

import os
import re
import random
import unicodedata
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox

# -------------------------------------------------------------
# PALETA DE COLORES (Estilo INDEL Dark / Neón)
# -------------------------------------------------------------
COLOR_BG = "#06060C"          # Fondo principal
COLOR_SURFACE = "#10101C"     # Fondo de tarjetas y paneles
COLOR_SURFACE2 = "#161626"    # Fondo de caja de texto
COLOR_LINE = "#242438"        # Bordes y separadores
COLOR_TEXT = "#E9E9F6"        # Texto general
COLOR_USER = "#00F0FF"        # Texto del usuario (Cian neón)
COLOR_BOT = "#39FF88"         # Texto del bot (Verde neón)
COLOR_SYSTEM = "#FFB300"      # Mensajes del sistema (Ámbar)
COLOR_DIM = "#8B8BA9"         # Texto secundario


class ChatBotBrain:
    """
    Cerebro del Asistente:
    Maneja el estado (memoria del usuario), normalización y el motor de intenciones.
    """
    def __init__(self):
        self.user_name = None  # Memoria en sesión para recordar el nombre

        # Definición de más de 10 intenciones con sus palabras clave y respuestas
        self.intents = {
            "saludo": {
                "keywords": ["hola", "buenos", "dias", "tardes", "noches", "que tal", "saludos", "hey"],
                "responses": [
                    "¡Hola! ¿En qué puedo ayudarte hoy?",
                    "¡Qué gusto saludarte! ¿Qué desafío resolveremos hoy?",
                    "¡Hola, futuro/a desarrollador/a! Estoy listo para tus consultas."
                ]
            },
            "despedida": {
                "keywords": ["adios", "chao", "hasta luego", "nos vemos", "bye", "cerrar", "salir"],
                "responses": [
                    "¡Hasta la próxima! Éxitos en tus líneas de código.",
                    "¡Nos vemos! Recuerda guardar tus cambios y comentar tu código.",
                    "¡Chao! Que tengas una excelente jornada."
                ]
            },
            "estado_animo": {
                "keywords": ["como estas", "que tal estas", "como te va", "como andas", "todo bien"],
                "responses": [
                    "¡Excelente! Mis algoritmos están corriendo al 100%. ¿Y tú cómo estás?",
                    "Todo perfecto por aquí, procesando datos a la velocidad de la luz. ¿Qué tal tú?",
                    "¡Con toda la energía para ayudarte a programar!"
                ]
            },
            "identidad": {
                "keywords": ["quien eres", "tu nombre", "como te llamas", "que eres", "presentate"],
                "responses": [
                    "Soy el Asistente Virtual INDEL 3DS, tu compañero para aprender Python y lógica de software.",
                    "Mi nombre es INDEL-Bot, un asistente programado con un motor de intenciones por puntuación.",
                    "Soy un chatbot creado para demostrar cómo procesar lenguaje natural sin modelos gigantes."
                ]
            },
            "chiste": {
                "keywords": ["chiste", "cuentame un chiste", "hazme reir", "gracioso", "broma"],
                "responses": [
                    "— Papá, ¿por qué el sol sale por el este?\n— Hijo, no toques nada, ¡funciona y no sabemos por qué!",
                    "Hay 10 tipos de personas en el mundo: las que entienden binario y las que no.",
                    "¿Qué le dice un bit a otro? Nos vemos en el bus.",
                    "Un programador va al supermercado y le dicen: «Trae una barra de pan y, si hay huevos, trae diez». Regresó con diez barras de pan."
                ]
            },
            "sobre_indel": {
                "keywords": ["indel", "instituto", "colegio", "3ds", "bachillerato", "software"],
                "responses": [
                    "INDEL forma a los mejores desarrolladores de software en 3DS. ¡El código se defiende, no solo se entrega!",
                    "En el Instituto Nacional de El Puerto (INDEL), 3° Desarrollo de Software construye proyectos reales.",
                    "¡Orgullo INDEL 3DS! Recuerda que 2 retos extra son obligatorios para el puntaje máximo."
                ]
            },
            "sobre_python": {
                "keywords": ["python", "lenguaje", "programar", "tkinter", "flet", "codigo"],
                "responses": [
                    "Python es un lenguaje interpretado, de tipado dinámico y súper versátil: desde scripts de consola hasta IA.",
                    "Python 3.12+ destaca por su legibilidad y soporte para GUI con Tkinter, CustomTkinter y Flet.",
                    "En Python: variables claras en español y un comentario explicando el 'por qué', no el 'qué'."
                ]
            },
            "hora_fecha": {
                "keywords": ["hora", "fecha", "que dia es", "que hora es", "momento", "tiempo"],
                "responses": []  # Respuesta dinámica calculada al momento
            },
            "agradecimiento": {
                "keywords": ["gracias", "muchas gracias", "te lo agradezco", "vales mil", "genial", "excelente"],
                "responses": [
                    "¡Con mucho gusto! Siempre es un placer ayudar.",
                    "¡De nada! Aquí estaré cuando me necesites.",
                    "¡A la orden! A seguir programando con todo."
                ]
            },
            "ayuda": {
                "keywords": ["ayuda", "comandos", "que sabes hacer", "opciones", "menu", "manual"],
                "responses": [
                    "Puedo ayudarte con:\n • Preguntarme la hora y fecha actual\n • Contarte chistes de programadores\n • Guardar y recordar tu nombre (ej: 'Me llamo Carlos')\n • Resolver operaciones matemáticas simples (ej: 'cuanto es 25 * 4')\n • Información sobre INDEL, Python y Desarrollo de Software\n • O simplemente platicar conmigo."
                ]
            }
        }

    def normalize(self, text: str) -> str:
        """
        Paso 1: Normalización de texto.
        Pasa a minúsculas, remueve tildes/acentos y elimina signos de puntuación.
        """
        # Convertir a minúsculas
        text = text.lower()
        # Remover tildes usando descomposición NFD
        text = "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        # Quitar signos de puntuación (dejar solo letras, números y espacios)
        text = re.sub(r"[^\w\s]", " ", text)
        # Reducir espacios múltiples a uno solo
        return " ".join(text.split())

    def evaluate_math(self, text: str) -> str | None:
        """Intenta detectar y resolver operaciones matemáticas básicas (suma, resta, multiplicación, división)."""
        clean_expr = re.sub(r"[^\d+\-*/. ]", "", text)
        # Buscar patrones como "15 + 4" o "100 / 2"
        match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", clean_expr)
        if match:
            n1, op, n2 = float(match.group(1)), match.group(2), float(match.group(3))
            try:
                if op == "+": res = n1 + n2
                elif op == "-": res = n1 - n2
                elif op == "*": res = n1 * n2
                elif op == "/":
                    if n2 == 0: return "No se puede dividir entre cero."
                    res = n1 / n2
                # Formatear si es entero exacto
                res_str = f"{res:.2f}".rstrip("0").rstrip(".")
                return f"El resultado de {match.group(0).strip()} es: {res_str}"
            except Exception:
                return None
        return None

    def detect_name(self, raw_text: str, norm_text: str) -> str | None:
        """Detecta si el usuario está diciendo su nombre o preguntando por él."""
        # Detectar asignación de nombre: "me llamo X", "mi nombre es X", "soy X"
        patterns = [
            r"me llamo\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)",
            r"mi nombre es\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)",
            r"soy\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)"
        ]
        for pat in patterns:
            m = re.search(pat, raw_text, re.IGNORECASE)
            if m:
                found_name = m.group(1).capitalize()
                # Evitar capturar palabras comunes
                if found_name.lower() not in ["un", "una", "el", "la", "estudiante", "programador"]:
                    self.user_name = found_name
                    return f"¡Mucho gusto, {self.user_name}! Me acordaré de tu nombre durante nuestra conversación."

        # Detectar pregunta por su nombre
        if any(k in norm_text for k in ["como me llamo", "sabes mi nombre", "cual es mi nombre", "quien soy"]):
            if self.user_name:
                return f"Te llamas {self.user_name}. ¡Tengo buena memoria!"
            else:
                return "Aún no me has dicho tu nombre. Puedes decirme: 'Me llamo...' y lo recordaré."

        return None

    def get_response(self, raw_input: str) -> str:
        """
        Paso 2, 3 y 4: Puntuar intenciones, decidir ganadora y responder.
        """
        normalized_input = self.normalize(raw_input)
        if not normalized_input:
            return "Parece que no escribiste nada. ¿En qué te puedo ayudar?"

        # 1. Verificar si el usuario interactúa con su nombre
        name_response = self.detect_name(raw_input, normalized_input)
        if name_response:
            return name_response

        # 2. Verificar si es una operación matemática
        math_response = self.evaluate_math(raw_input)
        if math_response:
            return math_response

        # 3. Puntuación de intenciones según palabras clave
        scores = {}
        for intent_name, data in self.intents.items():
            score = 0
            for kw in data["keywords"]:
                norm_kw = self.normalize(kw)
                # Coincidencia por palabra completa o frase exacta
                if re.search(r"\b" + re.escape(norm_kw) + r"\b", normalized_input):
                    score += 1
            scores[intent_name] = score

        # Obtener la intención con el puntaje más alto
        best_intent, max_score = max(scores.items(), key=lambda x: x[1])

        # Si ninguna intención sumó al menos 1 punto -> Mensaje por defecto orientativo
        if max_score < 1:
            return (
                "No logré entender tu mensaje con certeza. 🤔\n"
                "Prueba preguntándome:\n"
                " • '¿Qué hora es?'\n"
                " • 'Cuéntame un chiste'\n"
                " • '¿Qué sabes sobre Python?'\n"
                " • 'Me llamo [tu nombre]' o escribe 'ayuda'."
            )

        # Responder según la intención ganadora
        if best_intent == "hora_fecha":
            now = datetime.now()
            dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                     "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            dia_semana = dias[now.weekday()]
            dia_num = now.day
            mes_nombre = meses[now.month - 1]
            hora_str = now.strftime("%I:%M %p")
            return f"Hoy es {dia_semana} {dia_num} de {mes_nombre} del {now.year} y son las {hora_str}."

        # Elegir una respuesta al azar de la intención ganadora
        return random.choice(self.intents[best_intent]["responses"])


class ChatBotApp:
    """Interfaz gráfica de usuario con Tkinter."""
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Misión 04: ChatBot Asistente · INDEL 3DS")
        self.root.geometry("640x700")
        self.root.minsize(480, 500)
        self.root.configure(bg=COLOR_BG)

        self.brain = ChatBotBrain()
        self.chat_history = []  # Para exportar al cerrar

        self.build_ui()
        self.protocol_setup()

        # Mensaje de bienvenida inicial
        self.display_message("Sistema", "¡Bienvenido/a al Asistente INDEL 3DS! Escribe un mensaje o 'ayuda'.", COLOR_SYSTEM)

    def build_ui(self):
        # Header superior
        header = tk.Frame(self.root, bg=COLOR_SURFACE, height=50, bd=0)
        header.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(
            header,
            text="INDEL CHATBOT ASISTENTE",
            font=("Consolas", 14, "bold"),
            fg=COLOR_BOT,
            bg=COLOR_SURFACE
        )
        title_lbl.pack(side=tk.LEFT, padx=16, pady=12)

        subtitle_lbl = tk.Label(
            header,
            text="3° Software · 3DS 'B'",
            font=("Consolas", 10),
            fg=COLOR_DIM,
            bg=COLOR_SURFACE
        )
        subtitle_lbl.pack(side=tk.RIGHT, padx=16, pady=12)

        # Separador
        sep = tk.Frame(self.root, bg=COLOR_LINE, height=1)
        sep.pack(fill=tk.X)

        # Área de Historial (ScrolledText)
        self.txt_history = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            font=("Consolas", 11),
            insertbackground=COLOR_USER,
            relief=tk.FLAT,
            padx=14,
            pady=14
        )
        self.txt_history.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Configuración de etiquetas de estilo para el texto
        self.txt_history.tag_config("user_tag", foreground=COLOR_USER, font=("Consolas", 11, "bold"))
        self.txt_history.tag_config("bot_tag", foreground=COLOR_BOT, font=("Consolas", 11, "bold"))
        self.txt_history.tag_config("sys_tag", foreground=COLOR_SYSTEM, font=("Consolas", 10, "italic"))
        self.txt_history.tag_config("msg_body", foreground=COLOR_TEXT, font=("Consolas", 11))
        self.txt_history.tag_config("time_tag", foreground=COLOR_DIM, font=("Consolas", 9))

        # Deshabilitar edición directa del historial por el usuario
        self.txt_history.config(state=tk.DISABLED)

        # Área inferior de entrada y botón
        bottom_frame = tk.Frame(self.root, bg=COLOR_SURFACE, padx=12, pady=12)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.entry_message = tk.Entry(
            bottom_frame,
            bg=COLOR_SURFACE2,
            fg=COLOR_TEXT,
            font=("Consolas", 12),
            insertbackground=COLOR_USER,
            relief=tk.FLAT,
            bd=6
        )
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry_message.focus_set()

        # Vinculación de la tecla Enter
        self.entry_message.bind("<Return>", lambda event: self.send_message())

        btn_send = tk.Button(
            bottom_frame,
            text="ENVIAR ➔",
            font=("Consolas", 11, "bold"),
            bg=COLOR_USER,
            fg="#04040A",
            activebackground=COLOR_BOT,
            activeforeground="#04040A",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.send_message
        )
        btn_send.pack(side=tk.RIGHT)

    def protocol_setup(self):
        """Captura el cierre de la ventana para guardar el historial."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def display_message(self, sender: str, message: str, color_tag: str):
        """Inserta un mensaje en el ScrolledText habilitando y volviendo a deshabilitar."""
        self.txt_history.config(state=tk.NORMAL)

        now_str = datetime.now().strftime("%H:%M:%S")

        if sender == "Tú":
            self.txt_history.insert(tk.END, f"[{now_str}] ", "time_tag")
            self.txt_history.insert(tk.END, f"{sender}: ", "user_tag")
            self.txt_history.insert(tk.END, f"{message}\n\n", "msg_body")
        elif sender == "Bot":
            self.txt_history.insert(tk.END, f"[{now_str}] ", "time_tag")
            self.txt_history.insert(tk.END, f"Asistente: ", "bot_tag")
            self.txt_history.insert(tk.END, f"{message}\n\n", "msg_body")
        else:
            self.txt_history.insert(tk.END, f"[{now_str}] * {message} *\n\n", "sys_tag")

        self.txt_history.config(state=tk.DISABLED)
        self.txt_history.see(tk.END)  # Auto-scroll hacia abajo

        # Registrar en la lista de historial para exportación
        self.chat_history.append(f"[{now_str}] {sender}: {message}")

    def send_message(self):
        """Procesa el mensaje del usuario y programa la respuesta con delay no bloqueante."""
        raw_text = self.entry_message.get().strip()
        if not raw_text:
            return

        # Limpiar la caja de entrada
        self.entry_message.delete(0, tk.END)

        # Mostrar mensaje del usuario
        self.display_message("Tú", raw_text, COLOR_USER)

        # Simulación de respuesta natural tras un breve retraso usando after()
        self.root.after(450, lambda: self.bot_reply(raw_text))

    def bot_reply(self, user_text: str):
        """Calcula la respuesta mediante el cerebro y la muestra."""
        response = self.brain.get_response(user_text)
        self.display_message("Bot", response, COLOR_BOT)

    def on_closing(self):
        """Guarda la conversación en un archivo con fecha/hora antes de salir."""
        if len(self.chat_history) > 1:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"historial_chat_{timestamp}.txt"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"=== HISTORIAL DE CHAT · INDEL 3DS ===\n")
                    f.write(f"Fecha de guardado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 45 + "\n\n")
                    for line in self.chat_history:
                        f.write(line + "\n")
                print(f"[INFO] Historial exportado exitosamente como '{filename}'")
            except Exception as e:
                print(f"[ERROR] No se pudo guardar el archivo de historial: {e}")

        self.root.destroy()


if __name__ == "__main__":
    root_window = tk.Tk()
    app = ChatBotApp(root_window)
    root_window.mainloop()