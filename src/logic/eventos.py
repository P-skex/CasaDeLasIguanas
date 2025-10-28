import random
import pygame

class EventoManager:
    """Gestiona la ocurrencia y el efecto de eventos aleatorios."""
    def __init__(self, mundo, planificador):
        self.mundo = mundo
        self.planificador = planificador
        self.eventos_activos = []
        
        # --- ¡CAMBIO! Tiempo aumentado a 2-3 minutos ---
        self.tiempo_para_proximo_evento = random.randint(120*60, 180*60)

    def update(self):
        """Actualiza el temporizador y activa nuevos eventos."""
        # No actualizamos si ya hay un evento peligroso activo
        if self.mundo.evento_peligroso_activo is not None:
            return

        self.tiempo_para_proximo_evento -= 1
        if self.tiempo_para_proximo_evento <= 0:
            self.activar_evento_aleatorio()
            # Reinicia el temporizador
            self.tiempo_para_proximo_evento = random.randint(120*60, 180*60)

    def activar_evento_aleatorio(self):
        """Selecciona y activa un evento al azar."""
        # --- ¡CAMBIO AQUÍ! Elegimos entre 3 eventos ---
        eventos_posibles = [Plaga, LluviaAcida, SueloEsLava]
        evento_elegido = random.choice(eventos_posibles)
        # ---------------------------------------------
        
        evento = evento_elegido(self.mundo)
        evento.activar(self.planificador)
        # El log se maneja en el mundo o en el evento mismo

class Evento:
    """Clase base para todos los eventos."""
    def __init__(self, mundo):
        self.mundo = mundo
        self.nombre = "Evento Genérico"

    def activar(self, planificador):
        raise NotImplementedError

class Plaga(Evento):
    """Enferma a un número aleatorio de colonos sanos."""
    def __init__(self, mundo):
        super().__init__(mundo)
        self.nombre = "Plaga de Enfermedad"

    def activar(self, planificador):
        iguanas_sanas = [c for c in self.mundo.colonos if not c.es_enemigo and not c.esta_enfermo and c.vida > 0]
        if not iguanas_sanas:
            self.mundo.log_event("Una plaga pasó, pero no había nadie sano a quien infectar.")
            return

        max_a_enfermar = max(1, len(iguanas_sanas) // 2)
        num_a_enfermar = random.randint(1, max_a_enfermar)
        victimas = random.sample(iguanas_sanas, num_a_enfermar)
        nombres_victimas = []
        for v in victimas:
            v.enfermar()
            nombres_victimas.append(v.nombre)
        
        self.mundo.log_event(f"¡Una plaga ha enfermado a: {', '.join(nombres_victimas)}!")

# --- ¡NUEVO! Evento de Lluvia Ácida ---
class LluviaAcida(Evento):
    """Inicia el evento de lluvia ácida en el mundo."""
    def __init__(self, mundo):
        super().__init__(mundo)
        self.nombre = "Lluvia Ácida"

    def activar(self, planificador):
        self.mundo._iniciar_evento_peligroso("lluvia")
# ------------------------------------

# --- ¡NUEVO! Evento de Suelo es Lava ---
class SueloEsLava(Evento):
    """Inicia el evento 'El Suelo es Lava' en el mundo."""
    def __init__(self, mundo):
        super().__init__(mundo)
        self.nombre = "El Suelo es Lava"

    def activar(self, planificador):
        self.mundo._iniciar_evento_peligroso("lava")
# -------------------------------------

