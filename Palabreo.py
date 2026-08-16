import random
import json
import os
import unicodedata
from datetime import datetime

# ============================================
# 🎨 CONFIGURACIÓN DE COLORES ANSI
# ============================================

# Colores para terminal
VERDE = '\033[42m'      # Fondo verde
AMARILLO = '\033[43m'   # Fondo amarillo
GRIS = '\033[47m'       # Fondo gris
BLANCO = '\033[37m'     # Texto blanco
NEGRO = '\033[30m'      # Texto negro
RESET = '\033[0m'       # Resetear colores
NEGRITA = '\033[1m'     # Negrita

# Emojis para compartir
VERDE_EMOJI = '🟩'
AMARILLO_EMOJI = '🟨'
GRIS_EMOJI = '⬜'

# ============================================
# 📁 SISTEMA DE ESTADÍSTICAS
# ============================================

ARCHIVO_ESTADISTICAS = "estadisticas_palabreo.json"

def cargar_estadisticas():
    """Carga las estadísticas desde archivo JSON"""
    if os.path.exists(ARCHIVO_ESTADISTICAS):
        try:
            with open(ARCHIVO_ESTADISTICAS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "jugadas": 0,
        "ganadas": 0,
        "racha_actual": 0,
        "mejor_racha": 0,
        "intentos": [0, 0, 0, 0, 0, 0],  # Intentos 1-6
        "total_intentos": 0
    }

def guardar_estadisticas(estadisticas):
    """Guarda las estadísticas en archivo JSON"""
    with open(ARCHIVO_ESTADISTICAS, 'w', encoding='utf-8') as f:
        json.dump(estadisticas, f, indent=2)

def actualizar_estadisticas(estadisticas, ganado, intentos_usados):
    """Actualiza las estadísticas después de una partida"""
    estadisticas["jugadas"] += 1
    
    if ganado:
        estadisticas["ganadas"] += 1
        estadisticas["racha_actual"] += 1
        if estadisticas["racha_actual"] > estadisticas["mejor_racha"]:
            estadisticas["mejor_racha"] = estadisticas["racha_actual"]
        estadisticas["intentos"][intentos_usados - 1] += 1
        estadisticas["total_intentos"] += intentos_usados
    else:
        estadisticas["racha_actual"] = 0
    
    guardar_estadisticas(estadisticas)

# ============================================
# 📚 BANCO DE PALABRAS
# ============================================

def normalizar_texto(texto):
    """Elimina tildes y convierte a mayúsculas"""
    texto = texto.upper()
    # Normalizar Unicode para eliminar tildes
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def cargar_palabras(archivo="palabras_sv.txt"):
    """Carga las palabras desde el archivo de texto"""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            palabras = [linea.strip().upper() for linea in f if linea.strip()]
        return palabras
    except FileNotFoundError:
        print("❌ Archivo de palabras no encontrado")
        print("📝 Creando archivo con palabras por defecto...")
        # Palabras por defecto si no existe el archivo
        palabras_defecto = [
            "PUPUSA", "CASAS", "SALSA", "BAILE", "GENTE",
            "CALLE", "AMIGO", "FUEGO", "CAMPO", "RANCHO"
        ]
        with open(archivo, 'w', encoding='utf-8') as f:
            for palabra in palabras_defecto:
                f.write(palabra + "\n")
        return palabras_defecto

def elegir_palabra_dia(palabras):
    """Elige la palabra del día usando la fecha como semilla"""
    # Usar la fecha actual como semilla
    fecha = datetime.now().strftime("%Y%m%d")
    random.seed(int(fecha))
    return random.choice(palabras)

# ============================================
# 🎯 LÓGICA DEL JUEGO
# ============================================

def comparar_palabras(secreta, intento):
    """
    Compara el intento con la palabra secreta usando el algoritmo de dos pasadas
    Retorna una lista con: 'verde', 'amarillo', 'gris'
    """
    resultado = ['gris'] * 5
    conteo_secreta = {}
    
    # Contar letras disponibles en la palabra secreta
    for letra in secreta:
        conteo_secreta[letra] = conteo_secreta.get(letra, 0) + 1
    
    # PRIMERA PASADA: Marcar verdes y descontar
    for i in range(5):
        if intento[i] == secreta[i]:
            resultado[i] = 'verde'
            conteo_secreta[intento[i]] -= 1
    
    # SEGUNDA PASADA: Marcar amarillas
    for i in range(5):
        if resultado[i] == 'gris':
            if intento[i] in conteo_secreta and conteo_secreta[intento[i]] > 0:
                resultado[i] = 'amarillo'
                conteo_secreta[intento[i]] -= 1
    
    return resultado

def validar_intento(palabra, palabras_validas):
    """Valida que el intento sea una palabra válida de 5 letras"""
    # Convertir a mayúsculas y normalizar
    palabra = normalizar_texto(palabra)
    
    # Verificar longitud
    if len(palabra) != 5:
        return False, "Debe tener exactamente 5 letras"
    
    # Verificar que solo tenga letras
    if not palabra.isalpha():
        return False, "Solo letras (sin números ni símbolos)"
    
    # Verificar que esté en el banco de palabras
    if palabra not in palabras_validas:
        return False, "La palabra no está en el diccionario salvadoreño"
    
    return True, palabra

# ============================================
# 🎨 FUNCIONES VISUALES
# ============================================

def imprimir_con_color(letra, color):
    """Imprime una letra con el color de fondo correspondiente"""
    if color == 'verde':
        print(f"{VERDE}{BLANCO}{NEGRITA} {letra} {RESET}", end='')
    elif color == 'amarillo':
        print(f"{AMARILLO}{NEGRO}{NEGRITA} {letra} {RESET}", end='')
    else:  # gris
        print(f"{GRIS}{NEGRO} {letra} {RESET}", end='')

def mostrar_tablero(intentos, resultados):
    """Muestra el tablero con todos los intentos"""
    print("\n" + "=" * 40)
    print("   🎮 PALABREO SV")
    print("=" * 40)
    
    for i in range(6):
        if i < len(intentos):
            palabra = intentos[i]
            colores = resultados[i]
            print("   ", end='')
            for j in range(5):
                imprimir_con_color(palabra[j], colores[j])
            print()
        else:
            print("   ⬜⬜⬜⬜⬜")
    
    print("=" * 40)

def mostrar_teclado_virtual(letras_estado):
    """Muestra el teclado virtual con los estados de las letras"""
    filas = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    
    print("\n   TECLADO VIRTUAL")
    print("   " + "-" * 30)
    
    for fila in filas:
        print("   ", end='')
        for letra in fila:
            if letra in letras_estado:
                color = letras_estado[letra]
                if color == 'verde':
                    print(f"{VERDE}{BLANCO}{NEGRITA}{letra}{RESET}", end=' ')
                elif color == 'amarillo':
                    print(f"{AMARILLO}{NEGRO}{NEGRITA}{letra}{RESET}", end=' ')
                else:
                    print(f"{GRIS}{NEGRO}{letra}{RESET}", end=' ')
            else:
                print(f"{letra}", end=' ')
        print()
    print("   " + "-" * 30)

def actualizar_teclado(letras_estado, palabra, colores):
    """Actualiza el estado del teclado con nuevas letras"""
    for i in range(5):
        letra = palabra[i]
        color = colores[i]
        
        if letra not in letras_estado:
            letras_estado[letra] = color
        else:
            # Prioridad: verde > amarillo > gris
            if color == 'verde':
                letras_estado[letra] = 'verde'
            elif color == 'amarillo' and letras_estado[letra] != 'verde':
                letras_estado[letra] = 'amarillo'
            # Si es gris, solo se actualiza si no tiene mejor estado

def mostrar_estadisticas(estadisticas):
    """Muestra las estadísticas con barras horizontales"""
    print("\n" + "=" * 50)
    print("   📊 ESTADÍSTICAS")
    print("=" * 50)
    
    print(f"🎮 Partidas jugadas: {estadisticas['jugadas']}")
    print(f"✅ Partidas ganadas: {estadisticas['ganadas']}")
    
    if estadisticas['jugadas'] > 0:
        porcentaje = (estadisticas['ganadas'] / estadisticas['jugadas']) * 100
        print(f"📈 Porcentaje: {porcentaje:.1f}%")
    
    print(f"🔥 Racha actual: {estadisticas['racha_actual']}")
    print(f"🏆 Mejor racha: {estadisticas['mejor_racha']}")
    
    # Distribución de intentos
    print("\n   DISTRIBUCIÓN DE INTENTOS:")
    max_valor = max(estadisticas['intentos']) if estadisticas['intentos'] else 1
    
    for i, valor in enumerate(estadisticas['intentos'], 1):
        if valor > 0:
            barra = "█" * int((valor / max_valor) * 20)
            print(f"   {i}️⃣ {barra} {valor}")
    
    print("=" * 50)

def generar_resultado_compartir(intentos, resultados, palabra, ganado, intentos_usados):
    """Genera el resultado para compartir con emojis"""
    emojis = []
    for colores in resultados:
        fila = ''
        for color in colores:
            if color == 'verde':
                fila += VERDE_EMOJI
            elif color == 'amarillo':
                fila += AMARILLO_EMOJI
            else:
                fila += GRIS_EMOJI
        emojis.append(fila)
    
    resultado = "\n".join(emojis)
    titulo = "🎮 PALABREO SV"
    if ganado:
        mensaje = f"✅ ¡Adivinaste en {intentos_usados} intentos!"
    else:
        mensaje = f"❌ La palabra era: {palabra}"
    
    return f"{titulo}\n{mensaje}\n{resultado}"

# ============================================
# 🎮 FUNCIÓN PRINCIPAL DEL JUEGO
# ============================================

def jugar():
    """Función principal del juego"""
    # Activar colores en Windows
    if os.name == 'nt':
        os.system("")
    
    # Cargar palabras
    palabras = cargar_palabras()
    
    # Elegir palabra del día
    palabra_secreta = elegir_palabra_dia(palabras)
    
    # Estado del juego
    intentos = []
    resultados = []
    letras_estado = {}
    max_intentos = 6
    intento_actual = 0
    ganado = False
    
    # Cargar estadísticas
    estadisticas = cargar_estadisticas()
    
    # Mensaje de inicio
    print("\n" + "=" * 50)
    print("   🎮 PALABREO SV")
    print("=" * 50)
    print("   ¡Adivina la palabra salvadoreña!")
    print("   Tienes 6 intentos")
    print("   🟩 = Letra correcta y en su lugar")
    print("   🟨 = Letra correcta pero mal ubicada")
    print("   ⬜ = Letra incorrecta")
    print("=" * 50)
    print(f"   Palabra del día ({datetime.now().strftime('%d/%m/%Y')})")
    print("=" * 50)
    
    while intento_actual < max_intentos and not ganado:
        # Mostrar tablero
        mostrar_tablero(intentos, resultados)
        mostrar_teclado_virtual(letras_estado)
        
        # Pedir intento
        print(f"\n🔤 Intento {intento_actual + 1}/{max_intentos}")
        palabra_usuario = input("👉 Ingresa tu palabra: ").strip()
        
        # Validar
        valido, mensaje = validar_intento(palabra_usuario, palabras)
        
        if not valido:
            print(f"❌ {mensaje}")
            continue
        
        palabra_usuario = normalizar_texto(palabra_usuario)
        
        # Comparar
        colores = comparar_palabras(palabra_secreta, palabra_usuario)
        
        # Guardar intento
        intentos.append(palabra_usuario)
        resultados.append(colores)
        
        # Actualizar teclado
        actualizar_teclado(letras_estado, palabra_usuario, colores)
        
        # Verificar si ganó
        if all(color == 'verde' for color in colores):
            ganado = True
            break
        
        intento_actual += 1
    
    # Mostrar resultado final
    intento_actual += 1  # Ajustar para el intento usado (si ganó en el último, será 6)
    
    print("\n" + "=" * 50)
    mostrar_tablero(intentos, resultados)
    
    if ganado:
        mensajes = {
            1: "🎉 ¡INCREÍBLE! ¡Adivinaste en el primer intento! 🎉",
            2: "🌟 ¡Impresionante! ¡Adivinaste en 2 intentos!",
            3: "💪 ¡Bien hecho! ¡Adivinaste en 3 intentos!",
            4: "👍 ¡Buen trabajo! ¡Adivinaste en 4 intentos!",
            5: "😅 ¡Uf! ¡Adivinaste en el quinto intento!",
            6: "😮 ¡Milagro! ¡Adivinaste en el último intento!"
        }
        print(mensajes.get(intento_actual, f"✅ ¡Adivinaste en {intento_actual} intentos!"))
    else:
        print(f"❌ ¡Se acabaron los intentos!")
        print(f"📝 La palabra era: {palabra_secreta}")
    
    # Actualizar estadísticas
    actualizar_estadisticas(estadisticas, ganado, intento_actual)
    
    # Mostrar estadísticas
    mostrar_estadisticas(estadisticas)
    
    # Generar resultado para compartir
    print("\n📱 RESULTADO PARA COMPARTIR:")
    print("-" * 50)
    resultado_compartir = generar_resultado_compartir(
        intentos, resultados, palabra_secreta, ganado, intento_actual
    )
    print(resultado_compartir)
    print("-" * 50)
    
    return ganado, intento_actual

def jugar_otra_vez():
    """Pregunta si el jugador quiere jugar de nuevo"""
    while True:
        respuesta = input("\n🎮 ¿Quieres jugar otra vez? (s/n): ").strip().lower()
        if respuesta in ['s', 'si', 'sí']:
            return True
        elif respuesta in ['n', 'no']:
            return False
        else:
            print("❌ Responde 's' para sí o 'n' para no")

def main():
    """Punto de entrada del programa"""
    while True:
        jugar()
        if not jugar_otra_vez():
            print("\n👋 ¡Gracias por jugar PALABREO SV!")
            break

if __name__ == "__main__":
    main()