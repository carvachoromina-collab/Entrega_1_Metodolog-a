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
        self.id_unico = str(uuid.uuid4())[:8] # ID simulado
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
        # Aquí se podría inyectar lógica específica de e-commerce en el futuro
        return Pedido(origen, destino, canal="E-commerce")

class CreadorCanalPropio(CreadorPedido):
    """Fábrica concreta para pedidos que vienen de tiendas o canales propios."""
    def crear_pedido(self, origen, destino) -> Pedido:
        # Aquí se podría inyectar lógica específica de sucursales en el futuro
        return Pedido(origen, destino, canal="Canal Propio")

# ==========================================
# 3. PRINCIPIO SOLID: SRP (Single Responsibility)
# ==========================================
class ServicioRegistroPedidos:
    """
    Clase con una única responsabilidad: Orquestar el registro inicial de un pedido.
    No valida, no asigna, solo registra la creación usando la fábrica proporcionada.
    """
    def __init__(self, fabrica_creadora: CreadorPedido):
        self.fabrica = fabrica_creadora

    def registrar_nuevo_pedido(self, origen, destino) -> Pedido:
        # Delega la creación al factory correspondiente
        nuevo_pedido = self.fabrica.crear_pedido(origen, destino)
        print(f"✅ Nuevo registro exitoso: {nuevo_pedido}")
        return nuevo_pedido

# ==========================================
# SIMULACIÓN DEL CASO DE USO 1
# ==========================================
if __name__ == "__main__":
    print("--- Sistema de Logística: Ingreso de Pedidos ---\n")

    # 1. Llega un pedido desde E-commerce
    servicio_eco = ServicioRegistroPedidos(CreadorEcommerce())
    pedido1 = servicio_eco.registrar_nuevo_pedido(
        origen="Bodega Central Pudahuel", 
        destino="Casa Cliente - Santiago Centro"
    )

    # 2. Llega un pedido desde un Canal Propio (Tienda)
    servicio_propio = ServicioRegistroPedidos(CreadorCanalPropio())
    pedido2 = servicio_propio.registrar_nuevo_pedido(
        origen="Sucursal Viña del Mar", 
        destino="Oficina Cliente - Valparaíso"
    )