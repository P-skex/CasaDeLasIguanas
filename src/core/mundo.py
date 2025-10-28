import pygame
import pytmx
import random
import sys
from .colono import Colono
from .tarea import Tarea
from .game_object import GameObject
from src.logic.pathfinding import is_walkable

# Constantes
TILE_SIZE = 16
SPRITE_FRAME_WIDTH = 15
SPRITE_FRAME_HEIGHT = 18
SPRITE_X_OFFSET = 4
SPRITE_Y_OFFSET = 3
SPRITESHEET_COLUMNS = 24
SPRITESHEET_ROWS = 1

class Mundo:
    NOMBRES_ARTEFACTOS = {
        "crocs": "Crocs Sport",
        "pico": "Pico de Diamante",
        "guantes": "Guantes de Box",
        "escamas": "Escamas Forjadas"
    }

    def __init__(self, game_scale, view_tile_size):
        self.width = 0
        self.height = 0
        self.objetos = pygame.sprite.Group()
        self.objetos_por_pos = {}
        self.colonos = []
        self.colision_tiles = set()
        self.tmx_data = None
        self.tareas_asignadas = []
        self.event_log = []
        self.game_scale = game_scale
        self.view_tile_size = view_tile_size

        self.recursos = {"comida": 0, "madera": 0, "piedra": 0}

        # Sistema de Artefactos
        self.probabilidad_artefacto = 1 / 20
        self.inventario_artefactos = {"crocs": 0, "pico": 0, "guantes": 0, "escamas": 0}
        self.efectos_activos = {"crocs": 0, "pico": 0, "guantes": 0, "escamas": 0}
        self.DURACION_ARTEFACTO = 10 * 60

        self.posiciones_recursos_originales = {}
        self.INTERVALO_REGENERACION_MIN = 60 * 60
        self.INTERVALO_REGENERACION_MAX = 120 * 60
        self.tiempo_hasta_regeneracion = random.randint(
            self.INTERVALO_REGENERACION_MIN, self.INTERVALO_REGENERACION_MAX
        )

        self.frames_iguana_verde = None
        self.frames_iguana_amarilla = None
        self.frames_iguana_azul = None
        self.frames_iguana_roja = None
        self.posicion_inicial_jugador = (0, 0)

        self.recompensa_amarilla_dada = False
        self.recompensa_azul_dada = False
        self.juego_terminado = False

        # --- ¡NUEVO! Lógica de Evento Peligroso Genérico ---
        self.evento_peligroso_activo = None # None, "lluvia", "lava"
        self.evento_peligroso_timer = 0
        self.DURACION_EVENTO_PELIGROSO = 10 * 60 # 10 segundos
        self.COSTO_PROTECCION_MADERA = 3
        self.COSTO_PROTECCION_PIEDRA = 3
        self.paraguas_image_scaled = None # Para lluvia
        self.silla_image_scaled = None # Para lava
        self.proteccion_group = pygame.sprite.Group() # Un grupo para ambos
        # ------------------------------------------------

        self.inicializar_mundo()

    def _elegir_nombre_iguana(self, nombre_base, es_enemigo=False, color_enemigo=""):
        nombre_base = nombre_base.strip().lower(); nombre_capitalizado = nombre_base.capitalize()
        if es_enemigo: return nombre_capitalizado
        else:
            if nombre_base.endswith("a"): return f"{nombre_capitalizado} la Iguana"
            elif nombre_base.endswith("o"): return f"{nombre_capitalizado} el Iguano"
            else: return f"{nombre_capitalizado} la Iguana"

    def inicializar_mundo(self):
        self.cargar_mapa("assets/maps/mapaIguanas.tmx")

        # Carga de Spritesheets
        path_verde = "assets/sprites/iguanaVerde.png"; path_amarilla = "assets/sprites/iguanaAmarilla.png"
        path_azul = "assets/sprites/iguanaAzul.png"; path_roja = "assets/sprites/iguanaRoja.png"
        path_paraguas = "assets/sprites/paraguas.png"
        path_silla = "assets/sprites/silla.png" # ¡Asegúrate de tener este archivo!
        
        self.frames_iguana_verde = self._load_and_split_spritesheet(path_verde, SPRITE_FRAME_WIDTH, SPRITE_FRAME_HEIGHT, SPRITESHEET_COLUMNS)
        self.frames_iguana_amarilla = self._load_and_split_spritesheet(path_amarilla, SPRITE_FRAME_WIDTH, SPRITE_FRAME_HEIGHT, SPRITESHEET_COLUMNS)
        self.frames_iguana_azul = self._load_and_split_spritesheet(path_azul, SPRITE_FRAME_WIDTH, SPRITE_FRAME_HEIGHT, SPRITESHEET_COLUMNS)
        self.frames_iguana_roja = self._load_and_split_spritesheet(path_roja, SPRITE_FRAME_WIDTH, SPRITE_FRAME_HEIGHT, SPRITESHEET_COLUMNS)
        
        # Cargar y escalar imagen del paraguas
        try:
            img_p = pygame.image.load(path_paraguas).convert_alpha()
            scaled_w_p = self.view_tile_size; scaled_h_p = int(img_p.get_height() * (scaled_w_p / img_p.get_width()))
            self.paraguas_image_scaled = pygame.transform.scale(img_p, (scaled_w_p, scaled_h_p))
        except Exception as e:
            print(f"ERROR: No se encontró '{path_paraguas}'. {e}"); self._crear_fallback_proteccion("paraguas")

        # --- ¡NUEVO! Cargar y escalar imagen de la silla ---
        try:
            img_s = pygame.image.load(path_silla).convert_alpha()
            scaled_w_s = self.view_tile_size; scaled_h_s = int(img_s.get_height() * (scaled_w_s / img_s.get_width()))
            self.silla_image_scaled = pygame.transform.scale(img_s, (scaled_w_s, scaled_h_s))
        except Exception as e:
            print(f"ERROR: No se encontró '{path_silla}'. {e}"); self._crear_fallback_proteccion("silla")
        # ----------------------------------------------------

        if not (self.frames_iguana_verde and self.frames_iguana_amarilla and self.frames_iguana_azul and self.frames_iguana_roja):
             print("ERROR FATAL: No se pudieron cargar TODOS los spritesheets. Abortando."); sys.exit()

        # Nombres
        nombres_na = [
            "Martina","Juliana","Liliana","Luciana","Adriana","Diana","Ana","Viviana","Alana","Ivanna","Liana","Mariana","Simona",
            "Eliana","Ariana","Gianna","Roxana","Susana","Tatiana","Nathana","Juliano","Emiliano","Adriano","Marciano","Fabiano",
            "Silvano","Valeriano","Flaviano","Ignacio","Tachiquano","Yetusano","Lomecano","Elordiano","Marlon","Betano","Fulano",
            "Perengano","Merengano","Betano","Rana","Banana","Tuermana","Aldano"
        ]
        num_jugadores = 8; num_enemigos_amarillos = 6; num_enemigos_azules = 6; num_enemigos_rojos = 6
        total_necesarios = num_jugadores + num_enemigos_amarillos + num_enemigos_azules + num_enemigos_rojos
        if len(nombres_na) < total_necesarios:
            nombres_na.extend([f"Extra{i}" for i in range(total_necesarios - len(nombres_na))])
        nombres_disponibles = nombres_na[:]; random.shuffle(nombres_disponibles)
        
        stats_amarillo = {"max_vida": 133, "daño": 13}; stats_azul = {"max_vida": 166, "daño": 16}; stats_rojo = {"max_vida": 200, "daño": 20}

        # Creación Jugadores
        colono_clases_jugador = ["recolector", "recolector", "recolector", "guerrero", "guerrero", "guerrero", "curandero", "curandero"]
        start_x_jugador = self.width - 8; start_y_jugador = self.height - 8
        self.posicion_inicial_jugador = (start_x_jugador, start_y_jugador)
        for i in range(num_jugadores):
             r = i // 2; c = i % 2; tile_x = start_x_jugador + c * 2; tile_y = start_y_jugador + r * 2
             tile_x = max(0, min(tile_x, self.width - 1)); tile_y = max(0, min(tile_y, self.height - 1))
             nombre_base = nombres_disponibles.pop(); nombre_colono = self._elegir_nombre_iguana(nombre_base, False)
             clase_colono = colono_clases_jugador[i]
             colono = Colono(x=tile_x, y=tile_y, mundo=self, nombre=nombre_colono, clase=clase_colono,
                             game_scale=self.game_scale, view_tile_size=self.view_tile_size,
                             all_frames=self.frames_iguana_verde, es_enemigo=False, stats_enemigo=None, tribu="jugador")
             self.colonos.append(colono)

        # Creación Enemigos
        posiciones_enemigos = [
            (1, self.height - 3, num_enemigos_amarillos, self.frames_iguana_amarilla, stats_amarillo, "amarillo"),
            (self.width - 6, 1, num_enemigos_azules, self.frames_iguana_azul, stats_azul, "azul"),
            (1, 1, num_enemigos_rojos, self.frames_iguana_roja, stats_rojo, "rojo")
        ]
        for start_x, start_y, num, frames, stats, tribu in posiciones_enemigos:
            for i in range(num):
                tile_x_e = start_x + (i % 3) * 2; tile_y_e = start_y + (i // 3) * 2
                tile_x_e = max(0, min(tile_x_e, self.width - 1)); tile_y_e = max(0, min(tile_y_e, self.height - 1))
                nombre_base_enemigo = nombres_disponibles.pop()
                nombre_enemigo = self._elegir_nombre_iguana(nombre_base_enemigo, True)
                enemigo = Colono(x=tile_x_e, y=tile_y_e, mundo=self, nombre=nombre_enemigo, clase="guerrero",
                                 game_scale=self.game_scale, view_tile_size=self.view_tile_size,
                                 all_frames=frames, es_enemigo=True, stats_enemigo=stats, tribu=tribu)
                self.colonos.append(enemigo)

        nombres_fundacion = ", ".join([c.nombre for c in self.colonos if not c.es_enemigo][:2])
        self.log_event(f"Colonia de {len([c for c in self.colonos if not c.es_enemigo])} iguanas fundada.")
        total_enemigos = num_enemigos_amarillos + num_enemigos_azules + num_enemigos_rojos
        self.log_event(f"¡Aparecen {total_enemigos} iguanas enemigas!")

    # --- ¡NUEVO! Helper para crear imagen de fallback ---
    def _crear_fallback_proteccion(self, tipo):
        """Crea una imagen de fallback si no se encuentra el sprite."""
        color = (100, 100, 255, 150) if tipo == "paraguas" else (150, 100, 50, 150) # Azul o Marrón
        fallback_image = pygame.Surface((self.view_tile_size, self.view_tile_size), pygame.SRCALPHA)
        pygame.draw.rect(fallback_image, color, (0, 0, self.view_tile_size, self.view_tile_size)) # Un cuadrado
        
        if tipo == "paraguas":
            self.paraguas_image_scaled = fallback_image
        elif tipo == "silla":
            self.silla_image_scaled = fallback_image
    # ----------------------------------------------------

    def cargar_mapa(self, path):
        print(f"Cargando datos del mapa desde: {path}")
        try: self.tmx_data = pytmx.load_pygame(path, pixelalpha=True)
        except FileNotFoundError: print(f"ERROR FATAL: No se encontró '{path}'."); sys.exit()
        self.width = self.tmx_data.width; self.height = self.tmx_data.height
        self.posiciones_recursos_originales.clear(); self.colision_tiles.clear()
        for layer in self.tmx_data.layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                if layer.name == 'colisiones':
                    for x, y, gid in layer:
                        if gid != 0: self.colision_tiles.add((x, y))
            elif isinstance(layer, pytmx.TiledObjectGroup):
                if layer.name != "colisiones":
                    for obj in layer:
                        if obj.image:
                            tile_x=int(obj.x//TILE_SIZE); tile_y=int(obj.y//TILE_SIZE)
                            scaled_width=int(obj.width*self.game_scale); scaled_height=int(obj.height*self.game_scale)
                            try: scaled_image=pygame.transform.scale(obj.image,(scaled_width,scaled_height))
                            except Exception as e: print(f"    - Advertencia: No se pudo escalar '{obj.name}'. Error: {e}"); continue
                            if layer.name in ["comida","madera","piedra"]:
                                self.posiciones_recursos_originales[(tile_x,tile_y)]={'nombre':obj.name,'tipo':layer.name,'image_original':obj.image,'width_original':obj.width,'height_original':obj.height}
                            nuevo_objeto=GameObject(nombre=obj.name,tipo=layer.name,tile_x=tile_x,tile_y=tile_y,image=scaled_image,game_scale=self.game_scale,view_tile_size=self.view_tile_size)
                            self.objetos.add(nuevo_objeto); self.objetos_por_pos[(tile_x,tile_y)]=nuevo_objeto
    
    def _load_and_split_spritesheet(self, path, frame_width, frame_height, num_frames):
        try: spritesheet = pygame.image.load(path).convert_alpha()
        except pygame.error as e: print(f"Error cargando spritesheet '{path}': {e}"); return []
        frames = []; scaled_width = int(frame_width * self.game_scale); scaled_height = int(frame_height * self.game_scale)
        sheet_actual_width = spritesheet.get_width(); sheet_actual_height = spritesheet.get_height()
        for i in range(num_frames):
            start_x = i * frame_width + SPRITE_X_OFFSET; start_y = SPRITE_Y_OFFSET
            frame_rect = pygame.Rect(start_x, start_y, frame_width, frame_height)
            if frame_rect.right > sheet_actual_width or frame_rect.bottom > sheet_actual_height: continue
            try:
                frame_image = spritesheet.subsurface(frame_rect)
                scaled_frame = pygame.transform.scale(frame_image, (scaled_width, scaled_height))
                frames.append(scaled_frame)
            except ValueError as e: print(f"Error al cortar/escalar frame {i} de '{path}' con rect {frame_rect}: {e}")
        if not frames: print(f"Advertencia: No se cargaron frames válidos de '{path}'.")
        return frames

    def agregar_recursos(self, tipo_recurso, cantidad):
        mapa_tipo = {'comida': 'comida', 'madera': 'madera', 'piedra': 'piedra'}
        recurso = mapa_tipo.get(tipo_recurso)
        if recurso: 
            self.recursos[recurso] += cantidad
            self.log_event(f"¡+{cantidad} de {recurso}! (Total: {self.recursos[recurso]})")
            if random.random() < self.probabilidad_artefacto: self._encontrar_artefacto()
        else: print(f"Advertencia: Recurso desconocido '{tipo_recurso}'")
    
    def _encontrar_artefacto(self):
        tipo = random.choice(list(self.inventario_artefactos.keys()))
        self.inventario_artefactos[tipo] += 1
        nombre_display = self.NOMBRES_ARTEFACTOS.get(tipo, tipo.capitalize())
        self.log_event(f"¡Has encontrado: {nombre_display}!")
        self.log_event("Presiona F1-F4 para activarlo.")

    def activar_artefacto(self, tipo_artefacto):
        nombre_display = self.NOMBRES_ARTEFACTOS.get(tipo_artefacto, tipo_artefacto.capitalize())
        if tipo_artefacto not in self.inventario_artefactos: return
        if self.inventario_artefactos[tipo_artefacto] > 0:
            self.inventario_artefactos[tipo_artefacto] -= 1
            self.efectos_activos[tipo_artefacto] += self.DURACION_ARTEFACTO
            self._aplicar_efecto_global(tipo_artefacto)
            self.log_event(f"¡{nombre_display} activado por 10s!")
        else: self.log_event(f"No tienes más {nombre_display}.")
            
    def _aplicar_efecto_global(self, tipo_artefacto):
        for colono in self.colonos:
            if not colono.es_enemigo: colono.aplicar_buff(tipo_artefacto)

    def _desactivar_efecto(self, tipo_artefacto):
        nombre_display = self.NOMBRES_ARTEFACTOS.get(tipo_artefacto, tipo_artefacto.capitalize())
        self.log_event(f"¡Efecto de {nombre_display} ha terminado!")
        for colono in self.colonos:
            if not colono.es_enemigo: colono.quitar_buff(tipo_artefacto)

    def _update_efectos_activos(self):
        for tipo in list(self.efectos_activos.keys()):
            if self.efectos_activos[tipo] > 0:
                self.efectos_activos[tipo] -= 1
                if self.efectos_activos[tipo] == 0:
                    self._desactivar_efecto(tipo)

    def obtener_objetos_disponibles(self, tipo_objeto):
        objetos_ya_asignados = set(tarea.objeto_objetivo for tarea in self.tareas_asignadas if tarea.objeto_objetivo)
        return [obj for obj in self.objetos if obj.tipo == tipo_objeto and obj not in objetos_ya_asignados]

    def obtener_enfermos_sin_atender(self):
        enfermos_ya_asignados = set(tarea.colono_objetivo for tarea in self.tareas_asignadas if tarea.tipo == 'CURAR' and tarea.colono_objetivo)
        return [c for c in self.colonos if not c.es_enemigo and c.esta_enfermo and c not in enfermos_ya_asignados]

    def obtener_tristes_sin_atender(self, umbral_animo):
        tristes_ya_asignados = set(tarea.colono_objetivo for tarea in self.tareas_asignadas if tarea.tipo == 'ANIMAR' and tarea.colono_objetivo)
        return [
            c for c in self.colonos 
            if not c.es_enemigo and not c.esta_muerto and not c.esta_enfermo
            and c.estado_animo < umbral_animo
            and c not in tristes_ya_asignados
        ]

    def crear_tarea(self, tipo_tarea, posicion, objeto_objetivo=None, colono_objetivo=None):
        nueva_tarea = Tarea(tipo_tarea, posicion, objeto_objetivo=objeto_objetivo, colono_objetivo=colono_objetivo)
        self.tareas_asignadas.append(nueva_tarea)
        return nueva_tarea

    def eliminar_objeto(self, objeto):
        if objeto:
            pos_key = (objeto.tile_x, objeto.tile_y)
            if pos_key in self.objetos_por_pos and self.objetos_por_pos[pos_key] == objeto: del self.objetos_por_pos[pos_key]
            tarea_a_eliminar = next((t for t in self.tareas_asignadas if t.objeto_objetivo == objeto), None)
            if tarea_a_eliminar: self.eliminar_tarea(tarea_a_eliminar)
            objeto.kill()

    def eliminar_tarea(self, tarea):
        """Elimina cualquier tipo de tarea de la lista de asignadas."""
        if tarea in self.tareas_asignadas: 
            self.tareas_asignadas.remove(tarea)

    def eliminar_colono(self, colono_a_eliminar):
        if colono_a_eliminar in self.colonos:
            tribu = colono_a_eliminar.tribu
            self.colonos.remove(colono_a_eliminar)
            print(f"{colono_a_eliminar.nombre} ha sido eliminado del mundo.")
            self._chequear_recompensas_por_tribu(tribu)
        else: print(f"Advertencia: Se intentó eliminar a {colono_a_eliminar.nombre} no encontrado.")

    def log_event(self, mensaje):
        print(mensaje); self.event_log.insert(0, mensaje)
        if len(self.event_log) > 10: self.event_log.pop()

    def _regenerar_recursos(self):
        recursos_regenerados = 0
        posiciones_a_revisar = list(self.posiciones_recursos_originales.keys())
        for (x, y) in posiciones_a_revisar:
            if (x,y) not in self.posiciones_recursos_originales: continue
            data = self.posiciones_recursos_originales[(x,y)]
            if (x, y) not in self.objetos_por_pos:
                scaled_width=int(data['width_original']*self.game_scale); scaled_height=int(data['height_original']*self.game_scale)
                try: img_original=data['image_original']; scaled_image=pygame.transform.scale(img_original,(scaled_width,scaled_height))
                except Exception as e: print(f"Error escalando imagen para regenerar {data.get('nombre', 'Desc')} ({x},{y}): {e}"); continue
                nuevo_objeto=GameObject(nombre=data['nombre'],tipo=data['tipo'],tile_x=x,tile_y=y,image=scaled_image,game_scale=self.game_scale,view_tile_size=self.view_tile_size)
                self.objetos.add(nuevo_objeto); self.objetos_por_pos[(x, y)] = nuevo_objeto
                recursos_regenerados += 1
        if recursos_regenerados > 0: self.log_event(f"¡Se han regenerado {recursos_regenerados} recursos!")

    def _chequear_recompensas_por_tribu(self, tribu_eliminada):
        if tribu_eliminada == "jugador" or self.juego_terminado: return
        enemigos_restantes = [c for c in self.colonos if c.tribu == tribu_eliminada and not c.esta_muerto]
        if len(enemigos_restantes) > 0: return
        if tribu_eliminada == "amarillo" and not self.recompensa_amarilla_dada:
            self.log_event("¡Tribu Amarilla derrotada! +100 de cada recurso.")
            self.recursos["comida"] += 100; self.recursos["madera"] += 100; self.recursos["piedra"] += 100
            self.recompensa_amarilla_dada = True
        elif tribu_eliminada == "azul" and not self.recompensa_azul_dada:
            self.log_event("¡Tribu Azul derrotada! +200 de cada recurso.")
            self.recursos["comida"] += 200; self.recursos["madera"] += 200; self.recursos["piedra"] += 200
            self.recompensa_azul_dada = True
        elif tribu_eliminada == "rojo":
            self.log_event("¡VICTORIA! ¡Has derrotado a la Tribu Roja!")
            self.juego_terminado = True
            
    # --- ¡FUNCIONES DE EVENTO PELIGROSO GENÉRICAS! ---
    def _iniciar_evento_peligroso(self, tipo_evento):
        """Inicia un evento peligroso (lluvia o lava)."""
        if self.evento_peligroso_activo is not None: return # Ya hay un evento
        
        self.evento_peligroso_activo = tipo_evento
        self.evento_peligroso_timer = self.DURACION_EVENTO_PELIGROSO
        
        nombre_evento = "Lluvia Ácida" if tipo_evento == "lluvia" else "El Suelo es Lava"
        self.log_event(f"¡{nombre_evento} ha comenzado!")

        for colono in self.colonos:
            if not colono.es_enemigo and not colono.esta_muerto:
                # Chequea si tiene recursos
                if self.recursos["madera"] >= self.COSTO_PROTECCION_MADERA and \
                   self.recursos["piedra"] >= self.COSTO_PROTECCION_PIEDRA:
                    
                    self.recursos["madera"] -= self.COSTO_PROTECCION_MADERA
                    self.recursos["piedra"] -= self.COSTO_PROTECCION_PIEDRA
                    colono.construir_proteccion(tipo_evento) # Pasa el tipo de evento
                else:
                    colono.sin_proteccion()

    def _detener_evento_peligroso(self):
        """Detiene el evento peligroso actual."""
        if self.evento_peligroso_activo is None: return
        
        nombre_evento = "Lluvia Ácida" if self.evento_peligroso_activo == "lluvia" else "El Suelo es Lava"
        self.log_event(f"¡{nombre_evento} ha terminado!")
        
        self.evento_peligroso_activo = None
        self.evento_peligroso_timer = 0
        
        for colono in self.colonos:
            colono.quitar_proteccion()
        self.proteccion_group.empty() # Elimina todos los sprites de protección

    def _update_evento_peligroso(self):
        """Actualiza el temporizador del evento peligroso."""
        if self.evento_peligroso_activo is not None:
            self.evento_peligroso_timer -= 1
            if self.evento_peligroso_timer <= 0:
                self._detener_evento_peligroso()
    # --------------------------------------------------

    # --- ¡NUEVO! Función para Prueba de Estrés ---
    def iniciar_prueba_de_estres(self, acopio_tier_actual, damage_tier_actual, acopio_upgrades, damage_upgrades):
        """Crea 50 iguanas guerreras del jugador en la base."""
        nombres_para_prueba = [
            "Alfa", "Bravo", "Charlie", "Delta", "Eco", "Foxtrot", "Golf", "Hotel", "India", "Juliet",
            "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", "Sierra", "Tango",
            "Uniform", "Victor", "Whiskey", "Xray", "Yankee", "Zulu"
        ]
        creados = 0
        for i in range(50):
            posicion_spawn = self.buscar_posicion_libre_cercana(self.posicion_inicial_jugador[0], self.posicion_inicial_jugador[1], max_distancia=10)
            if not posicion_spawn:
                posicion_spawn = self.buscar_posicion_libre_cercana(1, 1, max_distancia=10)
                if not posicion_spawn:
                     self.log_event(f"Prueba de Estrés: No se encontró espacio para iguana {i+1}/50.")
                     continue
            
            nombre_base = f"Test{i}"
            if i < len(nombres_para_prueba): nombre_base = f"{nombres_para_prueba[i]}-{i}"
            else: nombre_base = f"Test{i}-{random.randint(100,999)}"
            
            nombre_colono = self._elegir_nombre_iguana(nombre_base, False)

            nuevo_colono = Colono(
                x=posicion_spawn[0], y=posicion_spawn[1], mundo=self,
                nombre=nombre_colono, clase="guerrero",
                game_scale=self.game_scale, view_tile_size=self.view_tile_size,
                all_frames=self.frames_iguana_verde, es_enemigo=False, stats_enemigo=None, tribu="jugador"
            )

            max_vida_actual = acopio_upgrades[acopio_tier_actual]["max_vida"]
            daño_actual = damage_upgrades[damage_tier_actual]["daño_guerrero"]
            nuevo_colono.set_max_vida(max_vida_actual); nuevo_colono.set_daño(daño_actual)
            self.colonos.append(nuevo_colono)
            creados += 1
        self.log_event(f"¡Prueba de Estrés: {creados}/50 iguanas guerreras creadas!")
    # -------------------------------------

    def update(self):
        for colono in self.colonos[:]:
             if colono not in self.colonos: continue
             colono.update()
        
        self._update_efectos_activos()
        self._update_evento_peligroso() # ¡Llama al update de evento!
        
        self.tiempo_hasta_regeneracion -= 1
        if self.tiempo_hasta_regeneracion <= 0:
            self._regenerar_recursos()
            self.tiempo_hasta_regeneracion = random.randint(self.INTERVALO_REGENERACION_MIN, self.INTERVALO_REGENERACION_MAX)

    def buscar_posicion_libre_cercana(self, origen_x, origen_y, max_distancia=5):
        for dist in range(1, max_distancia + 1):
            for i in range(dist):
                j = dist - i
                posiciones = [(origen_x + i, origen_y + j), (origen_x - i, origen_y - j),
                              (origen_x + j, origen_y - i), (origen_x - j, origen_y + i)]
                for check_pos in posiciones:
                    check_x, check_y = check_pos
                    if 0 <= check_x < self.width and 0 <= check_y < self.height and \
                       is_walkable(self, check_pos):
                        ocupado_por_colono = any(c.tile_x == check_x and c.tile_y == check_y for c in self.colonos)
                        ocupado_por_objeto = check_pos in self.objetos_por_pos
                        if not ocupado_por_colono and not ocupado_por_objeto: return check_pos
        return None

    def crear_nueva_iguana(self, clase_elegida, acopio_tier_actual, damage_tier_actual, acopio_upgrades, damage_upgrades):
        costo_comida=100; costo_madera=100; costo_piedra=100
        if self.recursos['comida']<costo_comida or self.recursos['madera']<costo_madera or self.recursos['piedra']<costo_piedra:
            self.log_event("Recursos insuficientes."); return False
        posicion_spawn = self.buscar_posicion_libre_cercana(self.posicion_inicial_jugador[0], self.posicion_inicial_jugador[1])
        if not posicion_spawn: self.log_event("No se encontró espacio libre."); return False
        self.recursos['comida']-=costo_comida; self.recursos['madera']-=costo_madera; self.recursos['piedra']-=costo_piedra
        nombres_na_full = ["Martina","Juliana", "Liliana", "Luciana", "Adriana", "Diana", "Ana", "Viviana", "Alana", "Ivanna", "Liana", "Mariana", "Simona", "Eliana", "Ariana", "Gianna", "Roxana", "Susana", "Tatiana", "Nathana", "Juliano", "Emiliano", "Adriano", "Marciano", "Fabiano", "Silvano", "Valeriano", "Flaviano", "Ignacio", "Tachiquano", "Yetusano", "Lomecano", "Elordiano", "Marlon", "Betano", "Fulano", "Perengano", "Merengano", "Rana", "Banana", "Tuermana", "Aldano"]
        nombres_usados = {c.nombre.split(' ')[0].lower() for c in self.colonos}
        nombres_disponibles_nuevos = [n for n in nombres_na_full if n.lower() not in nombres_usados]
        if not nombres_disponibles_nuevos: nombre_base = f"Iguana{len(self.colonos)}"
        else: nombre_base = random.choice(nombres_disponibles_nuevos)
        nombre_colono = self._elegir_nombre_iguana(nombre_base, False)
        nuevo_colono = Colono(x=posicion_spawn[0], y=posicion_spawn[1], mundo=self, nombre=nombre_colono, clase=clase_elegida,
                               game_scale=self.game_scale, view_tile_size=self.view_tile_size,
                               all_frames=self.frames_iguana_verde, es_enemigo=False, stats_enemigo=None, tribu="jugador")
        max_vida_actual = acopio_upgrades[acopio_tier_actual]["max_vida"]
        daño_actual = damage_upgrades[damage_tier_actual]["daño_guerrero"]
        nuevo_colono.set_max_vida(max_vida_actual); nuevo_colono.set_daño(daño_actual)
        self.colonos.append(nuevo_colono); self.log_event(f"¡Ha nacido {nuevo_colono.nombre} ({clase_elegida})!"); return True

