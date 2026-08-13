import flet as ft
import json
import os

ARCHIVO_JSON = "vaca_datos.json"

# ==========================================
# 1. MANEJO DE DATOS Y ALMACENAMIENTO (JSON)
# ==========================================

def cargar_datos():
    """Carga los datos desde el archivo JSON o crea una estructura vacía."""
    if os.path.exists(ARCHIVO_JSON):
        try:
            with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"evento_actual": {"integrantes": [], "gastos": []}}
    return {"evento_actual": {"integrantes": [], "gastos": []}}

def guardar_datos(datos):
    """Guarda los datos en el archivo al instante."""
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4)

# ==========================================
# 2. LA MATEMÁTICA Y EL ALGORITMO VORAZ
# ==========================================

def calcular_saldos(integrantes, gastos):
    """Calcula cuánto debe o le deben a cada persona en centavos."""
    saldos = {nombre: 0 for nombre in integrantes}
    
    for gasto in gastos:
        monto_centavos = int(round(gasto["monto"] * 100))
        pagador = gasto["pagador"]
        involucrados = gasto["involucrados"]
        
        if not involucrados:
            continue
            
        saldos[pagador] += monto_centavos
        
        cuota_base = monto_centavos // len(involucrados)
        centavos_sobrantes = monto_centavos % len(involucrados)
        
        for i, persona in enumerate(involucrados):
            cuota = cuota_base + (1 if i < centavos_sobrantes else 0)
            saldos[persona] -= cuota
            
    return saldos

def optimizar_pagos(saldos):
    """Algoritmo Voraz (Greedy) para minimizar transacciones."""
    deudores = []
    acreedores = []
    
    for nombre, saldo in saldos.items():
        if saldo < 0:
            deudores.append([-saldo, nombre]) 
        elif saldo > 0:
            acreedores.append([saldo, nombre])
            
    deudores.sort(reverse=True, key=lambda x: x[0])
    acreedores.sort(reverse=True, key=lambda x: x[0])
    
    movimientos = []
    i, j = 0, 0
    
    while i < len(deudores) and j < len(acreedores):
        deuda, deudor = deudores[i]
        credito, acreedor = acreedores[j]
        
        monto_transferir = min(deuda, credito)
        
        movimientos.append({
            "de": deudor,
            "para": acreedor,
            "monto": monto_transferir / 100.0 
        })
        
        deudores[i][0] -= monto_transferir
        acreedores[j][0] -= monto_transferir
        
        if deudores[i][0] == 0:
            i += 1
        if acreedores[j][0] == 0:
            j += 1
            
    return movimientos

# ==========================================
# 3. INTERFAZ GRÁFICA (FLET)
# ==========================================

def main(page: ft.Page):
    page.title = "La Vaca 🐮 - Cuentas Claras"
    page.theme_mode = "dark"
    page.scroll = "adaptive"
    page.padding = 20

    try:
        page.window.width = 400
        page.window.height = 800
    except AttributeError:
        try:
            page.window_width = 400
            page.window_height = 800
        except Exception:
            pass

    datos = cargar_datos()
    evento = datos["evento_actual"]

    # --- COMPONENTES VISUALES ---
    
    def mostrar_mensaje(texto, error=False):
        snack = ft.SnackBar(
            content=ft.Text(texto), 
            bgcolor="red" if error else "green"
        )
        try:
            page.open(snack)
        except AttributeError:
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
        lista_integrantes.controls.clear()
        for integrante in evento["integrantes"]:
            lista_integrantes.controls.append(
                ft.ListTile(
                    title=ft.Text(integrante),
                    leading=ft.Icon("person"),
                    trailing=ft.IconButton(
                        icon="delete", 
                        icon_color="red",
                        on_click=lambda e, nom=integrante: eliminar_integrante(nom)
                    )
                )
            )
        actualizar_opciones_gastos()
        page.update()

    def agregar_integrante(e):
        nombre = txt_nuevo_integrante.value.strip()
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
        drop_pagador.options = [ft.dropdown.Option(i) for i in evento["integrantes"]]
        col_involucrados.controls = [
            ft.Checkbox(label=i, value=True) for i in evento["integrantes"]
        ]

    def agregar_gasto(e):
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
        
        txt_concepto.value = ""
        txt_monto.value = ""
        mostrar_mensaje("Gasto registrado con éxito.")
        actualizar_resumen()

    btn_agregar_gasto = ft.ElevatedButton("Registrar Gasto", on_click=agregar_gasto, bgcolor="blue", color="white")

    # --- PESTAÑA 3: RESUMEN Y PAGOS ---
    resumen_col = ft.Column()
    pagos_col = ft.Column()
    
    def copiar_portapapeles(e):
        texto = "🐮 RESUMEN DE LA VACA 🐮\n\n"
        for p in pagos_col.controls:
            if isinstance(p, ft.Text):
                texto += p.value + "\n"
        try:
            page.set_clipboard(texto)
        except Exception:
            pass
        mostrar_mensaje("¡Plan de pagos copiado al portapapeles listo para WhatsApp!")

    btn_compartir = ft.ElevatedButton("📋 Copiar para WhatsApp", on_click=copiar_portapapeles, bgcolor="green", color="white")

    def actualizar_resumen():
        resumen_col.controls.clear()
        pagos_col.controls.clear()
        
        if not evento["integrantes"]:
            resumen_col.controls.append(ft.Text("No hay integrantes aún."))
            page.update()
            return
            
        saldos = calcular_saldos(evento["integrantes"], evento["gastos"])
        
        resumen_col.controls.append(ft.Text("Estado de Cuentas:", weight="bold", size=18))
        for nombre, saldo_centavos in saldos.items():
            saldo = saldo_centavos / 100.0
            color_texto = "green" if saldo > 0 else "red" if saldo < 0 else "grey"
            texto = f"{nombre}: {'Le deben' if saldo > 0 else 'Debe'} ${abs(saldo):.2f}" if saldo != 0 else f"{nombre}: Saldo $0.00"
            resumen_col.controls.append(ft.Text(texto, color=color_texto, weight="bold"))
            
        pagos = optimizar_pagos(saldos)
        pagos_col.controls.append(ft.Text("Plan de Pagos (Minimizado):", weight="bold", size=18, color="cyan"))
        
        if not pagos:
            pagos_col.controls.append(ft.Text("💸 ¡Todos están al día! Cuentas saldadas."))
        else:
            for p in pagos:
                pagos_col.controls.append(ft.Text(f"👉 {p['de']} le transfiere a {p['para']}: ${p['monto']:.2f}"))
                
        page.update()

    # --- VISTAS DE LAS PESTAÑAS ---
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

    vista_saldos = ft.Container(
        padding=10,
        content=ft.Column([
            resumen_col,
            ft.Divider(),
            pagos_col,
            ft.Container(height=20),
            btn_compartir
        ], scroll="adaptive")
    )

    # Contenedor dinámico de vista activa
    contenedor_principal = ft.Container(content=vista_grupo, expand=True)

    # --- NAVEGACIÓN PERSONALIZADA (100% INMUNE A ERRORES DE VERSION) ---
    def cambiar_tab(e, index):
        vistas = [vista_grupo, vista_gastos, vista_saldos]
        contenedor_principal.content = vistas[index]
        
        # Resaltar botón activo
        btn_tab_grupo.bgcolor = "blue" if index == 0 else "grey_800"
        btn_tab_gastos.bgcolor = "blue" if index == 1 else "grey_800"
        btn_tab_saldos.bgcolor = "blue" if index == 2 else "grey_800"
        
        page.update()

    btn_tab_grupo = ft.ElevatedButton("👥 Grupo", on_click=lambda e: cambiar_tab(e, 0), bgcolor="blue", color="white")
    btn_tab_gastos = ft.ElevatedButton("🛒 Gastos", on_click=lambda e: cambiar_tab(e, 1), bgcolor="grey_800", color="white")
    btn_tab_saldos = ft.ElevatedButton("💰 Saldos", on_click=lambda e: cambiar_tab(e, 2), bgcolor="grey_800", color="white")

    barra_navegacion = ft.Row([btn_tab_grupo, btn_tab_gastos, btn_tab_saldos], alignment="center")

    page.add(
        ft.Text("🐮 LA VACA", size=24, weight="bold", color="amber"),
        barra_navegacion,
        ft.Divider(),
        contenedor_principal
    )
    
    actualizar_lista_integrantes()
    actualizar_resumen()

if __name__ == "__main__":
    ft.app(target=main)