import pandas as pd
import matplotlib.pyplot as plt

def simular_caso_real(datos_mensuales, cap_bat_kwh=100, pot_bat_kw=50, eficiencia=0.90):
    """
    Simulación basada en los 4 meses reales de facturas proporcionados.
    """
    print(f"\n--- SIMULACIÓN: BATERÍA {cap_bat_kwh} kWh | INVERSOR {pot_bat_kw} kW ---")
    print(f"--- CLIENTE: BAR DE XEMA Y JAIME SL (Tarifa 3.0TD) ---\n")
    
    resultados = []
    ahorro_total_periodo = 0
    
    for mes in datos_mensuales:
        nombre = mes['periodo']
        dias_mes = 30 # Estandarización
        
        # 1. Extraemos datos del mes
        consumo_red_total = mes['consumo_red']
        excedente_total = mes['excedente']
        precio_compra = mes['precio_compra_medio']
        precio_venta_excedente = mes['precio_venta'] # Repsol le paga a 0.10 fijo según facturas
        
        # 2. Promedios Diarios (El "Día Tipo" extraído con las 4 facturas que tenemos)
        cons_diario = consumo_red_total / dias_mes
        exc_diario = excedente_total / dias_mes
        
        # 3. Lógica de la Batería (Diaria)
        # ¿Cuánta energía solar SOBRA que podríamos guardar?
        energia_solar_disponible = exc_diario
        
        # Limitante 1: Tamaño de la batería (por ahora siempre será 100kWh)
        # Limitante 2: Potencia de carga (multiplicada por horas de sol efectivas, aprox 4h pico)
        # El inversor no limita la carga total diaria, solo la instantánea (50kW).
        # Se puede capturar todo el excedente hasta llenar la batería.
        carga_bruta = min(energia_solar_disponible, cap_bat_kwh)
        
        # Aplicamos eficiencia (pérdida al guardar y sacar) más consumo interno del inversor etc...
        # Si guardo 100, recupero 90.
        energia_descargable_neta = carga_bruta * eficiencia
        
        # ¿Cuánta de esa energía guardada podemos USAR realmente?
        # No podemos descargar más de lo que consumimos de red por la noche/mañana.
        energia_aprovechada = min(energia_descargable_neta, cons_diario)
        
        # 4. Cálculo Económico (El "Spread")
        
        # A) AHORRO BRUTO: Dejamos de comprar X kWh de la red al precio de consumo
        dinero_ahorrado_compra = energia_aprovechada * precio_compra
        
        # B) COSTE DE OPORTUNIDAD: Esa energía que guardamos, ya no la vendemos a la red
        # Ojo: Sacrificamos la "carga_bruta" (antes de pérdidas) que hubiéramos vertido.
        dinero_perdido_venta = carga_bruta * precio_venta_excedente
        
        # C) AHORRO NETO DIARIO
        ahorro_neto_dia = dinero_ahorrado_compra - dinero_perdido_venta
        
        # Totales Mes
        ahorro_mensual = ahorro_neto_dia * dias_mes
        ahorro_total_periodo += ahorro_mensual
        
        resultados.append({
            'Periodo': nombre,
            'Consumo_Red_kWh': int(consumo_red_total),
            'Excedente_Solar_kWh': int(excedente_total),
            'Solar_Guardada_Dia': round(carga_bruta, 1),
            'Bat_Aprovechada_Dia': round(energia_aprovechada, 1),
            'Precio_Compra_Medio': round(precio_compra, 3),
            'Ahorro_Mensual_Eur': round(ahorro_mensual, 2)
        })

    # Crear DataFrame
    df = pd.DataFrame(resultados)
    
    # Visualización de datos
    print(df[['Periodo', 'Excedente_Solar_kWh', 'Precio_Compra_Medio', 'Ahorro_Mensual_Eur']].to_string(index=False))
    
    print("-" * 50)
    print(f"AHORRO TOTAL (4 Meses analizados): {ahorro_total_periodo:,.2f} €")
    
    # Proyección Anual (Extrapolación simple x3)
    proyeccion = ahorro_total_periodo * 3
    print(f"PROYECCIÓN AHORRO ANUAL ESTIMADO:  {proyeccion:,.2f} €")
    print("-" * 50)
    
    # Retorno de Inversión (ROI)
    # Coste estimado batería industrial 100kWh instalada (aprox 300€/kWh)
    coste_bateria_est = 30000 
    amortizacion_years = coste_bateria_est / proyeccion if proyeccion > 0 else 999
    
    print(f"Coste estimado Batería (100kWh):   {coste_bateria_est:,.0f} €")
    print(f"Tiempo de Amortización (años):     {amortizacion_years:.1f} años")
    print("\nNOTA: El ahorro es bajo porque Repsol te paga muy bien los excedentes (0.10€)")
    print("y compras la luz relativamente barata (promedio 0.14€). El margen es pequeño.")

# --- DATOS CARGADOS MANUALMENTE DE LAS FACTURAS ---
datos_reales = [
    {
        'periodo': 'Mar-Abr', 
        # Factura 2: Consumo muy bajo, mucho excedente
        'consumo_red': 2955, 
        'excedente': 1940, 
        'precio_compra_medio': 0.115, # P4, P5, P6 predominan (baratos)
        'precio_venta': 0.10
    },
    {
        'periodo': 'Abr-May', 
        # Factura 4: Similar a la anterior
        'consumo_red': 3397, 
        'excedente': 1708, 
        'precio_compra_medio': 0.120, 
        'precio_venta': 0.10
    },
    {
        'periodo': 'May-Jun', 
        # Factura 3: Sube el consumo (Empieza calor), baja excedente
        'consumo_red': 5891, 
        'excedente': 1352, 
        'precio_compra_medio': 0.145, # Entra más consumo en horas caras
        'precio_venta': 0.10
    },
    {
        'periodo': 'Jun-Jul', 
        # Factura 1: Consumo muy alto, excedente se mantiene
        'consumo_red': 6563, 
        'excedente': 1399, 
        'precio_compra_medio': 0.165, # Julio es caro (P1/P2)
        'precio_venta': 0.10
    }
]

# Ejecutar
simular_caso_real(datos_reales, cap_bat_kwh=100)