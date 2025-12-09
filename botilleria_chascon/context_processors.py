from ventas.models import Trabajador, Turno

def trabajador_context(request):
    trabajador = None
    turno = None

    trabajador_id = request.session.get("trabajador_id")
    turno_id = request.session.get("turno_id")

    if trabajador_id:
        try:
            trabajador = Trabajador.objects.get(id=trabajador_id)
        except Trabajador.DoesNotExist:
            trabajador = None

    if turno_id:
        try:
            turno = Turno.objects.get(id=turno_id)
        except Turno.DoesNotExist:
            turno = None

    return {
        "trabajador_sesion": trabajador,
        "turno_sesion": turno,
    }
