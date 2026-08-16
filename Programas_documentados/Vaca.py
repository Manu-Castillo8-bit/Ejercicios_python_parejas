import flet as ft
import json
import os

# Archivo local donde se guardarán los datos de la aplicación
ARCHIVO_JSON = "vaca_datos.json"

# ==========================================
# 1. MANEJO DE DATOS Y ALMACENAMIENTO (JSON)
# ==========================================

def cargar_datos():
    """
    Carga los datos desde el archivo JSON local.
    
    Si el archivo no existe o está corrupto, retorna un diccionario con
    una estructura base vacía lista para usarse.
    
    Returns:
        dict: Estructura de datos con integrantes y gastos.
    """
    if os.path.exists(ARCHIVO_JSON):
        try:
            with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            # En caso de error de lectura, devuelve la estructura por defecto
            return {"evento_actual": {"integrantes": [], "gastos": []}}
    return {"evento_actual": {"integrantes": [], "gastos": []}}

def guardar_datos(datos):
    """
    Guarda el diccionario de datos actual en el archivo JSON.
    
    Args:
        datos (dict): Los datos del evento a guardar.
    """
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4)

# ==========================================
# 2. LA MATEMÁTICA Y EL ALGORITMO VORAZ
# ==========================================

def calcular_saldos(integrantes, gastos):
    """
    Calcula el balance general de cada persona (cuánto debe o le deben).
    Trabaja con centavos para evitar errores de precisión con números decimales.
    
    Args:
        integrantes (list): Lista de nombres de las personas.
        gastos (list): Lista de diccionarios con los detalles de cada gasto.
        
    Returns:
        dict: Diccionario donde la clave es el nombre y el valor es el saldo en centavos.
              (Saldo positivo = le deben dinero; Saldo negativo = debe dinero).
    """
    saldos = {nombre: 0 for nombre in integrantes}
    
    for gasto in gastos:
        # Convertir monto a centavos
        monto_centavos = int(round(gasto["monto"] * 100))
        pagador = gasto["pagador"]
        involucrados = gasto["involucrados"]
        
        if not involucrados:
            continue
            
        # Al pagador se le suma el total del gasto (se le debe esa cantidad)
        saldos[pagador] += monto_centavos
        
        # Dividir el gasto entre los involucrados
        cuota_base = monto_centavos // len(involucrados)
        centavos_sobrantes = monto_centavos % len(involucrados)
        
        # Restar la cuota correspondiente a cada involucrado
        for i, persona in enumerate(involucrados):
            # Se reparte el sobrante (centavos sueltos) entre los primeros de la lista
            cuota = cuota_base + (1 if i < centavos_sobrantes else 0)
            saldos[persona] -= cuota
            
    return saldos

def optimizar_pagos(saldos):
    """
    Utiliza un algoritmo voraz (Greedy) para minimizar el número de transferencias
    necesarias para saldar las deudas entre el grupo.
    
    Args:
        saldos (dict): Diccionario con los balances en centavos.
        
    Returns:
        list: Lista de diccionarios con las instrucciones de pago.
    """
    deudores = []
    acreedores = []
    
    # Separar en quienes deben (saldo negativo) y quienes reciben (saldo positivo)
    for nombre, saldo in saldos.items():
        if saldo < 0:
            deudores.append([-saldo, nombre])  # Guardar deuda en valor absoluto
        elif saldo > 0:
            acreedores.append([saldo, nombre])
            
    # Ordenar de mayor a menor para emparejar primero las deudas más grandes
    deudores.sort(reverse=True, key=lambda x: x[0])
    acreedores.sort(reverse=True, key=lambda x: x[0])
    
    movimientos = []
    i, j = 0, 0
    
    # Emparejar deudores con acreedores
    while i < len(deudores) and j < len(acreedores):
        deuda, deudor = deudores[i]
        credito, acreedor = acreedores[j]
        
        # El monto a transferir es el menor entre la deuda actual y el crédito actual
        monto_transferir = min(deuda, credito)
        
        movimientos.append({
            "de": deudor,
            "para": acreedor,
            "monto": monto_transferir / 100.0  # Convertir de centavos a formato moneda
        })
        
        # Actualizar los saldos restantes tras esta transferencia
        deudores[i][0] -= monto_transferir
        acreedores[j][0] -= monto_transferir
        
        # Si la persona ya saldó su cuenta, pasamos al siguiente
        if deudores[i][0] == 0:
            i += 1
        if acreedores[j][0] == 0:
            j += 1
            
    return movimientos

# ==========================================
# 3. INTERFAZ GRÁFICA (FLET)
# ==========================================

def main(page: ft.Page):
    """
    Punto de entrada de la interfaz gráfica. 
    Define la estructura visual y la lógica de interacción del usuario.
    """
    # Configuración principal de la ventana
    page.title = "La Vaca 🐮 - Cuentas Claras"
    page.theme_mode = "dark"
    page.scroll = "adaptive"
    page.padding = 20

    # Forzar dimensiones iniciales de la ventana (con manejo de excepciones de versión)
    try:
        page.window.width = 400
        page.window.height = 800
    except AttributeError:
        try:
            page.window_width = 400
            page.window_height = 800
        except Exception:
            pass

    # Cargar datos iniciales
    datos = cargar_datos()
    evento = datos["evento_actual"]

    # --- FUNCIONES DE APOYO VISUAL ---
    
    def mostrar_mensaje(texto, error=False):
        """Muestra una notificación tipo SnackBar en la parte inferior."""
        snack = ft.SnackBar(
            content=ft.Text(texto), 
            bgcolor="red" if error else "green"
        )
        try:
            page.open(snack)
        except AttributeError:
            # Compatibilidad con versiones más antiguas de Flet
            try:
                page.snack_bar = snack
                page.snack_bar.open = True
                page.update()
            except Exception:
                pass

    # --- PESTAÑA 1: INTEGRANTES ---
    txt_nuevo_integrante = ft.TextField(label="Nombre del integrante", expand=True)
    lista_integrantes = ft.ListView(spacing=10, height=200)

    def actualizar_lista_integrantes():
        """Refresca la vista de la lista de personas agregadas al evento."""
        lista_integrantes.controls.clear()
        
        icon_persona = getattr(ft.Icons, "PERSON", "person") if hasattr(ft, "Icons") else "person"
        icon_borrar = getattr(ft.Icons, "DELETE", "delete") if hasattr(ft, "Icons") else "delete"

        for integrante in evento["integrantes"]:
            lista_integrantes.controls.append(
                ft.ListTile(
                    title=ft.Text(integrante),
                    leading=ft.Icon(icon_persona),
                    trailing=ft.IconButton(
                        icon=icon_borrar,
                        icon_color="red",
                        tooltip="Eliminar integrante",
                        on_click=lambda e, nom=integrante: eliminar_integrante(nom)
                    )
                )
            )
        actualizar_opciones_gastos()
        page.update()

    def agregar_integrante(e):
        """Valida e inserta un nuevo participante en la base de datos."""
        nombre = txt_nuevo_integrante.value.strip()
        
        # Validaciones de campo
        if not nombre:
            mostrar_mensaje("Ingresa un nombre válido.", error=True)
            return
        if nombre in evento["integrantes"]:
            mostrar_mensaje("Este integrante ya existe.", error=True)
            return
            
        evento["integrantes"].append(nombre)
        txt_nuevo_integrante.value = ""
        guardar_datos(datos)
        actualizar_lista_integrantes()
        mostrar_mensaje(f"{nombre} agregado.")

    def eliminar_integrante(nombre):
        """Elimina a una persona siempre y cuando no esté vinculada a un gasto."""
        # Verificar si la persona está involucrada en gastos previos
        en_gasto = any(
            g["pagador"] == nombre or nombre in g["involucrados"] 
            for g in evento["gastos"]
        )
        if en_gasto:
            mostrar_mensaje("No puedes eliminar a alguien que ya tiene gastos registrados.", error=True)
            return
            
        evento["integrantes"].remove(nombre)
        guardar_datos(datos)
        actualizar_lista_integrantes()
        mostrar_mensaje(f"{nombre} eliminado.")

    btn_agregar_integrante = ft.ElevatedButton("Agregar", on_click=agregar_integrante)
    
    # --- PESTAÑA 2: GASTOS ---
    txt_concepto = ft.TextField(label="¿Qué compraron? (Ej. Pizza)")
    txt_monto = ft.TextField(label="Monto ($)", keyboard_type="number")
    drop_pagador = ft.Dropdown(label="¿Quién pagó?")
    col_involucrados = ft.Column(scroll="adaptive")

    def actualizar_opciones_gastos():
        """Actualiza el dropdown de pagadores y los checkboxes de involucrados."""
        drop_pagador.options = [ft.dropdown.Option(i) for i in evento["integrantes"]]
        col_involucrados.controls = [
            ft.Checkbox(label=i, value=True) for i in evento["integrantes"]
        ]

    def agregar_gasto(e):
        """Valida y procesa un nuevo gasto."""
        concepto = txt_concepto.value.strip()
        
        try:
            monto = float(txt_monto.value)
            if monto <= 0: raise ValueError
        except:
            mostrar_mensaje("El monto debe ser un número positivo.", error=True)
            return
            
        pagador = drop_pagador.value
        if not pagador:
            mostrar_mensaje("Selecciona quién pagó.", error=True)
            return
            
        # Extraer quiénes tienen el checkbox marcado
        involucrados = [cb.label for cb in col_involucrados.controls if cb.value]
        if not involucrados:
            mostrar_mensaje("Selecciona al menos un involucrado.", error=True)
            return
            
        evento["gastos"].append({
            "concepto": concepto,
            "monto": monto,
            "pagador": pagador,
            "involucrados": involucrados
        })
        guardar_datos(datos)
        
        # Limpiar formulario
        txt_concepto.value = ""
        txt_monto.value = ""
        mostrar_mensaje("Gasto registrado con éxito.")
        actualizar_resumen()

    btn_agregar_gasto = ft.ElevatedButton("Registrar Gasto", on_click=agregar_gasto, bgcolor="blue", color="white")

    # --- PESTAÑA 3: RESUMEN Y PAGOS ---
    resumen_col = ft.Column()
    pagos_col = ft.Column()
    
    # Área de texto de solo lectura para copiar fácilmente los resultados (ideal para WhatsApp)
    txt_copiable = ft.TextField(
        label="📋 Resumen listo para copiar",
        multiline=True,
        read_only=True,
        min_lines=6,
        max_lines=10,
    )

    def actualizar_resumen():
        """Calcula el estado actual de las deudas y genera el texto de resumen."""
        resumen_col.controls.clear()
        pagos_col.controls.clear()
        
        if not evento["integrantes"]:
            resumen_col.controls.append(ft.Text("No hay integrantes aún."))
            txt_copiable.value = "No hay datos para copiar."
            page.update()
            return
            
        saldos = calcular_saldos(evento["integrantes"], evento["gastos"])
        
        resumen_col.controls.append(ft.Text("Estado de Cuentas:", weight="bold", size=18))
        
        # Preparar texto en formato Markdown para redes sociales/chats
        texto_para_copiar = "🐮 *RESUMEN DE LA VACA* 🐮\n\n📊 *Estado de Cuentas:*\n"

        # Mostrar estado individual
        for nombre, saldo_centavos in saldos.items():
            saldo = saldo_centavos / 100.0
            color_texto = "green" if saldo > 0 else "red" if saldo < 0 else "grey"
            linea_texto = f"{nombre}: {'Le deben' if saldo > 0 else 'Debe'} ${abs(saldo):.2f}" if saldo != 0 else f"{nombre}: Saldo $0.00"
            
            resumen_col.controls.append(ft.Text(linea_texto, color=color_texto, weight="bold"))
            texto_para_copiar += f"• {linea_texto}\n"
            
        # Calcular y mostrar transferencias minimizadas
        pagos = optimizar_pagos(saldos)
        pagos_col.controls.append(ft.Text("Plan de Pagos (Minimizado):", weight="bold", size=18, color="cyan"))
        texto_para_copiar += "\n💸 *Plan de Pagos:*\n"
        
        if not pagos:
            pagos_col.controls.append(ft.Text("💸 ¡Todos están al día! Cuentas saldadas."))
            texto_para_copiar += "¡Todos están al día!"
        else:
            for p in pagos:
                linea_pago = f"👉 {p['de']} le transfiere a {p['para']}: ${p['monto']:.2f}"
                pagos_col.controls.append(ft.Text(linea_pago))
                texto_para_copiar += f"{linea_pago}\n"
                
        # Insertar todo el resumen en el TextField
        txt_copiable.value = texto_para_copiar
        page.update()

    # --- ESTRUCTURA DE LAS VISTAS (TABS) ---
    vista_grupo = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Row([txt_nuevo_integrante, btn_agregar_integrante]),
            ft.Divider(),
            lista_integrantes
        ])
    )

    vista_gastos = ft.Container(
        padding=10,
        content=ft.Column([
            txt_concepto,
            txt_monto,
            drop_pagador,
            ft.Text("¿Entre quiénes se divide?"),
            ft.Container(content=col_involucrados, height=150),
            btn_agregar_gasto
        ], scroll="adaptive")
    )

    vista_saldos = ft.SelectionArea(
        content=ft.Container(
            padding=10,
            content=ft.Column([
                resumen_col,
                ft.Divider(),
                pagos_col,
                ft.Divider(),
                ft.Text("👇 Mantén presionado el texto de abajo para copiarlo:", weight="bold", color="amber"),
                txt_copiable
            ], scroll="adaptive")
        )
    )

    # Contenedor dinámico que alternará entre las distintas vistas
    contenedor_principal = ft.Container(content=vista_grupo, expand=True)

    def cambiar_tab(e, index):
        """Alterna el contenido principal y cambia el estilo de los botones del menú."""
        vistas = [vista_grupo, vista_gastos, vista_saldos]
        contenedor_principal.content = vistas[index]
        
        btn_tab_grupo.bgcolor = "blue" if index == 0 else "grey_800"
        btn_tab_gastos.bgcolor = "blue" if index == 1 else "grey_800"
        btn_tab_saldos.bgcolor = "blue" if index == 2 else "grey_800"
        
        page.update()

    # Botones de navegación
    btn_tab_grupo = ft.ElevatedButton("👥 Grupo", on_click=lambda e: cambiar_tab(e, 0), bgcolor="blue", color="white")
    btn_tab_gastos = ft.ElevatedButton("🛒 Gastos", on_click=lambda e: cambiar_tab(e, 1), bgcolor="grey_800", color="white")
    btn_tab_saldos = ft.ElevatedButton("💰 Saldos", on_click=lambda e: cambiar_tab(e, 2), bgcolor="grey_800", color="white")

    barra_navegacion = ft.Row([btn_tab_grupo, btn_tab_gastos, btn_tab_saldos], alignment="center")

    # Agregar la estructura principal a la página
    page.add(
        ft.Text("🐮 LA VACA", size=24, weight="bold", color="amber"),
        barra_navegacion,
        ft.Divider(),
        contenedor_principal
    )
    
    # Carga inicial de datos al iniciar la app
    actualizar_lista_integrantes()
    actualizar_resumen()

# Ejecución de la aplicación
if __name__ == "__main__":
    ft.app(target=main)