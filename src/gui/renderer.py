import pygame
import pytmx

TILE_SIZE = 16
# Constantes de la UI
UI_PANEL_WIDTH = 280
GAME_AREA_WIDTH = 1280 - UI_PANEL_WIDTH
UI_BG_COLOR = (40, 40, 55); UI_BORDER_COLOR = (80, 80, 100); TEXT_COLOR = (230, 230, 230)
HEADER_COLOR = (150, 180, 255); RECURSO_COLOR = (255, 220, 150)
ARTEFACTO_COLOR = (255, 100, 255); EFECTO_ACTIVO_COLOR = (100, 255, 255)
STATE_IDLE_COLOR=(100,200,100); STATE_MOVING_COLOR=(100,150,255); STATE_WORKING_COLOR=(255,180,80)
STATE_PLANNING_COLOR=(200,120,200); STATE_SICK_COLOR=(180,50,180); STATE_MANUAL_COLOR=(255,255,100)
STATE_CHASING_COLOR=(255,100,100); STATE_ATTACKING_COLOR=(255,50,50); TASK_HEAL_COLOR=(50,255,180)
TASK_CHEER_COLOR = (255, 180, 255); EVENTO_LLUVIA_COLOR = (255, 100, 100)
EVENTO_LAVA_COLOR = (255, 150, 0) # Naranja
MENU_BG_COLOR=(30,30,40,230); MENU_BORDER_COLOR=(100,100,120); MENU_TEXT_COLOR=(200,200,220)
MENU_HIGHLIGHT_COLOR=(255,255,150); MENU_CAN_AFFORD_COLOR=(100,255,100); MENU_CANNOT_AFFORD_COLOR=(255,100,100)
MENU_COST_COLOR_WOOD=(180,140,90); MENU_COST_COLOR_STONE=(150,150,160); MENU_COST_COLOR_FOOD=(200, 180, 100)
TIER_COLORS=[(255,255,255),(100,100,255),(180,80,180),(255,255,0)]
ENEMY_NAME_COLOR=(255,80,80)
HEALTH_BAR_BG = (80, 0, 0); HEALTH_BAR_HIGH = (0, 200, 0); HEALTH_BAR_MEDIUM = (255, 255, 0);
HEALTH_BAR_LOW = (255, 0, 0); HEALTH_BAR_BORDER = (50, 50, 50)
VICTORY_BG_COLOR = (20, 20, 30, 240); VICTORY_TEXT_COLOR = (255, 255, 100); VICTORY_PROMPT_COLOR = (180, 180, 180)
SPLASH_BG_COLOR = (10, 15, 20); SPLASH_TITLE_COLOR = (100, 255, 100); SPLASH_PROMPT_COLOR = (200, 200, 200)
INFO_BG_COLOR = (20, 20, 30); INFO_TITLE_COLOR = (255, 255, 150); INFO_TEXT_COLOR = (200, 200, 220)


class Renderer:
    """Maneja todas las operaciones de dibujo para el juego."""
    def __init__(self, screen, mundo, game, screen_width, screen_height, game_scale, view_tile_size, ui_width=None):
        self.screen = screen; self.mundo = mundo; self.game = game
        self.SCREEN_WIDTH = screen_width; self.SCREEN_HEIGHT = screen_height
        self.game_scale = game_scale; self.view_tile_size = view_tile_size
        
        # Fuentes
        self.ui_font = pygame.font.SysFont("Arial", 18); self.log_font = pygame.font.SysFont("Consolas", 14)
        self.colono_name_font = pygame.font.SysFont("Arial", 12); self.stats_font = pygame.font.SysFont("Arial", 15)
        self.artefacto_font = pygame.font.SysFont("Arial", 16)
        self.menu_title_font = pygame.font.SysFont("Arial", 28, bold=True); self.menu_section_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.menu_font = pygame.font.SysFont("Arial", 18); self.menu_cost_font = pygame.font.SysFont("Arial", 16)
        self.menu_prompt_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.victory_title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.victory_prompt_font = pygame.font.SysFont("Arial", 24)
        self.splash_title_font = pygame.font.SysFont("Arial", 52, bold=True)
        self.splash_prompt_font = pygame.font.SysFont("Arial", 26, italic=True)
        self.info_title_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.info_font = pygame.font.SysFont("Arial", 18)
        self.info_note_font = pygame.font.SysFont("Arial", 16, italic=True)
        self.tribu_stats_font = pygame.font.SysFont("Consolas", 14)
        self.game_time_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.evento_font = pygame.font.SysFont("Arial", 16, bold=True)

        # Cargar imagen de fondo del Splash Screen
        self.fondo_splash_scaled = None
        try:
            path_fondo = "assets/sprites/fondo.png"
            img_fondo = pygame.image.load(path_fondo).convert()
            self.fondo_splash_scaled = pygame.transform.scale(img_fondo, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        except Exception as e:
            print(f"ERROR: No se pudo cargar la imagen de fondo '{path_fondo}': {e}")
            self.fondo_splash_scaled = None # Usará color sólido como fallback
        
        # --- ¡NUEVO! Cargar imagen de fondo del Final Screen ---
        self.fondo_fin_scaled = None
        try:
            path_fin = "assets/sprites/fin.png"
            img_fin = pygame.image.load(path_fin).convert()
            # Escalamos la imagen al tamaño total de la ventana
            self.fondo_fin_scaled = pygame.transform.scale(img_fin, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        except Exception as e:
            print(f"ERROR: No se pudo cargar la imagen de fin '{path_fin}': {e}")
            self.fondo_fin_scaled = None # Usará color sólido como fallback
        # -----------------------------------------------------


    def draw(self, camera_x, camera_y, selected_colono,
             showing_acopio_menu, creando_iguana_clase,
             acopio_tier, damage_tier,
             acopio_upgrades, damage_upgrades,
             juego_terminado, game_state,
             showing_tribu_menu,
             dia, mes, año,
             debug_mode=False):
        
        self.screen.fill(UI_BG_COLOR)

        if game_state == 'SPLASH_SCREEN': self._draw_splash_screen()
        elif game_state == 'INFO_SCREEN': self._draw_info_screen()
        else:
            game_surface = self.screen.subsurface(pygame.Rect(0, 0, GAME_AREA_WIDTH, self.SCREEN_HEIGHT))
            camera_rect = pygame.Rect(camera_x, camera_y, GAME_AREA_WIDTH, self.SCREEN_HEIGHT)
            self._draw_game_world(game_surface, camera_x, camera_y, camera_rect, selected_colono, acopio_tier, damage_tier)
            self._draw_ui_panel(selected_colono, acopio_tier, damage_tier)
            self._draw_game_time_overlay(dia, mes, año)
            
            if showing_acopio_menu:
                 self._draw_acopio_menu(acopio_tier, damage_tier, acopio_upgrades, damage_upgrades, creando_iguana_clase)
            elif showing_tribu_menu:
                 self._draw_tribu_menu()
            elif juego_terminado:
                 self._draw_victory_screen()
        
        pygame.display.flip()

    def _draw_game_world(self, surface, camera_x, camera_y, camera_rect, selected_colono, acopio_tier, damage_tier):
        surface.fill((25, 25, 40))
        self._draw_map(surface, camera_x, camera_y, camera_rect)
        self._draw_objects(surface, camera_x, camera_y, camera_rect)
        self._draw_tareas(surface, camera_x, camera_y, camera_rect)
        self._draw_colonos(surface, camera_x, camera_y, camera_rect, selected_colono, acopio_tier, damage_tier)
        self._draw_protecciones(surface, camera_x, camera_y, camera_rect)
        self._draw_log(surface)

    def _draw_game_time_overlay(self, dia, mes, año):
        time_text = f"Año {año} - Mes {mes} - Día {dia}"
        time_surf = self.game_time_font.render(time_text, True, (255, 255, 255))
        time_rect = time_surf.get_rect(centerx=GAME_AREA_WIDTH // 2, top=10)
        self.screen.blit(time_surf, time_rect)

    def _draw_splash_screen(self):
        if self.fondo_splash_scaled:
            self.screen.blit(self.fondo_splash_scaled, (0, 0))
        else:
            self.screen.fill(SPLASH_BG_COLOR) # Fallback de color sólido
        
        title_text = "Entrar a la Casa De Las Iguanas"; title_surf = self.splash_title_font.render(title_text, True, SPLASH_TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 40)); self.screen.blit(title_surf, title_rect)
        prompt_text = "Presiona [ESPACIO] para continuar"; prompt_surf = self.splash_prompt_font.render(prompt_text, True, SPLASH_PROMPT_COLOR)
        prompt_rect = prompt_surf.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 50)); self.screen.blit(prompt_surf, prompt_rect)

    def _draw_info_screen(self):
        self.screen.fill(INFO_BG_COLOR)
        x_margin = 50; y_offset = 50
        title_surf = self.info_title_font.render("Información útil:", True, INFO_TITLE_COLOR)
        self.screen.blit(title_surf, (x_margin, y_offset)); y_offset += title_surf.get_height() + 30
        tips = [
            "- No dudes en recolectar muchos recursos, sin duda serán muy útiles a la hora de",
            "  conquistar el mapa, y quizás encuentres algún artefacto perdido.",
            "- Los recursos sirven para mejorar a tus iguanas, incluso crear nuevas, desde el",
            "  centro de acopio (tecla [Z]).",
            "- Cuidado con las enfermedades o que alguna iguana sufra alguna tragedia, si te",
            "  llega a suceder alguna, no dudes en acudir a tus curanderos (tecla [C]).",
            "- Las iguanas amarillas deberían de ser tu primer objetivo, no lucen tan imponentes,",
            "  quizás al eliminarlas obtengas alguna recompensa, las azules digamos que son el",
            "  punto medio, pero si llegas a ver a una roja, simplemente CORRE.",
            "- NOTA: no te acerques a 5 tiles de distancia de cualquier iguana enemiga, son",
            "  altamente hostiles y no dudarán en acabar contigo si te acercas, te recomiendo",
            "  estar bien preparado antes de luchar; prepara a tu ejército."
        ]
        for line in tips:
            font_to_use = self.info_font; color = INFO_TEXT_COLOR; x_pos = x_margin
            if line.strip().startswith("NOTA:"): font_to_use = self.info_note_font; color = (255, 100, 100); y_offset += 10
            elif not line.strip().startswith("-"): x_pos += 15
            line_surf = font_to_use.render(line, True, color); self.screen.blit(line_surf, (x_pos, y_offset)); y_offset += font_to_use.get_linesize()
        prompt_text = "Presiona [ESPACIO] para comenzar"
        prompt_surf = self.splash_prompt_font.render(prompt_text, True, SPLASH_PROMPT_COLOR)
        prompt_rect = prompt_surf.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - 60)); self.screen.blit(prompt_surf, prompt_rect)
    
    def _draw_victory_screen(self):
        # --- ¡CAMBIO AQUÍ! Dibuja la imagen de fondo del final ---
        if self.fondo_fin_scaled:
            self.screen.blit(self.fondo_fin_scaled, (0, 0))
        else:
            # Si la imagen no carga, usa el color de fondo original con transparencia
            overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(VICTORY_BG_COLOR)
            self.screen.blit(overlay, (0, 0))
        # --------------------------------------------------------
        
        # Superponer un semi-transparente para asegurar la legibilidad del texto
        overlay_text = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_text.fill((20, 20, 30, 150)) # Un poco más transparente que VICTORY_BG_COLOR
        self.screen.blit(overlay_text, (0,0))

        title_text = "Te toca apagar las luces de La Casa De Las Iguanas"; title_surf = self.victory_title_font.render(title_text, True, VICTORY_TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 30)); self.screen.blit(title_surf, title_rect)
        prompt_text = "Presiona [ESPACIO] para salir."; prompt_surf = self.victory_prompt_font.render(prompt_text, True, VICTORY_PROMPT_COLOR)
        prompt_rect = prompt_surf.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 40)); self.screen.blit(prompt_surf, prompt_rect)


    def _draw_acopio_menu(self, acopio_tier, damage_tier, acopio_upgrades, damage_upgrades, creando_iguana_clase):
        menu_width = 550; menu_height = 550
        menu_x = (self.SCREEN_WIDTH - menu_width) // 2; menu_y = (self.SCREEN_HEIGHT - menu_height) // 2
        menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA); menu_surface.fill(MENU_BG_COLOR)
        border_rect = pygame.Rect(0, 0, menu_width, menu_height); pygame.draw.rect(menu_surface, MENU_BORDER_COLOR, border_rect, 3)
        y_offset = 20
        title_surf = self.menu_title_font.render("Centro de Acopio", True, MENU_HIGHLIGHT_COLOR)
        title_rect = title_surf.get_rect(centerx=menu_width // 2, top=y_offset); menu_surface.blit(title_surf, title_rect)
        y_offset += title_surf.get_height() + 25
        section_vida_surf = self.menu_section_font.render("Acopio (Vida) - Mejorar con [U]", True, HEADER_COLOR)
        menu_surface.blit(section_vida_surf, (30, y_offset)); y_offset += section_vida_surf.get_height() + 5
        tier_text = f" Tier Actual: {acopio_tier}"; tier_surf = self.menu_font.render(tier_text, True, MENU_TEXT_COLOR)
        menu_surface.blit(tier_surf, (40, y_offset)); y_offset += tier_surf.get_height() + 3
        max_vida_actual = acopio_upgrades[acopio_tier]["max_vida"]; vida_text = f" Vida Máxima: {max_vida_actual}"
        vida_surf = self.menu_font.render(vida_text, True, MENU_TEXT_COLOR); menu_surface.blit(vida_surf, (40, y_offset))
        y_offset += vida_surf.get_height() + 8
        next_acopio_tier = acopio_tier + 1
        if next_acopio_tier < len(acopio_upgrades):
            upgrade_info = acopio_upgrades[next_acopio_tier]; costo = upgrade_info["costo_comida"]; new_max_vida = upgrade_info["max_vida"]
            can_afford = self.mundo.recursos["comida"] >= costo; costo_color = MENU_CAN_AFFORD_COLOR if can_afford else MENU_CANNOT_AFFORD_COLOR
            prox_text = f" Próximo Tier ({next_acopio_tier}):"; prox_surf = self.menu_font.render(prox_text, True, MENU_HIGHLIGHT_COLOR)
            menu_surface.blit(prox_surf, (40, y_offset)); y_offset += prox_surf.get_height() + 2
            costo_text = f"  Costo: {costo} Comida"; costo_surf = self.menu_cost_font.render(costo_text, True, costo_color)
            menu_surface.blit(costo_surf, (50, y_offset)); y_offset += costo_surf.get_height() + 2
            beneficio_text = f"  Vida -> {new_max_vida}"; beneficio_surf = self.menu_cost_font.render(beneficio_text, True, MENU_TEXT_COLOR)
            menu_surface.blit(beneficio_surf, (50, y_offset))
        else: y_offset = self._draw_line_on_surface(menu_surface, " (Máximo Nivel)", self.menu_font, MENU_HIGHLIGHT_COLOR, y_offset, 40, 0)
        y_offset += 20
        section_daño_surf = self.menu_section_font.render("Herrería (Daño) - Mejorar con [I]", True, HEADER_COLOR)
        menu_surface.blit(section_daño_surf, (30, y_offset)); y_offset += section_daño_surf.get_height() + 5
        tier_text_d = f" Tier Actual: {damage_tier}"; tier_surf_d = self.menu_font.render(tier_text_d, True, MENU_TEXT_COLOR)
        menu_surface.blit(tier_surf_d, (40, y_offset)); y_offset += tier_surf_d.get_height() + 3
        daño_actual = damage_upgrades[damage_tier]["daño_guerrero"]
        daño_text = f" Daño Guerrero: {daño_actual}"; daño_surf = self.menu_font.render(daño_text, True, MENU_TEXT_COLOR)
        menu_surface.blit(daño_surf, (40, y_offset)); y_offset += daño_surf.get_height() + 8
        next_damage_tier = damage_tier + 1
        if next_damage_tier < len(damage_upgrades):
            upgrade_info_d = damage_upgrades[next_damage_tier]; costo_p = upgrade_info_d["costo_piedra"]; costo_m = upgrade_info_d["costo_madera"]
            new_daño = upgrade_info_d["daño_guerrero"]
            can_afford_d = self.mundo.recursos["piedra"] >= costo_p and self.mundo.recursos["madera"] >= costo_m
            costo_p_color = MENU_CAN_AFFORD_COLOR if self.mundo.recursos["piedra"] >= costo_p else MENU_CANNOT_AFFORD_COLOR
            costo_m_color = MENU_CAN_AFFORD_COLOR if self.mundo.recursos["madera"] >= costo_m else MENU_CANNOT_AFFORD_COLOR
            prox_text_d = f" Próximo Tier ({next_damage_tier}):"; prox_surf_d = self.menu_font.render(prox_text_d, True, MENU_HIGHLIGHT_COLOR)
            menu_surface.blit(prox_surf_d, (40, y_offset)); y_offset += prox_surf_d.get_height() + 2
            costo_p_text = f"  Costo: {costo_p} Piedra"; costo_p_surf = self.menu_cost_font.render(costo_p_text, True, costo_p_color)
            menu_surface.blit(costo_p_surf, (50, y_offset)); y_offset += costo_p_surf.get_height() + 1
            costo_m_text = f"         {costo_m} Madera"; costo_m_surf = self.menu_cost_font.render(costo_m_text, True, costo_m_color)
            menu_surface.blit(costo_m_surf, (50, y_offset)); y_offset += costo_m_surf.get_height() + 2
            beneficio_text_d = f"  Daño -> {new_daño}"; beneficio_surf_d = self.menu_cost_font.render(beneficio_text_d, True, MENU_TEXT_COLOR)
            menu_surface.blit(beneficio_surf_d, (50, y_offset))
        else: y_offset = self._draw_line_on_surface(menu_surface, " (Máximo Nivel)", self.menu_font, MENU_HIGHLIGHT_COLOR, y_offset, 40, 0)
        y_offset += 20
        section_crear_surf = self.menu_section_font.render("Criadero - Crear Iguana [N]", True, HEADER_COLOR)
        menu_surface.blit(section_crear_surf, (30, y_offset)); y_offset += section_crear_surf.get_height() + 5
        costo_c = 100; costo_m = 100; costo_p = 100
        can_afford_new = self.mundo.recursos["comida"] >= costo_c and self.mundo.recursos["madera"] >= costo_m and self.mundo.recursos["piedra"] >= costo_p
        costo_c_color = MENU_CAN_AFFORD_COLOR if self.mundo.recursos["comida"] >= costo_c else MENU_CANNOT_AFFORD_COLOR
        costo_m_color = MENU_CAN_AFFORD_COLOR if self.mundo.recursos["madera"] >= costo_m else MENU_CANNOT_AFFORD_COLOR
        costo_p_color = MENU_CAN_AFFORD_COLOR if self.mundo.recursos["piedra"] >= costo_p else MENU_CANNOT_AFFORD_COLOR
        costo_c_text = f" Costo: {costo_c} Comida"; costo_c_surf = self.menu_cost_font.render(costo_c_text, True, costo_c_color)
        costo_m_text = f"        {costo_m} Madera"; costo_m_surf = self.menu_cost_font.render(costo_m_text, True, costo_m_color)
        costo_p_text = f"        {costo_p} Piedra"; costo_p_surf = self.menu_cost_font.render(costo_p_text, True, costo_p_color)
        menu_surface.blit(costo_c_surf, (40, y_offset)); y_offset += costo_c_surf.get_height() + 1
        menu_surface.blit(costo_m_surf, (40, y_offset)); y_offset += costo_m_surf.get_height() + 1
        menu_surface.blit(costo_p_surf, (40, y_offset)); y_offset += costo_p_surf.get_height() + 8
        if creando_iguana_clase == "SELECT_CLASS":
             prompt_text = "Elige Clase:"; prompt_surf = self.menu_prompt_font.render(prompt_text, True, MENU_HIGHLIGHT_COLOR)
             menu_surface.blit(prompt_surf, (40, y_offset)); y_offset += prompt_surf.get_height() + 3
             y_offset = self._draw_line_on_surface(menu_surface, "[1] Recolector", self.menu_font, TEXT_COLOR, y_offset, 50, 0)
             y_offset = self._draw_line_on_surface(menu_surface, "[2] Guerrero", self.menu_font, TEXT_COLOR, y_offset, 50, 0)
             y_offset = self._draw_line_on_surface(menu_surface, "[3] Curandero", self.menu_font, TEXT_COLOR, y_offset, 50, 0)
        elif can_afford_new:
             instruccion_text = "Presiona [N] para iniciar creación"
             instruccion_surf = self.menu_font.render(instruccion_text, True, MENU_CAN_AFFORD_COLOR)
             instruccion_rect = instruccion_surf.get_rect(centerx=menu_width // 2, top=y_offset)
             menu_surface.blit(instruccion_surf, instruccion_rect)
        else:
             instruccion_text = "Recursos insuficientes"
             instruccion_surf = self.menu_font.render(instruccion_text, True, MENU_CANNOT_AFFORD_COLOR)
             instruccion_rect = instruccion_surf.get_rect(centerx=menu_width // 2, top=y_offset)
             menu_surface.blit(instruccion_surf, instruccion_rect)
        y_offset += 40
        cerrar_text = "Presiona [Z] o [ESC] para cerrar"
        cerrar_surf = self.menu_font.render(cerrar_text, True, MENU_TEXT_COLOR)
        cerrar_rect = cerrar_surf.get_rect(centerx=menu_width // 2, bottom=menu_height - 20)
        menu_surface.blit(cerrar_surf, cerrar_rect)
        self.screen.blit(menu_surface, (menu_x, menu_y))

    def _draw_tribu_menu(self):
        menu_width = 700; menu_height = 550
        menu_x = (self.SCREEN_WIDTH - menu_width) // 2; menu_y = (self.SCREEN_HEIGHT - menu_height) // 2
        menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA); menu_surface.fill(MENU_BG_COLOR)
        border_rect = pygame.Rect(0, 0, menu_width, menu_height); pygame.draw.rect(menu_surface, MENU_BORDER_COLOR, border_rect, 3)
        y_offset = 20
        title_surf = self.menu_title_font.render("Estado de la Tribu", True, MENU_HIGHLIGHT_COLOR)
        title_rect = title_surf.get_rect(centerx=menu_width // 2, top=y_offset); menu_surface.blit(title_surf, title_rect)
        y_offset += title_surf.get_height() + 20
        header_text = f"{'Nombre':<30} {'Clase':<12} {'V/VM':<9} {'Ánimo':<7} {'Daño':<5} {'Estado':<10}"
        header_surf = self.tribu_stats_font.render(header_text, True, HEADER_COLOR)
        menu_surface.blit(header_surf, (30, y_offset)); y_offset += header_surf.get_height() + 5
        pygame.draw.line(menu_surface, HEADER_COLOR, (30, y_offset), (menu_width - 30, y_offset), 1); y_offset += 5
        jugadores = [c for c in self.mundo.colonos if not c.es_enemigo and not c.esta_muerto]
        enemigos = [c for c in self.mundo.colonos if c.es_enemigo and not c.esta_muerto]
        def dibujar_iguana_stats(colono, y_pos, color):
            nombre = colono.nombre[:28]; clase = colono.clase
            vida = f"{colono.vida}/{colono.max_vida}"; animo = f"{colono.estado_animo}%"
            daño = f"{colono.daño}" if colono.clase == 'guerrero' else "-"
            estado = colono.estado
            if colono.esta_enfermo: estado = "ENFERMO"
            stats_text = f"{nombre:<30} {clase:<12} {vida:<9} {animo:<7} {daño:<5} {estado:<10}"
            stats_surf = self.tribu_stats_font.render(stats_text, True, color)
            menu_surface.blit(stats_surf, (30, y_pos))
            return y_pos + stats_surf.get_height() + 2
        y_offset = self._draw_line_on_surface(menu_surface, "Tu Colonia:", self.menu_font, TIER_COLORS[1], y_offset, 30, 0); y_offset += 5
        for colono in jugadores: y_offset = dibujar_iguana_stats(colono, y_offset, TEXT_COLOR)
        y_offset += 15
        y_offset = self._draw_line_on_surface(menu_surface, "Enemigos:", self.menu_font, ENEMY_NAME_COLOR, y_offset, 30, 0); y_offset += 5
        for colono in enemigos: y_offset = dibujar_iguana_stats(colono, y_offset, ENEMY_NAME_COLOR)
        cerrar_text = "Presiona [T] o [ESC] para cerrar"
        cerrar_surf = self.menu_font.render(cerrar_text, True, MENU_TEXT_COLOR)
        cerrar_rect = cerrar_surf.get_rect(centerx=menu_width // 2, bottom=menu_height - 20)
        menu_surface.blit(cerrar_surf, cerrar_rect)
        self.screen.blit(menu_surface, (menu_x, menu_y))

    def _draw_map(self, surface, camera_x, camera_y, camera_rect):
        if self.mundo.tmx_data:
            for layer in self.mundo.tmx_data.visible_layers:
                if layer.name == "colisiones": continue
                if isinstance(layer, pytmx.TiledTileLayer):
                    for x, y, gid in layer:
                        tile = self.mundo.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            tile_rect = pygame.Rect(x*self.view_tile_size, y*self.view_tile_size, self.view_tile_size, self.view_tile_size)
                            if camera_rect.colliderect(tile_rect):
                                try: scaled_tile = pygame.transform.scale(tile, (self.view_tile_size, self.view_tile_size)); surface.blit(scaled_tile, (tile_rect.x - camera_x, tile_rect.y - camera_y))
                                except ValueError: pygame.draw.rect(surface, (255,0,255), tile_rect.move(-camera_x,-camera_y))

    def _draw_objects(self, surface, camera_x, camera_y, camera_rect):
        for sprite in self.mundo.objetos:
            if camera_rect.colliderect(sprite.rect):
                surface.blit(sprite.image, sprite.rect.move(-camera_x, -camera_y))
                
    def _draw_protecciones(self, surface, camera_x, camera_y, camera_rect):
        for sprite in self.mundo.proteccion_group:
            if camera_rect.colliderect(sprite.rect):
                surface.blit(sprite.image, sprite.rect.move(-camera_x, -camera_y))

    def _draw_colonos(self, surface, camera_x, camera_y, camera_rect, selected_colono, acopio_tier, damage_tier):
        for colono in self.mundo.colonos:
            if colono.esta_muerto: continue
            expanded_rect = colono.rect.inflate(0, 40)
            if camera_rect.colliderect(expanded_rect):
                if colono.path: self._draw_path(surface, colono.path, camera_x, camera_y)
                surface.blit(colono.image, colono.rect.move(-camera_x, -camera_y))
                if colono == selected_colono:
                    center_x=colono.rect.centerx-camera_x; center_y=colono.rect.centery-camera_y
                    radius = self.view_tile_size//2 + 2; pygame.draw.circle(surface,(255,255,255),(center_x,center_y),radius,2)
                if colono.es_enemigo: name_color = ENEMY_NAME_COLOR
                else: effective_tier = min(acopio_tier, damage_tier); tier_index = min(effective_tier, len(TIER_COLORS) - 1); name_color = TIER_COLORS[tier_index]
                
                estado_str = "HIDING" if colono.estado == 'HIDING' else colono.estado
                text_str = colono.nombre + (f" ({estado_str})" if colono.es_enemigo or colono.estado != 'IDLE' else "")
                if not colono.es_enemigo and colono.esta_enfermo: text_str += " [ENFERMO]"
                
                text_surface = self.colono_name_font.render(text_str, True, name_color)
                base_x = colono.rect.centerx - camera_x; base_y = colono.rect.y - camera_y
                bar_width = self.view_tile_size * 0.8; bar_height = 5
                bar_x = base_x - (bar_width // 2); bar_y = base_y - bar_height - 2
                health_percent = colono.vida / colono.max_vida
                health_color = HEALTH_BAR_LOW if health_percent < 0.3 else HEALTH_BAR_MEDIUM if health_percent < 0.6 else HEALTH_BAR_HIGH
                pygame.draw.rect(surface, HEALTH_BAR_BG, (bar_x, bar_y, bar_width, bar_height))
                current_health_width = int(bar_width * health_percent)
                if current_health_width > 0: pygame.draw.rect(surface, health_color, (bar_x, bar_y, current_health_width, bar_height))
                pygame.draw.rect(surface, HEALTH_BAR_BORDER, (bar_x, bar_y, bar_width, bar_height), 1)
                text_x = base_x - (text_surface.get_width() // 2); text_y = bar_y - text_surface.get_height() - 1
                surface.blit(text_surface, (text_x, text_y))

    def _draw_tareas(self, surface, camera_x, camera_y, camera_rect):
        for tarea in self.mundo.tareas_asignadas:
            if tarea.estado=='COMPLETED': continue
            task_rect = pygame.Rect(tarea.posicion[0]*self.view_tile_size, tarea.posicion[1]*self.view_tile_size, self.view_tile_size, self.view_tile_size)
            if camera_rect.colliderect(task_rect):
                color = (255,0,0)
                if tarea.tipo=='CURAR': color=TASK_HEAL_COLOR
                elif tarea.tipo == 'ANIMAR': color = TASK_CHEER_COLOR
                elif tarea.estado=='ASSIGNED': color=(255,255,0)
                center_x=tarea.posicion[0]*self.view_tile_size + self.view_tile_size//2 - camera_x
                center_y=tarea.posicion[1]*self.view_tile_size + self.view_tile_size//2 - camera_y
                pygame.draw.circle(surface,color,(center_x,center_y),self.view_tile_size//2,3)

    def _draw_path(self, surface, path, camera_x, camera_y):
        if len(path) > 1:
            points=[(p[0]*self.view_tile_size+self.view_tile_size//2-camera_x, p[1]*self.view_tile_size+self.view_tile_size//2-camera_y) for p in path]
            pygame.draw.lines(surface, (255,255,0), False, points, 2)

    def _draw_log(self, surface):
        y_offset = 10
        for i, mensaje in enumerate(self.mundo.event_log):
            alpha = max(0, 255-(i*50)); text_surface=self.log_font.render(mensaje,True,(255,255,255)); text_surface.set_alpha(alpha)
            surface.blit(text_surface, (10, y_offset)); y_offset += 20

    def _draw_ui_panel(self, selected_colono, acopio_tier, damage_tier):
        panel_rect=pygame.Rect(GAME_AREA_WIDTH, 0, UI_PANEL_WIDTH, self.SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, UI_BG_COLOR, panel_rect)
        pygame.draw.line(self.screen, UI_BORDER_COLOR, (GAME_AREA_WIDTH, 0), (GAME_AREA_WIDTH, self.SCREEN_HEIGHT), 2)
        y_offset = 20
        y_offset = self._draw_line(self.screen, "CONTROLES", self.ui_font, HEADER_COLOR, y_offset)
        if selected_colono is None:
            y_offset = self._draw_line(self.screen, "[1-3] Recolectar recursos", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[C] Curar Enfermedad", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[F] Ataque General", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[Z] Centro de Acopio", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[T] Estado de la Tribu", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[F1-F4] Usar Artefacto", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[Flechas] Mover Cámara", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[WASD] Mover Iguana (al sel.)", self.ui_font, (150,150,150), y_offset)
            y_offset = self._draw_line(self.screen, "[0] Prueba de Estrés", self.ui_font, (150,150,150), y_offset)
            y_offset = self._draw_line(self.screen, "[O] Lluvia Ácida (Debug)", self.ui_font, (150,150,150), y_offset)
            y_offset = self._draw_line(self.screen, "[8] Suelo es Lava (Debug)", self.ui_font, (150,150,150), y_offset)
        else:
            y_offset = self._draw_line(self.screen, f"[SELEC: {selected_colono.nombre}]", self.ui_font, STATE_MANUAL_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[WASD] Mover Iguana", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[H] Comer (Cura 10 V)", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[ESC] Deseleccionar", self.ui_font, TEXT_COLOR, y_offset)
            y_offset = self._draw_line(self.screen, "[Flechas] Mover Cámara", self.ui_font, TEXT_COLOR, y_offset)
        y_offset = self._draw_line(self.screen, "[ESC] Salir/Cerrar", self.ui_font, TEXT_COLOR, y_offset); y_offset += 10
        
        y_offset = self._draw_line(self.screen, "RECURSOS", self.ui_font, HEADER_COLOR, y_offset)
        y_offset = self._draw_line(self.screen, f"Comida: {self.mundo.recursos['comida']}", self.ui_font, RECURSO_COLOR, y_offset)
        y_offset = self._draw_line(self.screen, f"Madera: {self.mundo.recursos['madera']}", self.ui_font, RECURSO_COLOR, y_offset)
        y_offset = self._draw_line(self.screen, f"Piedra: {self.mundo.recursos['piedra']}", self.ui_font, RECURSO_COLOR, y_offset); y_offset += 10
        y_offset = self._draw_line(self.screen, f"Acopio Tier: {acopio_tier}", self.ui_font, HEADER_COLOR, y_offset)
        y_offset = self._draw_line(self.screen, f"Daño Tier: {damage_tier}", self.ui_font, HEADER_COLOR, y_offset); y_offset += 10
        y_offset = self._draw_line(self.screen, "ARTEFACTOS", self.ui_font, HEADER_COLOR, y_offset)
        nombres_artefactos = self.mundo.NOMBRES_ARTEFACTOS
        y_offset = self._draw_line(self.screen, f"[F1] {nombres_artefactos['crocs']}: {self.mundo.inventario_artefactos['crocs']}", self.artefacto_font, ARTEFACTO_COLOR, y_offset, 30)
        y_offset = self._draw_line(self.screen, f"[F2] {nombres_artefactos['pico']}: {self.mundo.inventario_artefactos['pico']}", self.artefacto_font, ARTEFACTO_COLOR, y_offset, 30)
        y_offset = self._draw_line(self.screen, f"[F3] {nombres_artefactos['guantes']}: {self.mundo.inventario_artefactos['guantes']}", self.artefacto_font, ARTEFACTO_COLOR, y_offset, 30)
        y_offset = self._draw_line(self.screen, f"[F4] {nombres_artefactos['escamas']}: {self.mundo.inventario_artefactos['escamas']}", self.artefacto_font, ARTEFACTO_COLOR, y_offset, 30); y_offset += 5
        
        y_offset = self._draw_line(self.screen, "EVENTOS ACTIVOS", self.ui_font, HEADER_COLOR, y_offset)
        hay_efectos = False
        if self.mundo.evento_peligroso_activo == "lluvia":
            segundos = (self.mundo.evento_peligroso_timer // 60) + 1
            y_offset = self._draw_line(self.screen, f" Lluvia Ácida: {segundos}s", self.evento_font, EVENTO_LLUVIA_COLOR, y_offset, 30); hay_efectos = True
        elif self.mundo.evento_peligroso_activo == "lava":
             segundos = (self.mundo.evento_peligroso_timer // 60) + 1
             y_offset = self._draw_line(self.screen, f" Suelo es Lava: {segundos}s", self.evento_font, EVENTO_LAVA_COLOR, y_offset, 30); hay_efectos = True

        for efecto, tiempo in self.mundo.efectos_activos.items():
            if tiempo > 0:
                nombre_display = self.mundo.NOMBRES_ARTEFACTOS.get(efecto, efecto.capitalize())
                segundos = (tiempo // 60) + 1
                y_offset = self._draw_line(self.screen, f" {nombre_display}: {segundos}s", self.artefacto_font, EFECTO_ACTIVO_COLOR, y_offset, 30); hay_efectos = True
        if not hay_efectos: y_offset = self._draw_line(self.screen, " Ninguno", self.artefacto_font, (150,150,150), y_offset, 30)
        y_offset += 15
        
        y_offset = self._draw_line(self.screen, "COLONIA (Jugador)", self.ui_font, HEADER_COLOR, y_offset)
        colonos_vivos_jugador = [c for c in self.mundo.colonos if not c.es_enemigo and not c.esta_muerto]
        altura_iguana = self.stats_font.get_linesize() * 2 + self.ui_font.get_linesize() + 7
        if altura_iguana <= 0: altura_iguana = 50
        espacio_restante = self.SCREEN_HEIGHT - y_offset - 20
        max_colonos_visibles = max(1, espacio_restante // altura_iguana)
        for i, colono in enumerate(colonos_vivos_jugador):
            if i >= max_colonos_visibles:
                 y_offset = self._draw_line(self.screen, f"... y {len(colonos_vivos_jugador) - max_colonos_visibles} más", self.stats_font, TEXT_COLOR, y_offset, 30); break
            
            estado = colono.estado; color_estado=TEXT_COLOR
            if colono.esta_enfermo: color_estado=STATE_SICK_COLOR
            elif estado=='IDLE': color_estado=STATE_IDLE_COLOR
            elif estado=='MOVING': color_estado=STATE_MOVING_COLOR
            elif estado=='WORKING' or estado=='EATING': color_estado=STATE_WORKING_COLOR
            elif estado=='PLANNING': color_estado=STATE_PLANNING_COLOR
            elif estado=='MANUAL': color_estado=STATE_MANUAL_COLOR
            elif estado=='CHASING': color_estado=STATE_CHASING_COLOR
            elif estado=='ATTACKING': color_estado=STATE_ATTACKING_COLOR
            elif estado=='HIDING': color_estado=STATE_IDLE_COLOR
            
            text_color_nombre=TEXT_COLOR
            if colono==selected_colono: text_color_nombre=STATE_MANUAL_COLOR
            else: effective_tier = min(acopio_tier, damage_tier); tier_index = min(effective_tier, len(TIER_COLORS) - 1); text_color_nombre = TIER_COLORS[tier_index]
            info_nombre = f"{colono.nombre}"
            y_offset = self._draw_line(self.screen, info_nombre, self.ui_font, text_color_nombre, y_offset, 20)
            daño_str = f" | D:{colono.daño}" if colono.clase == "guerrero" else ""
            info_salud = f"  V:{colono.vida}/{colono.max_vida} | Á:{colono.estado_animo}/100{daño_str}"
            y_offset = self._draw_line(self.screen, info_salud, self.stats_font, TEXT_COLOR, y_offset, 30)
            info_estado_str = f"  > {estado}" + (" [ENFERMO]" if colono.esta_enfermo else "")
            y_offset = self._draw_line(self.screen, info_estado_str, self.ui_font, color_estado, y_offset, 30); y_offset += 5

    def _draw_line_on_surface(self, surface, text, font, color, y_offset, x_offset, surface_origin_x=0):
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, (x_offset, y_offset))
        return y_offset + font.get_linesize() + 2

    def _draw_line(self, surface, text, font, color, y_offset, x_offset=20):
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, (GAME_AREA_WIDTH + x_offset, y_offset))
        return y_offset + font.get_linesize() + 2

