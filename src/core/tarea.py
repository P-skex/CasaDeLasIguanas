import itertools

class Tarea:
    """Representa una tarea a completar."""
    id_iter = itertools.count()
    
    def __init__(self, tipo, posicion, prioridad_base=10, objeto_objetivo=None, colono_objetivo=None):
        self.id = next(Tarea.id_iter)
        self.tipo = tipo  # 'MINAR', 'TALAR', 'RECOGER', 'CURAR'
        self.posicion = posicion  # (x, y) del tile objetivo
        self.prioridad_base = prioridad_base
        self.prioridad_final = prioridad_base
        self.estado = 'PENDING' 
        self.colono_asignado = None
        self.duracion = 180 # Duración base, curar podría ser más rápido
        if self.tipo == 'CURAR':
            self.duracion = 120 # Curar es un poco más rápido (2 segundos)

        # --- ¡CAMBIO AQUÍ! ---
        # Ahora una tarea puede tener un objeto O un colono como objetivo
        self.objeto_objetivo = objeto_objetivo
        self.colono_objetivo = colono_objetivo
        # --------------------

    def calcular_prioridad_final(self, colono):
        """Calcula la prioridad basada en la distancia (usado solo para recursos)."""
        # Las tareas de curar tienen prioridad fija por ahora
        if self.tipo != 'CURAR':
            distancia = abs(colono.tile_x - self.posicion[0]) + abs(colono.tile_y - self.posicion[1])
            self.prioridad_final = self.prioridad_base - (distancia * 0.1)

    def __lt__(self, other):
        """Comparación para el heap (solo eventos, no usado para auto-asignación)."""
        return self.prioridad_final < other.prioridad_final

