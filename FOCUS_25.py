import asyncio
from datetime import datetime, timedelta
import json
import os
import flet as ft


# ============= MODELOS =============
class Session:

    def __init__(self, date, subject, duration, xp, hour=None):
        self.date = date
        self.subject = subject
        self.duration = duration
        self.xp = xp
        self.hour = hour if hour is not None else datetime.now().hour

    def to_dict(self):
        return {
            "date": self.date,
            "subject": self.subject,
            "duration": self.duration,
            "xp": self.xp,
            "hour": self.hour,
        }

    @staticmethod
    def from_dict(data):
        return Session(
            data["date"],
            data["subject"],
            data["duration"],
            data["xp"],
            data.get("hour", 12),
        )


class SessionManager:

    def __init__(self):
        self.sessions = []
        self.file_path = "data/sessions.json"
        self.load_sessions()

    def load_sessions(self):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.sessions = [Session.from_dict(s) for s in data]
        except Exception as e:
            print(f"Error cargando sesiones: {e}")
            self.sessions = []

    def save_sessions(self):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(
                    [s.to_dict() for s in self.sessions],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            print(f"Error guardando sesiones: {e}")

    def add_session(self, session):
        self.sessions.append(session)
        self.save_sessions()

    def get_sessions_by_date(self, date):
        return [s for s in self.sessions if s.date == date]

    def get_earned_achievements(self):
        earned = set()

        if len(self.sessions) > 0:
            earned.add("first_session")

        for date in set(s.date for s in self.sessions):
            if len(self.get_sessions_by_date(date)) >= 4:
                earned.add("four_in_day")

        total_minutes = sum(s.duration for s in self.sessions)
        if total_minutes >= 600:
            earned.add("ten_hours")

        if self.calculate_streak() >= 7:
            earned.add("seven_day_streak")

        if any(s.hour < 7 for s in self.sessions):
            earned.add("early_bird")

        for date in set(s.date for s in self.sessions):
            subjects = set(s.subject for s in self.get_sessions_by_date(date))
            if len(subjects) >= 3:
                earned.add("three_subjects")

        return earned

    def calculate_streak(self):
        if not self.sessions:
            return 0

        dates = set(s.date for s in self.sessions)
        if not dates:
            return 0

        streak = 0
        check_date = datetime.now()
        date_str = check_date.strftime("%Y-%m-%d")

        if date_str not in dates:
            check_date -= timedelta(days=1)
            date_str = check_date.strftime("%Y-%m-%d")

        while date_str in dates:
            streak += 1
            check_date -= timedelta(days=1)
            date_str = check_date.strftime("%Y-%m-%d")

        return streak


class UserStats:

    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.stats = {}

    def update_stats(self):
        sessions = self.session_manager.sessions

        total_sessions = len(sessions)
        total_minutes = sum(s.duration for s in sessions)
        total_hours = total_minutes / 60

        total_xp = sum(s.xp for s in sessions)
        level = total_xp // 100 + 1
        experience = total_xp % 100

        subject_counts = {}
        for s in sessions:
            subject_counts[s.subject] = (
                subject_counts.get(s.subject, 0) + s.duration
            )
        top_subject = (
            max(subject_counts, key=subject_counts.get)
            if subject_counts
            else "Ninguna"
        )

        week_data = {}
        today = datetime.now()
        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            day_sessions = self.session_manager.get_sessions_by_date(date)
            week_data[date] = sum(s.duration for s in day_sessions)

        week_data_inverted = dict(reversed(list(week_data.items())))

        self.stats = {
            "total_sessions": total_sessions,
            "total_hours": total_hours,
            "total_xp": total_xp,
            "level": level,
            "next_level_xp": 100,
            "experience": experience,
            "streak": self.session_manager.calculate_streak(),
            "top_subject": top_subject,
            "week_data": week_data_inverted,
        }

    def get_stats(self):
        return self.stats


# ============= APP PRINCIPAL =============
class FocusApp:

    def __init__(self):
        self.session_manager = SessionManager()
        self.user_stats = UserStats(self.session_manager)

        self.is_running = False
        self.is_paused = False

        self.focus_duration = 25 * 60
        self.short_break_duration = 5 * 60
        self.long_break_duration = 15 * 60

        self.current_time = self.focus_duration
        self.max_time = self.focus_duration
        self.target_end_time = None

        self.session_count = 0
        self.current_mode = "focus"
        self.current_subject = "Matemática"
        self.task = None

        self.subjects = [
            "Matemática",
            "Base de Datos",
            "Inglés",
            "Física",
            "Programación",
            "Otra",
        ]

        self.achievements = [
            {
                "id": "first_session",
                "name": "Primera Sesión",
                "icon": "🌟",
                "requirement": "Completar tu primera sesión",
            },
            {
                "id": "four_in_day",
                "name": "Racha Diaria",
                "icon": "🔥",
                "requirement": "4 sesiones en un día",
            },
            {
                "id": "ten_hours",
                "name": "Dedicación",
                "icon": "⏱️",
                "requirement": "Acumular 10 horas",
            },
            {
                "id": "seven_day_streak",
                "name": "Semana Completa",
                "icon": "📅",
                "requirement": "Racha de 7 días",
            },
            {
                "id": "early_bird",
                "name": "Madrugador",
                "icon": "🌅",
                "requirement": "Sesión antes de las 7:00 a. m.",
            },
            {
                "id": "three_subjects",
                "name": "Versátil",
                "icon": "📚",
                "requirement": "3 materias en un día",
            },
        ]

    async def main(self, page: ft.Page):
        self.page = page
        page.title = "FOCUS 25"
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#0a0a1a"
        page.padding = 20

        self.session_manager.load_sessions()
        self.user_stats.update_stats()

        self.timer_view = self.create_timer_view()
        self.stats_view = self.create_stats_view()
        self.achievements_view = self.create_achievements_view()

        self.nav_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.TIMER, label="Temporizador"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BAR_CHART, label="Estadísticas"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.EMOJI_EVENTS, label="Logros"
                ),
            ],
            on_change=self.change_view,
        )

        self.content_container = ft.Container(
            content=self.timer_view, expand=True, padding=10
        )

        page.add(
            ft.Column(
                [self.content_container, self.nav_bar], expand=True, spacing=0
            )
        )

        self.update_stats_display(refresh_page=False)
        self.update_achievements_display(refresh_page=False)
        page.update()

    def play_sound(self):
        """Reproduce sonido con soporte corregido para Flet mediante page.run_js()."""
        try:
            sound_url = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"
            if hasattr(self.page, "run_js"):
                self.page.run_js(f"new Audio('{sound_url}').play();")
            elif hasattr(self.page, "launch_url"):
                self.page.launch_url(
                    f"javascript:new Audio('{sound_url}').play();"
                )
        except Exception as e:
            print(f"Error al reproducir sonido: {e}")

    def change_view(self, e):
        index = e.control.selected_index
        if index == 0:
            self.content_container.content = self.timer_view
            self.update_timer_display()
        elif index == 1:
            self.content_container.content = self.stats_view
            self.update_stats_display(refresh_page=False)
        elif index == 2:
            self.content_container.content = self.achievements_view
            self.update_achievements_display(refresh_page=False)
        self.page.update()

    def toggle_test_mode(self, e):
        is_test = self.test_mode_switch.value
        if is_test:
            self.focus_duration = 10
            self.short_break_duration = 5
            self.long_break_duration = 10
        else:
            self.focus_duration = 25 * 60
            self.short_break_duration = 5 * 60
            self.long_break_duration = 15 * 60

        if not self.is_running:
            if self.current_mode == "focus":
                self.max_time = self.focus_duration
            elif self.current_mode == "short_break":
                self.max_time = self.short_break_duration
            else:
                self.max_time = self.long_break_duration
            self.current_time = self.max_time
            self.update_timer_display()

    def create_timer_view(self):
        self.subject_dropdown = ft.Dropdown(
            width=180,
            options=[ft.dropdown.Option(subject) for subject in self.subjects],
            value="Matemática",
        )
        self.subject_dropdown.on_change = self.on_subject_change

        self.subject_input = ft.TextField(
            width=130,
            label="Otra materia",
            visible=False,
            on_submit=self.on_custom_subject,
        )

        self.test_mode_switch = ft.Switch(
            label="Modo Prueba (10s)",
            value=False,
            on_change=self.toggle_test_mode,
        )

        self.mode_title = ft.Text(
            "ENFOQUE", size=24, weight=ft.FontWeight.BOLD, color="#4FC3F7"
        )

        self.progress_ring = ft.ProgressRing(
            value=1.0,
            width=230,
            height=230,
            stroke_width=12,
            color="#4FC3F7",
            bgcolor="#1A1A3A",
        )

        self.time_display = ft.Text(
            "25:00", size=56, weight=ft.FontWeight.BOLD, color="#FFFFFF"
        )

        self.session_status = ft.Text(
            "Listo para comenzar", size=16, color="#8888AA"
        )

        self.session_counter = ft.Text(
            f"Sesión {self.session_count + 1}", size=14, color="#666688"
        )

        self.honor_notice = ft.Text(
            "🤝 Modo Honor: Esta app no bloquea el teléfono",
            size=11,
            color="#555577",
            italic=True,
        )

        self.start_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_FILLED,
            icon_size=60,
            icon_color="#4CAF50",
            on_click=self.start_timer,
        )

        self.pause_btn = ft.IconButton(
            icon=ft.Icons.PAUSE_CIRCLE_FILLED,
            icon_size=60,
            icon_color="#FFEB3B",
            on_click=self.pause_timer,
            visible=False,
        )

        self.reset_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_size=38,
            icon_color="#8888AA",
            on_click=self.reset_timer,
        )

        button_container = ft.Row(
            [self.reset_btn, self.start_btn, self.pause_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [self.subject_dropdown, self.subject_input],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    self.test_mode_switch,
                    ft.Container(height=5),
                    self.mode_title,
                    ft.Container(height=5),
                    ft.Stack(
                        [
                            self.progress_ring,
                            ft.Container(
                                content=ft.Column(
                                    [
                                        self.time_display,
                                        ft.Text(
                                            "minutos", size=14, color="#8888AA"
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                width=230,
                                height=230,
                            ),
                        ],
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(height=5),
                    self.session_status,
                    self.session_counter,
                    self.honor_notice,
                    ft.Container(height=10),
                    button_container,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
        )

    def create_stats_view(self):
        self.total_sessions_text = ft.Text(
            "0", size=36, weight=ft.FontWeight.BOLD, color="#FFFFFF"
        )
        self.total_hours_text = ft.Text(
            "0", size=36, weight=ft.FontWeight.BOLD, color="#FFFFFF"
        )
        self.level_text = ft.Text(
            "Nivel 1", size=22, weight=ft.FontWeight.BOLD, color="#4FC3F7"
        )
        self.experience_text = ft.Text("0/100 XP", size=14, color="#8888AA")
        self.streak_text = ft.Text("🔥 0 días", size=16, color="#FFFFFF")

        self.bars_container = ft.Column(spacing=5)
        self.top_subject_text = ft.Text("Ninguna", size=16, color="#FFFFFF")

        self.exp_progress = ft.ProgressBar(
            width=280, value=0, color="#4FC3F7", bgcolor="#1A1A3A"
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "ESTADÍSTICAS",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#FFFFFF",
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    self.total_sessions_text,
                                    ft.Text(
                                        "Sesiones", size=12, color="#8888AA"
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0,
                            ),
                            ft.Column(
                                [
                                    self.total_hours_text,
                                    ft.Text("Horas", size=12, color="#8888AA"),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0,
                            ),
                            ft.Column(
                                [
                                    self.streak_text,
                                    ft.Text("Racha", size=12, color="#8888AA"),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "PROGRESO",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color="#FFFFFF",
                    ),
                    self.level_text,
                    self.experience_text,
                    self.exp_progress,
                    ft.Container(height=15),
                    ft.Text(
                        "ÚLTIMA SEMANA",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color="#FFFFFF",
                    ),
                    self.bars_container,
                    ft.Container(height=10),
                    ft.Text("Materia más usada:", size=13, color="#8888AA"),
                    self.top_subject_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )

    def create_achievements_view(self):
        self.achievements_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=180,
            spacing=12,
            run_spacing=12,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "LOGROS",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#FFFFFF",
                    ),
                    ft.Container(height=10),
                    self.achievements_grid,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
        )

    def on_subject_change(self, e):
        if self.subject_dropdown.value == "Otra":
            self.subject_input.visible = True
        else:
            self.subject_input.visible = False
            self.current_subject = self.subject_dropdown.value
        self.page.update()

    def on_custom_subject(self, e):
        if self.subject_input.value:
            self.current_subject = self.subject_input.value
            self.subject_input.visible = False
            self.subject_dropdown.value = "Otra"
            self.page.update()

    async def timer_task(self):
        """Tarea asíncrona del temporizador basada en tiempo real para evitar congelamientos."""
        try:
            while self.is_running and not self.is_paused:
                now = datetime.now()
                remaining = int(
                    (self.target_end_time - now).total_seconds() + 0.5
                )

                if remaining >= 0:
                    self.current_time = remaining
                    self.update_timer_display()
                    await asyncio.sleep(0.5)
                else:
                    self.current_time = 0
                    self.update_timer_display()
                    await self.complete_session()
                    break
        except asyncio.CancelledError:
            pass

    async def start_timer(self, e):
        if not self.current_subject:
            self.current_subject = "Matemática"

        if self.task and not self.task.done():
            self.task.cancel()

        self.is_running = True
        self.is_paused = False
        self.start_btn.visible = False
        self.pause_btn.visible = True

        # Establece el momento exacto en el que finalizará
        self.target_end_time = datetime.now() + timedelta(
            seconds=self.current_time
        )

        if self.current_time == self.max_time:
            if self.current_mode == "focus":
                self.session_status.value = "🎯 Enfoque activo"
            else:
                self.session_status.value = "☕ Descanso activo"
        else:
            self.session_status.value = "▶ Continuando..."

        self.task = asyncio.create_task(self.timer_task())
        self.page.update()

    async def pause_timer(self, e):
        if self.is_running:
            self.is_paused = True
            if self.task and not self.task.done():
                self.task.cancel()

            # Guardar el tiempo restante actual al pausar
            if self.target_end_time:
                remaining = int(
                    (self.target_end_time - datetime.now()).total_seconds()
                )
                self.current_time = max(0, remaining)

            self.pause_btn.visible = False
            self.start_btn.visible = True
            self.session_status.value = "⏸ Pausado"
            self.update_timer_display()

    async def reset_timer(self, e):
        self.is_running = False
        self.is_paused = False
        if self.task and not self.task.done():
            self.task.cancel()

        self.current_time = self.max_time
        self.start_btn.visible = True
        self.pause_btn.visible = False

        if self.current_mode == "focus":
            self.session_status.value = "Listo para comenzar"
        else:
            self.session_status.value = "Listo para descansar"

        self.update_timer_display()

    def update_timer_display(self):
        minutes = self.current_time // 60
        seconds = self.current_time % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.time_display.value = time_str

        progress = (
            self.current_time / self.max_time if self.max_time > 0 else 1.0
        )
        self.progress_ring.value = progress

        if self.current_mode == "focus":
            color = "#4FC3F7" if progress > 0.3 else "#FF9800"
            self.progress_ring.color = color
        else:
            self.progress_ring.color = "#4CAF50"

        if hasattr(self, "page") and self.page:
            self.page.update()

    def show_level_up_dialog(self, new_level):
        dlg = ft.AlertDialog(
            title=ft.Text(
                "🎉 ¡NIVEL ALCANZADO!",
                weight=ft.FontWeight.BOLD,
                color="#4FC3F7",
            ),
            content=ft.Text(
                f"¡Felicidades! Has subido al Nivel {new_level}.\n¡Sigue así!",
                size=16,
            ),
            actions=[
                ft.TextButton(
                    "¡Genial!", on_click=lambda e: self.page.close(dlg)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        self.page.open(dlg)

    async def complete_session(self):
        self.play_sound()

        if self.current_mode == "focus":
            old_level = self.user_stats.get_stats().get("level", 1)

            session = Session(
                date=datetime.now().strftime("%Y-%m-%d"),
                subject=self.current_subject,
                duration=max(1, self.focus_duration // 60),
                xp=10,
                hour=datetime.now().hour,
            )
            self.session_manager.add_session(session)
            self.user_stats.update_stats()

            new_level = self.user_stats.get_stats().get("level", 1)
            if new_level > old_level:
                self.show_level_up_dialog(new_level)

            self.session_count += 1
            self.session_counter.value = f"Sesión {self.session_count + 1}"
            self.session_status.value = "🎉 ¡Sesión completada! (+10 XP)"

            await asyncio.sleep(2)

            if (self.session_count % 4) == 0:
                self.current_mode = "long_break"
                self.max_time = self.long_break_duration
                self.mode_title.value = "DESCANSO LARGO"
                self.mode_title.color = "#CE93D8"
                self.session_status.value = "🌿 Tiempo de descanso largo"
            else:
                self.current_mode = "short_break"
                self.max_time = self.short_break_duration
                self.mode_title.value = "DESCANSO CORTO"
                self.mode_title.color = "#81C784"
                self.session_status.value = "☕ Tiempo de descanso corto"

        else:
            self.current_mode = "focus"
            self.max_time = self.focus_duration
            self.mode_title.value = "ENFOQUE"
            self.mode_title.color = "#4FC3F7"
            self.session_status.value = "🎯 ¡Nueva sesión lista!"

        self.current_time = self.max_time
        self.is_running = False
        self.is_paused = False
        self.start_btn.visible = True
        self.pause_btn.visible = False

        self.update_timer_display()
        self.update_stats_display(refresh_page=False)
        self.update_achievements_display(refresh_page=False)
        self.page.update()

    def update_stats_display(self, refresh_page=True):
        stats = self.user_stats.get_stats()

        self.total_sessions_text.value = str(stats.get("total_sessions", 0))
        self.total_hours_text.value = str(
            round(stats.get("total_hours", 0), 1)
        )
        self.level_text.value = f"Nivel {stats.get('level', 1)}"
        self.experience_text.value = f"{stats.get('experience', 0)}/{stats.get('next_level_xp', 100)} XP"

        exp_progress = (
            stats.get("experience", 0) / stats.get("next_level_xp", 100)
            if stats.get("next_level_xp", 100) > 0
            else 0
        )
        self.exp_progress.value = min(exp_progress, 1.0)

        self.streak_text.value = f"🔥 {stats.get('streak', 0)} días"
        self.top_subject_text.value = stats.get("top_subject", "Ninguna")

        self.update_bars(stats.get("week_data", {}))
        if refresh_page and hasattr(self, "page"):
            self.page.update()

    def update_bars(self, week_data):
        """Actualiza el gráfico mapeando correctamente el día de la semana real según la fecha."""
        self.bars_container.controls.clear()
        max_minutes = (
            max(week_data.values())
            if week_data and sum(week_data.values()) > 0
            else 1
        )

        day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

        for date_str, minutes in week_data.items():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = day_names[date_obj.weekday()]
            except Exception:
                day_name = date_str

            bar_width = (minutes / max_minutes) * 180 if max_minutes > 0 else 0

            self.bars_container.controls.append(
                ft.Row(
                    [
                        ft.Text(day_name, width=35, size=13, color="#FFFFFF"),
                        ft.Container(
                            height=20,
                            width=max(bar_width, 5),
                            bgcolor="#4FC3F7" if minutes > 0 else "#1A1A3A",
                            border_radius=4,
                        ),
                        ft.Text(
                            f"{minutes}m", size=11, width=35, color="#8888AA"
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

    def update_achievements_display(self, refresh_page=True):
        self.achievements_grid.controls.clear()

        earned = self.session_manager.get_earned_achievements()

        for achievement in self.achievements:
            is_earned = achievement["id"] in earned

            color = "#4CAF50" if is_earned else "#666688"
            bgcolor = "#1A1A3A" if is_earned else "#0A0A1A"

            border_style = (
                ft.Border(
                    top=ft.BorderSide(2, color),
                    bottom=ft.BorderSide(2, color),
                    left=ft.BorderSide(2, color),
                    right=ft.BorderSide(2, color),
                )
                if is_earned
                else None
            )

            self.achievements_grid.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(achievement["icon"], size=36),
                            ft.Text(
                                achievement["name"],
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=color,
                            ),
                            ft.Text(
                                achievement["requirement"],
                                size=11,
                                color="#8888AA",
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=3,
                    ),
                    bgcolor=bgcolor,
                    border_radius=10,
                    padding=10,
                    border=border_style,
                )
            )

        if refresh_page and hasattr(self, "page"):
            self.page.update()


# ============= EJECUCIÓN =============
if __name__ == "__main__":
    app = FocusApp()
    ft.app(target=app.main)