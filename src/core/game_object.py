import pygame
import random

# TILE_SIZE no es estrictamente necesario aquí, pero puede ser útil para debug
TILE_SIZE = 16

class GameObject(pygame.sprite.Sprite):
    """Representa un objeto interactivo en el mundo (piedra, árbol, comida, etc.)"""
    # --- ¡CORRECCIÓN AQUÍ! ---
    # Ajustamos los parámetros que recibe __init__ para que coincidan con la llamada en mundo.py
    def __init__(self, nombre, tipo, tile_x, tile_y, image, game_scale, view_tile_size):
        super().__init__()
        self.image = image # La imagen ya viene escalada desde Mundo
        self.nombre = nombre # Nombre individual del objeto (ej. "RocaGrande")
        self.tipo = tipo   # Tipo = Nombre de la capa (ej. "piedra")

        self.tile_x = tile_x # Posición en la cuadrícula
        self.tile_y = tile_y

        # Calculamos la posición en píxeles usando view_tile_size
        pixel_x = tile_x * view_tile_size
        pixel_y = tile_y * view_tile_size

        # El rect se posiciona usando los píxeles calculados
        self.rect = self.image.get_rect(topleft=(pixel_x, pixel_y))

        # Asignamos cantidad aleatoria solo si es un recurso recolectable
        if self.tipo in ["comida", "madera", "piedra"]:
            self.cantidad = random.randint(1, 3)
        else:
            self.cantidad = 0 # Otros objetos (ej. 'acopio') no tienen cantidad

    def __str__(self):
        cantidad_str = f" ({self.cantidad})" if self.cantidad > 0 else ""
        return f"Objeto '{self.nombre}' ({self.tipo}{cantidad_str}) en tile ({self.tile_x}, {self.tile_y})"

