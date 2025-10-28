import pygame
import random
import math
from src.logic.pathfinding import a_star, is_walkable
# Importamos GameObject para el paraguas/silla
from .game_object import GameObject 

TILE_SIZE = 16
SPRITE_FRAME_WIDTH = 15
SPRITE_FRAME_HEIGHT = 18
SPRITE_X_OFFSET = 4
SPRITE_Y_OFFSET = 3
SPRITESHEET_COLUMNS = 24

# Índices de animación
IDLE_FRAMES_START_INDEX = 0
IDLE_FRAMES_END_INDEX = 0
WALK_FRAMES_START_INDEX = 1
WALK_FRAMES_END_INDEX = 3
WORK_FRAMES_START_INDEX = 4
WORK_FRAMES_END_INDEX = 6
ATTACK_FRAMES_START_INDEX = 7
ATTACK_FRAMES_END_INDEX = 9
DIE_FRAME_INDEX = 22

class Colono:
    """Representa un colono (jugador o enemigo) animado."""
    # Constantes de Ánimo
    PROBABILIDAD_ACCIDENTE = 1 / 20
    PENALIZACION_ANIMO_ACCIDENTE = 20
    LIMITE_ANIMO_PARA_TRABAJAR = 5
    BONUS_ANIMO_CURANDERO = 10
    COSTO_ANIMO_TAREA = 5
    COSTO_ANIMO_ATAQUE = 3
    PERDIDA_ANIMO_PASIVA = 10
    TIEMPO_PERDIDA_PASIVA = 60 * 60

    def __init__(self, x, y, mundo, nombre, clase, game_scale, view_tile_size, all_frames, es_enemigo=False, stats_enemigo=None, tribu="jugador"):
        self.mundo = mundo
        self.nombre = nombre
        self.clase = clase
        self.es_enemigo = es_enemigo
        self.tribu = tribu

        self.view_tile_size = view_tile_size
        self.game_scale = game_scale

        # Stats Base
        if self.es_enemigo:
            default_stats = {"max_vida": 100, "daño": 10}
            if stats_enemigo is None: stats_enemigo = default_stats
            self.max_vida_base = stats_enemigo.get("max_vida", default_stats["max_vida"])
            self.daño_base = stats_enemigo.get("daño", default_stats["daño"])
            self.clase = "guerrero"
        else:
            self.max_vida_base = 100
            self.daño_base = 10 if self.clase == "guerrero" else 0
        
        self.max_vida = self.max_vida_base
        self.vida = self.max_vida
        self.daño = self.daño_base
        self.velocidad_base = 1.0 * self.game_scale
        self.duracion_trabajo_base = 180
        self.velocidad = self.velocidad_base
        self.duracion_trabajo = self.duracion_trabajo_base
        self.buffs_activos = set()

        self.estado_animo = 100
        self.esta_enfermo = False
        self.temporizador_enfermedad = 0
        self.SEGUNDOS_ENTRE_DAÑO = 3
        self.esta_muerto = False

        self.tile_x = x; self.tile_y = y
        self.pos = pygame.Vector2(self.tile_x * self.view_tile_size, self.tile_y * self.view_tile_size)

        # --- ¡NUEVO ESTADO HIDING! ---
        self.estado = 'IDLE' # IDLE, PLANNING, MOVING, WORKING, EATING, MANUAL, CHASING, ATTACKING, DIE, HIDING
        # -----------------------------

        self.tarea_actual = None; self.path = []; self.work_timer = 0
        
        # --- ¡CORRECCIÓN AQUÍ! Restauramos las variables de tiempo ---
        self.tiempo_min_quieto = 3 * 60 # Mínimo 3 segundos quieto (a 60 FPS)
        self.tiempo_max_quieto = 8 * 60 # Máximo 8 segundos quieto
        self.idle_timer_vagabundeo = random.randint(self.tiempo_min_quieto, self.tiempo_max_quieto)
        # -----------------------------------------------------------
        
        self.tiempo_hasta_perdida_animo = self.TIEMPO_PERDIDA_PASIVA

        self.radio_deteccion = 5
        self.objetivo_ataque = None
        self.attack_cooldown = 60
        self.tiempo_hasta_proximo_ataque = 0
        
        # --- ¡NUEVO! Lógica de Evento Peligroso Genérico ---
        self.proteccion_sprite = None # Referencia al objeto Paraguas/Silla
        self.damage_timer_evento = 60 # Cooldown para daño por evento (1 seg)
        # -------------------------------------------------

        self.animations = {}; self.facing = 'right'; self.current_animation = 'idle_right'
        self.current_frame_index = 0.0; self.animation_speed = 0.2

        self._setup_animations_from_frames(all_frames)

        if not self.animations or 'idle_right' not in self.animations or not self.animations['idle_right']:
             print(f"ERROR: No se pudo configurar imagen inicial para {self.nombre}."); self._usar_fallback_imagen()
        else: self.image = self.animations['idle_right'][0]
        self.rect = self.image.get_rect()

    def _usar_fallback_imagen(self):
        scaled_w = int(SPRITE_FRAME_WIDTH * self.game_scale); scaled_h = int(SPRITE_FRAME_HEIGHT * self.game_scale)
        self.image = pygame.Surface((scaled_w, scaled_h))
        color = (255, 255, 0) if self.es_enemigo else (200, 150, 50); self.image.fill(color)
        print(f"Usando color de fallback para {self.nombre}")

    def _setup_animations_from_frames(self, all_frames_scaled):
        num_loaded_frames = len(all_frames_scaled)
        if not all_frames_scaled: print(f"Error: Lista de frames vacía para {self.nombre}."); return
        
        def get_frames(start_idx, end_idx):
            s = min(start_idx, num_loaded_frames - 1); e_slice = min(end_idx + 1, num_loaded_frames)
            if s < 0 or s >= e_slice:
                 idle_f = min(IDLE_FRAMES_START_INDEX, num_loaded_frames - 1)
                 print(f"Advertencia: Rango inválido [{start_idx}-{end_idx}]. Usando IDLE frame {idle_f}.")
                 return [all_frames_scaled[idle_f]] if 0 <= idle_f < num_loaded_frames else []
            return all_frames_scaled[s : e_slice]

        idle_frames=get_frames(IDLE_FRAMES_START_INDEX, IDLE_FRAMES_END_INDEX)
        walk_frames=get_frames(WALK_FRAMES_START_INDEX, WALK_FRAMES_END_INDEX)
        work_frames=get_frames(WORK_FRAMES_START_INDEX, WORK_FRAMES_END_INDEX)
        attack_frames=get_frames(ATTACK_FRAMES_START_INDEX, ATTACK_FRAMES_END_INDEX)
        die_frames=get_frames(DIE_FRAME_INDEX, DIE_FRAME_INDEX)
        if not idle_frames: print(f"Error crítico: No se pudo cargar frame IDLE para {self.nombre}."); return

        self.animations['idle_right']=idle_frames; self.animations['idle_left']=[pygame.transform.flip(f,True,False) for f in idle_frames]
        self.animations['idle_up']=self.animations['idle_right']; self.animations['idle_down']=self.animations['idle_left']
        self.animations['walk_right']=walk_frames; self.animations['walk_left']=[pygame.transform.flip(f,True,False) for f in walk_frames]
        self.animations['walk_up']=walk_frames; self.animations['walk_down']=self.animations['walk_left']
        self.animations['work_right']=work_frames; self.animations['work_left']=[pygame.transform.flip(f,True,False) for f in work_frames]
        self.animations['work_up']=work_frames; self.animations['work_down']=self.animations['work_left']
        self.animations['attack_right']=attack_frames; self.animations['attack_left']=[pygame.transform.flip(f,True,False) for f in attack_frames]
        self.animations['attack_up']=attack_frames; self.animations['attack_down']=self.animations['attack_left']
        self.animations['die']=die_frames
        self.animations['eat_right'] = work_frames; self.animations['eat_left'] = [pygame.transform.flip(f, True, False) for f in work_frames]
        self.animations['eat_up'] = work_frames; self.animations['eat_down'] = work_frames
        self.animations['animar_right'] = work_frames; self.animations['animar_left'] = [pygame.transform.flip(f, True, False) for f in work_frames]
        self.animations['animar_up'] = work_frames; self.animations['animar_down'] = work_frames
        self.animations['hiding_right'] = idle_frames
        self.animations['hiding_left'] = [pygame.transform.flip(f, True, False) for f in idle_frames]
        self.animations['hiding_up'] = idle_frames
        self.animations['hiding_down'] = idle_frames

    def set_animation(self, anim_name):
        if anim_name not in self.animations or not self.animations[anim_name]:
             base_anim = anim_name.split('_')[0]
             fallback_anim = anim_name.replace(base_anim, 'idle')
             if fallback_anim in self.animations and self.animations[fallback_anim]: anim_name = fallback_anim
             elif 'idle_right' in self.animations and self.animations['idle_right']: anim_name = 'idle_right'
             else: return
        if self.current_animation != anim_name:
            self.current_animation = anim_name; self.current_frame_index = 0.0

    def _update_animation(self):
        if self.current_animation not in self.animations or not self.animations[self.current_animation]: return
        anim = self.animations[self.current_animation]; num_frames = len(anim)
        if num_frames == 0: return
        if self.current_animation == 'die' and int(self.current_frame_index) == num_frames - 1: pass
        elif 'idle' not in self.current_animation and 'hiding' not in self.current_animation:
            self.current_frame_index = (self.current_frame_index + self.animation_speed) % num_frames
        else: self.current_frame_index = 0
        frame_idx = int(self.current_frame_index)
        if 0 <= frame_idx < num_frames: self.image = anim[frame_idx]
        if hasattr(self, 'rect'): self.rect.size = self.image.get_size()
        else: self.rect = self.image.get_rect()

    def cancelar_accion_actual(self):
        if self.tarea_actual:
            if self.tarea_actual.tipo in ('CURAR', 'ANIMAR'): self.mundo.eliminar_tarea(self.tarea_actual)
            elif self.tarea_actual.objeto_objetivo: self.mundo.eliminar_tarea(self.tarea_actual)
            self.mundo.log_event(f"{self.nombre} canceló {self.tarea_actual.tipo}.")
            self.tarea_actual = None
        elif self.estado == 'EATING': self.mundo.log_event(f"{self.nombre} dejó de comer.")
        self.path = []; self.objetivo_ataque = None; self.work_timer = 0

    def asignar_tarea(self, tarea):
        # Chequeo de evento peligroso
        if self.mundo.evento_peligroso_activo is not None:
            tarea.estado = 'PENDING'; self.mundo.eliminar_tarea(tarea); return
            
        if self.es_enemigo or self.estado == 'MANUAL' or self.esta_muerto or self.estado == 'EATING':
            tarea.estado = 'PENDING'; self.mundo.eliminar_tarea(tarea); return
        if self.estado_animo < self.LIMITE_ANIMO_PARA_TRABAJAR and tarea.tipo != 'ANIMAR':
            self.mundo.log_event(f"{self.nombre} está demasiado triste para {tarea.tipo}.")
            tarea.estado = 'PENDING'; self.mundo.eliminar_tarea(tarea)
            return

        if self.estado == 'MOVING' and not self.tarea_actual: self.path = []
        self.tarea_actual = tarea
        if self.clase == "recolector" and "pico" in self.buffs_activos: self.duracion_trabajo = 1
        else: self.duracion_trabajo = self.duracion_trabajo_base
        if tarea.tipo == 'CURAR': self.duracion_trabajo = 120
        elif tarea.tipo == 'ANIMAR': self.duracion_trabajo = 120
        self.estado = 'PLANNING'
        start = (self.tile_x, self.tile_y); end = self.tarea_actual.posicion
        self.path = a_star(self.mundo, start, end)
        if self.path:
            self.path.pop(0)
            if not self.path:
                 if (tarea.tipo in ('CURAR', 'ANIMAR') and abs(start[0] - tarea.colono_objetivo.tile_x) <= 1 and abs(start[1] - tarea.colono_objetivo.tile_y) <= 1) or \
                    (tarea.objeto_objetivo and start == end):
                      self.estado = 'WORKING'; self.work_timer = self.duracion_trabajo
                      self.pos = pygame.Vector2(self.tile_x * self.view_tile_size, self.tile_y * self.view_tile_size)
                 else:
                      self.mundo.log_event(f"ADVERTENCIA: {self.nombre} path vacío para {tarea.tipo} en {end} desde {start}.")
                      self.tarea_actual.estado = 'PENDING'; self.mundo.eliminar_tarea(self.tarea_actual); self.tarea_actual = None; self.estado = 'IDLE'
            else: self.estado = 'MOVING'
        else:
            self.mundo.log_event(f"ADVERTENCIA: {self.nombre} no encontró camino a {end} para tarea {tarea.tipo}.")
            self.tarea_actual.estado = 'PENDING'; self.mundo.eliminar_tarea(self.tarea_actual); self.tarea_actual = None; self.estado = 'IDLE'

    def _actualizar_estado_salud(self):
        if not self.es_enemigo and self.esta_enfermo:
            self.temporizador_enfermedad -= 1
            if self.temporizador_enfermedad <= 0:
                self.recibir_daño(1, "enfermedad", None); self.recibir_penalizacion_animo(2, "enfermedad")
                self.temporizador_enfermedad = 60 * self.SEGUNDOS_ENTRE_DAÑO
                if self.vida > 0: self.mundo.log_event(f"{self.nombre} se siente mal...")
        if not self.es_enemigo and self.clase != 'curandero':
            self.tiempo_hasta_perdida_animo -= 1
            if self.tiempo_hasta_perdida_animo <= 0:
                self.recibir_penalizacion_animo(self.PERDIDA_ANIMO_PASIVA, "aburrimiento")
                self.tiempo_hasta_perdida_animo = self.TIEMPO_PERDIDA_PASIVA

    def enfermar(self):
        if not self.es_enemigo and not self.esta_enfermo:
            self.esta_enfermo = True; self.recibir_penalizacion_animo(20, "enfermedad")
            self.temporizador_enfermedad = 60 * self.SEGUNDOS_ENTRE_DAÑO
            self.mundo.log_event(f"¡{self.nombre} se ha enfermado!")

    def curar(self):
        if not self.es_enemigo and self.esta_enfermo:
            self.esta_enfermo = False; self.recibir_mejora_animo(10)
            self.mundo.log_event(f"¡{self.nombre} ha sido curado!")

    def set_max_vida(self, nueva_max_vida):
        if not self.es_enemigo:
            vida_anterior = self.max_vida; self.max_vida_base = nueva_max_vida
            if "escamas" in self.buffs_activos: self.max_vida = int(self.max_vida_base * 1.25)
            else: self.max_vida = self.max_vida_base
            if self.max_vida > vida_anterior: pass
            self.vida = min(self.vida, self.max_vida)

    def set_daño(self, nuevo_daño):
        if not self.es_enemigo and self.clase == "guerrero":
            self.daño_base = nuevo_daño
            if "guantes" in self.buffs_activos: self.daño = int(self.daño_base * 1.25)
            else: self.daño = self.daño_base

    def aplicar_buff(self, tipo_artefacto):
        if tipo_artefacto in self.buffs_activos: return
        self.buffs_activos.add(tipo_artefacto)
        if tipo_artefacto == "crocs": self.velocidad = self.velocidad_base * 2.0
        elif tipo_artefacto == "pico" and self.clase == "recolector": self.duracion_trabajo = 1
        elif tipo_artefacto == "guantes" and self.clase == "guerrero": self.daño = int(self.daño_base * 1.25)
        elif tipo_artefacto == "escamas":
            vida_anterior = self.vida; self.max_vida = int(self.max_vida_base * 1.25)
            self.vida = min(self.max_vida, vida_anterior + (self.max_vida - self.max_vida_base))

    def quitar_buff(self, tipo_artefacto):
        if tipo_artefacto not in self.buffs_activos: return
        self.buffs_activos.remove(tipo_artefacto)
        if tipo_artefacto == "crocs": self.velocidad = self.velocidad_base
        elif tipo_artefacto == "pico" and self.clase == "recolector": self.duracion_trabajo = self.duracion_trabajo_base
        elif tipo_artefacto == "guantes" and self.clase == "guerrero": self.daño = self.daño_base
        elif tipo_artefacto == "escamas":
            self.max_vida = self.max_vida_base; self.vida = min(self.vida, self.max_vida)

    def start_manual_control(self):
        if self.mundo.evento_peligroso_activo is not None: return
        if not self.es_enemigo and not self.esta_muerto:
            self.cancelar_accion_actual()
            self.estado = 'MANUAL'
            self.set_animation(f'idle_{self.facing}')

    def stop_manual_control(self):
        if not self.es_enemigo and self.estado == 'MANUAL':
             self.estado = 'IDLE'; self.set_animation(f'idle_{self.facing}')

    def handle_manual_input(self, move_input):
        if self.es_enemigo or self.estado != 'MANUAL' or self.esta_muerto or self.mundo.evento_peligroso_activo is not None: return
        move_vector = pygame.Vector2(0, 0); is_moving = False
        if move_input['up']: move_vector.y -= 1; self.facing = 'up'; is_moving = True
        if move_input['down']: move_vector.y += 1; self.facing = 'down'; is_moving = True
        if move_input['left']: move_vector.x -= 1; self.facing = 'left'; is_moving = True
        if move_input['right']: move_vector.x += 1; self.facing = 'right'; is_moving = True
        target_anim_manual = f'idle_{self.facing}'
        if is_moving: target_anim_manual = f'walk_{self.facing}'
        self.set_animation(target_anim_manual)
        if is_moving:
            if move_vector.length() > 0: move_vector = move_vector.normalize() * self.velocidad
            new_pos = self.pos + move_vector
            current_width = self.image.get_width(); current_height = self.image.get_height()
            offset_x_col = (self.view_tile_size - current_width) // 2
            offset_y_col = self.view_tile_size - current_height
            next_rect = pygame.Rect(new_pos.x + offset_x_col, new_pos.y + offset_y_col, current_width, current_height)
            can_move = True
            feet_center_x = next_rect.centerx; feet_center_y = next_rect.bottom - 1
            new_tile_x = int(feet_center_x // self.view_tile_size); new_tile_y = int(feet_center_y // self.view_tile_size)
            if not (0 <= new_tile_x < self.mundo.width and 0 <= new_tile_y < self.mundo.height) or \
               (new_tile_x, new_tile_y) in self.mundo.colision_tiles:
                 can_move = False
            if can_move: self.pos = new_pos; self.tile_x = new_tile_x; self.tile_y = new_tile_y

    def _iniciar_vagabundeo(self):
        if self.mundo.evento_peligroso_activo is not None: return
        direcciones_posibles = [(0, -1), (0, 1), (-1, 0), (1, 0)]; random.shuffle(direcciones_posibles)
        for dx, dy in direcciones_posibles:
            next_tile_x = self.tile_x + dx; next_tile_y = self.tile_y + dy; next_pos = (next_tile_x, next_tile_y)
            if is_walkable(self.mundo, next_pos):
                ocupado = any(c.tile_x == next_tile_x and c.tile_y == next_tile_y for c in self.mundo.colonos if c != self and not c.esta_muerto)
                if not ocupado:
                    self.path = [next_pos]; self.estado = 'MOVING'
                    if abs(dx) > abs(dy): self.facing = 'right' if dx > 0 else 'left'
                    else: self.facing = 'down' if dy > 0 else 'up'
                    self.idle_timer_vagabundeo = random.randint(3*60, 8*60); return
        self.idle_timer_vagabundeo = random.randint(1*60, 3*60)

    def _buscar_objetivo_cercano(self, es_enemigo_buscando):
        objetivo_cercano = None; min_dist = self.radio_deteccion
        for otro_colono in self.mundo.colonos:
            if otro_colono.es_enemigo != es_enemigo_buscando and not otro_colono.esta_muerto:
                 dist_tiles = abs(self.tile_x - otro_colono.tile_x) + abs(self.tile_y - otro_colono.tile_y)
                 if dist_tiles < min_dist: min_dist = dist_tiles; objetivo_cercano = otro_colono
        return objetivo_cercano

    def recibir_daño(self, cantidad, razon="ataque", atacante=None):
        if self.esta_muerto: return
        self.vida = max(0, self.vida - cantidad)
        if razon == "ataque":
            self.mundo.log_event(f"¡{self.nombre} recibe {cantidad} de daño de {atacante.nombre if atacante else '??'}! (Vida: {self.vida}/{self.max_vida})")
        
        if not self.es_enemigo and self.clase == 'guerrero' and not self.esta_muerto and \
           atacante and atacante.es_enemigo and \
           self.estado not in ['CHASING', 'ATTACKING', 'MANUAL', 'HIDING']:
            
            self.mundo.log_event(f"¡{self.nombre} contraataca a {atacante.nombre}!")
            self.cancelar_accion_actual()
            self.objetivo_ataque = atacante
            self.estado = 'CHASING'
        if self.vida == 0: self.morir()

    def morir(self):
        if self.esta_muerto: return
        self.mundo.log_event(f"¡{self.nombre} ha muerto!")
        self.esta_muerto = True; self.estado = 'DIE'
        self.set_animation('die'); self.path = []; self.tarea_actual = None; self.objetivo_ataque = None
        self.esta_enfermo = False; self.mundo.eliminar_colono(self)
        tarea_curacion = next((t for t in self.mundo.tareas_asignadas if t.tipo in ('CURAR','ANIMAR') and (t.colono_objetivo == self or t.colono_asignado == self)), None)
        if tarea_curacion:
            self.mundo.eliminar_tarea(tarea_curacion)
            curador = tarea_curacion.colono_asignado; paciente = tarea_curacion.colono_objetivo
            if curador and curador != self and not curador.esta_muerto: curador.tarea_actual = None; curador.estado = 'IDLE'
            elif paciente and paciente != self and not paciente.esta_muerto and paciente.estado == 'IDLE': pass
            
    def iniciar_comer(self):
        if self.es_enemigo or self.esta_muerto or self.estado not in ['IDLE', 'MANUAL'] or self.mundo.evento_peligroso_activo is not None:
            self.mundo.log_event(f"{self.nombre} no puede comer ahora."); return
        costo_comida = 5
        if self.mundo.recursos['comida'] >= costo_comida:
            if self.vida >= self.max_vida:
                 self.mundo.log_event(f"{self.nombre} ya tiene la vida al máximo."); return
            self.mundo.recursos['comida'] -= costo_comida
            self.estado = 'EATING'; self.work_timer = 3 * 60
            self.mundo.log_event(f"{self.nombre} está comiendo... (-{costo_comida} comida)")
            self.recibir_penalizacion_animo(self.COSTO_ANIMO_TAREA, "comer")
            self.set_animation(f'eat_{self.facing}')
        else: self.mundo.log_event(f"¡No hay suficiente comida para comer! (Necesitas {costo_comida})")

    def recibir_penalizacion_animo(self, cantidad, razon):
        if self.esta_muerto or self.es_enemigo or self.clase == 'curandero': return
        self.estado_animo = max(0, self.estado_animo - cantidad)
        if cantidad > 1:
            self.mundo.log_event(f"{self.nombre} pierde {cantidad} de ánimo por {razon}.")
            if self.estado_animo < self.LIMITE_ANIMO_PARA_TRABAJAR:
                 self.mundo.log_event(f"¡{self.nombre} está demasiado triste para trabajar!")

    def recibir_mejora_animo(self, cantidad):
        if self.esta_muerto or self.es_enemigo: return
        self.estado_animo = min(100, self.estado_animo + cantidad)

    # --- ¡MÉTODOS GENÉRICOS PARA EVENTOS PELIGROSOS! ---
    def construir_proteccion(self, tipo_evento):
        """Llamado por el evento. Crea una protección (paraguas o silla)."""
        if self.esta_muerto or self.es_enemigo: return
        self.cancelar_accion_actual()
        self.estado = 'HIDING'
        
        imagen_proteccion = None
        if tipo_evento == "lluvia":
            imagen_proteccion = self.mundo.paraguas_image_scaled
        elif tipo_evento == "lava":
            imagen_proteccion = self.mundo.silla_image_scaled # <-- Usa la imagen de la silla
            
        if imagen_proteccion is None:
             print(f"ERROR: No se encontró imagen para protección de tipo {tipo_evento}")
             self.sin_proteccion()
             return

        proteccion = GameObject(
            nombre=tipo_evento.capitalize(), tipo="proteccion_fx",
            tile_x=self.tile_x, tile_y=self.tile_y,
            image=imagen_proteccion,
            game_scale=self.game_scale, view_tile_size=self.view_tile_size
        )
        self.proteccion_sprite = proteccion
        self.mundo.proteccion_group.add(proteccion) # Usa el grupo genérico
        self.mundo.log_event(f"{self.nombre} usa {tipo_evento.capitalize()} para protegerse.")

    def sin_proteccion(self):
        """Llamado por el evento si no hay recursos."""
        if self.esta_muerto or self.es_enemigo: return
        self.cancelar_accion_actual()
        self.estado = 'HIDING'
        self.mundo.log_event(f"¡{self.nombre} no tiene recursos para protegerse!")

    def quitar_proteccion(self):
        """Llamado por el mundo cuando el evento termina."""
        if self.esta_muerto or self.es_enemigo: return
        if self.estado == 'HIDING':
            self.estado = 'IDLE'
            self.idle_timer_vagabundeo = random.randint(1*60, 3*60)
        if self.proteccion_sprite:
            self.proteccion_sprite.kill()
            self.proteccion_sprite = None
    # ------------------------------------------------

    def update(self):
        if self.esta_muerto:
             self._update_animation()
             return

        # --- Lógica de Evento Peligroso (Genérico) ---
        if self.mundo.evento_peligroso_activo is not None and not self.es_enemigo:
            if self.estado != 'HIDING':
                self.cancelar_accion_actual()
                self.estado = 'HIDING'
            
            if not self.proteccion_sprite:
                self.damage_timer_evento -= 1
                if self.damage_timer_evento <= 0:
                    razon_daño = "Lluvia Ácida" if self.mundo.evento_peligroso_activo == "lluvia" else "Suelo de Lava"
                    self.recibir_daño(2, razon_daño, None)
                    self.damage_timer_evento = 60
            
            self.set_animation(f'hiding_{self.facing}')
            self._update_animation()
            
            if self.proteccion_sprite:
                tile_center_x = self.pos.x + self.view_tile_size // 2
                tile_bottom_y = self.pos.y + self.view_tile_size
                offset_proteccion = self.rect.height
                self.proteccion_sprite.rect.midbottom = (tile_center_x, tile_bottom_y - offset_proteccion)

            tile_center_x = self.pos.x + self.view_tile_size // 2
            tile_bottom_y = self.pos.y + self.view_tile_size
            self.rect.midbottom = (tile_center_x, tile_bottom_y)
            
            return # BLOQUEA TODAS LAS DEMÁS ACCIONES
        # -----------------------------------------------

        if not self.es_enemigo: self._actualizar_estado_salud()
        target_anim = f'idle_{self.facing}'

        # IA (Jugador y Enemigo)
        if self.estado == 'IDLE' or self.estado == 'MOVING':
            if self.clase == 'guerrero' and not self.esta_enfermo and self.estado_animo >= self.LIMITE_ANIMO_PARA_TRABAJAR:
                objetivo = self._buscar_objetivo_cercano(self.es_enemigo)
                if objetivo:
                     if self.objetivo_ataque != objetivo: self.objetivo_ataque = objetivo; self.mundo.log_event(f"¡{self.nombre} fija objetivo en {objetivo.nombre}!")
                     self.estado = 'CHASING'
                     start = (self.tile_x, self.tile_y); end = (objetivo.tile_x, objetivo.tile_y)
                     self.path = a_star(self.mundo, start, end)
                     if self.path: self.path.pop(0)
                     else: self.estado = 'IDLE'; self.objetivo_ataque = None
            
            if self.estado == 'IDLE':
                self.idle_timer_vagabundeo -= 1
                if self.idle_timer_vagabundeo <= 0: self._iniciar_vagabundeo()
            
            target_anim = f'walk_{self.facing}' if self.estado == 'MOVING' else f'idle_{self.facing}'
        
        elif self.estado == 'CHASING':
            if self.objetivo_ataque and not self.objetivo_ataque.esta_muerto:
                 dist_x = abs(self.tile_x - self.objetivo_ataque.tile_x); dist_y = abs(self.tile_y - self.objetivo_ataque.tile_y)
                 if dist_x + dist_y <= 1:
                      self.estado = 'ATTACKING'; self.path = []; self.tiempo_hasta_proximo_ataque = 0
                      target_anim = f'attack_{self.facing}'
                 elif not self.path:
                      start = (self.tile_x, self.tile_y); end = (self.objetivo_ataque.tile_x, self.objetivo_ataque.tile_y)
                      self.path = a_star(self.mundo, start, end)
                      if self.path: self.path.pop(0); target_anim = f'walk_{self.facing}'
                      else: self.estado = 'IDLE'; self.objetivo_ataque = None
                 else: target_anim = f'walk_{self.facing}'
            else: self.estado = 'IDLE'; self.objetivo_ataque = None; self.path = []
        
        elif self.estado == 'ATTACKING': target_anim = f'attack_{self.facing}'
        
        # Jugador (estados no-IA)
        elif self.estado == 'MANUAL': pass 
        elif self.estado == 'WORKING': target_anim = f'work_{self.facing}'
        elif self.estado == 'EATING': target_anim = f'work_{self.facing}'

        if self.estado != 'MANUAL': self.set_animation(target_anim)
        self._update_animation()

        if self.estado == 'MOVING' or self.estado == 'CHASING': self.seguir_camino()
        elif self.estado == 'WORKING': self.trabajar()
        elif self.estado == 'EATING': self.comer()
        elif self.estado == 'ATTACKING': self.atacar_objetivo()
        
        if self.estado != 'HIDING':
            tile_center_x = self.pos.x + self.view_tile_size // 2
            tile_bottom_y = self.pos.y + self.view_tile_size
            self.rect.midbottom = (tile_center_x, tile_bottom_y)

    def seguir_camino(self):
        if not self.path:
            if self.tarea_actual: self.estado = 'WORKING'; self.work_timer = self.duracion_trabajo
            elif self.estado == 'CHASING' and self.objetivo_ataque and not self.objetivo_ataque.esta_muerto:
                 dist_x = abs(self.tile_x - self.objetivo_ataque.tile_x); dist_y = abs(self.tile_y - self.objetivo_ataque.tile_y)
                 if dist_x + dist_y <= 1: self.estado = 'ATTACKING'; self.tiempo_hasta_proximo_ataque = 0
                 else: self.estado = 'IDLE'; self.objetivo_ataque = None
            else: self.estado = 'IDLE'; self.idle_timer_vagabundeo = random.randint(3*60, 8*60); self.objetivo_ataque = None
            return
        target_tile = self.path[0]
        target_pixel_pos = pygame.Vector2(target_tile[0] * self.view_tile_size, target_tile[1] * self.view_tile_size)
        direction_vec = (target_pixel_pos - self.pos)
        if direction_vec.length() > 0:
            dx = direction_vec.x; dy = direction_vec.y
            if abs(dx) > abs(dy): self.facing = 'right' if dx > 0 else 'left'
            else: self.facing = 'down' if dy > 0 else 'up'
        if direction_vec.length() > self.velocidad: direction_vec.normalize_ip(); direction_vec *= self.velocidad
        self.pos += direction_vec
        self.tile_x = int(self.rect.midbottom[0] // self.view_tile_size)
        self.tile_y = int(self.rect.midbottom[1] // self.view_tile_size)
        dist_to_target_corner = (target_pixel_pos - self.pos).length()
        if dist_to_target_corner < self.velocidad * 0.5:
             self.pos = target_pixel_pos; self.tile_x, self.tile_y = target_tile; self.path.pop(0)

    def comer(self):
        self.work_timer -= 1
        if self.work_timer <= 0:
            self.vida = min(self.max_vida, self.vida + 10)
            self.recibir_penalizacion_animo(self.COSTO_ANIMO_TAREA, "comer")
            self.mundo.log_event(f"¡{self.nombre} recuperó 10 de vida comiendo!")
            self.estado = 'IDLE'
            self.idle_timer_vagabundeo = random.randint(self.tiempo_min_quieto, self.tiempo_max_quieto)

    def trabajar(self):
        if self.es_enemigo: self.estado = 'IDLE'; return
        
        self.work_timer -= 1
        if self.work_timer <= 0:
            if self.tarea_actual:
                tipo_tarea = self.tarea_actual.tipo
                if self.tarea_actual.objeto_objetivo:
                    tipo_recurso = self.tarea_actual.objeto_objetivo.tipo; cantidad = self.tarea_actual.objeto_objetivo.cantidad
                    self.mundo.agregar_recursos(tipo_recurso, cantidad)
                    self.recibir_penalizacion_animo(self.COSTO_ANIMO_TAREA, f"recolectar {tipo_recurso}")
                    if self.clase == 'recolector' and tipo_recurso in ['madera', 'piedra'] and random.random() < self.PROBABILIDAD_ACCIDENTE:
                        self.sufrir_accidente(tipo_recurso)
                    self.mundo.eliminar_objeto(self.tarea_actual.objeto_objetivo)
                elif tipo_tarea == 'CURAR' and self.tarea_actual.colono_objetivo:
                    objetivo = self.tarea_actual.colono_objetivo
                    if not objetivo.esta_muerto and objetivo.esta_enfermo:
                        objetivo.curar(); self.recibir_mejora_animo(self.BONUS_ANIMO_CURANDERO)
                        self.mundo.log_event(f"{self.nombre} ha curado a {objetivo.nombre} (+10 Ánimo).")
                    else: self.mundo.log_event(f"{self.nombre} intentó curar, pero objetivo no válido.")
                    self.mundo.eliminar_tarea(self.tarea_actual)
                elif tipo_tarea == 'ANIMAR' and self.tarea_actual.colono_objetivo:
                    objetivo = self.tarea_actual.colono_objetivo
                    if not objetivo.esta_muerto and objetivo.estado_animo < 100:
                        objetivo.recibir_mejora_animo(self.BONUS_ANIMO_CURANDERO)
                        self.mundo.log_event(f"{self.nombre} ha animado a {objetivo.nombre} (+10 Ánimo).")
                    else: self.mundo.log_event(f"{self.nombre} intentó animar, pero objetivo no válido.")
                    self.mundo.eliminar_tarea(self.tarea_actual)
                
                self.tarea_actual = None
            self.estado = 'IDLE'
            self.idle_timer_vagabundeo = random.randint(3*60, 8*60)

    def sufrir_accidente(self, tipo_recurso):
        mensaje = "se astilló" if tipo_recurso == 'madera' else "se lesionó"
        self.recibir_penalizacion_animo(self.PENALIZACION_ANIMO_ACCIDENTE, mensaje)

    def recibir_mejora_animo(self, cantidad):
        if self.esta_muerto or self.es_enemigo: return
        self.estado_animo = min(100, self.estado_animo + cantidad)

    def atacar_objetivo(self):
        if self.clase != "guerrero" or self.esta_muerto or not self.objetivo_ataque or self.objetivo_ataque.esta_muerto:
            self.estado = 'IDLE'; self.objetivo_ataque = None; return
        dist_x = abs(self.tile_x - self.objetivo_ataque.tile_x); dist_y = abs(self.tile_y - self.objetivo_ataque.tile_y)
        if dist_x + dist_y > 1:
             self.estado = 'CHASING'
             start = (self.tile_x, self.tile_y); end = (self.objetivo_ataque.tile_x, self.objetivo_ataque.tile_y)
             self.path = a_star(self.mundo, start, end)
             if self.path: self.path.pop(0)
             else: self.estado = 'IDLE'; self.objetivo_ataque = None
             return
        self.tiempo_hasta_proximo_ataque -= 1
        if self.tiempo_hasta_proximo_ataque <= 0:
            self.mundo.log_event(f"¡{self.nombre} ataca a {self.objetivo_ataque.nombre}!")
            self.objetivo_ataque.recibir_daño(self.daño, "ataque", self)
            if not self.es_enemigo:
                self.recibir_penalizacion_animo(self.COSTO_ANIMO_ATAQUE, "atacar")
            self.tiempo_hasta_proximo_ataque = self.attack_cooldown
            self.set_animation(f'attack_{self.facing}')
            if self.objetivo_ataque.esta_muerto:
                 self.estado = 'IDLE'; self.objetivo_ataque = None

    def __str__(self):
        prefix = "[ENEMIGO] " if self.es_enemigo else ""
        daño_str = f" D:{self.daño}" if self.clase == "guerrero" else ""
        target_str = f" -> {self.objetivo_ataque.nombre}" if self.objetivo_ataque else ""
        return f"{prefix}{self.nombre}({self.clase}) ({self.tile_x},{self.tile_y}) V:{self.vida}/{self.max_vida} A:{self.estado_animo}{daño_str} E:{self.estado}{target_str}"

