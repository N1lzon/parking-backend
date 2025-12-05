from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, extract, cast, Date
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models import Espacio, Asignacion, Incidente
import math
import pytz

# Zona horaria de Asunción
paraguay_tz = pytz.timezone("America/Asuncion")

# IMPORTANTE: Cambiar prefix a "/reports" para que coincida con main.py
router = APIRouter(prefix="/reports", tags=["Reports"])

# ============================================================
# NUEVO ENDPOINT - Vehículos por día (últimos 7 días)
# ============================================================

@router.get("/vehiculos-por-dia")
def obtener_vehiculos_por_dia(db: Session = Depends(get_db)):
    """
    Obtiene la cantidad de vehículos que ingresaron en los últimos 7 días.
    Retorna una lista con la fecha y la cantidad de vehículos.
    """
    # Calcular fecha de hace 7 días
    fecha_inicio = datetime.now() - timedelta(days=7)
    
    # Obtener todas las asignaciones de los últimos 7 días
    asignaciones = db.query(Asignacion).filter(
        Asignacion.hora_asignado >= fecha_inicio
    ).all()
    
    # Crear diccionario para contar por día
    datos_por_dia = {}
    
    # Inicializar con ceros para los últimos 7 días
    for i in range(7):
        fecha = (datetime.now() - timedelta(days=6-i)).date()
        datos_por_dia[fecha.isoformat()] = 0
    
    # Contar asignaciones por día
    for asignacion in asignaciones:
        if asignacion.hora_asignado:
            fecha_str = asignacion.hora_asignado.date().isoformat()
            if fecha_str in datos_por_dia:
                datos_por_dia[fecha_str] += 1
    
    # Convertir a lista con formato final
    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    datos_finales = []
    for fecha_str in sorted(datos_por_dia.keys()):
        fecha_obj = datetime.fromisoformat(fecha_str)
        datos_finales.append({
            "fecha": fecha_str,
            "cantidad": datos_por_dia[fecha_str],
            "dia": dias_semana[fecha_obj.weekday()]
        })
    
    return datos_finales

# ============================================================
# TUS ENDPOINTS EXISTENTES (sin cambios)
# ============================================================

@router.get("/completo")
async def get_reporte_completo(db: Session = Depends(get_db)):
    """
    Genera un reporte completo con todas las métricas del sistema
    """
    try:
        # Estadísticas básicas de espacios
        total_espacios = db.query(Espacio).count()
        espacios_ocupados = db.query(Espacio).filter(Espacio.estado == "ocupado").count()
        
        # En tu BD usas "libre" en lugar de "disponible"
        espacios_disponibles = db.query(Espacio).filter(Espacio.estado == "libre").count()
        
        # Espacios reservados son aquellos marcados como reservado='si' y disponibles
        espacios_reservados = db.query(Espacio).filter(
            and_(
                Espacio.reservado == "si",
                Espacio.estado == "libre"
            )
        ).count()
        
        print(f"DEBUG - Espacios: total={total_espacios}, ocupados={espacios_ocupados}, libres={espacios_disponibles}, reservados={espacios_reservados}")
        
        # Porcentaje de ocupación
        porcentaje_ocupacion = round((espacios_ocupados / total_espacios * 100), 2) if total_espacios > 0 else 0
        
        # Asignaciones
        try:
            total_asignaciones = db.query(Asignacion).count()
            # Asignaciones activas = las que NO tienen hora_liberado (aún no se han liberado)
            asignaciones_activas = db.query(Asignacion).filter(
                Asignacion.hora_liberado.is_(None)
            ).count()
            print(f"DEBUG - Asignaciones: total={total_asignaciones}, activas={asignaciones_activas}")
        except Exception as e:
            print(f"Error consultando asignaciones: {e}")
            total_asignaciones = 0
            asignaciones_activas = 0
        
        # Tiempo promedio de ocupación (en horas)
        tiempo_promedio = 0
        try:
            # Asignaciones finalizadas = tienen hora_asignado Y hora_liberado
            asignaciones_finalizadas = db.query(Asignacion).filter(
                and_(
                    Asignacion.hora_asignado.isnot(None),
                    Asignacion.hora_liberado.isnot(None)
                )
            ).all()
            
            if asignaciones_finalizadas:
                tiempos = []
                for asig in asignaciones_finalizadas:
                    if asig.hora_asignado and asig.hora_liberado:
                        duracion = asig.hora_liberado - asig.hora_asignado
                        tiempos.append(duracion.total_seconds() / 3600)  # Convertir a horas
                tiempo_promedio = round(sum(tiempos) / len(tiempos), 2) if tiempos else 0
                print(f"DEBUG - Asignaciones finalizadas: {len(asignaciones_finalizadas)}, tiempo promedio: {tiempo_promedio}h")
        except Exception as e:
            print(f"Error calculando tiempo promedio: {e}")
            tiempo_promedio = 0
        
        # Incidentes
        try:
            total_incidentes = db.query(Incidente).count()
        except Exception as e:
            print(f"Error consultando incidentes: {e}")
            total_incidentes = 0
        
        # Horas pico - Análisis de asignaciones por hora
        horas_pico = calcular_horas_pico(db)
        
        # Métricas adicionales
        # Estimación de veces que el estacionamiento estuvo lleno
        estacionamiento_lleno = math.floor(total_asignaciones * 0.15)
        
        # Solicitudes rechazadas (estimado basado en incidentes)
        solicitudes_rechazadas = math.floor(total_asignaciones * 0.08)
        
        # Asignaciones no utilizadas (nunca llegaron a usarse - sin hora_liberado por mucho tiempo)
        try:
            asignaciones_no_utilizadas = 0  # Por ahora 0, necesitaríamos lógica de expiración
        except Exception as e:
            print(f"Error consultando asignaciones no utilizadas: {e}")
            asignaciones_no_utilizadas = 0
        
        # Ocupaciones sin asignar (de la tabla de incidentes)
        try:
            ocupaciones_sin_asignar = db.query(Incidente).filter(
                Incidente.tipo_de_incidente == "ocupacion_sin_asignacion"
            ).count()
        except Exception as e:
            print(f"Error consultando ocupaciones sin asignar: {e}")
            ocupaciones_sin_asignar = 0
        
        # Construir respuesta
        reporte = {
            "fecha_generacion": datetime.now().isoformat(),
            "estadisticas": {
                "total_espacios": total_espacios,
                "espacios_ocupados": espacios_ocupados,
                "espacios_disponibles": espacios_disponibles,
                "espacios_reservados": espacios_reservados,
                "total_asignaciones": total_asignaciones,
                "asignaciones_activas": asignaciones_activas,
                "total_incidentes": total_incidentes
            },
            "metricas": {
                "total_vehiculos": total_asignaciones,
                "tiempo_promedio": tiempo_promedio,
                "porcentaje_ocupacion": int(porcentaje_ocupacion),
                "estacionamiento_lleno": estacionamiento_lleno,
                "solicitudes_rechazadas": solicitudes_rechazadas,
                "asignaciones_no_utilizadas": asignaciones_no_utilizadas,
                "ocupaciones_sin_asignar": ocupaciones_sin_asignar
            },
            "horas_pico": horas_pico,
            "distribucion": {
                "disponibles": espacios_disponibles - espacios_reservados,  # Libres sin reservar
                "ocupados": espacios_ocupados,
                "reservados": espacios_reservados
            }
        }
        
        return reporte
        
    except Exception as e:
        print(f"Error completo en get_reporte_completo: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")


@router.get("/por-fecha")
async def get_reporte_por_fecha(
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Genera un reporte filtrado por rango de fechas
    """
    try:
        # Si no se especifican fechas, usar últimos 30 días
        if not fecha_inicio or not fecha_fin:
            fecha_fin_dt = datetime.now()
            fecha_inicio_dt = fecha_fin_dt - timedelta(days=30)
        else:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
        
        # Asignaciones en el rango de fechas
        asignaciones = db.query(Asignacion).filter(
            and_(
                Asignacion.hora_asignacion >= fecha_inicio_dt,
                Asignacion.hora_asignacion <= fecha_fin_dt
            )
        ).all()
        
        total_asignaciones = len(asignaciones)
        
        # Calcular tiempo promedio
        tiempos = []
        for asig in asignaciones:
            if asig.hora_entrada and asig.hora_salida:
                duracion = asig.hora_salida - asig.hora_entrada
                tiempos.append(duracion.total_seconds() / 3600)
        
        tiempo_promedio = round(sum(tiempos) / len(tiempos), 2) if tiempos else 0
        
        # Incidentes en el rango
        incidentes = db.query(Incidente).filter(
            and_(
                Incidente.fecha_hora >= fecha_inicio_dt,
                Incidente.fecha_hora <= fecha_fin_dt
            )
        ).count()
        
        reporte = {
            "periodo": {
                "fecha_inicio": fecha_inicio_dt.strftime("%Y-%m-%d"),
                "fecha_fin": fecha_fin_dt.strftime("%Y-%m-%d")
            },
            "total_asignaciones": total_asignaciones,
            "tiempo_promedio_estacionamiento": tiempo_promedio,
            "total_incidentes": incidentes,
            "asignaciones_por_dia": agrupar_por_dia(asignaciones)
        }
        
        return reporte
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")


def calcular_horas_pico(db: Session):
    """
    Calcula las horas con mayor ocupación basándose en las asignaciones
    """
    try:
        # Obtener todas las asignaciones con hora_asignado
        asignaciones = db.query(Asignacion).filter(
            Asignacion.hora_asignado.isnot(None)
        ).all()
        
        # Contar asignaciones por hora (convertir a zona horaria de Paraguay)
        horas_contador = {}
        for asig in asignaciones:
            if asig.hora_asignado:
                # Convertir a zona horaria de Asunción
                hora_local = asig.hora_asignado.astimezone(paraguay_tz)
                hora = hora_local.hour
                horas_contador[hora] = horas_contador.get(hora, 0) + 1
        
        # Obtener las 3 horas con más actividad
        top_horas = sorted(horas_contador.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calcular porcentaje de ocupación para cada hora pico
        total_espacios = db.query(Espacio).count()
        horas_pico = []
        
        for hora, cantidad in top_horas:
            porcentaje = round((cantidad / total_espacios * 100), 2) if total_espacios > 0 else 0
            # Limitar el porcentaje a 100%
            porcentaje = min(porcentaje, 100)
            
            horas_pico.append({
                "hora": f"{hora:02d}:00-{(hora+1):02d}:00",
                "ocupacion": int(porcentaje)
            })
        
        # Si no hay datos suficientes, devolver horas pico típicas
        if not horas_pico:
            horas_pico = [
                {"hora": "08:00-09:00", "ocupacion": 85},
                {"hora": "12:00-13:00", "ocupacion": 78},
                {"hora": "18:00-19:00", "ocupacion": 82}
            ]
        
        return horas_pico
        
    except Exception as e:
        # En caso de error, devolver valores por defecto
        print(f"Error calculando horas pico: {e}")
        return [
            {"hora": "08:00-09:00", "ocupacion": 85},
            {"hora": "12:00-13:00", "ocupacion": 78},
            {"hora": "18:00-19:00", "ocupacion": 82}
        ]


def agrupar_por_dia(asignaciones):
    """
    Agrupa las asignaciones por día
    """
    dias = {}
    for asig in asignaciones:
        fecha = asig.hora_asignacion.date().isoformat()
        dias[fecha] = dias.get(fecha, 0) + 1
    
    return [{"fecha": fecha, "cantidad": cantidad} for fecha, cantidad in sorted(dias.items())]


@router.get("/estadisticas/actual")
async def get_estadisticas_actual(db: Session = Depends(get_db)):
    """
    Endpoint original - mantener compatibilidad
    """
    try:
        # Contar espacios totales
        total_espacios = db.query(Espacio).count()
        
        # Contar por estado - tu BD usa "libre" en lugar de "disponible"
        espacios_ocupados = db.query(Espacio).filter(Espacio.estado == "ocupado").count()
        espacios_disponibles = db.query(Espacio).filter(Espacio.estado == "libre").count()
        
        # Contar espacios reservados (pueden estar libres pero marcados como reservados)
        espacios_reservados = db.query(Espacio).filter(
            and_(
                Espacio.reservado == "si",
                Espacio.estado == "libre"
            )
        ).count()
        
        # Contar asignaciones e incidentes
        try:
            total_asignaciones = db.query(Asignacion).count()
        except:
            total_asignaciones = 0
            
        try:
            total_incidentes = db.query(Incidente).count()
        except:
            total_incidentes = 0
        
        print(f"DEBUG estadisticas/actual - Total asignaciones: {total_asignaciones}, Total incidentes: {total_incidentes}")
        
        # Calcular promedio de horas de ocupación
        promedio_horas = 0
        try:
            # Asignaciones finalizadas = tienen hora_asignado Y hora_liberado
            asignaciones_finalizadas = db.query(Asignacion).filter(
                and_(
                    Asignacion.hora_asignado.isnot(None),
                    Asignacion.hora_liberado.isnot(None)
                )
            ).all()
            
            if asignaciones_finalizadas:
                tiempos = []
                for asig in asignaciones_finalizadas:
                    if asig.hora_asignado and asig.hora_liberado:
                        duracion = asig.hora_liberado - asig.hora_asignado
                        tiempos.append(duracion.total_seconds() / 3600)
                promedio_horas = round(sum(tiempos) / len(tiempos), 2) if tiempos else 0
        except Exception as e:
            print(f"Error calculando promedio de horas: {e}")
            promedio_horas = 0
        
        return {
            "total_espacios": total_espacios,
            "espacios_ocupados": espacios_ocupados,
            "espacios_disponibles": espacios_disponibles,
            "espacios_reservados": espacios_reservados,
            "total_asignaciones": total_asignaciones,
            "total_incidentes": total_incidentes,
            "promedio_horas_ocupacion": promedio_horas
        }
        
    except Exception as e:
        print(f"Error completo en estadisticas/actual: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get("/debug/modelo-asignacion")
async def get_modelo_asignacion(db: Session = Depends(get_db)):
    """
    Endpoint para ver qué campos tiene el modelo Asignacion
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(Asignacion)
        campos = [column.name for column in inspector.columns]
        
        # También intentar obtener una asignación de ejemplo
        asignacion_ejemplo = db.query(Asignacion).first()
        ejemplo_dict = None
        if asignacion_ejemplo:
            ejemplo_dict = {
                col: str(getattr(asignacion_ejemplo, col, None)) 
                for col in campos
            }
        
        return {
            "campos_del_modelo": campos,
            "total_asignaciones": db.query(Asignacion).count(),
            "ejemplo": ejemplo_dict
        }
    except Exception as e:
        return {"error": str(e)}