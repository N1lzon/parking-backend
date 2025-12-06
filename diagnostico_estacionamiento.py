#!/usr/bin/env python3
# Script para diagnosticar "Estacionamiento Lleno"
# Ejecutar: python diagnostico_estacionamiento.py

import sys
sys.path.append('.')

from app.database import SessionLocal
from app.models import Espacio, Asignacion
from datetime import datetime, timedelta
from collections import defaultdict

def get_semana_actual():
    hoy = datetime.now()
    dias_desde_lunes = hoy.weekday()
    lunes = hoy - timedelta(days=dias_desde_lunes)
    domingo = lunes + timedelta(days=6)
    
    fecha_inicio = lunes.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_fin = domingo.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return fecha_inicio, fecha_fin

db = SessionLocal()

print("=" * 60)
print("🔍 DIAGNÓSTICO: Estacionamiento Lleno")
print("=" * 60)
print()

# 1. Contar espacios
espacios = db.query(Espacio).all()
total_espacios = len(espacios)
espacios_reservados = len([e for e in espacios if e.reservado == 'si'])
espacios_no_reservados = total_espacios - espacios_reservados
espacios_ocupados_ahora = len([e for e in espacios if e.estado == 'ocupado'])

print(f"📊 ESPACIOS:")
print(f"   Total: {total_espacios}")
print(f"   Reservados: {espacios_reservados}")
print(f"   No Reservados: {espacios_no_reservados}")
print(f"   Ocupados AHORA: {espacios_ocupados_ahora}")
print()

# 2. Verificar si está lleno AHORA
if espacios_ocupados_ahora >= espacios_no_reservados:
    print(f"✅ El estacionamiento está LLENO ahora mismo!")
    print(f"   {espacios_ocupados_ahora} ocupados >= {espacios_no_reservados} no reservados")
else:
    print(f"⚠️  El estacionamiento NO está lleno ahora")
    print(f"   {espacios_ocupados_ahora} ocupados < {espacios_no_reservados} no reservados")
print()

# 3. Analizar asignaciones de la semana
fecha_inicio, fecha_fin = get_semana_actual()
print(f"📅 SEMANA ACTUAL:")
print(f"   Inicio: {fecha_inicio}")
print(f"   Fin: {fecha_fin}")
print()

asignaciones_semana = db.query(Asignacion).filter(
    Asignacion.hora_asignado >= fecha_inicio,
    Asignacion.hora_asignado <= fecha_fin
).all()

print(f"🚗 ASIGNACIONES ESTA SEMANA: {len(asignaciones_semana)}")
print()

# 4. Calcular ocupación por hora
print("⏰ CALCULANDO OCUPACIÓN POR HORA...")
ocupacion_por_hora = defaultdict(int)

for asig in asignaciones_semana:
    hora_inicio = asig.hora_asignado.replace(minute=0, second=0, microsecond=0)
    
    if asig.hora_liberado:
        hora_fin = asig.hora_liberado.replace(minute=0, second=0, microsecond=0)
    else:
        hora_fin = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    hora_actual = hora_inicio
    while hora_actual <= hora_fin:
        ocupacion_por_hora[hora_actual] += 1
        hora_actual += timedelta(hours=1)

# 5. Encontrar horas llenas
horas_llenas = []
for hora, cantidad in ocupacion_por_hora.items():
    if cantidad >= espacios_no_reservados:
        horas_llenas.append((hora, cantidad))

print(f"\n🔥 HORAS CON ESTACIONAMIENTO LLENO: {len(horas_llenas)}")
print()

if horas_llenas:
    print("📋 DETALLE DE HORAS LLENAS:")
    for hora, cantidad in sorted(horas_llenas)[:10]:  # Mostrar primeras 10
        print(f"   {hora.strftime('%Y-%m-%d %H:00')} - {cantidad} vehículos (>= {espacios_no_reservados})")
    
    if len(horas_llenas) > 10:
        print(f"   ... y {len(horas_llenas) - 10} horas más")
else:
    print("⚠️  No hay horas con estacionamiento lleno esta semana")
    print()
    print("💡 POSIBLES RAZONES:")
    print("   1. No ha habido suficientes asignaciones simultáneas")
    print("   2. Las asignaciones ya fueron liberadas")
    print("   3. Necesitas ocupar más espacios al mismo tiempo")
    print()
    print("🔧 PARA PROBAR:")
    print(f"   1. Asigna {espacios_no_reservados} espacios sin liberar")
    print(f"   2. Espera 5 segundos")
    print(f"   3. Ve a Reports")
    print(f"   4. Debería mostrar al menos 1 en 'Estacionamiento Lleno'")

print()
print("=" * 60)

# 6. Mostrar máximo de ocupación
if ocupacion_por_hora:
    max_ocupacion = max(ocupacion_por_hora.values())
    print(f"\n📊 MÁXIMO DE OCUPACIÓN: {max_ocupacion} vehículos simultáneos")
    print(f"   Necesario para lleno: {espacios_no_reservados}")
    
    if max_ocupacion < espacios_no_reservados:
        faltantes = espacios_no_reservados - max_ocupacion
        print(f"   ⚠️  Faltan {faltantes} vehículos para llenar el estacionamiento")

db.close()