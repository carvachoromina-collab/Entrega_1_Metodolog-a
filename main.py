from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import uuid
from typing import List, Optional


# =========================================================
# 1. ENTIDAD PRINCIPAL DEL DOMINIO
# =========================================================
class Pedido:
    """
    Entidad central del dominio logístico.
    Representa una solicitud de entrega y su ciclo de vida.
    """

    def __init__(
        self,
        origen: str,
        punto_origen: str,
        destino: str,
        destinatario: str,
        contacto: str,
        canal_origen: str,
        tipo_entrega: str,
        ventana_tiempo: Optional[str],
        tipo_carga: str,
        peso_estimado: float,
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
        self.repartidor_asignado: Optional[Repartidor] = None

    def __str__(self) -> str:
        return (
            f"Pedido [{self.id_pedido}] | Canal: {self.canal_origen} | "
            f"Estado: {self.estado} | {self.origen} -> {self.destino}"
        )

    def validar(self) -> None:
        if self.estado != "Creado":
            raise ValueError(
                f"El pedido no puede validarse desde el estado '{self.estado}'."
            )
        self.estado = "Validado"

    def marcar_como_asignado(self, repartidor: "Repartidor") -> None:
        if self.estado != "Validado":
            raise ValueError("El pedido debe estar Validado antes de ser asignado.")
        self.repartidor_asignado = repartidor
        self.estado = "Asignado"

    def iniciar_ruta(self) -> None:
        if self.estado != "Asignado":
            raise ValueError("El pedido debe estar Asignado antes de pasar a En ruta.")
        self.estado = "En ruta"

    def marcar_entregado(self) -> None:
        if self.estado != "En ruta":
            raise ValueError(
                "El pedido debe estar En ruta antes de marcarse como Entregado."
            )
        self.estado = "Entregado"

    def cancelar(self) -> None:
        if self.estado == "Entregado":
            raise ValueError("Un pedido entregado no puede cancelarse.")
        self.estado = "Cancelado"


# =========================================================
# 2. FACTORY METHOD: CREACIÓN DE PEDIDOS
# =========================================================
class CreadorPedido(ABC):
    @abstractmethod
    def crear_pedido(
        self,
        origen: str,
        punto_origen: str,
        destino: str,
        destinatario: str,
        contacto: str,
        tipo_entrega: str,
        ventana_tiempo: Optional[str],
        tipo_carga: str,
        peso_estimado: float,
    ) -> Pedido:
        pass


class CreadorEcommerce(CreadorPedido):
    def crear_pedido(
        self,
        origen: str,
        punto_origen: str,
        destino: str,
        destinatario: str,
        contacto: str,
        tipo_entrega: str,
        ventana_tiempo: Optional[str],
        tipo_carga: str,
        peso_estimado: float,
    ) -> Pedido:
        return Pedido(
            origen=origen,
            punto_origen=punto_origen,
            destino=destino,
            destinatario=destinatario,
            contacto=contacto,
            canal_origen="E-commerce",
            tipo_entrega=tipo_entrega,
            ventana_tiempo=ventana_tiempo,
            tipo_carga=tipo_carga,
            peso_estimado=peso_estimado,
        )


class CreadorCanalPropio(CreadorPedido):
    def crear_pedido(
        self,
        origen: str,
        punto_origen: str,
        destino: str,
        destinatario: str,
        contacto: str,
        tipo_entrega: str,
        ventana_tiempo: Optional[str],
        tipo_carga: str,
        peso_estimado: float,
    ) -> Pedido:
        return Pedido(
            origen=origen,
            punto_origen=punto_origen,
            destino=destino,
            destinatario=destinatario,
            contacto=contacto,
            canal_origen="Canal Propio",
            tipo_entrega=tipo_entrega,
            ventana_tiempo=ventana_tiempo,
            tipo_carga=tipo_carga,
            peso_estimado=peso_estimado,
        )


class ServicioRegistroPedidos:
    """
    Orquesta el registro inicial del pedido usando la fábrica adecuada.
    """

    def __init__(self, fabrica_creadora: CreadorPedido):
        self.fabrica = fabrica_creadora

    def registrar_nuevo_pedido(
        self,
        origen: str,
        punto_origen: str,
        destino: str,
        destinatario: str,
        contacto: str,
        tipo_entrega: str,
        ventana_tiempo: Optional[str],
        tipo_carga: str,
        peso_estimado: float,
    ) -> Pedido:
        pedido = self.fabrica.crear_pedido(
            origen=origen,
            punto_origen=punto_origen,
            destino=destino,
            destinatario=destinatario,
            contacto=contacto,
            tipo_entrega=tipo_entrega,
            ventana_tiempo=ventana_tiempo,
            tipo_carga=tipo_carga,
            peso_estimado=peso_estimado,
        )
        print(f"✅ Pedido creado correctamente: {pedido}")
        return pedido


# =========================================================
# 3. SPECIFICATION: VALIDACIÓN DE PEDIDOS
# =========================================================
class ReglaValidacion(ABC):
    @abstractmethod
    def es_valida(self, pedido: Pedido) -> bool:
        pass

    @abstractmethod
    def mensaje_error(self) -> str:
        pass


class ValidacionOrigen(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        return (
            isinstance(pedido.origen, str)
            and len(pedido.origen.strip()) > 5
            and isinstance(pedido.punto_origen, str)
            and len(pedido.punto_origen.strip()) > 0
        )

    def mensaje_error(self) -> str:
        return "Falta información válida de origen o identificación del punto de origen."


class ValidacionDestino(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        return (
            isinstance(pedido.destino, str)
            and len(pedido.destino.strip()) > 5
            and isinstance(pedido.destinatario, str)
            and len(pedido.destinatario.strip()) > 0
            and isinstance(pedido.contacto, str)
            and len(pedido.contacto.strip()) > 0
        )

    def mensaje_error(self) -> str:
        return "Falta información válida de destino, destinatario o contacto."


class ValidacionEntrega(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        if pedido.tipo_entrega not in ["Normal", "Express", "Programada"]:
            return False
        if pedido.tipo_entrega == "Programada" and not pedido.ventana_tiempo:
            return False
        return True

    def mensaje_error(self) -> str:
        return "La información de entrega es inválida."


class ValidacionLogistica(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        return (
            isinstance(pedido.tipo_carga, str)
            and len(pedido.tipo_carga.strip()) > 0
            and pedido.peso_estimado > 0
        )

    def mensaje_error(self) -> str:
        return "La información logística es inválida."


class ValidacionIdentificacion(ReglaValidacion):
    def es_valida(self, pedido: Pedido) -> bool:
        return bool(pedido.id_pedido) and bool(pedido.canal_origen)

    def mensaje_error(self) -> str:
        return "El pedido no cuenta con identificación válida."


class ValidadorPedido:
    """
    Servicio de dominio que encapsula las reglas de validación.
    """

    def __init__(self):
        self.reglas: List[ReglaValidacion] = [
            ValidacionOrigen(),
            ValidacionDestino(),
            ValidacionEntrega(),
            ValidacionLogistica(),
            ValidacionIdentificacion(),
        ]

    def validar(self, pedido: Pedido) -> tuple[bool, str]:
        if pedido.estado != "Creado":
            return False, f"El pedido no puede validarse desde el estado '{pedido.estado}'."

        for regla in self.reglas:
            if not regla.es_valida(pedido):
                return False, regla.mensaje_error()

        pedido.validar()
        return True, "Pedido validado correctamente."


# =========================================================
# 4. REPARTIDORES
# =========================================================
class Repartidor:
    def __init__(self, id_repartidor: str, capacidad_maxima: float):
        self.id_repartidor = id_repartidor
        self.capacidad_maxima = capacidad_maxima
        self.carga_actual = 0.0
        self.disponible = True
        self.pedidos_asignados: List[Pedido] = []

    def puede_recibir_pedido(self, peso_pedido: float) -> bool:
        if not self.disponible:
            return False
        return (self.carga_actual + peso_pedido) <= self.capacidad_maxima

    def acoplar_pedido(self, pedido: Pedido) -> None:
        if not self.puede_recibir_pedido(pedido.peso_estimado):
            raise ValueError(
                f"El repartidor {self.id_repartidor} no puede recibir el pedido por capacidad."
            )
        self.carga_actual += pedido.peso_estimado
        self.pedidos_asignados.append(pedido)

    def __str__(self) -> str:
        return (
            f"Repartidor [{self.id_repartidor}] | Disponible: {self.disponible} | "
            f"Carga: {self.carga_actual}/{self.capacidad_maxima}"
        )


# =========================================================
# 5. STRATEGY: ASIGNACIÓN DE PEDIDOS
# =========================================================
class EstrategiaAsignacion(ABC):
    @abstractmethod
    def asignar(self, pedido: Pedido, repartidores: List[Repartidor]) -> Optional[Repartidor]:
        pass


class AsignarPorMenorCarga(EstrategiaAsignacion):
    def asignar(self, pedido: Pedido, repartidores: List[Repartidor]) -> Optional[Repartidor]:
        candidatos = [r for r in repartidores if r.puede_recibir_pedido(pedido.peso_estimado)]
        if not candidatos:
            return None
        return min(candidatos, key=lambda r: r.carga_actual)


class AsignacionService:
    def __init__(self, estrategia: EstrategiaAsignacion):
        self.estrategia = estrategia

    def ejecutar_asignacion(
        self, pedido: Pedido, repartidores: List[Repartidor]
    ) -> tuple[bool, str]:
        if pedido.estado != "Validado":
            return False, "El pedido debe estar Validado antes de ser asignado."

        repartidor = self.estrategia.asignar(pedido, repartidores)
        if repartidor is None:
            return False, "No existe un repartidor disponible para este pedido."

        repartidor.acoplar_pedido(pedido)
        pedido.marcar_como_asignado(repartidor)
        return True, f"Pedido asignado al repartidor {repartidor.id_repartidor}."


# =========================================================
# 6. GESTIÓN DE INCIDENCIAS
# =========================================================
class Incidencia:
    def __init__(self, pedido: Pedido, motivo: str):
        if not pedido:
            raise ValueError("Toda incidencia debe estar asociada a un pedido.")
        self.id_caso = str(uuid.uuid4())[:8]
        self.pedido = pedido
        self.motivo = motivo
        self.estado = "Abierta"
        self.resolucion: Optional[str] = None

    def resolver(self, detalle_resolucion: str) -> None:
        if not detalle_resolucion.strip():
            raise ValueError("Una incidencia no puede cerrarse sin resolución.")
        self.resolucion = detalle_resolucion
        self.estado = "Resuelta"

    def __str__(self) -> str:
        return (
            f"Incidencia [{self.id_caso}] | Pedido: {self.pedido.id_pedido} | "
            f"Estado: {self.estado} | Motivo: {self.motivo}"
        )


class IncidenciaReclamo(Incidencia):
    pass


class IncidenciaFactory:
    @staticmethod
    def crear_incidencia(tipo: str, pedido: Pedido, motivo: str) -> Incidencia:
        if tipo.lower() == "reclamo":
            return IncidenciaReclamo(pedido, motivo)
        raise ValueError(f"Tipo de incidencia '{tipo}' no soportado.")


class GestorIncidencias:
    def registrar_reclamo(self, pedido: Pedido, motivo: str) -> Incidencia:
        if pedido.estado != "Entregado":
            raise ValueError(
                "Solo un pedido entregado puede generar una incidencia de reclamo."
            )
        incidencia = IncidenciaFactory.crear_incidencia("reclamo", pedido, motivo)
        print(f"⚠️ Incidencia registrada: {incidencia}")
        return incidencia


# =========================================================
# 7. SIMULACIÓN GENERAL
# =========================================================
if __name__ == "__main__":
    print("\n=== SISTEMA DE LOGÍSTICA: SIMULACIÓN DE 4 CASOS DE USO ===\n")

    # -----------------------------------------------------
    # CASO DE USO 1: Crear pedido desde distintos canales
    # -----------------------------------------------------
    print("1) CREACIÓN DE PEDIDOS")
    servicio_eco = ServicioRegistroPedidos(CreadorEcommerce())
    pedido1 = servicio_eco.registrar_nuevo_pedido(
        origen="Bodega Central Pudahuel",
        punto_origen="BOD-001",
        destino="Casa Cliente - Santiago Centro",
        destinatario="Juan Pérez",
        contacto="+56912345678",
        tipo_entrega="Express",
        ventana_tiempo=None,
        tipo_carga="Caja mediana",
        peso_estimado=5.0,
    )

    servicio_propio = ServicioRegistroPedidos(CreadorCanalPropio())
    pedido2 = servicio_propio.registrar_nuevo_pedido(
        origen="Sucursal Viña del Mar",
        punto_origen="SUC-010",
        destino="Oficina Cliente - Valparaíso",
        destinatario="María Soto",
        contacto="+56987654321",
        tipo_entrega="Programada",
        ventana_tiempo="09:00 - 12:00",
        tipo_carga="Sobre",
        peso_estimado=1.5,
    )

    # -----------------------------------------------------
    # CASO DE USO 2: Validar pedido
    # -----------------------------------------------------
    print("\n2) VALIDACIÓN DE PEDIDOS")
    validador = ValidadorPedido()

    resultado1, mensaje1 = validador.validar(pedido1)
    print("Pedido 1:", "✅" if resultado1 else "❌", mensaje1)

    resultado2, mensaje2 = validador.validar(pedido2)
    print("Pedido 2:", "✅" if resultado2 else "❌", mensaje2)

    # -----------------------------------------------------
    # CASO DE USO 3: Registrar repartidor y asignar pedido
    # -----------------------------------------------------
    print("\n3) GESTIÓN DE REPARTIDORES Y ASIGNACIÓN")
    repartidores = [
        Repartidor("REP-001", capacidad_maxima=10.0),
        Repartidor("REP-002", capacidad_maxima=3.0),
    ]

    for r in repartidores:
        print("Registrado:", r)

    servicio_asignacion = AsignacionService(AsignarPorMenorCarga())

    exito_asignacion, mensaje_asignacion = servicio_asignacion.ejecutar_asignacion(
        pedido1, repartidores
    )
    print("Pedido 1:", "✅" if exito_asignacion else "❌", mensaje_asignacion)

    if exito_asignacion:
        pedido1.iniciar_ruta()
        print(f"➡️ Pedido {pedido1.id_pedido} pasó a estado: {pedido1.estado}")
        pedido1.marcar_entregado()
        print(f"📦 Pedido {pedido1.id_pedido} pasó a estado: {pedido1.estado}")

    # -----------------------------------------------------
    # CASO DE USO 4: Gestión de incidencias
    # -----------------------------------------------------
    print("\n4) GESTIÓN DE INCIDENCIAS")
    gestor_incidencias = GestorIncidencias()

    try:
        incidencia = gestor_incidencias.registrar_reclamo(
            pedido1,
            "El cliente indica que recibió el paquete con daño exterior.",
        )
        incidencia.resolver("Se revisó el caso y se generó compensación al cliente.")
        print(f"✅ Incidencia resuelta: {incidencia}")
    except ValueError as e:
        print(f"❌ Error en incidencias: {e}")

    print("\n=== FIN DE LA SIMULACIÓN ===\n")
