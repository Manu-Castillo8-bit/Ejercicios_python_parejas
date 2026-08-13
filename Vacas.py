"""
====================================================================
GUÍA DE MISIONES PYTHON - INDEL 3DS "B"
MISIÓN 6: Optimización de Carga del Camión de Vacas (Flet GUI)
Algoritmo: Problema de la Mochila 0/1 (Programación Dinámica)
====================================================================
"""

from dataclasses import dataclass
from typing import List, Tuple
import flet as ft


@dataclass
class Vaca:
    nombre: str
    peso: int       # En kilogramos
    litros: float   # En litros de leche


def optimizar_mochila(vacas: List[Vaca], capacidad_max: int) -> Tuple[float, int, List[Vaca]]:
    """Resuelve la mochila 0/1 para maximizar la producción de leche."""
    n = len(vacas)
    if n == 0 or capacidad_max <= 0:
        return 0.0, 0, []

    dp = [[0.0] * (capacidad_max + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        vaca = vacas[i - 1]
        peso = vaca.peso
        litros = vaca.litros

        for w in range(capacidad_max + 1):
            if peso <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - peso] + litros)
            else:
                dp[i][w] = dp[i - 1][w]

    seleccionadas = []
    w_restante = capacidad_max
    for i in range(n, 0, -1):
        if dp[i][w_restante] != dp[i - 1][w_restante]:
            vaca_elegida = vacas[i - 1]
            seleccionadas.append(vaca_elegida)
            w_restante -= vaca_elegida.peso

    seleccionadas.reverse()
    peso_total = sum(v.peso for v in seleccionadas)
    max_produccion = dp[n][capacidad_max]

    return max_produccion, peso_total, seleccionadas


def main(page: ft.Page):
    page.title = "Misión 6: Camión de Vacas · Mochila 0/1"
    page.theme_mode = "dark"
    page.padding = 20
    page.scroll = "adaptive"

    lista_vacas: List[Vaca] = []

    def mostrar_mensaje(texto: str, es_error: bool = False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(texto, color="white"),
            bgcolor="red700" if es_error else "teal700",
            duration=3000
        )
        page.snack_bar.open = True
        page.update()

    # Campos de Entrada
    txt_capacidad = ft.TextField(
        label="🚚 Capacidad del Camión (kg)",
        hint_text="Ej: 700",
        value="700",
        keyboard_type="number",
        width=260,
        border_color="cyan400"
    )

    txt_nombre = ft.TextField(
        label="🐄 Nombre / Id Vaca",
        hint_text="Ej: Margarita",
        width=220
    )

    txt_peso = ft.TextField(
        label="⚖️ Peso (kg)",
        hint_text="Ej: 360",
        keyboard_type="number",
        width=160
    )

    txt_litros = ft.TextField(
        label="🥛 Producción (Litros)",
        hint_text="Ej: 40.5",
        keyboard_type="number",
        width=180
    )

    # Tabla de vacas
    tabla_vacas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Peso (kg)"), numeric=True),
            ft.DataColumn(ft.Text("Litros (L)"), numeric=True),
            ft.DataColumn(ft.Text("Acción")),
        ],
        rows=[]
    )

    lbl_produccion_total = ft.Text("0.00 L", size=28, weight="bold", color="greenAccent")
    lbl_peso_usado = ft.Text("0 kg cargados", size=15, color="cyan200")
    lbl_peso_restante = ft.Text("Restante: 0 kg", size=15, color="amberAccent")
    barra_peso = ft.ProgressBar(value=0.0, width=400, color="cyan400", bgcolor="grey800")

    # Tabla de resultados
    tabla_seleccionadas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Vaca Seleccionada")),
            ft.DataColumn(ft.Text("Peso (kg)"), numeric=True),
            ft.DataColumn(ft.Text("Producción (L)"), numeric=True),
        ],
        rows=[]
    )

    def actualizar_tabla():
        tabla_vacas.rows.clear()
        for idx, vaca in enumerate(lista_vacas, start=1):
            def crear_borrar(index=idx-1):
                return lambda e: eliminar_vaca(index)

            tabla_vacas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(idx))),
                        ft.DataCell(ft.Text(vaca.nombre, weight="w500")),
                        ft.DataCell(ft.Text(f"{vaca.peso} kg")),
                        ft.DataCell(ft.Text(f"{vaca.litros:.2f} L")),
                        ft.DataCell(
                            ft.IconButton(
                                icon="delete",
                                icon_color="red400",
                                tooltip="Eliminar",
                                on_click=crear_borrar()
                            )
                        ),
                    ]
                )
            )
        page.update()

    def agregar_vaca(e):
        nombre = txt_nombre.value.strip()
        peso_str = txt_peso.value.strip()
        litros_str = txt_litros.value.strip()

        if not nombre:
            mostrar_mensaje("Debes ingresar el nombre de la vaca.", es_error=True)
            return

        try:
            peso = int(peso_str)
            litros = float(litros_str)
            if peso <= 0 or litros <= 0:
                raise ValueError()
        except ValueError:
            mostrar_mensaje("El peso y los litros deben ser números positivos.", es_error=True)
            return

        lista_vacas.append(Vaca(nombre, peso, litros))
        txt_nombre.value = ""
        txt_peso.value = ""
        txt_litros.value = ""
        actualizar_tabla()
        mostrar_mensaje(f"Vaca '{nombre}' agregada con éxito.")

    def eliminar_vaca(index: int):
        if 0 <= index < len(lista_vacas):
            eliminada = lista_vacas.pop(index)
            actualizar_tabla()
            mostrar_mensaje(f"Se eliminó a '{eliminada.nombre}'.")

    def cargar_datos_ejemplo(e):
        txt_capacidad.value = "700"
        lista_vacas.clear()
        lista_vacas.extend([
            Vaca("Margarita", 360, 40.0),
            Vaca("Lola",      250, 35.0),
            Vaca("Manchas",   400, 43.0),
            Vaca("Pinta",     180, 28.0),
            Vaca("Blanca",    220, 25.0),
            Vaca("Estrella",  120, 18.0),
        ])
        actualizar_tabla()
        mostrar_mensaje("Se cargaron 6 vacas de ejemplo (Capacidad: 700 kg).")

    def limpiar_todo(e):
        lista_vacas.clear()
        actualizar_tabla()
        tabla_seleccionadas.rows.clear()
        lbl_produccion_total.value = "0.00 L"
        lbl_peso_usado.value = "0 kg cargados"
        lbl_peso_restante.value = "Restante: 0 kg"
        barra_peso.value = 0.0
        page.update()
        mostrar_mensaje("Se limpiaron todos los datos.")

    def calcular_optimizacion(e):
        if not lista_vacas:
            mostrar_mensaje("Debes registrar al menos una vaca antes de calcular.", es_error=True)
            return

        try:
            capacidad = int(txt_capacidad.value.strip())
            if capacidad <= 0:
                raise ValueError()
        except ValueError:
            mostrar_mensaje("La capacidad del camión debe ser un entero positivo.", es_error=True)
            return

        max_litros, peso_usado, seleccionadas = optimizar_mochila(lista_vacas, capacidad)

        lbl_produccion_total.value = f"{max_litros:.2f} Litros"
        lbl_peso_usado.value = f"Cargado: {peso_usado:,} kg de {capacidad:,} kg"
        lbl_peso_restante.value = f"Espacio Libre: {capacidad - peso_usado:,} kg"
        barra_peso.value = (peso_usado / capacidad) if capacidad > 0 else 0.0

        tabla_seleccionadas.rows.clear()
        for v in seleccionadas:
            tabla_seleccionadas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"🐄 {v.nombre}", weight="bold", color="cyan100")),
                        ft.DataCell(ft.Text(f"{v.peso} kg")),
                        ft.DataCell(ft.Text(f"{v.litros:.2f} L", color="green300")),
                    ]
                )
            )

        page.update()
        mostrar_mensaje("¡Carga optimizada con éxito!")

    # Cargar datos al iniciar
    cargar_datos_ejemplo(None)

    # Componentes visuales
    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("🚜", size=32),
                ft.Text("MISIÓN 6: OPTIMIZACIÓN DE CARGA DE VACAS", size=22, weight="bold"),
            ]),
            ft.Text("Problema de la Mochila 0/1 con Programación Dinámica · INDEL 3DS \"B\"", color="grey400", size=13)
        ]),
        padding=15,
        bgcolor="#1E1E2E",
        border_radius=10
    )

    card_entradas = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("1. Configuración de Entrada", size=18, weight="bold", color="cyan300"),
                ft.Row([txt_capacidad]),
                ft.Divider(),
                ft.Text("Registrar Nueva Vaca:", size=15, weight="w500"),
                ft.Row([txt_nombre, txt_peso, txt_litros], wrap=True),
                ft.Row([
                    ft.ElevatedButton("➕ Agregar Vaca", on_click=agregar_vaca, bgcolor="cyan700", color="white"),
                    ft.OutlinedButton("🔄 Cargar Datos de Prueba", on_click=cargar_datos_ejemplo),
                    ft.OutlinedButton("🧹 Limpiar Todo", on_click=limpiar_todo),
                ], wrap=True),
            ]),
            padding=15
        )
    )

    card_tabla_vacas = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("2. Vacas Disponibles en el Corral", size=18, weight="bold", color="cyan300"),
                ft.Column([tabla_vacas], height=220, scroll="adaptive"),
                ft.FilledButton(
                    "🚀 OPTIMIZAR CARGA DEL CAMIÓN",
                    on_click=calcular_optimizacion,
                    style=ft.ButtonStyle(bgcolor="green700", padding=15),
                    width=350
                )
            ]),
            padding=15
        )
    )

    card_resultados = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("3. Resultados de la Carga Óptima", size=18, weight="bold", color="greenAccent"),
                ft.Row([
                    ft.Column([
                        ft.Text("Producción Máxima Obtenida:", size=14, color="grey400"),
                        lbl_produccion_total,
                    ]),
                    ft.VerticalDivider(width=30),
                    ft.Column([
                        lbl_peso_usado,
                        barra_peso,
                        lbl_peso_restante,
                    ]),
                ], alignment="spaceEvenly"),
                ft.Divider(),
                ft.Text("Vacas seleccionadas que suben al camión:", size=15, weight="bold"),
                ft.Column([tabla_seleccionadas], height=200, scroll="adaptive")
            ]),
            padding=20
        )
    )

    page.add(
        header,
        card_entradas,
        card_tabla_vacas,
        card_resultados
    )


if __name__ == "__main__":
    ft.app(target=main)