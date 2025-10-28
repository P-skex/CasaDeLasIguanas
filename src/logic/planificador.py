from src.data_structures.priority_queue import PriorityQueue
from src.core.tarea import Tarea
import random
from .pathfinding import is_walkable, a_star

class Planificador:
    """Decide qué colono JUGADOR debe realizar qué tarea."""
    def __init__(self, mundo):
        self.mundo = mundo
        self.solicitudes_pendientes = []
        self.pq_eventos = PriorityQueue()
        self.mapa_tipo_tarea_a_objeto = {'RECOGER': 'comida', 'TALAR': 'madera', 'MINAR': 'piedra'}
        self.mapa_clase_a_tareas = {
            'recolector': ['RECOGER', 'TALAR', 'MINAR'],
            'guerrero': ['ATTACK'],
            'curandero': ['CURAR', 'ANIMAR']
        }
        self.TAREA_ANIMAR_UMBRAL = 90

    def solicitar_tarea(self, tipo_tarea):
        self.solicitudes_pendientes.append(tipo_tarea); print(f"Solicitando tarea de recurso: {tipo_tarea}")

    def solicitar_curacion(self):
        print("Solicitando tarea de curación..."); self.ejecutar_asignacion_curacion()
        
    def solicitar_ataque_general(self):
        """Ordena a todos los guerreros jugadores aptos que ataquen al enemigo más cercano."""
        self.mundo.log_event("¡A LA CARGA! Buscando objetivos...")
        
        # --- ¡CAMBIO AQUÍ! ---
        # Ahora también incluye guerreros que están 'MOVING' (vagabundeando)
        guerreros_disponibles = [
            c for c in self.mundo.colonos 
            if not c.es_enemigo 
            and c.clase == 'guerrero' 
            # Acepta IDLE o MOVING (siempre que no sea por una tarea, lo cual 'tarea_actual' ya cubre)
            and (c.estado == 'IDLE' or (c.estado == 'MOVING' and not c.tarea_actual))
            and not c.esta_enfermo 
            and c.vida > 0
            and c.estado_animo >= c.LIMITE_ANIMO_PARA_TRABAJAR
        ]
        # ----------------------------------------------------
        
        enemigos_vivos = [e for e in self.mundo.colonos if e.es_enemigo and not e.esta_muerto]

        if not guerreros_disponibles:
            self.mundo.log_event("No hay guerreros listos para el ataque."); return
        if not enemigos_vivos:
            self.mundo.log_event("¡No quedan enemigos!"); return

        asignaciones = 0
        for guerrero in guerreros_disponibles:
            enemigo_mas_cercano = min(
                enemigos_vivos, 
                key=lambda e: abs(guerrero.tile_x - e.tile_x) + abs(guerrero.tile_y - e.tile_y)
            )
            
            guerrero.objetivo_ataque = enemigo_mas_cercano
            guerrero.estado = 'CHASING' # El estado 'CHASING' iniciará el pathfinding en colono.update
            # Reseteamos el path de vagabundeo si lo tenía
            guerrero.path = [] 
            self.mundo.log_event(f"¡{guerrero.nombre} va a atacar a {enemigo_mas_cercano.nombre}!")
            asignaciones += 1
        
        if asignaciones == 0:
             self.mundo.log_event("Guerreros listos, pero no se encontraron rutas.")
             
    def update(self):
        if self.solicitudes_pendientes:
            tipo_tarea_recurso = self.solicitudes_pendientes.pop(0)
            self.ejecutar_asignacion_recurso(tipo_tarea_recurso)
        
        # Estas tareas automáticas se siguen ejecutando
        self.ejecutar_asignacion_curacion()
        self.ejecutar_asignacion_animo()

    def ejecutar_asignacion_recurso(self, tipo_tarea):
        clase_requerida = 'recolector'
        colonos_aptos = [
            c for c in self.mundo.colonos 
            if not c.es_enemigo and c.estado == 'IDLE' and c.clase == clase_requerida 
            and not c.esta_enfermo and c.vida > 0
            and c.estado_animo >= c.LIMITE_ANIMO_PARA_TRABAJAR
        ]

        if not colonos_aptos:
            if [c for c in self.mundo.colonos if not c.es_enemigo and c.clase == clase_requerida and c.estado == 'IDLE' and c.estado_animo < c.LIMITE_ANIMO_PARA_TRABAJAR]:
                self.mundo.log_event(f"¡Recolectores están muy tristes para {tipo_tarea}!")
            return

        tipo_objeto = self.mapa_tipo_tarea_a_objeto.get(tipo_tarea)
        objetos_disponibles = self.mundo.obtener_objetos_disponibles(tipo_objeto)
        if not objetos_disponibles:
            self.mundo.log_event(f"No hay más '{tipo_objeto}' disponibles."); return

        mejor_par = None; min_distancia = float('inf'); mejor_posicion_destino = None
        for colono in colonos_aptos:
            objeto_mas_cercano = min(objetos_disponibles, key=lambda obj: abs(colono.tile_x - obj.tile_x) + abs(colono.tile_y - obj.tile_y))
            posicion_adyacente = self.encontrar_posicion_adyacente_valida(objeto_mas_cercano.tile_x, objeto_mas_cercano.tile_y, colono)
            if not posicion_adyacente: continue
            distancia = abs(colono.tile_x - posicion_adyacente[0]) + abs(colono.tile_y - posicion_adyacente[1])
            if distancia < min_distancia:
                min_distancia = distancia; mejor_par = (colono, objeto_mas_cercano); mejor_posicion_destino = posicion_adyacente

        if mejor_par:
            (mejor_colono, mejor_objeto) = mejor_par
            nueva_tarea = self.mundo.crear_tarea(tipo_tarea, mejor_posicion_destino, objeto_objetivo=mejor_objeto)
            mejor_colono.asignar_tarea(nueva_tarea)
            self.mundo.log_event(f"¡{mejor_colono.nombre} va a {tipo_tarea} cerca de ({mejor_objeto.tile_x}, {mejor_objeto.tile_y})!")
        else:
            self.mundo.log_event(f"No se pudo encontrar par colono/objeto accesible para {tipo_tarea}.")

    def ejecutar_asignacion_curacion(self):
        curanderos_disponibles = [c for c in self.mundo.colonos if not c.es_enemigo and c.estado == 'IDLE' and c.clase == 'curandero' and not c.esta_enfermo and c.vida > 0]
        if not curanderos_disponibles: return

        enfermos_necesitados = self.mundo.obtener_enfermos_sin_atender()
        if not enfermos_necesitados: return
        
        for curandero in curanderos_disponibles:
             if not enfermos_necesitados: break
             enfermo_objetivo = min(enfermos_necesitados, key=lambda e: abs(curandero.tile_x - e.tile_x) + abs(curandero.tile_y - e.tile_y))
             posicion_destino = self.encontrar_posicion_adyacente_valida(enfermo_objetivo.tile_x, enfermo_objetivo.tile_y, curandero)
             if posicion_destino:
                 nueva_tarea = self.mundo.crear_tarea('CURAR', posicion_destino, colono_objetivo=enfermo_objetivo)
                 curandero.asignar_tarea(nueva_tarea)
                 self.mundo.log_event(f"¡{curandero.nombre} va a CURAR a {enfermo_objetivo.nombre}!")
                 enfermos_necesitados.remove(enfermo_objetivo)

    def ejecutar_asignacion_animo(self):
        """Busca iguanas tristes y asigna curanderos para animarlas."""
        curanderos_disponibles = [
            c for c in self.mundo.colonos 
            if not c.es_enemigo and c.estado == 'IDLE' 
            and c.clase == 'curandero' 
            and not c.esta_enfermo and c.vida > 0
        ]
        if not curanderos_disponibles: return

        tristes_necesitados = self.mundo.obtener_tristes_sin_atender(self.TAREA_ANIMAR_UMBRAL)
        if not tristes_necesitados: return
        
        for curandero in curanderos_disponibles:
            if not tristes_necesitados: break
            triste_objetivo = min(tristes_necesitados, key=lambda t: abs(curandero.tile_x - t.tile_x) + abs(curandero.tile_y - t.tile_y))
            posicion_destino = self.encontrar_posicion_adyacente_valida(triste_objetivo.tile_x, triste_objetivo.tile_y, curandero)
            if posicion_destino:
                nueva_tarea = self.mundo.crear_tarea('ANIMAR', posicion_destino, colono_objetivo=triste_objetivo)
                curandero.asignar_tarea(nueva_tarea)
                self.mundo.log_event(f"¡{curandero.nombre} va a ANIMAR a {triste_objetivo.nombre}!")
                tristes_necesitados.remove(triste_objetivo)

    def encontrar_posicion_adyacente_valida(self, target_x, target_y, actor=None):
        posiciones_a_chequear = [(target_x + dx, target_y + dy) for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]]
        posiciones_validas = []
        for check_pos in posiciones_a_chequear:
            if is_walkable(self.mundo, check_pos):
                colono_en_pos = next((c for c in self.mundo.colonos if c.tile_x == check_pos[0] and c.tile_y == check_pos[1] and not c.esta_muerto), None)
                if not colono_en_pos:
                    posiciones_validas.append(check_pos)
        if not posiciones_validas: return None
        if actor: return min(posiciones_validas, key=lambda pos: abs(actor.tile_x - pos[0]) + abs(actor.tile_y - pos[1]))
        else: return posiciones_validas[0]

    def reorganizar_heap(self): pass

