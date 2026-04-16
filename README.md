from abc import ABC, abstractmethod

class ReglaValidacion(ABC):
    @abstractmethod
    def es_valida(self, pedido):
        pass

    @abstractmethod
    def mensaje_error(self):
        pass


class ValidacionOrigen(ReglaValidacion):
    def es_valida(self, pedido):
        return pedido.origen is not None and pedido.origen.get("es_interpretable", False)

    def mensaje_error(self):
        return "El origen no cumple con las condiciones minimas de validacion"


class ValidacionDestino(ReglaValidacion):
    def es_valida(self, pedido):
        return pedido.destino is not None and pedido.destino.get("es_interpretable", False)

    def mensaje_error(self):
        return "El destino no cumple con las condiciones minimas de validacion"


class ValidacionEntrega(ReglaValidacion):
    def es_valida(self, pedido):
        entrega = pedido.entrega
        if entrega is None:
            return False
        if entrega.get("tipo") == "programada" and not entrega.get("ventana_tiempo"):
            return False
        return True

    def mensaje_error(self):
        return "La informacion de entrega no es valida"


class ValidacionLogistica(ReglaValidacion):
    def es_valida(self, pedido):
        logistica = pedido.logistica
        return logistica is not None and logistica.get("peso_estimado", 0) > 0

    def mensaje_error(self):
        return "La informacion logistica no es valida"


class ValidacionIdentificacion(ReglaValidacion):
    def es_valida(self, pedido):
        return bool(pedido.id_pedido) and bool(pedido.canal_origen)

    def mensaje_error(self):
        return "Falta identificacion del pedido"


class ValidadorPedido:
    def __init__(self):
        self.reglas = [
            ValidacionOrigen(),
            ValidacionDestino(),
            ValidacionEntrega(),
            ValidacionLogistica(),
            ValidacionIdentificacion()
        ]

    def validar(self, pedido):
        for regla in self.reglas:
            if not regla.es_valida(pedido):
                return False, regla.mensaje_error()

        pedido.estado = "Validado"
        return True, "Pedido validado correctamente"
