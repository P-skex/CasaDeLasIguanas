import pygame
import sys
import random
from src.core.mundo import Mundo
from src.logic.planificador import Planificador
from src.logic.eventos import EventoManager
from src.gui.renderer import Renderer

# --- Constantes del Juego ---
TILE_SIZE = 16
GAME_SCALE = 4.5
VIEW_TILE_SIZE = int(TILE_SIZE * GAME_SCALE)
GAME_AREA_WIDTH = 1000
UI_PANEL_WIDTH = 280
SCREEN_WIDTH = GAME_AREA_WIDTH + UI_PANEL_WIDTH
SCREEN_HEIGHT = 800
FPS = 60
GAME_TITLE = "ColonySim"

class Game:
    def __init__(self):
        pygame.init()

        self.SCREEN_HEIGHT = SCREEN_HEIGHT; self.GAME_WIDTH = GAME_AREA_WIDTH; self.UI_WIDTH = UI_PANEL_WIDTH
        self.screen = pygame.display.set_mode((self.GAME_WIDTH + self.UI_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE); self.clock = pygame.time.Clock()
        self.is_running = True; self.debug_mode = False
        self.game_state = 'SPLASH_SCREEN'
        self.showing_tribu_menu = False
        self.camera_x = 0; self.camera_y = 0; self.camera_speed = 2 * GAME_SCALE
        self.selected_colono = None; self.showing_acopio_menu = False
        self.creando_iguana_clase = None

        # Tiempo
        self.total_frames = 0
        self.dia = 1; self.mes = 1; self.año = 1
        self.FRAMES_POR_DIA = 10 * FPS

        # Mejoras Acopio
        self.acopio_tier = 0
        self.acopio_upgrades = [{"costo_comida": 0,"max_vida": 100},{"costo_comida": 30,"max_vida": 130},
                                {"costo_comida": 60,"max_vida": 160},{"costo_comida": 100,"max_vida": 200}]
        # Mejoras Daño
        self.damage_tier = 0
        self.damage_upgrades = [{"costo_piedra": 0,"costo_madera": 0,"daño_guerrero": 10},{"costo_piedra": 20,"costo_madera": 20,"daño_guerrero": 20},
                                {"costo_piedra": 40,"costo_madera": 40,"daño_guerrero": 30},{"costo_piedra": 50,"costo_madera": 50,"daño_guerrero": 40}]

        self.mundo = Mundo(GAME_SCALE, VIEW_TILE_SIZE)
        self.planificador = Planificador(self.mundo)
        self.evento_manager = EventoManager(self.mundo, self.planificador)
        self.renderer = Renderer(self.screen, self.mundo, self, self.GAME_WIDTH, self.SCREEN_HEIGHT, GAME_SCALE, VIEW_TILE_SIZE, self.UI_WIDTH)

        self.map_width_px = self.mundo.width * VIEW_TILE_SIZE; self.map_height_px = self.mundo.height * VIEW_TILE_SIZE
        max_camera_x = max(0, self.map_width_px - self.GAME_WIDTH); max_camera_y = max(0, self.map_height_px - self.SCREEN_HEIGHT)
        self.camera_x = max_camera_x; self.camera_y = max_camera_y

        initial_max_vida = self.acopio_upgrades[self.acopio_tier]["max_vida"]
        initial_daño = self.damage_upgrades[self.damage_tier]["daño_guerrero"]
        for colono in self.mundo.colonos:
            colono.set_max_vida(initial_max_vida); colono.set_daño(initial_daño)

    def run(self):
        while self.is_running:
            self.process_events()
            
            if (self.showing_acopio_menu and not self.creando_iguana_clase == "SELECT_CLASS") or \
               self.showing_tribu_menu or self.mundo.juego_terminado or self.game_state != 'PLAYING':
                pass # Pausa
            else: self.update()
                
            self.render()
            self.clock.tick(FPS)
        pygame.quit(); sys.exit()

    def process_events(self):
        
        # Lógica de Estado de Juego (Intro/Fin)
        if self.game_state == 'SPLASH_SCREEN':
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.is_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: self.game_state = 'INFO_SCREEN'
                    if event.key == pygame.K_ESCAPE: self.is_running = False
            return
        if self.game_state == 'INFO_SCREEN':
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.is_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: self.game_state = 'PLAYING'
                    if event.key == pygame.K_ESCAPE: self.is_running = False
            return
        if self.mundo.juego_terminado:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.is_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE: self.is_running = False
            return
            
        keys = pygame.key.get_pressed()

        if not self.showing_acopio_menu and not self.showing_tribu_menu:
            if keys[pygame.K_LEFT]: self.camera_x -= self.camera_speed
            if keys[pygame.K_RIGHT]: self.camera_x += self.camera_speed
            if keys[pygame.K_UP]: self.camera_y -= self.camera_speed
            if keys[pygame.K_DOWN]: self.camera_y += self.camera_speed
        
        if self.selected_colono and not self.showing_acopio_menu and not self.showing_tribu_menu:
             move_input = {'up': keys[pygame.K_w], 'down': keys[pygame.K_s], 'left': keys[pygame.K_a], 'right': keys[pygame.K_d]}
             self.selected_colono.handle_manual_input(move_input)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.is_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.creando_iguana_clase == "SELECT_CLASS": self.creando_iguana_clase = None
                    elif self.showing_acopio_menu: self.showing_acopio_menu = False
                    elif self.showing_tribu_menu: self.showing_tribu_menu = False
                    elif self.selected_colono: self.selected_colono.stop_manual_control(); self.selected_colono = None
                    else: self.is_running = False
                if event.key == pygame.K_z:
                    self.showing_acopio_menu = not self.showing_acopio_menu; self.showing_tribu_menu = False
                    self.creando_iguana_clase = None
                    if self.showing_acopio_menu and self.selected_colono: self.selected_colono.stop_manual_control(); self.selected_colono = None
                if event.key == pygame.K_t:
                    self.showing_tribu_menu = not self.showing_tribu_menu; self.showing_acopio_menu = False
                    self.creando_iguana_clase = None
                    if self.showing_tribu_menu and self.selected_colono: self.selected_colono.stop_manual_control(); self.selected_colono = None

                if self.showing_acopio_menu:
                    if self.creando_iguana_clase == "SELECT_CLASS":
                        clase_elegida = None
                        if event.key == pygame.K_1: clase_elegida = "recolector"
                        elif event.key == pygame.K_2: clase_elegida = "guerrero"
                        elif event.key == pygame.K_3: clase_elegida = "curandero"
                        if clase_elegida:
                             creado = self.mundo.crear_nueva_iguana(clase_elegida, self.acopio_tier, self.damage_tier, self.acopio_upgrades, self.damage_upgrades)
                             if creado: self.showing_acopio_menu = False
                             self.creando_iguana_clase = None
                    else:
                        if event.key == pygame.K_u: self.attempt_upgrade_acopio()
                        if event.key == pygame.K_i: self.attempt_upgrade_damage()
                        if event.key == pygame.K_n:
                             costo_c=100; costo_m=100; costo_p=100
                             if self.mundo.recursos['comida']>=costo_c and self.mundo.recursos['madera']>=costo_m and self.mundo.recursos['piedra']>=costo_p:
                                 self.creando_iguana_clase = "SELECT_CLASS"; self.mundo.log_event("Elige clase: [1] Recolector, [2] Guerrero, [3] Curandero")
                             else: self.mundo.log_event(f"Recursos insuficientes ({costo_c}C/{costo_m}M/{costo_p}P).")

                elif not self.showing_tribu_menu: # Teclas que solo funcionan si NINGÚN menú está abierto
                    if self.selected_colono is None:
                        if event.key == pygame.K_1: self.planificador.solicitar_tarea('RECOGER')
                        if event.key == pygame.K_2: self.planificador.solicitar_tarea('TALAR')
                        if event.key == pygame.K_3: self.planificador.solicitar_tarea('MINAR')
                        if event.key == pygame.K_c: self.planificador.solicitar_curacion()
                        if event.key == pygame.K_f: self.planificador.solicitar_ataque_general()
                        if event.key == pygame.K_e: self.evento_manager.activar_evento_aleatorio()
                        if event.key == pygame.K_0: self.ejecutar_prueba_de_estres()
                        
                        # --- ¡NUEVO! Triggers Manuales de Eventos ---
                        if event.key == pygame.K_o:
                            self.mundo._iniciar_evento_peligroso("lluvia")
                        if event.key == pygame.K_8:
                            self.mundo._iniciar_evento_peligroso("lava")
                        # ------------------------------------------
                    
                    if self.selected_colono:
                        if event.key == pygame.K_h: self.selected_colono.iniciar_comer()
                    
                    if event.key == pygame.K_F1: self.mundo.activar_artefacto("crocs")
                    if event.key == pygame.K_F2: self.mundo.activar_artefacto("pico")
                    if event.key == pygame.K_F3: self.mundo.activar_artefacto("guantes")
                    if event.key == pygame.K_F4: self.mundo.activar_artefacto("escamas")

            if not self.showing_acopio_menu and not self.showing_tribu_menu and not self.mundo.juego_terminado and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if pos[0] >= self.GAME_WIDTH: continue
                    world_x = pos[0] + self.camera_x; world_y = pos[1] + self.camera_y
                    clicked_colono = next((c for c in self.mundo.colonos if not c.es_enemigo and not c.esta_muerto and c.rect.collidepoint(world_x, world_y)), None)
                    if not clicked_colono and self.selected_colono: self.selected_colono.stop_manual_control(); self.selected_colono = None
                    elif clicked_colono and clicked_colono != self.selected_colono:
                         if self.selected_colono: self.selected_colono.stop_manual_control()
                         self.selected_colono = clicked_colono; self.selected_colono.start_manual_control(); print(f"Seleccionado: {self.selected_colono.nombre}")
                    elif clicked_colono and clicked_colono == self.selected_colono:
                         self.selected_colono.stop_manual_control(); self.selected_colono = None
                         
    def ejecutar_prueba_de_estres(self):
        """Llama al mundo para crear 50 guerreros."""
        self.mundo.log_event("¡PRUEBA DE ESTRÉS INICIADA!")
        self.mundo.iniciar_prueba_de_estres(
            self.acopio_tier, self.damage_tier,
            self.acopio_upgrades, self.damage_upgrades
        )

    def attempt_upgrade_acopio(self):
        next_tier = self.acopio_tier + 1
        if next_tier >= len(self.acopio_upgrades): self.mundo.log_event("¡Acopio ya está al máximo nivel!"); return
        upgrade_info = self.acopio_upgrades[next_tier]; costo = upgrade_info["costo_comida"]
        if self.mundo.recursos["comida"] >= costo:
            self.mundo.recursos["comida"] -= costo; self.acopio_tier = next_tier
            new_max_vida = upgrade_info["max_vida"]
            for colono in self.mundo.colonos: colono.set_max_vida(new_max_vida)
            self.mundo.log_event(f"¡Acopio mejorado a Tier {self.acopio_tier}! Vida máxima: {new_max_vida}.")
        else: self.mundo.log_event(f"No hay suficiente comida (Necesitas {costo}).")

    def attempt_upgrade_damage(self):
        next_tier = self.damage_tier + 1
        if next_tier >= len(self.damage_upgrades): self.mundo.log_event("¡Mejoras de daño ya están al máximo nivel!"); return
        upgrade_info = self.damage_upgrades[next_tier]; costo_p = upgrade_info["costo_piedra"]; costo_m = upgrade_info["costo_madera"]
        if self.mundo.recursos["piedra"] >= costo_p and self.mundo.recursos["madera"] >= costo_m:
            self.mundo.recursos["piedra"] -= costo_p; self.mundo.recursos["madera"] -= costo_m
            self.damage_tier = next_tier; new_daño = upgrade_info["daño_guerrero"]
            for colono in self.mundo.colonos: colono.set_daño(new_daño)
            self.mundo.log_event(f"¡Daño mejorado a Tier {self.damage_tier}! Daño guerrero: {new_daño}.")
        else: self.mundo.log_event(f"Recursos insuficientes (Necesitas {costo_p} Piedra, {costo_m} Madera).")

    def update(self):
        # Actualiza el tiempo
        self.total_frames += 1
        if self.total_frames % self.FRAMES_POR_DIA == 0:
            self.dia += 1
            if self.dia > 30:
                self.dia = 1; self.mes += 1
                if self.mes > 12: self.mes = 1; self.año += 1
        
        # Actualiza cámara y mundo
        max_camera_x = max(0, self.map_width_px - self.GAME_WIDTH); max_camera_y = max(0, self.map_height_px - self.SCREEN_HEIGHT)
        self.camera_x = max(0, min(self.camera_x, max_camera_x)); self.camera_y = max(0, min(self.camera_y, max_camera_y))
        self.planificador.update()
        self.evento_manager.update()
        self.mundo.update()

    def render(self):
        self.renderer.draw(
            self.camera_x, self.camera_y, self.selected_colono,
            self.showing_acopio_menu, self.creando_iguana_clase,
            self.acopio_tier, self.damage_tier,
            self.acopio_upgrades, self.damage_upgrades,
            self.mundo.juego_terminado,
            self.game_state,
            self.showing_tribu_menu,
            self.dia, self.mes, self.año,
            self.debug_mode
        )

if __name__ == '__main__':
    game = Game()
    game.run()

