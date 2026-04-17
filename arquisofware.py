from abc import ABC, abstractmethod
from datetime import datetime
import uuid


# Pedido representa la unidad principal del flujo logístico.
class Pedido:
    def __init__(
        self,
        origen,
        punto_origen,
        destino,
        destinatario,
        contacto,
        canal_origen,
        tipo_entrega,
        ventana_tiempo,
        tipo_carga,
        peso_estimado,
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
        return f"Pedido [{self.id_pedido}] | Canal: {self.canal_origen} | Estado: {self.estado}"

    def validar(self):
        self.estado = "Validado"

    def dejar_pendiente_asignacion(self):
        self.estado = "Pendiente de asignación"

    def asignar(self, repartidor):
        self.repartidor_asignado = repartidor
        self.estado = "Asignado"

    def iniciar_despacho(self):
        self.estado = "En ruta"

    def marcar_entregado(self):
        self.estado = "Entregado"


# Cada canal crea pedidos con su propia fábrica.
class CreadorPedido(ABC):
    @abstractmethod
    def crear_pedido(
        self,
        origen,
        punto_origen,
        destino,
        destinatario,
        contacto,
        tipo_entrega,
        ventana_tiempo,
        tipo_carga,
        peso_estimado,
    ):
        pass


class CreadorWeb(CreadorPedido):
    def crear_pedido(
        self,
        origen,
        punto_origen,
        destino,
        destinatario,
        contacto,
        tipo_entrega,
        ventana_tiempo,
        tipo_carga,
        peso_estimado,
    ):
        return Pedido(
            origen,
            punto_origen,
            destino,
            destinatario,
            contacto,
            "Web",
            tipo_entrega,
            ventana_tiempo,
            tipo_carga,
            peso_estimado,
        )


class CreadorSucursal(CreadorPedido):
    def crear_pedido(
        self,
        origen,
        punto_origen,
        destino,
        destinatario,
        contacto,
        tipo_entrega,
        ventana_tiempo,
        tipo_carga,
        peso_estimado,
    ):
        return Pedido(
            origen,
            punto_origen,
            destino,
            destinatario,
            contacto,
            "Sucursal",
            tipo_entrega,
            ventana_tiempo,
            tipo_carga,
            peso_estimado,
        )


class RegistroPedidos:
    def __init__(self, creador):
        self.creador = creador

    def registrar(
        self,
        origen,
        punto_origen,
        destino,
        destinatario,
        contacto,
        tipo_entrega,
        ventana_tiempo,
        tipo_carga,
        peso_estimado,
    ):
        pedido = self.creador.crear_pedido(
            origen,
            punto_origen,
            destino,
            destinatario,
            contacto,
            tipo_entrega,
            ventana_tiempo,
            tipo_carga,
            peso_estimado,
        )
        print("Pedido registrado:", pedido)
        return pedido


# Las reglas se separan para no dejar toda la validación en una sola clase.
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
        return "Falta información válida de origen."


class ReglaDestino(ReglaValidacion):
    def es_valida(self, pedido):
        return (
            bool(pedido.destino.strip())
            and bool(pedido.destinatario.strip())
            and bool(pedido.contacto.strip())
        )

    def mensaje_error(self):
        return "Falta información válida de destino o contacto."


class ReglaEntrega(ReglaValidacion):
    def es_valida(self, pedido):
        tipos_validos = ["Normal", "Express", "Programada"]
        return (
            pedido.tipo_entrega in tipos_validos
            and (pedido.tipo_entrega != "Programada" or bool(pedido.ventana_tiempo))
        )

    def mensaje_error(self):
        return "La información de entrega no cumple las condiciones mínimas."


class ReglaLogistica(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.tipo_carga.strip()) and pedido.peso_estimado > 0

    def mensaje_error(self):
        return "La información logística es inválida."


class ValidadorPedido:
    def __init__(self):
        self.reglas = [
            ReglaOrigen(),
            ReglaDestino(),
            ReglaEntrega(),
            ReglaLogistica(),
        ]

    def validar(self, pedido):
        if pedido.estado != "Creado":
            return False, "El pedido no puede validarse desde ese estado."

        for regla in self.reglas:
            if not regla.es_valida(pedido):
                return False, regla.mensaje_error()

        pedido.validar()
        return True, "El pedido quedó validado."


# Repartidor representa un recurso operativo disponible para despacho.
class Repartidor:
    def __init__(self, codigo, capacidad_maxima):
        self.codigo = codigo
        self.capacidad_maxima = capacidad_maxima
        self.carga_actual = 0
        self.disponible = True

    def puede_tomar(self, pedido):
        return self.disponible and (self.carga_actual + pedido.peso_estimado) <= self.capacidad_maxima

    def tomar_pedido(self, pedido):
        self.carga_actual += pedido.peso_estimado

    def __str__(self):
        return f"Repartidor [{self.codigo}] | Carga {self.carga_actual}/{self.capacidad_maxima}"


# La estrategia permite cambiar la forma de elegir repartidor.
class EstrategiaAsignacion(ABC):
    @abstractmethod
    def seleccionar(self, pedido, repartidores):
        pass


class AsignacionPorCarga(EstrategiaAsignacion):
    def seleccionar(self, pedido, repartidores):
        candidatos = [r for r in repartidores if r.puede_tomar(pedido)]
        return min(candidatos, key=lambda r: r.carga_actual) if candidatos else None


class GestorDespacho:
    def __init__(self, estrategia):
        self.estrategia = estrategia

    def asignar_pedido(self, pedido, repartidores):
        if pedido.estado != "Validado":
            return False, "El pedido debe estar validado antes de asignarse."

        pedido.dejar_pendiente_asignacion()
        elegido = self.estrategia.seleccionar(pedido, repartidores)

        if elegido is None:
            return False, "No hay repartidores compatibles con el pedido."

        elegido.tomar_pedido(pedido)
        pedido.asignar(elegido)
        return True, f"Pedido asignado a {elegido.codigo}."


# Toda incidencia queda asociada a un pedido específico.
class Incidencia:
    def __init__(self, pedido, motivo):
        self.id_caso = str(uuid.uuid4())[:8]
        self.pedido = pedido
        self.motivo = motivo
        self.estado = "Abierta"
        self.resolucion = None

    def resolver(self, detalle):
        if not detalle.strip():
            raise ValueError("La incidencia necesita una resolución.")
        self.resolucion = detalle
        self.estado = "Resuelta"

    def __str__(self):
        return f"Incidencia [{self.id_caso}] | Pedido {self.pedido.id_pedido} | {self.estado}"


class ReclamoEntrega(Incidencia):
    pass


class FabricaIncidencias:
    @staticmethod
    def crear(tipo, pedido, motivo):
        if tipo.lower() == "reclamo":
            return ReclamoEntrega(pedido, motivo)
        raise ValueError("Tipo de incidencia no reconocido.")


class SoporteIncidencias:
    def registrar_reclamo(self, pedido, motivo):
        if pedido.estado != "Entregado":
            raise ValueError("El reclamo solo se registra sobre pedidos entregados.")
        caso = FabricaIncidencias.crear("reclamo", pedido, motivo)
        print("Caso de soporte creado:", caso)
        return caso


if __name__ == "__main__":
    print("\n--- Simulación de operación logística ---\n")

    # Caso 1: ingreso de pedido desde un canal
    registro_web = RegistroPedidos(CreadorWeb())
    pedido_base = registro_web.registrar(
        "Centro de Distribución Quilpué",
        "CD-014",
        "Av. Libertad 245, Viña del Mar",
        "Camila Rojas",
        "+56944556677",
        "Programada",
        "15:00 - 18:00",
        "Paquete frágil",
        4.2,
    )

    # Caso 2: validación del pedido
    revisor = ValidadorPedido()
    ok, mensaje = revisor.validar(pedido_base)
    print("Resultado validación:", mensaje)

    # Caso 3: asignación a un repartidor disponible
    flota = [
        Repartidor("VAL-01", 8.0),
        Repartidor("VAL-02", 12.0),
    ]
    for repartidor in flota:
        print("Repartidor disponible:", repartidor)

    despachador = GestorDespacho(AsignacionPorCarga())
    ok, mensaje = despachador.asignar_pedido(pedido_base, flota)
    print("Resultado asignación:", mensaje)

    if ok:
        pedido_base.iniciar_despacho()
        print("Estado actual del pedido:", pedido_base.estado)
        pedido_base.marcar_entregado()
        print("Estado final del pedido:", pedido_base.estado)

    # Caso 4: registro y cierre de incidencia
    soporte = SoporteIncidencias()
    caso_soporte = soporte.registrar_reclamo(
        pedido_base,
        "Cliente reporta deterioro visible en el embalaje al momento de recibir."
    )
    caso_soporte.resolver("Se revisó el caso y se aprobó compensación parcial.")
    print("Caso de soporte cerrado:", caso_soporte)

    print("\n--- Fin de la simulación ---\n")
