from abc import ABC, abstractmethod
from datetime import datetime
import uuid


# =========================
# 1. PEDIDO
# =========================
class Pedido:
    def __init__(
        self, origen, punto_origen, destino, destinatario, contacto,
        canal_origen, tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
    ):
        self.id_pedido = str(uuid.uuid4())[:8]
        self.origen = origen
        self.punto_origen = punto_origen
        self.destino = destino
        self.destinatario = destinatario
        self.contacto = contacto
        self.canal_origen = canal_origen
        self.tipo_entrega = tipo_entrega
        self.ventana_tiempo = ventana_tiempo
        self.tipo_carga = tipo_carga
        self.peso_estimado = peso_estimado
        self.estado = "Creado"
        self.fecha_creacion = datetime.now()
        self.repartidor_asignado = None

    def __str__(self):
        return f"Pedido [{self.id_pedido}] | {self.canal_origen} | {self.estado}"

    def validar(self):
        self.estado = "Validado"

    def marcar_pendiente_asignacion(self):
        self.estado = "Pendiente de asignación"

    def marcar_como_asignado(self, repartidor):
        self.repartidor_asignado = repartidor
        self.estado = "Asignado"

    def iniciar_ruta(self):
        self.estado = "En ruta"

    def marcar_entregado(self):
        self.estado = "Entregado"


# =========================
# 2. FACTORY METHOD
# =========================
class CreadorPedido(ABC):
    @abstractmethod
    def crear_pedido(
        self, origen, punto_origen, destino, destinatario, contacto,
        tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
    ):
        pass


class CreadorEcommerce(CreadorPedido):
    def crear_pedido(
        self, origen, punto_origen, destino, destinatario, contacto,
        tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
    ):
        return Pedido(
            origen, punto_origen, destino, destinatario, contacto,
            "E-commerce", tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
        )


class CreadorCanalPropio(CreadorPedido):
    def crear_pedido(
        self, origen, punto_origen, destino, destinatario, contacto,
        tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
    ):
        return Pedido(
            origen, punto_origen, destino, destinatario, contacto,
            "Canal Propio", tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
        )


class ServicioRegistroPedidos:
    def __init__(self, fabrica):
        self.fabrica = fabrica

    def registrar_nuevo_pedido(
        self, origen, punto_origen, destino, destinatario, contacto,
        tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
    ):
        pedido = self.fabrica.crear_pedido(
            origen, punto_origen, destino, destinatario, contacto,
            tipo_entrega, ventana_tiempo, tipo_carga, peso_estimado
        )
        print(f"✅ Pedido creado: {pedido}")
        return pedido


# =========================
# 3. SPECIFICATION
# =========================
class ReglaValidacion(ABC):
    @abstractmethod
    def es_valida(self, pedido):
        pass

    @abstractmethod
    def mensaje_error(self):
        pass


class ValidacionOrigen(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.origen.strip()) and bool(pedido.punto_origen.strip())

    def mensaje_error(self):
        return "Origen inválido."


class ValidacionDestino(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.destino.strip()) and bool(pedido.destinatario.strip()) and bool(pedido.contacto.strip())

    def mensaje_error(self):
        return "Destino, destinatario o contacto inválido."


class ValidacionEntrega(ReglaValidacion):
    def es_valida(self, pedido):
        if pedido.tipo_entrega not in ["Normal", "Express", "Programada"]:
            return False
        if pedido.tipo_entrega == "Programada" and not pedido.ventana_tiempo:
            return False
        return True

    def mensaje_error(self):
        return "Información de entrega inválida."


class ValidacionLogistica(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.tipo_carga.strip()) and pedido.peso_estimado > 0

    def mensaje_error(self):
        return "Información logística inválida."


class ValidadorPedido:
    def __init__(self):
        self.reglas = [
            ValidacionOrigen(),
            ValidacionDestino(),
            ValidacionEntrega(),
            ValidacionLogistica()
        ]

    def validar(self, pedido):
        if pedido.estado != "Creado":
            return False, "El pedido no puede validarse desde ese estado."

        for regla in self.reglas:
            if not regla.es_valida(pedido):
                return False, regla.mensaje_error()

        pedido.validar()
        return True, "Pedido validado correctamente."


# =========================
# 4. REPARTIDOR
# =========================
class Repartidor:
    def __init__(self, id_repartidor, capacidad_maxima):
        self.id_repartidor = id_repartidor
        self.capacidad_maxima = capacidad_maxima
        self.carga_actual = 0
        self.disponible = True

    def puede_recibir_pedido(self, peso_pedido):
        return self.disponible and (self.carga_actual + peso_pedido) <= self.capacidad_maxima

    def acoplar_pedido(self, pedido):
        self.carga_actual += pedido.peso_estimado

    def __str__(self):
        return f"Repartidor [{self.id_repartidor}] | Carga {self.carga_actual}/{self.capacidad_maxima}"


# =========================
# 5. STRATEGY
# =========================
class EstrategiaAsignacion(ABC):
    @abstractmethod
    def asignar(self, pedido, repartidores):
        pass


class AsignarPorMenorCarga(EstrategiaAsignacion):
    def asignar(self, pedido, repartidores):
        candidatos = [r for r in repartidores if r.puede_recibir_pedido(pedido.peso_estimado)]
        return min(candidatos, key=lambda r: r.carga_actual) if candidatos else None


class AsignacionService:
    def __init__(self, estrategia):
        self.estrategia = estrategia

    def ejecutar_asignacion(self, pedido, repartidores):
        if pedido.estado != "Validado":
            return False, "El pedido debe estar Validado antes de ser asignado."

        pedido.marcar_pendiente_asignacion()
        repartidor = self.estrategia.asignar(pedido, repartidores)

        if not repartidor:
            return False, "No hay repartidor disponible."

        repartidor.acoplar_pedido(pedido)
        pedido.marcar_como_asignado(repartidor)
        return True, f"Pedido asignado a {repartidor.id_repartidor}."


# =========================
# 6. INCIDENCIAS
# =========================
class Incidencia:
    def __init__(self, pedido, motivo):
        self.id_caso = str(uuid.uuid4())[:8]
        self.pedido = pedido
        self.motivo = motivo
        self.estado = "Abierta"
        self.resolucion = None

    def resolver(self, detalle_resolucion):
        if not detalle_resolucion.strip():
            raise ValueError("Una incidencia no puede cerrarse sin resolución.")
        self.resolucion = detalle_resolucion
        self.estado = "Resuelta"

    def __str__(self):
        return f"Incidencia [{self.id_caso}] | Pedido {self.pedido.id_pedido} | {self.estado}"


class IncidenciaReclamo(Incidencia):
    pass


class IncidenciaFactory:
    @staticmethod
    def crear_incidencia(tipo, pedido, motivo):
        if tipo.lower() == "reclamo":
            return IncidenciaReclamo(pedido, motivo)
        raise ValueError("Tipo de incidencia no soportado.")


class GestorIncidencias:
    def registrar_reclamo(self, pedido, motivo):
        if pedido.estado != "Entregado":
            raise ValueError("Solo un pedido entregado puede generar reclamo.")
        incidencia = IncidenciaFactory.crear_incidencia("reclamo", pedido, motivo)
        print(f"⚠️ Incidencia registrada: {incidencia}")
        return incidencia


# =========================
# 7. SIMULACIÓN
# =========================
if __name__ == "__main__":
    print("\n=== SIMULACIÓN LOGÍSTICA ===\n")

    # CU1: Crear pedido
    servicio_eco = ServicioRegistroPedidos(CreadorEcommerce())
    pedido1 = servicio_eco.registrar_nuevo_pedido(
        "Bodega Central Pudahuel", "BOD-001", "Casa Cliente - Santiago Centro",
        "Juan Pérez", "+56912345678", "Express", None, "Caja mediana", 5.0
    )

    # CU2: Validar pedido
    validador = ValidadorPedido()
    ok, msg = validador.validar(pedido1)
    print("✅" if ok else "❌", msg)

    # CU3: Asignar repartidor
    repartidores = [Repartidor("REP-001", 10.0), Repartidor("REP-002", 3.0)]
    for r in repartidores:
        print("Registrado:", r)

    servicio_asignacion = AsignacionService(AsignarPorMenorCarga())
    ok, msg = servicio_asignacion.ejecutar_asignacion(pedido1, repartidores)
    print("✅" if ok else "❌", msg)

    if ok:
        pedido1.iniciar_ruta()
        print(f"➡️ Pedido {pedido1.id_pedido} pasó a estado: {pedido1.estado}")
        pedido1.marcar_entregado()
        print(f"📦 Pedido {pedido1.id_pedido} pasó a estado: {pedido1.estado}")

    # CU4: Gestionar incidencia
    gestor = GestorIncidencias()
    incidencia = gestor.registrar_reclamo(
        pedido1,
        "El cliente indica que recibió el paquete con daño exterior."
    )
    incidencia.resolver("Se revisó el caso y se generó compensación al cliente.")
    print(f"✅ Incidencia resuelta: {incidencia}")

    print("\n=== FIN DE LA SIMULACIÓN ===\n")
