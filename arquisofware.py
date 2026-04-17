from abc import ABC, abstractmethod
from datetime import datetime
import uuid

class Pedido:
    def __init__(self, origen, punto_origen, destino, destinatario, contacto,
                 canal, tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado):
        self.id_pedido = str(uuid.uuid4())[:8]
        self.origen = origen
        self.punto_origen = punto_origen
        self.destino = destino
        self.destinatario = destinatario
        self.contacto = contacto
        self.canal = canal
        self.tipo_entrega = tipo_entrega
        self.ventana_tiempo = ventana_tiempo
        self.tipo_carga = tipo_carga
        self.peso_estimado = peso_estimado
        self.estado = "Creado"
        self.fecha_creacion = datetime.now()
        self.repartidor = None

    def validar(self):
        self.estado = "Validado"

    def dejar_pendiente(self):
        self.estado = "Pendiente de asignación"

    def asignar(self, repartidor):
        self.repartidor = repartidor
        self.estado = "Asignado"

    def salir_a_reparto(self):
        self.estado = "En ruta"

    def entregar(self):
        self.estado = "Entregado"


class CreadorPedido(ABC):
    @abstractmethod
    def crear(self, origen, punto_origen, destino, destinatario, contacto,
              tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado):
        pass


class CreadorMarketplace(CreadorPedido):
    def crear(self, origen, punto_origen, destino, destinatario, contacto,
              tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado):
        return Pedido(origen, punto_origen, destino, destinatario, contacto,
                      "Marketplace", tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado)


class CreadorSucursal(CreadorPedido):
    def crear(self, origen, punto_origen, destino, destinatario, contacto,
              tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado):
        return Pedido(origen, punto_origen, destino, destinatario, contacto,
                      "Sucursal", tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado)


class RegistroPedidos:
    def __init__(self, creador):
        self.creador = creador

    def ingresar(self, origen, punto_origen, destino, destinatario, contacto,
                 tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado):
        return self.creador.crear(origen, punto_origen, destino, destinatario, contacto,
                                  tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado)


class ReglaValidacion(ABC):
    @abstractmethod
    def es_valida(self, pedido):
        pass

    @abstractmethod
    def mensaje_error(self):
        pass


class ReglaOrigen(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.origen.strip()) and bool(pedido.punto_origen.strip())

    def mensaje_error(self):
        return "No se pudo validar el origen."


class ReglaDestino(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.destino.strip()) and bool(pedido.destinatario.strip()) and bool(pedido.contacto.strip())

    def mensaje_error(self):
        return "El destino o el contacto están incompletos."


class ReglaEntrega(ReglaValidacion):
    def es_valida(self, pedido):
        tipos = ["Normal", "Express", "Programada"]
        return pedido.tipo_entrega in tipos and (pedido.tipo_entrega != "Programada" or bool(pedido.ventana_tiempo))

    def mensaje_error(self):
        return "La modalidad de entrega no es válida."


class ReglaLogistica(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.tipo_carga.strip()) and pedido.peso_estimado > 0

    def mensaje_error(self):
        return "La información logística es inválida."


class ValidadorPedido:
    def __init__(self):
        self.reglas = [ReglaOrigen(), ReglaDestino(), ReglaEntrega(), ReglaLogistica()]

    def validar(self, pedido):
        if pedido.estado != "Creado":
            return False, "El pedido no puede validarse desde su estado actual."
        for regla in self.reglas:
            if not regla.es_valida(pedido):
                return False, regla.mensaje_error()
        pedido.validar()
        return True, "El pedido fue validado correctamente."


class Repartidor:
    def __init__(self, codigo, capacidad):
        self.codigo = codigo
        self.capacidad = capacidad
        self.carga_actual = 0
        self.disponible = True

    def puede_tomar(self, pedido):
        return self.disponible and (self.carga_actual + pedido.peso_estimado) <= self.capacidad


class EstrategiaAsignacion(ABC):
    @abstractmethod
    def seleccionar(self, pedido, repartidores):
        pass


class AsignacionMenorCarga(EstrategiaAsignacion):
    def seleccionar(self, pedido, repartidores):
        disponibles = [r for r in repartidores if r.puede_tomar(pedido)]
        return min(disponibles, key=lambda r: r.carga_actual) if disponibles else None


class ServicioDespacho:
    def __init__(self, estrategia):
        self.estrategia = estrategia

    def asignar(self, pedido, repartidores):
        if pedido.estado != "Validado":
            return False, "El pedido debe estar validado antes de asignarse."
        pedido.dejar_pendiente()
        elegido = self.estrategia.seleccionar(pedido, repartidores)
        if not elegido:
            return False, "No hay capacidad disponible para este pedido."
        elegido.carga_actual += pedido.peso_estimado
        pedido.asignar(elegido)
        return True, f"Pedido asignado a {elegido.codigo}."


class Incidencia:
    def __init__(self, pedido, motivo):
        self.id_caso = str(uuid.uuid4())[:8]
        self.pedido = pedido
        self.motivo = motivo
        self.estado = "Abierta"
        self.resolucion = None

    def pasar_a_revision(self):
        self.estado = "En análisis"

    def cerrar(self, detalle):
        if not detalle.strip():
            raise ValueError("La incidencia requiere una resolución.")
        self.resolucion = detalle
        self.estado = "Resuelta"


class ReclamoPostEntrega(Incidencia):
    pass


class FabricaIncidencias:
    @staticmethod
    def crear(tipo, pedido, motivo):
        if tipo.lower() == "reclamo":
            return ReclamoPostEntrega(pedido, motivo)
        raise ValueError("Tipo de incidencia no disponible.")


class Soporte:
    def registrar_reclamo(self, pedido, motivo):
        if pedido.estado != "Entregado":
            raise ValueError("Solo se aceptan reclamos sobre pedidos entregados.")
        return FabricaIncidencias.crear("reclamo", pedido, motivo)


def ejecutar():
    print("\n--- Simulación de operación logística ---\n")

    print("[CU1] Registro de pedido")
    registro = RegistroPedidos(CreadorMarketplace())
    pedido = registro.ingresar(
        "Centro Logístico Quilpué",
        "QLP-014",
        "Av. Libertad 245, Viña del Mar",
        "Camila Rojas",
        "+56944556677",
        "Programada",
        "15:00 - 18:00",
        "Paquete frágil",
        4.2
    )
    print(f"Pedido registrado desde {pedido.canal}. Estado: {pedido.estado}")

    print("\n[CU2] Validación")
    validador = ValidadorPedido()
    ok, mensaje = validador.validar(pedido)
    print("Resultado:", mensaje)
    if not ok:
        return

    print("\n[CU3] Asignación")
    flota = [Repartidor("VINA-01", 8.0), Repartidor("VINA-02", 12.0)]
    print("Repartidores disponibles: VINA-01 y VINA-02")
    despacho = ServicioDespacho(AsignacionMenorCarga())
    ok, mensaje = despacho.asignar(pedido, flota)
    print("Resultado:", mensaje)
    if not ok:
        return
    pedido.salir_a_reparto()
    print("Estado actual del pedido:", pedido.estado)
    pedido.entregar()
    print("Estado final del pedido:", pedido.estado)

    print("\n[CU4] Incidencia")
    soporte = Soporte()
    caso = soporte.registrar_reclamo(
        pedido,
        "Cliente reporta paquete roto al momento de la entrega."
    )
    print("Incidencia registrada. Estado:", caso.estado)
    caso.pasar_a_revision()
    print("Incidencia en revisión. Estado:", caso.estado)
    caso.cerrar("Se aprueba beneficio comercial para compensar el problema.")
    print("Incidencia resuelta. Estado:", caso.estado)

    print("\n--- Fin de la simulación ---\n")


if __name__ == "__main__":
    ejecutar()
