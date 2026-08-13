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

        # --- MODO PROFE ---
        self.modo_profe_activo = False
        
        # Banco de preguntas frecuentes
        self.faq_profe = {
            "que es python": "Python es un lenguaje de programación de alto nivel, interpretado y muy popular por ser fácil de leer y escribir.",
            "que es una libreria": "Una librería (o biblioteca) es un conjunto de código preescrito que puedes reutilizar para no tener que programar todo desde cero.",
            "que es flet": "Flet es un framework que permite crear aplicaciones web, de escritorio y móviles interactivas usando solo Python (está basado en Flutter).",
            "venv": "Un .venv (entorno virtual) es una carpeta aislada para tu proyecto donde instalas librerías sin afectar al resto de proyectos en tu computadora.",
            "que es una variable": "Una variable es un espacio en la memoria de la computadora donde guardamos un dato que puede cambiar durante la ejecución del programa.",
            "que es un string": "Un string (o cadena de texto) es un tipo de dato que representa texto. En Python se escribe entre comillas simples o dobles.",
            "que es un int": "Un 'int' (entero) es un tipo de dato numérico que representa números enteros, sin parte decimal (ej: 5, -10, 42).",
            "que es un float": "Un 'float' (flotante) es un tipo de dato numérico que representa números con decimales (ej: 3.14, -0.5).",
            "que es un booleano": "Un booleano es un tipo de dato que solo puede tener dos valores: True (Verdadero) o False (Falso).",
            "que es una lista": "Una lista es una colección ordenada y modificable de elementos. En Python se escriben entre corchetes [ ].",
            "que es un diccionario": "Un diccionario es una colección de datos en formato 'clave: valor'. Se escriben entre llaves { }.",
            "que es un bucle": "Un bucle (o ciclo) es una estructura que repite un bloque de código varias veces mientras se cumpla una condición.",
            "que es un for": "El bucle 'for' se usa para iterar sobre una secuencia (como una lista o un string) un número determinado de veces.",
            "que es un while": "El bucle 'while' repite un bloque de código mientras una condición siga siendo verdadera.",
            "que es un if": "La sentencia 'if' se usa para tomar decisiones: si una condición es verdadera, se ejecuta un bloque de código.",
            "que es un else": "El 'else' acompaña al 'if' y se ejecuta cuando la condición del 'if' es falsa.",
            "que es un elif": "El 'elif' (else if) permite evaluar múltiples condiciones en cadena si la primera (if) fue falsa.",
            "que es una funcion": "Una función es un bloque de código reutilizable que realiza una tarea específica y solo se ejecuta cuando es llamada.",
            "que es print": "La función print() se utiliza para mostrar texto o variables en la consola.",
            "que es indentacion": "La indentación son los espacios al inicio de una línea de código. En Python es obligatoria para definir bloques de código (como dentro de un if o una función).",
            "que es un comentario": "Un comentario es una nota en el código que el programa ignora. Se usa para explicar qué hace el código. En Python inician con #.",
            "que es la sintaxis": "La sintaxis es el conjunto de reglas que definen cómo se debe escribir el código para que la computadora lo entienda.",
            "que es un modulo": "Un módulo es un archivo que contiene código Python (funciones, variables, clases) que puedes importar y usar en otros archivos.",
            "que es un ide": "Un IDE (Entorno de Desarrollo Integrado) es un programa como VS Code o PyCharm que nos da herramientas para escribir, probar y corregir código más fácil."
        }

        # --- INICIO AGREGADO: PALABRAS CLAVE Y RESPUESTAS DE ÁNIMO ---
        self.frustration_keywords = [
            "no entiendo", "dificil", "estresado", "estresada", "estres", "frustrado", 
            "frustrada", "no me sale", "no puedo", "imposible", "me rindo", "rendirme", 
            "complicado", "no sirve", "no entiendo nada", "cansado", "cansada", 
            "bloqueado", "bloqueada", "odio esto", "no me funciona", "harto", "harta"
        ]
        
        self.frustration_responses = [
            "Programar puede ser desafiante al principio, pero no te desanimes. 🌿 Tómate un pequeño descanso, respira hondo y verás que al volver todo estará más claro. ¿Qué parte te está costando más?",
            "¡Tranquilo/a! Pasar por momentos de bloqueo o frustración es una parte normal y necesaria de aprender a programar. Todos los desarrolladores pasan por esto. ¡Vas a lograrlo!",
            "Cometer errores y sentirse atascado es justo cómo se aprende. No te rindas, ve paso a paso o prueba activar el 'modo profe' para repasar los conceptos básicos. ¡Aquí estoy para apoyarte!",
            "Sé que puede ser frustrante cuando el código no sale a la primera, pero recuerda que cada error corregido es un aprendizaje nuevo. ¡Tú puedes con esto!"
        ]
        # --- FIN AGREGADO: ÁNIMO ---

        # Definición de intenciones normales
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
                "keywords": ["python", "lenguaje", "programar", "tkinter", "codigo"],
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
                    "Puedo ayudarte con:\n • Preguntarme la hora y fecha actual\n • Contarte chistes de programadores\n • Guardar y recordar tu nombre\n • Resolver operaciones matemáticas simples\n • Activar el 'modo profe' para resolver dudas de clase\n • Información sobre INDEL y Python."
                ]
            }
        }

    def normalize(self, text: str) -> str:
        """
        Paso 1: Normalización de texto.
        Pasa a minúsculas, remueve tildes/acentos y elimina signos de puntuación.
        """
        text = text.lower()
        text = "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        text = re.sub(r"[^\w\s]", " ", text)
        return " ".join(text.split())

    def evaluate_math(self, text: str) -> str | None:
        """Intenta detectar y resolver operaciones matemáticas básicas."""
        clean_expr = re.sub(r"[^\d+\-*/. ]", "", text)
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
                res_str = f"{res:.2f}".rstrip("0").rstrip(".")
                return f"El resultado de {match.group(0).strip()} es: {res_str}"
            except Exception:
                return None
        return None

    def detect_name(self, raw_text: str, norm_text: str) -> str | None:
        """Detecta si el usuario está diciendo su nombre o preguntando por él."""
        patterns = [
            r"me llamo\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)",
            r"mi nombre es\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)",
            r"soy\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)"
        ]
        for pat in patterns:
            m = re.search(pat, raw_text, re.IGNORECASE)
            if m:
                found_name = m.group(1).capitalize()
                if found_name.lower() not in ["un", "una", "el", "la", "estudiante", "programador"]:
                    self.user_name = found_name
                    return f"¡Mucho gusto, {self.user_name}! Me acordaré de tu nombre durante nuestra conversación."

        if any(k in norm_text for k in ["como me llamo", "sabes mi nombre", "cual es mi nombre", "quien soy"]):
            if self.user_name:
                return f"Te llamas {self.user_name}. ¡Tengo buena memoria!"
            else:
                return "Aún no me has dicho tu nombre. Puedes decirme: 'Me llamo...' y lo recordaré."

        return None

    # --- INICIO AGREGADO: MÉTODO PARA DETECTAR FRUSTRACIÓN ---
    def detect_frustration(self, norm_text: str) -> str | None:
        """Detecta si el usuario expresa frustración o desánimo y devuelve una respuesta empática."""
        for kw in self.frustration_keywords:
            norm_kw = self.normalize(kw)
            if norm_kw in norm_text:
                return random.choice(self.frustration_responses)
        return None
    # --- FIN AGREGADO: MÉTODO PARA DETECTAR FRUSTRACIÓN ---

    def get_response(self, raw_input: str) -> str:
        """
        Paso 2, 3 y 4: Puntuar intenciones, decidir ganadora y responder.
        """
        normalized_input = self.normalize(raw_input)
        if not normalized_input:
            return "Parece que no escribiste nada. ¿En qué te puedo ayudar?"

        # LÓGICA DEL MODO PROFE
        if "modo profe" in normalized_input and not self.modo_profe_activo:
            self.modo_profe_activo = True
            return "¡Modo Profe activado! 🧑‍🏫 Hazme tus preguntas del módulo sobre Python, Flet, librerías, etc. (Escribe 'salir profe' para desactivarlo)."
        
        if "salir profe" in normalized_input and self.modo_profe_activo:
            self.modo_profe_activo = False
            return "Modo Profe desactivado. ¡Volvemos al asistente normal! 🤖"

        if self.modo_profe_activo:
            for pregunta, respuesta in self.faq_profe.items():
                if pregunta in normalized_input:
                    return respuesta
            return "Hmm, no tengo esa respuesta en mi banco de preguntas. Intenta preguntar sobre qué es Python, variables, listas, flet, venv, etc."

        # 1. Verificar si expresa frustración o desánimo
        frustration_response = self.detect_frustration(normalized_input)
        if frustration_response:
            return frustration_response

        # 2. Verificar si el usuario interactúa con su nombre
        name_response = self.detect_name(raw_input, normalized_input)
        if name_response:
            return name_response

        # 3. Verificar si es una operación matemática
        math_response = self.evaluate_math(raw_input)
        if math_response:
            return math_response

        # 4. Puntuación de intenciones según palabras clave
        scores = {}
        for intent_name, data in self.intents.items():
            score = 0
            for kw in data["keywords"]:
                norm_kw = self.normalize(kw)
                if re.search(r"\b" + re.escape(norm_kw) + r"\b", normalized_input):
                    score += 1
            scores[intent_name] = score

        best_intent, max_score = max(scores.items(), key=lambda x: x[1])

        if max_score < 1:
            return (
                "No logré entender tu mensaje con certeza. 🤔\n"
                "Prueba preguntándome:\n"
                " • '¿Qué hora es?'\n"
                " • 'Cuéntame un chiste'\n"
                " • 'Activa el modo profe'\n"
                " • 'Me llamo [tu nombre]' o escribe 'ayuda'."
            )

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