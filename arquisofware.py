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
        return Pedido(
            origen, punto_origen, destino, destinatario, contacto,
            "Marketplace", tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
        )


class CreadorSucursal(CreadorPedido):
    def crear(self, origen, punto_origen, destino, destinatario, contacto,
              tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado):
        return Pedido(
            origen, punto_origen, destino, destinatario, contacto,
            "Sucursal", tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
        )


class RegistroPedidos:
    def __init__(self, creador):
        self.creador = creador

    def ingresar(self, origen, punto_origen, destino, destinatario, contacto,
                 tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado):
        return self.creador.crear(
            origen, punto_origen, destino, destinatario, contacto,
            tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
        )


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
        return "No fue posible validar el origen del pedido."


class ReglaDestino(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.destino.strip()) and bool(pedido.destinatario.strip()) and bool(pedido.contacto.strip())

    def mensaje_error(self):
        return "Faltan datos de destino o contacto."


class ReglaEntrega(ReglaValidacion):
    def es_valida(self, pedido):
        tipos_validos = ["Normal", "Express", "Programada"]
        return pedido.tipo_entrega in tipos_validos and (
            pedido.tipo_entrega != "Programada" or bool(pedido.ventana_tiempo)
        )

    def mensaje_error(self):
        return "La modalidad de entrega no es válida."


class ReglaLogistica(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.tipo_carga.strip()) and pedido.peso_estimado > 0

    def mensaje_error(self):
        return "La información logística no cumple las condiciones mínimas."


class ValidadorPedido:
    def __init__(self):
        self.reglas = [
            ReglaOrigen(),
            ReglaDestino(),
            ReglaEntrega(),
            ReglaLogistica()
        ]

    def validar(self, pedido):
        if pedido.estado != "Creado":
            return False, "El pedido no puede validarse desde su estado actual."

        for regla in self.reglas:
            if not regla.es_valida(pedido):
                return False, regla.mensaje_error()

        pedido.validar()
        return True, "Pedido validado con éxito."


class Repartidor:
    def __init__(self, codigo, capacidad):
        self.codigo = codigo
        self.capacidad = capacidad
        self.carga_actual = 0
        self.disponible = True

    def puede_tomar(self, pedido):
        return self.disponible and (self.carga_actual + pedido.peso_estimado) <= self.capacidad

    def cargar(self, pedido):
        self.carga_actual += pedido.peso_estimado


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
            return False, "No se encontró capacidad disponible para este pedido."

        elegido.cargar(pedido)
        pedido.asignar(elegido)
        return True, f"Pedido asignado a {elegido.codigo}."


class Incidencia:
    def __init__(self, pedido, motivo):
        self.pedido = pedido
        self.motivo = motivo
        self.estado = "Abierta"
        self.resolucion = None

    def pasar_a_revision(self):
        self.estado = "En análisis"

    def cerrar(self, detalle):
        if not detalle.strip():
            raise ValueError("La incidencia necesita una resolución.")
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
    print("\n" + "=" * 56)
    print("--- FLUJO DE OPERACIÓN LOGÍSTICA ---")
    print("=" * 56)

    print("\n[CAPTURA] Registro y validación del pedido...")

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
    print(f"-> Pedido registrado correctamente. Estado: {pedido.estado}")

    validador = ValidadorPedido()
    ok, mensaje = validador.validar(pedido)
    if not ok:
        print(f"-> Validación rechazada: {mensaje}")
        return
    print(f"-> {mensaje} Estado: {pedido.estado}")

    print("\n[OPERACIÓN] Asignación y despacho...")

    flota = [
        Repartidor("VINA-01", 8.0),
        Repartidor("VINA-02", 12.0)
    ]
    print(f"-> Repartidor {flota[0].codigo} disponible con capacidad {flota[0].capacidad} kg.")
    print(f"-> Repartidor {flota[1].codigo} disponible con capacidad {flota[1].capacidad} kg.")

    despacho = ServicioDespacho(AsignacionMenorCarga())
    ok, mensaje = despacho.asignar(pedido, flota)
    if not ok:
        print(f"-> No fue posible asignar el pedido: {mensaje}")
        return

    print(f"-> {mensaje}")
    print(f"-> Estado después de asignación: {pedido.estado}")

    pedido.salir_a_reparto()
    print(f"-> El pedido salió a reparto. Estado: {pedido.estado}")

    pedido.entregar()
    print(f"-> Entrega confirmada. Estado final: {pedido.estado}")

    print("\n[SOPORTE] Gestión de incidencia posterior a la entrega...")

    soporte = Soporte()
    caso = soporte.registrar_reclamo(
        pedido,
        "Cliente informa que recibió el paquete roto."
    )
    print(f"-> Incidencia registrada. Motivo: {caso.motivo}")
    print(f"-> Estado inicial de la incidencia: {caso.estado}")

    caso.pasar_a_revision()
    print(f"-> La incidencia pasó a revisión. Estado: {caso.estado}")

    solucion = "Se recompensó al cliente con un beneficio comercial por el inconveniente."
    caso.cerrar(solucion)
    print(f"-> Resolución aplicada: {solucion}")
    print(f"-> Estado final de la incidencia: {caso.estado}")

    print("\n" + "=" * 56)
    print("--- FIN DE LA SIMULACIÓN ---")
    print("=" * 56 + "\n")


if __name__ == "__main__":
    ejecutar()
