from abc import ABC, abstractmethod
from datetime import datetime
import uuid

# ==========================================
# 1. ENTIDAD DEL DOMINIO
# ==========================================
class Pedido:
    """
    Entidad principal que representa una solicitud de logística.
    """
    def __init__(self, origen, destino, canal):
        self.id_unico = str(uuid.uuid4())[:8]  # ID simulado
        self.origen = origen
        self.destino = destino
        self.canal = canal
        # Regla de negocio: El pedido nace en estado "Creado"
        self.estado = "Creado"
        self.fecha_creacion = datetime.now()

    def __str__(self):
        return f"Pedido [{self.id_unico}] | Canal: {self.canal} | Estado: {self.estado} | Ruta: {self.origen} -> {self.destino}"


# ==========================================
# 2. PATRÓN DE DISEÑO: FACTORY METHOD
# ==========================================
class CreadorPedido(ABC):
    """
    Interfaz abstracta del Factory Method.
    Deja que las subclases decidan cómo instanciar el pedido.
    """
    @abstractmethod
    def crear_pedido(self, origen, destino) -> Pedido:
        pass


class CreadorEcommerce(CreadorPedido):
    """Fábrica concreta para pedidos que vienen de plataformas E-commerce."""
    def crear_pedido(self, origen, destino) -> Pedido:
        return Pedido(origen, destino, canal="E-commerce")


class CreadorCanalPropio(CreadorPedido):
    """Fábrica concreta para pedidos que vienen de tiendas o canales propios."""
    def crear_pedido(self, origen, destino) -> Pedido:
        return Pedido(origen, destino, canal="Canal Propio")


# ==========================================
# 3. PRINCIPIO SOLID: SRP (Single Responsibility)
# ==========================================
class ServicioRegistroPedidos:
    """
    Clase con una única responsabilidad: orquestar el registro inicial de un pedido.
    No valida, no asigna, solo registra la creación usando la fábrica proporcionada.
    """
    def __init__(self, fabrica_creadora: CreadorPedido):
        self.fabrica = fabrica_creadora

    def registrar_nuevo_pedido(self, origen, destino) -> Pedido:
        nuevo_pedido = self.fabrica.crear_pedido(origen, destino)
        print(f"✅ Nuevo registro exitoso: {nuevo_pedido}")
        return nuevo_pedido


# ==========================================
# 4. CASO DE USO 2: VALIDACIÓN DE PEDIDO
#    PATRÓN: Specification
# ==========================================
class ReglaValidacion(ABC):
    """
    Interfaz base para las reglas de validación.
    """
    @abstractmethod
    def es_valida(self, pedido: Pedido) -> bool:
        pass

    @abstractmethod
    def mensaje_error(self) -> str:
        pass


class ValidacionOrigen(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        return isinstance(pedido.origen, str) and len(pedido.origen.strip()) > 5

    def mensaje_error(self) -> str:
        return "El origen no cumple con las condiciones mínimas de validación."


class ValidacionDestino(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        return isinstance(pedido.destino, str) and len(pedido.destino.strip()) > 5

    def mensaje_error(self) -> str:
        return "El destino no cumple con las condiciones mínimas de validación."


class ValidacionCanal(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        return pedido.canal in ["E-commerce", "Canal Propio"]

    def mensaje_error(self) -> str:
        return "El canal de origen no es válido."


class ValidacionIdentificacion(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        return bool(pedido.id_unico)

    def mensaje_error(self) -> str:
        return "El pedido no cuenta con identificación válida."


class ValidadorPedido:
    """
    Servicio encargado de aplicar reglas del dominio
    para decidir si un pedido puede avanzar a estado Validado.
    """
    def __init__(self):
        self.reglas = [
            ValidacionOrigen(),
            ValidacionDestino(),
            ValidacionCanal(),
            ValidacionIdentificacion()
        ]

    def validar(self, pedido: Pedido):
        if pedido.estado != "Creado":
            return False, f"El pedido no puede validarse desde el estado {pedido.estado}."

        for regla in self.reglas:
            if not regla.es_valida(pedido):
                return False, regla.mensaje_error()

        pedido.estado = "Validado"
        return True, "Pedido validado correctamente."


# ==========================================
# 5. SIMULACIÓN DE LOS CASOS DE USO 1 Y 2
# ==========================================
if __name__ == "__main__":
    print("--- Sistema de Logística: Registro y Validación de Pedidos ---\n")

    # Caso de Uso 1: registro desde e-commerce
    servicio_eco = ServicioRegistroPedidos(CreadorEcommerce())
    pedido1 = servicio_eco.registrar_nuevo_pedido(
        origen="Bodega Central Pudahuel",
        destino="Casa Cliente - Santiago Centro"
    )

    # Caso de Uso 2: validación del pedido
    validador = ValidadorPedido()
    resultado, mensaje = validador.validar(pedido1)

    if resultado:
        print(f"✅ {mensaje}")
    else:
        print(f"❌ {mensaje}")

    print(f"Estado final del pedido: {pedido1.estado}")
