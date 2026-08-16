import random
import time
import os
import json
from datetime import datetime

# ============================================
# 🎮 CONSTANTES DEL JUEGO (REGLAS DEL NEGOCIO)
# ============================================
CAPITAL_INICIAL = 50.00
DIAS_TOTALES = 14
META_MINIMA = 120.00
META_LEYENDA = 200.00

# Costos por tipo de pupusa
COSTOS = {
    "queso": 0.18,
    "frijol con queso": 0.14,
    "revuelta": 0.26
}

# Demanda base y efectos
DEMANDA_BASE = 40
EFECTO_PRECIO = 6
PRECIO_REFERENCIA = 0.60

# Efectos del clima
CLIMA = {
    "soleado": 8,
    "nublado": 0,
    "lluvia": -14
}

# Eventos posibles
EVENTOS = [
    "feria patronal",
    "se fue la luz",
    "sube el queso",
    "reseña viral",
    "inspección"
]

# ============================================
# 📁 SISTEMA DE TABLA DE HONOR
# ============================================

ARCHIVO_HONOR = "tabla_honor.json"

def cargar_tabla_honor():
    """Carga la tabla de honor desde archivo"""
    if os.path.exists(ARCHIVO_HONOR):
        try:
            with open(ARCHIVO_HONOR, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def guardar_tabla_honor(nombre, capital, reputacion, dias):
    """Guarda un nuevo récord en la tabla de honor"""
    tabla = cargar_tabla_honor()
    
    nuevo_record = {
        "nombre": nombre,
        "capital": round(capital, 2),
        "reputacion": round(reputacion, 1),
        "dias": dias,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    tabla.append(nuevo_record)
    # Ordenar por capital (mayor a menor)
    tabla.sort(key=lambda x: x["capital"], reverse=True)
    # Mantener solo los 5 mejores
    tabla = tabla[:5]
    
    with open(ARCHIVO_HONOR, 'w', encoding='utf-8') as f:
        json.dump(tabla, f, indent=2, ensure_ascii=False)
    
    return tabla

def mostrar_tabla_honor():
    """Muestra la tabla de honor"""
    tabla = cargar_tabla_honor()
    
    if not tabla:
        print("\n📋 Aún no hay registros en la tabla de honor")
        return
    
    print("\n╔" + "═" * 58 + "╗")
    print("║  🏆 TABLA DE HONOR  {' ' * 37}║")
    print("╠" + "═" * 58 + "╣")
    print("║  #  NOMBRE         CAPITAL   ⭐  DÍAS  FECHA  ║")
    print("╠" + "═" * 58 + "╣")
    
    for i, record in enumerate(tabla, 1):
        nombre = record["nombre"][:12].ljust(12)
        capital = f"${record['capital']:.2f}".ljust(9)
        reputacion = f"{record['reputacion']:.1f}".ljust(4)
        dias = str(record["dias"]).ljust(5)
        fecha = record["fecha"][:10]
        print(f"║  {i}  {nombre} {capital} {reputacion} {dias} {fecha} ║")
    
    print("╚" + "═" * 58 + "╝")

# ============================================
# 🎨 FUNCIONES VISUALES MEJORADAS
# ============================================

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def formatear_moneda(cantidad):
    return f"${cantidad:.2f}"

def mostrar_barra_progreso(valor, maximo, titulo="", ancho=20):
    """Crea una barra de progreso visual"""
    if maximo <= 0:
        return "[░░░░░░░░░░░░░░░░░░░░] 0%"
    
    porcentaje = min(100, int((valor / maximo) * 100))
    lleno = int((porcentaje / 100) * ancho)
    vacio = ancho - lleno
    
    barra = "█" * lleno + "░" * vacio
    return f"[{barra}] {porcentaje}%"

def mostrar_ticket_dia(dia, tipo, preparadas, vendidas, sobrantes, 
                       costo_produccion, precio, ingresos, ganancia, 
                       capital, reputacion, demanda, evento):
    """Muestra un ticket de venta con formato real"""
    print("\n" + "═" * 50)
    print("          🧾 TICKET DE VENTA - DÍA " + str(dia))
    print("═" * 50)
    print(f"  🥘 Tipo:     {tipo}")
    print(f"  👥 Demanda:  {demanda} clientes")
    print(f"  🛒 Preparadas: {preparadas} pupusas")
    print(f"  ✅ Vendidas:  {vendidas} pupusas")
    print(f"  ❌ Perdidas:  {sobrantes} pupusas")
    print("─" * 50)
    print(f"  💰 Costo prod: {formatear_moneda(costo_produccion)}")
    print(f"  💲 Precio:    {formatear_moneda(precio)}")
    print(f"  💵 Ingresos:  {formatear_moneda(ingresos)}")
    print("─" * 50)
    print(f"  📈 Ganancia:  {formatear_moneda(ganancia)}")
    print(f"  💰 Capital:   {formatear_moneda(capital)}")
    print(f"  ⭐ Reputación: {reputacion:.1f}/5")
    if evento:
        print(f"  🎭 Evento:    {evento}")
    print("═" * 50)

# ============================================
# 🎯 FUNCIONES DEL JUEGO (REGLAS DEL NEGOCIO)
# ============================================

def seleccionar_tipo_pupusa():
    """Permite al jugador seleccionar el tipo de pupusa"""
    while True:
        print("\n╔" + "═" * 58 + "╗")
        print("║  📋 SELECCIONA TU PUPUSA  {' ' * 33}║")
        print("╠" + "═" * 58 + "╣")
        print("║  1. 🧀 Queso                 ($0.18 c/u)  ║")
        print("║  2. 🫘 Frijol con queso      ($0.14 c/u)  ║")
        print("║  3. 🌶️ Revuelta              ($0.26 c/u)  ║")
        print("╚" + "═" * 58 + "╝")
        
        opcion = input("\n👉 Selecciona el tipo (1-3): ").strip()
        
        if opcion == "1":
            return "queso"
        elif opcion == "2":
            return "frijol con queso"
        elif opcion == "3":
            return "revuelta"
        else:
            print("❌ Opción inválida. ¡Elige 1, 2 o 3!")
            time.sleep(1)

def obtener_cantidad_pupusas(capital, tipo):
    """Obtiene cuántas pupusas preparar con validación"""
    costo_unitario = COSTOS[tipo]
    max_posible = int(capital / costo_unitario) if costo_unitario > 0 else 0
    
    while True:
        try:
            print(f"\n💰 Capital disponible: {formatear_moneda(capital)}")
            print(f"🧮 Costo unitario: {formatear_moneda(costo_unitario)}")
            print(f"📊 Máximo posible: {max_posible} pupusas")
            
            cantidad = input(f"\n🔢 ¿Cuántas pupusas preparar? (mínimo 1): ")
            cantidad = int(cantidad)
            
            if cantidad <= 0:
                print("❌ ¡Debes preparar al menos 1 pupusa!")
                continue
                
            costo_total = cantidad * costo_unitario
            if costo_total > capital:
                print(f"❌ ¡No tienes suficiente capital!")
                print(f"   Necesitas: {formatear_moneda(costo_total)}")
                print(f"   Tienes: {formatear_moneda(capital)}")
                continue
                
            return cantidad
            
        except ValueError:
            print("❌ ¡Eso no es un número! Ingresa un valor válido.")

def generar_clima():
    """Genera el clima del día"""
    climas = ["soleado", "nublado", "lluvia"]
    clima = random.choice(climas)
    return clima, CLIMA[clima]

def generar_evento(dia):
    """Genera un evento aleatorio (1 de cada 4 días)"""
    if random.randint(1, 4) == 1:
        return random.choice(EVENTOS)
    return None

def calcular_demanda(clima_efecto, precio, reputacion, evento):
    """Calcula la demanda del día basada en todos los factores"""
    # Demanda base + reputación
    demanda = DEMANDA_BASE + (reputacion * 4)
    
    # Efecto del clima
    demanda += clima_efecto
    
    # Efecto del precio
    diferencia_precio = precio - PRECIO_REFERENCIA
    ajuste_precio = (diferencia_precio / 0.05) * EFECTO_PRECIO
    demanda += ajuste_precio
    
    # Efecto de eventos
    if evento == "feria patronal":
        demanda *= 2
    elif evento == "se fue la luz":
        demanda = 0
    
    # Asegurar que la demanda no sea negativa
    demanda = max(0, int(demanda))
    
    return demanda

def establecer_precio():
    """Permite al jugador establecer el precio de venta"""
    while True:
        try:
            print("\n💲 ESTABLECE TU PRECIO")
            print("═" * 40)
            print("💰 Precio mínimo: $0.25")
            print("💰 Precio máximo: $1.50")
            print("💰 Precio de referencia: $0.60 (demanda balanceada)")
            
            precio = input("\n👉 Ingresa el precio de venta por pupusa: $")
            precio = float(precio)
            
            if 0.25 <= precio <= 1.50:
                if precio < 0.60:
                    print(f"📈 Precio bajo: atraerás más clientes")
                elif precio > 0.60:
                    print(f"📉 Precio alto: perderás algunos clientes")
                else:
                    print("⚖️ Precio balanceado: demanda normal")
                time.sleep(0.5)
                return precio
            else:
                print("❌ El precio debe estar entre $0.25 y $1.50")
        except ValueError:
            print("❌ ¡Eso no es un número válido!")

def procesar_dia(capital, reputacion, dia, historial):
    """Procesa un día completo del juego"""
    print(f"\n🌅 INICIO DEL DÍA {dia}/{DIAS_TOTALES}")
    print(f"💰 Capital: {formatear_moneda(capital)}")
    print(f"⭐ Reputación: {reputacion:.1f}/5")
    time.sleep(1)
    
    # 1. Generar clima
    clima, clima_efecto = generar_clima()
    print(f"\n☀️ Clima: {clima.upper()} ({clima_efecto:+d} clientes)")
    time.sleep(1)
    
    # 2. Generar evento
    evento = generar_evento(dia)
    if evento:
        print(f"\n🎭 ¡EVENTO ESPECIAL! {evento.upper()}")
        time.sleep(1)
    
    # 3. Seleccionar tipo de pupusa
    tipo = seleccionar_tipo_pupusa()
    costo_unitario = COSTOS[tipo]
    
    # 4. Establecer cantidad
    cantidad = obtener_cantidad_pupusas(capital, tipo)
    costo_produccion = cantidad * costo_unitario
    
    # 5. Aplicar evento "sube el queso"
    if evento == "sube el queso":
        costo_produccion *= 1.30
        print(f"\n⚠️ ¡Costo aumentado! Ahora: {formatear_moneda(costo_produccion)}")
        time.sleep(1)
    
    # 6. Establecer precio
    precio = establecer_precio()
    
    # 7. Calcular demanda
    demanda = calcular_demanda(clima_efecto, precio, reputacion, evento)
    
    # 8. Procesar ventas
    if evento == "se fue la luz":
        ventas = 0
        sobrantes = cantidad
    else:
        ventas = min(demanda, cantidad)
        sobrantes = cantidad - ventas
        
        if evento == "feria patronal":
            print("🎪 ¡Feria patronal! Demanda duplicada")
        
        if evento == "inspección":
            print("🔍 ¡Inspección! Multa de $5")
            capital -= 5
    
    # 9. Calcular ingresos y ganancia
    ingresos = ventas * precio
    ganancia = ingresos - costo_produccion
    capital = capital + ganancia
    
    # 10. Actualizar reputación
    if ventas == cantidad and demanda > 0:
        reputacion += 0.2
    elif ventas < cantidad and cantidad > 0:
        reputacion -= 0.4
    
    if precio > 1.00:
        reputacion -= 0.3
    
    if evento == "reseña viral":
        reputacion += 1
    
    reputacion = max(0, min(5, reputacion))
    
    # 11. Mostrar ticket del día
    mostrar_ticket_dia(dia, tipo, cantidad, ventas, sobrantes, 
                       costo_produccion, precio, ingresos, ganancia, 
                       capital, reputacion, demanda, evento)
    
    # 12. Guardar en historial
    registro = {
        "dia": dia,
        "tipo": tipo,
        "preparadas": cantidad,
        "vendidas": ventas,
        "sobrantes": sobrantes,
        "costo": round(costo_produccion, 2),
        "precio": round(precio, 2),
        "ingresos": round(ingresos, 2),
        "ganancia": round(ganancia, 2),
        "capital": round(capital, 2),
        "reputacion": round(reputacion, 1),
        "demanda": demanda,
        "evento": evento,
        "clima": clima
    }
    historial.append(registro)
    
    return capital, reputacion, historial

def mostrar_resumen_final(historial, capital, reputacion, dias_jugados, completo):
    """Muestra un resumen completo con gráficos"""
    print("\n╔" + "═" * 58 + "╗")
    print("║  📊 RESUMEN FINAL  {' ' * 38}║")
    print("╚" + "═" * 58 + "╝")
    
    if not historial:
        print("No hay datos para mostrar")
        return
    
    # Encontrar mejor y peor día
    mejor_dia = max(historial, key=lambda x: x["ganancia"])
    peor_dia = min(historial, key=lambda x: x["ganancia"])
    
    total_vendido = sum(d["vendidas"] for d in historial)
    ganancia_total = sum(d["ganancia"] for d in historial)
    
    print("\n📈 ESTADÍSTICAS:")
    print(f"  🏆 Mejor día: Día {mejor_dia['dia']} - Ganancia: {formatear_moneda(mejor_dia['ganancia'])}")
    print(f"  📉 Peor día: Día {peor_dia['dia']} - Ganancia: {formatear_moneda(peor_dia['ganancia'])}")
    print(f"  🛒 Total vendido: {total_vendido} pupusas")
    print(f"  💰 Ganancia acumulada: {formatear_moneda(ganancia_total)}")
    print(f"  💰 Capital final: {formatear_moneda(capital)}")
    print(f"  ⭐ Reputación final: {reputacion:.1f}/5")
    
    # Gráfico de barras de ganancias por día
    print("\n📊 GANANCIAS POR DÍA:")
    max_ganancia = max(1, max(d["ganancia"] for d in historial))
    
    for registro in historial:
        dia = registro["dia"]
        ganancia = registro["ganancia"]
        barra = "█" * int((abs(ganancia) / max_ganancia) * 15) if ganancia >= 0 else "░" * int((abs(ganancia) / max_ganancia) * 15)
        color = "🟩" if ganancia >= 0 else "🟥"
        print(f"  Día {dia:2d}: {color} {barra:15} {formatear_moneda(ganancia)}")
    
    # Evaluación final
    print("\n" + "═" * 50)
    if completo:
        if capital >= META_LEYENDA:
            print("🏆 ¡ERES UNA LEYENDA! La pupusería más exitosa del país")
        elif capital >= META_MINIMA:
            print("✅ ¡SOBREVIVISTE! Demostraste que sirves para esto")
        else:
            print("😅 Sobreviviste pero no alcanzaste la meta mínima")
    else:
        print("💀 GAME OVER - La crisis te ganó")
    print("═" * 50)

def jugar():
    """Función principal del juego"""
    # Estado inicial
    capital = CAPITAL_INICIAL
    reputacion = 3.0
    dia = 1
    historial = []
    
    # Pantalla de inicio
    limpiar_pantalla()
    print("\n╔" + "═" * 58 + "╗")
    print("║  🏪 PUPUSA TYCOON  {' ' * 37}║")
    print("║  De pupusería a imperio en 14 días  {' ' * 23}║")
    print("╚" + "═" * 58 + "╝")
    
    print(f"\n💰 Capital inicial: {formatear_moneda(CAPITAL_INICIAL)}")
    print(f"🎯 Meta: {formatear_moneda(META_MINIMA)}")
    print(f"🏆 Leyenda: {formatear_moneda(META_LEYENDA)}")
    
    nombre = input("\n👤 Ingresa tu nombre para la tabla de honor: ").strip()
    if not nombre:
        nombre = "Anónimo"
    
    input("\n🎮 Presiona ENTER para comenzar...")
    
    # Bucle principal
    while dia <= DIAS_TOTALES and capital >= 0:
        capital, reputacion, historial = procesar_dia(capital, reputacion, dia, historial)
        
        if capital < 0:
            limpiar_pantalla()
            print("\n💀 ¡QUEBROSTE!")
            print(f"Te quedaste sin capital en el día {dia}")
            break
        
        if dia < DIAS_TOTALES:
            input("\n⏳ Presiona ENTER para continuar...")
        
        dia += 1
    
    # Mostrar resumen final
    limpiar_pantalla()
    completo = (dia > DIAS_TOTALES and capital >= 0)
    mostrar_resumen_final(historial, capital, reputacion, dia - 1, completo)
    
    # Guardar en tabla de honor si terminó exitosamente
    if completo and capital >= META_MINIMA:
        tabla = guardar_tabla_honor(nombre, capital, reputacion, dia - 1)
        print("\n🏆 ¡Récord guardado en la tabla de honor!")
        mostrar_tabla_honor()

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
            print("\n👋 ¡Gracias por jugar Pupusa Tycoon!")
            print("🍽️ ¡Que tengas éxito en tu pupusería!")
            break

if __name__ == "__main__":
    main()