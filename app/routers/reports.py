from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Asignacion, Espacio, Incidente
from collections import defaultdict

# Importar SolicitudAyuda solo si existe
try:
    from ..models import SolicitudAyuda
    AYUDA_DISPONIBLE = True
except ImportError:
    AYUDA_DISPONIBLE = False
    print("⚠️  Tabla SolicitudAyuda no disponible")

router = APIRouter(prefix="/reports", tags=["Reports"])

def get_semana_actual():
    """
    Obtener el rango de fechas de la semana actual (Lunes a Domingo)
    """
    try:
        hoy = datetime.now()
        dias_desde_lunes = hoy.weekday()
        lunes = hoy - timedelta(days=dias_desde_lunes)
        domingo = lunes + timedelta(days=6)
        
        fecha_inicio = lunes.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = domingo.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return fecha_inicio, fecha_fin
    except Exception as e:
        print(f"Error en get_semana_actual: {e}")
        hoy = datetime.now()
        fecha_fin = hoy
        fecha_inicio = hoy - timedelta(days=7)
        return fecha_inicio, fecha_fin

@router.get("/rango-detallado")
def obtener_reporte_rango_detallado(
    fecha_inicio: str,
    fecha_fin: str,
    db: Session = Depends(get_db)
):
    """Obtener reporte con métricas desglosadas por día (para Excel)"""
    try:
        # Convertir strings a datetime
        fecha_inicio_dt = datetime.fromisoformat(fecha_inicio).replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dt = datetime.fromisoformat(fecha_fin).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # ============================================================
        # MÉTRICAS POR DÍA
        # ============================================================
        metricas_por_dia = []
        
        # Iterar cada día en el rango
        fecha_actual = fecha_inicio_dt
        while fecha_actual <= fecha_fin_dt:
            dia_inicio = fecha_actual.replace(hour=0, minute=0, second=0, microsecond=0)
            dia_fin = fecha_actual.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Asignaciones del día
            asignaciones_dia = db.query(Asignacion).filter(
                Asignacion.hora_asignado >= dia_inicio,
                Asignacion.hora_asignado <= dia_fin
            ).all()
            
            # Calcular tiempo promedio del día
            tiempos = []
            for asig in asignaciones_dia:
                if asig.hora_liberado:
                    hora_asignado = asig.hora_asignado.replace(tzinfo=None) if asig.hora_asignado.tzinfo else asig.hora_asignado
                    hora_liberado = asig.hora_liberado.replace(tzinfo=None) if asig.hora_liberado.tzinfo else asig.hora_liberado
                    tiempo = (hora_liberado - hora_asignado).total_seconds() / 3600
                    if tiempo > 0:
                        tiempos.append(tiempo)
            
            tiempo_promedio = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0
            
            # Solicitudes de ayuda del día
            solicitudes_ayuda = 0
            if AYUDA_DISPONIBLE:
                try:
                    solicitudes_ayuda = db.query(SolicitudAyuda).filter(
                        SolicitudAyuda.fecha_hora >= dia_inicio,
                        SolicitudAyuda.fecha_hora <= dia_fin
                    ).count()
                except:
                    pass
            
            # Estacionamiento lleno del día
            estacionamiento_lleno = db.query(Incidente).filter(
                Incidente.tipo_de_incidente == "estacionamiento_lleno",
                Incidente.hora_de_registro >= dia_inicio,
                Incidente.hora_de_registro <= dia_fin
            ).count()
            
            # Solicitudes rechazadas del día
            solicitudes_rechazadas = db.query(Incidente).filter(
                Incidente.tipo_de_incidente == "solicitud_rechazada",
                Incidente.hora_de_registro >= dia_inicio,
                Incidente.hora_de_registro <= dia_fin
            ).count()
            
            # Incidentes manuales del día
            incidentes_dia = db.query(Incidente).filter(
                Incidente.hora_de_registro >= dia_inicio,
                Incidente.hora_de_registro <= dia_fin,
                Incidente.tipo_de_incidente.notin_(["estacionamiento_lleno", "solicitud_rechazada"])
            ).count()
            
            metricas_por_dia.append({
                "fecha": fecha_actual.date().isoformat(),
                "total_vehiculos": len(asignaciones_dia),
                "tiempo_promedio": tiempo_promedio,
                "solicitudes_ayuda": solicitudes_ayuda,
                "estacionamiento_lleno": estacionamiento_lleno,
                "solicitudes_rechazadas": solicitudes_rechazadas,
                "incidentes_manuales": incidentes_dia
            })
            
            # Siguiente día
            fecha_actual += timedelta(days=1)
        
        # ============================================================
        # HORAS PICO (del rango completo)
        # ============================================================
        asignaciones_rango = db.query(Asignacion).filter(
            Asignacion.hora_asignado >= fecha_inicio_dt,
            Asignacion.hora_asignado <= fecha_fin_dt
        ).all()
        
        horas_ocupacion = {}
        for asig in asignaciones_rango:
            hora = asig.hora_asignado.hour
            horas_ocupacion[hora] = horas_ocupacion.get(hora, 0) + 1
        
        horas_pico_list = sorted(
            [{"hora": f"{h:02d}:00-{(h+1):02d}:00", "ocupacion": count} 
             for h, count in horas_ocupacion.items()],
            key=lambda x: x["ocupacion"],
            reverse=True
        )[:10]  # Top 10 horas
        
        if horas_pico_list:
            max_ocupacion = horas_pico_list[0]["ocupacion"]
            for hora in horas_pico_list:
                hora["ocupacion"] = round((hora["ocupacion"] / max_ocupacion * 100), 0) if max_ocupacion > 0 else 0
        
        # ============================================================
        # INCIDENTES (del rango completo)
        # ============================================================
        incidentes_lista = db.query(Incidente).filter(
            Incidente.hora_de_registro >= fecha_inicio_dt,
            Incidente.hora_de_registro <= fecha_fin_dt
        ).order_by(Incidente.hora_de_registro.desc()).all()
        
        incidentes_dict = []
        for inc in incidentes_lista:
            incidentes_dict.append({
                "id": inc.id,
                "tipo_de_incidente": inc.tipo_de_incidente,
                "hora_de_registro": inc.hora_de_registro.isoformat(),
                "hora_de_solucion": inc.hora_de_solucion.isoformat() if inc.hora_de_solucion else None,
                "nota": inc.nota,
                "id_de_espacio": inc.id_de_espacio,
                "espacio": {
                    "numero_de_espacio": inc.espacio.numero_de_espacio if inc.espacio else None
                }
            })
        
        print(f"📊 REPORTE DETALLADO:")
        print(f"   Rango: {fecha_inicio} - {fecha_fin}")
        print(f"   Días: {len(metricas_por_dia)}")
        print(f"   Incidentes: {len(incidentes_dict)}")
        
        return {
            "periodo": {
                "inicio": fecha_inicio_dt.isoformat(),
                "fin": fecha_fin_dt.isoformat()
            },
            "metricas_por_dia": metricas_por_dia,
            "horas_pico": horas_pico_list,
            "incidentes": incidentes_dict
        }
        
    except Exception as e:
        print(f"❌ Error en /reports/rango-detallado: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rango")
def obtener_reporte_rango(
    fecha_inicio: str,
    fecha_fin: str,
    db: Session = Depends(get_db)
):
    """Obtener reporte para un rango de fechas específico"""
    try:
        # Convertir strings a datetime
        fecha_inicio_dt = datetime.fromisoformat(fecha_inicio).replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dt = datetime.fromisoformat(fecha_fin).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Obtener todos los espacios
        espacios = db.query(Espacio).all()
        total_espacios = len(espacios)
        
        if total_espacios == 0:
            return {
                "periodo": {
                    "tipo": "personalizado",
                    "inicio": fecha_inicio_dt.isoformat(),
                    "fin": fecha_fin_dt.isoformat()
                },
                "estadisticas": {"total_incidentes": 0, "semana_actual": False},
                "metricas": {
                    "total_vehiculos": 0,
                    "tiempo_promedio": 0,
                    "porcentaje_ocupacion": 0,
                    "solicitudes_ayuda": 0,
                    "estacionamiento_lleno": 0,
                    "solicitudes_rechazadas": 0,
                    "asignaciones_no_utilizadas": 0
                },
                "horas_pico": [],
                "distribucion": {
                    "disponibles": 0,
                    "ocupados": 0,
                    "reservados": 0,
                    "total": 0
                },
                "incidentes": []
            }
        
        espacios_disponibles = len([e for e in espacios if e.estado == 'libre'])
        espacios_ocupados = len([e for e in espacios if e.estado == 'ocupado'])
        espacios_reservados = len([e for e in espacios if e.reservado == 'si'])
        
        # Obtener asignaciones del rango
        asignaciones_rango = db.query(Asignacion).filter(
            Asignacion.hora_asignado >= fecha_inicio_dt,
            Asignacion.hora_asignado <= fecha_fin_dt
        ).all()
        
        total_vehiculos = len(asignaciones_rango)
        
        # Calcular tiempo promedio
        tiempos = []
        for asig in asignaciones_rango:
            if asig.hora_liberado:
                hora_asignado = asig.hora_asignado.replace(tzinfo=None) if asig.hora_asignado.tzinfo else asig.hora_asignado
                hora_liberado = asig.hora_liberado.replace(tzinfo=None) if asig.hora_liberado.tzinfo else asig.hora_liberado
                
                tiempo = (hora_liberado - hora_asignado).total_seconds() / 3600
                
                if tiempo > 0:
                    tiempos.append(tiempo)
        
        tiempo_promedio = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0
        
        # Porcentaje de ocupación actual
        porcentaje_ocupacion = round((espacios_ocupados / total_espacios * 100), 0) if total_espacios > 0 else 0
        
        # Solicitudes de ayuda
        solicitudes_ayuda = 0
        if AYUDA_DISPONIBLE:
            try:
                solicitudes_ayuda = db.query(SolicitudAyuda).filter(
                    SolicitudAyuda.fecha_hora >= fecha_inicio_dt,
                    SolicitudAyuda.fecha_hora <= fecha_fin_dt
                ).count()
            except:
                pass
        
        # Horas pico
        horas_ocupacion = {}
        for asig in asignaciones_rango:
            hora = asig.hora_asignado.hour
            horas_ocupacion[hora] = horas_ocupacion.get(hora, 0) + 1
        
        horas_pico_list = sorted(
            [{"hora": f"{h:02d}:00-{(h+1):02d}:00", "ocupacion": count} 
             for h, count in horas_ocupacion.items()],
            key=lambda x: x["ocupacion"],
            reverse=True
        )[:3]
        
        if horas_pico_list:
            max_ocupacion = horas_pico_list[0]["ocupacion"]
            for hora in horas_pico_list:
                hora["ocupacion"] = round((hora["ocupacion"] / max_ocupacion * 100), 0) if max_ocupacion > 0 else 0
        
        # Estacionamiento lleno
        estacionamiento_lleno = db.query(Incidente).filter(
            Incidente.tipo_de_incidente == "estacionamiento_lleno",
            Incidente.hora_de_registro >= fecha_inicio_dt,
            Incidente.hora_de_registro <= fecha_fin_dt
        ).count()
        
        # Solicitudes rechazadas
        solicitudes_rechazadas = db.query(Incidente).filter(
            Incidente.tipo_de_incidente == "solicitud_rechazada",
            Incidente.hora_de_registro >= fecha_inicio_dt,
            Incidente.hora_de_registro <= fecha_fin_dt
        ).count()
        
        # Asignaciones no utilizadas
        asignaciones_no_utilizadas = 0
        for asig in asignaciones_rango:
            if asig.hora_liberado:
                duracion_segundos = (asig.hora_liberado - asig.hora_asignado).total_seconds()
                if duracion_segundos < 60:
                    asignaciones_no_utilizadas += 1
        
        # Incidentes manuales
        total_incidentes = db.query(Incidente).filter(
            Incidente.hora_de_registro >= fecha_inicio_dt,
            Incidente.hora_de_registro <= fecha_fin_dt,
            Incidente.tipo_de_incidente.notin_(["estacionamiento_lleno", "solicitud_rechazada"])
        ).count()
        
        # Lista completa de incidentes
        incidentes_lista = db.query(Incidente).filter(
            Incidente.hora_de_registro >= fecha_inicio_dt,
            Incidente.hora_de_registro <= fecha_fin_dt
        ).order_by(Incidente.hora_de_registro.desc()).all()
        
        incidentes_dict = []
        for inc in incidentes_lista:
            incidentes_dict.append({
                "id": inc.id,
                "tipo_de_incidente": inc.tipo_de_incidente,
                "hora_de_registro": inc.hora_de_registro.isoformat(),
                "hora_de_solucion": inc.hora_de_solucion.isoformat() if inc.hora_de_solucion else None,
                "nota": inc.nota,
                "id_de_espacio": inc.id_de_espacio,
                "espacio": {
                    "numero_de_espacio": inc.espacio.numero_de_espacio if inc.espacio else None
                }
            })
        
        print(f"📊 REPORTE PERSONALIZADO:")
        print(f"   Rango: {fecha_inicio} - {fecha_fin}")
        print(f"   Vehículos: {total_vehiculos}")
        print(f"   Incidentes: {len(incidentes_dict)}")
        
        return {
            "periodo": {
                "tipo": "personalizado",
                "inicio": fecha_inicio_dt.isoformat(),
                "fin": fecha_fin_dt.isoformat()
            },
            "estadisticas": {
                "total_incidentes": total_incidentes,
                "semana_actual": False
            },
            "metricas": {
                "total_vehiculos": total_vehiculos,
                "tiempo_promedio": tiempo_promedio,
                "porcentaje_ocupacion": int(porcentaje_ocupacion),
                "solicitudes_ayuda": solicitudes_ayuda,
                "estacionamiento_lleno": estacionamiento_lleno,
                "solicitudes_rechazadas": solicitudes_rechazadas,
                "asignaciones_no_utilizadas": asignaciones_no_utilizadas
            },
            "horas_pico": horas_pico_list,
            "distribucion": {
                "disponibles": espacios_disponibles,
                "ocupados": espacios_ocupados,
                "reservados": espacios_reservados,
                "total": total_espacios
            },
            "incidentes": incidentes_dict
        }
        
    except Exception as e:
        print(f"❌ Error en /reports/rango: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/completo")
def obtener_reporte_completo(db: Session = Depends(get_db)):
    """Obtener reporte completo del sistema para la semana actual"""
    try:
        fecha_inicio, fecha_fin = get_semana_actual()
        
        # Obtener todos los espacios
        espacios = db.query(Espacio).all()
        total_espacios = len(espacios)
        
        if total_espacios == 0:
            return {
                "periodo": {
                    "tipo": "semana_actual",
                    "inicio": fecha_inicio.isoformat(),
                    "fin": fecha_fin.isoformat()
                },
                "estadisticas": {"total_incidentes": 0, "semana_actual": True},
                "metricas": {
                    "total_vehiculos": 0,
                    "tiempo_promedio": 0,
                    "porcentaje_ocupacion": 0,
                    "solicitudes_ayuda": 0,
                    "estacionamiento_lleno": 0,
                    "solicitudes_rechazadas": 0,
                    "asignaciones_no_utilizadas": 0
                },
                "horas_pico": [],
                "distribucion": {
                    "disponibles": 0,
                    "ocupados": 0,
                    "reservados": 0,
                    "total": 0
                }
            }
        
        espacios_disponibles = len([e for e in espacios if e.estado == 'libre'])
        espacios_ocupados = len([e for e in espacios if e.estado == 'ocupado'])
        espacios_reservados = len([e for e in espacios if e.reservado == 'si'])
        
        # Obtener asignaciones de la semana
        asignaciones_semana = db.query(Asignacion).filter(
            Asignacion.hora_asignado >= fecha_inicio,
            Asignacion.hora_asignado <= fecha_fin
        ).all()
        
        total_vehiculos = len(asignaciones_semana)
        
        # Calcular tiempo promedio
        tiempos = []
        for asig in asignaciones_semana:
            if asig.hora_liberado:
                # Convertir a naive datetime para evitar problemas de timezone
                hora_asignado = asig.hora_asignado.replace(tzinfo=None) if asig.hora_asignado.tzinfo else asig.hora_asignado
                hora_liberado = asig.hora_liberado.replace(tzinfo=None) if asig.hora_liberado.tzinfo else asig.hora_liberado
                
                tiempo = (hora_liberado - hora_asignado).total_seconds() / 3600
                
                # Solo agregar tiempos positivos (válidos)
                if tiempo > 0:
                    tiempos.append(tiempo)
                else:
                    print(f"⚠️ Tiempo negativo detectado: Asignación {asig.id} - {tiempo:.2f}h")
        
        tiempo_promedio = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0
        
        # Porcentaje de ocupación actual
        porcentaje_ocupacion = round((espacios_ocupados / total_espacios * 100), 0) if total_espacios > 0 else 0
        
        # Solicitudes de ayuda
        solicitudes_ayuda = 0
        if AYUDA_DISPONIBLE:
            try:
                solicitudes_ayuda = db.query(SolicitudAyuda).filter(
                    SolicitudAyuda.fecha_hora >= fecha_inicio,
                    SolicitudAyuda.fecha_hora <= fecha_fin
                ).count()
            except:
                pass
        
        # ============================================================
        # HORAS PICO
        # ============================================================
        horas_ocupacion = {}
        for asig in asignaciones_semana:
            hora = asig.hora_asignado.hour
            horas_ocupacion[hora] = horas_ocupacion.get(hora, 0) + 1
        
        horas_pico_list = sorted(
            [{"hora": f"{h:02d}:00-{(h+1):02d}:00", "ocupacion": count} 
             for h, count in horas_ocupacion.items()],
            key=lambda x: x["ocupacion"],
            reverse=True
        )[:3]
        
        if horas_pico_list:
            max_ocupacion = horas_pico_list[0]["ocupacion"]
            for hora in horas_pico_list:
                hora["ocupacion"] = round((hora["ocupacion"] / max_ocupacion * 100), 0) if max_ocupacion > 0 else 0
        
        # ============================================================
        # ESTACIONAMIENTO LLENO - Contar desde tabla INCIDENTES
        # ============================================================
        estacionamiento_lleno = db.query(Incidente).filter(
            Incidente.tipo_de_incidente == "estacionamiento_lleno",
            Incidente.hora_de_registro >= fecha_inicio,
            Incidente.hora_de_registro <= fecha_fin
        ).count()
        
        print(f"📊 Estacionamiento lleno esta semana: {estacionamiento_lleno} veces (desde incidentes)")
        
        # ============================================================
        # SOLICITUDES RECHAZADAS - Contar desde tabla INCIDENTES
        # ============================================================
        solicitudes_rechazadas = db.query(Incidente).filter(
            Incidente.tipo_de_incidente == "solicitud_rechazada",
            Incidente.hora_de_registro >= fecha_inicio,
            Incidente.hora_de_registro <= fecha_fin
        ).count()
        
        print(f"🚫 Solicitudes rechazadas esta semana: {solicitudes_rechazadas}")
        
        # ============================================================
        # ASIGNACIONES NO UTILIZADAS - Por implementar
        # ============================================================
        # Criterio: Asignaciones que fueron liberadas en menos de 1 minuto
        asignaciones_no_utilizadas = 0
        for asig in asignaciones_semana:
            if asig.hora_liberado:
                duracion_segundos = (asig.hora_liberado - asig.hora_asignado).total_seconds()
                if duracion_segundos < 60:  # Menos de 1 minuto
                    asignaciones_no_utilizadas += 1
        
        # ============================================================
        # INCIDENTES TOTALES (excluyendo automáticos)
        # ============================================================
        # Total de incidentes MANUALES (no automáticos)
        total_incidentes = db.query(Incidente).filter(
            Incidente.hora_de_registro >= fecha_inicio,
            Incidente.hora_de_registro <= fecha_fin,
            # Excluir incidentes automáticos del sistema
            Incidente.tipo_de_incidente.notin_(["estacionamiento_lleno", "solicitud_rechazada"])
        ).count()
        
        # ============================================================
        # LISTA COMPLETA DE INCIDENTES (para exportación)
        # ============================================================
        incidentes_lista = db.query(Incidente).filter(
            Incidente.hora_de_registro >= fecha_inicio,
            Incidente.hora_de_registro <= fecha_fin
        ).order_by(Incidente.hora_de_registro.desc()).all()
        
        # Convertir a diccionarios para JSON
        incidentes_dict = []
        for inc in incidentes_lista:
            incidentes_dict.append({
                "id": inc.id,
                "tipo_de_incidente": inc.tipo_de_incidente,
                "hora_de_registro": inc.hora_de_registro.isoformat(),
                "hora_de_solucion": inc.hora_de_solucion.isoformat() if inc.hora_de_solucion else None,
                "nota": inc.nota,
                "id_de_espacio": inc.id_de_espacio,
                "espacio": {
                    "numero_de_espacio": inc.espacio.numero_de_espacio if inc.espacio else None
                }
            })
        
        print(f"📊 RESUMEN SEMANA:")
        print(f"   Vehículos: {total_vehiculos}")
        print(f"   Estacionamiento lleno: {estacionamiento_lleno} veces")
        print(f"   Solicitudes rechazadas: {solicitudes_rechazadas}")
        print(f"   Asignaciones no utilizadas: {asignaciones_no_utilizadas}")
        print(f"   Incidentes manuales: {total_incidentes}")
        
        return {
            "periodo": {
                "tipo": "semana_actual",
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "estadisticas": {
                "total_incidentes": total_incidentes,
                "semana_actual": True
            },
            "metricas": {
                "total_vehiculos": total_vehiculos,
                "tiempo_promedio": tiempo_promedio,
                "porcentaje_ocupacion": int(porcentaje_ocupacion),
                "solicitudes_ayuda": solicitudes_ayuda,
                "estacionamiento_lleno": estacionamiento_lleno,
                "solicitudes_rechazadas": solicitudes_rechazadas,
                "asignaciones_no_utilizadas": asignaciones_no_utilizadas
            },
            "horas_pico": horas_pico_list,
            "distribucion": {
                "disponibles": espacios_disponibles,
                "ocupados": espacios_ocupados,
                "reservados": espacios_reservados,
                "total": total_espacios
            },
            "incidentes": incidentes_dict  # Lista completa de incidentes
        }
        
    except Exception as e:
        print(f"❌ Error en /reports/completo: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/estadisticas/actual")
def obtener_estadisticas_actuales(db: Session = Depends(get_db)):
    """Obtener estadísticas en tiempo real (sin filtro de semana)"""
    try:
        espacios = db.query(Espacio).all()
        
        disponibles = sum(1 for e in espacios if e.estado == 'libre')
        ocupados = sum(1 for e in espacios if e.estado == 'ocupado')
        reservados = sum(1 for e in espacios if e.reservado == 'si')
        
        return {
            "disponibles": disponibles,
            "ocupados": ocupados,
            "reservados": reservados,
            "total": len(espacios),
            "porcentaje_ocupacion": round((ocupados / len(espacios) * 100), 0) if espacios else 0
        }
    except Exception as e:
        print(f"Error en estadisticas/actual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehiculos-por-dia")
def obtener_vehiculos_por_dia(db: Session = Depends(get_db)):
    """Obtener vehículos ingresados por día en la semana actual"""
    try:
        fecha_inicio, fecha_fin = get_semana_actual()
        
        asignaciones = db.query(Asignacion).filter(
            Asignacion.hora_asignado >= fecha_inicio,
            Asignacion.hora_asignado <= fecha_fin
        ).all()
        
        conteo_por_fecha = {}
        for asig in asignaciones:
            fecha_str = asig.hora_asignado.date().isoformat()
            conteo_por_fecha[fecha_str] = conteo_por_fecha.get(fecha_str, 0) + 1
        
        dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        resultado = []
        
        fecha_actual = fecha_inicio.date()
        while fecha_actual <= fecha_fin.date():
            fecha_str = fecha_actual.isoformat()
            dia_semana = dias_es[fecha_actual.weekday()]
            cantidad = conteo_por_fecha.get(fecha_str, 0)
            
            resultado.append({
                "fecha": fecha_str,
                "cantidad": cantidad,
                "dia_semana": dia_semana
            })
            
            fecha_actual += timedelta(days=1)
        
        return resultado
        
    except Exception as e:
        print(f"Error en vehiculos-por-dia: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))