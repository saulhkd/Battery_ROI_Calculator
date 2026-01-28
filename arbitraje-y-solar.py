import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def simular_arbitraje_y_solar(datos_facturas, cap_bat=100, pot_bat=50, eficiencia=0.90):
    """
    Simula el ahorro combinando autoconsumo de excedentes y arbitraje de precios de red.
    Genera perfiles horarios a partir de datos mensuales.
    """
    print(f"\n--- INICIO SIMULACIÓN: SOLAR + ARBITRAJE ---")
    print(f"Batería: {cap_bat} kWh | Potencia: {pot_bat} kW | Eficiencia: {int(eficiencia*100)}%")
    print("-" * 60)
    
    resultados_mes = []
    
    ahorro_total = 0
    
    for mes in datos_facturas:
        nombre = mes['mes']
        dias = 30
        horas_totales = dias * 24
        
        # --- 1. GENERAR PERFIL SINTÉTICO HORARIO (Hora a Hora) ---
        df = pd.DataFrame(index=range(horas_totales))
        df['hora_dia'] = df.index % 24
        
        # A) Perfil de Consumo (Hostelería: alto mediodía y noche)
        # Pesos: Madrugada(0.4), Mañana(0.8), Comida(1.5), Tarde(0.8), Cena(1.6)
        condiciones = [
            (df['hora_dia'] < 8),
            (df['hora_dia'] >= 8) & (df['hora_dia'] < 12),
            (df['hora_dia'] >= 12) & (df['hora_dia'] < 17),
            (df['hora_dia'] >= 17) & (df['hora_dia'] < 20),
            (df['hora_dia'] >= 20)
        ]
        pesos = [0.4, 0.8, 2, 0.8, 1] 
        df['perfil_base'] = np.select(condiciones, pesos)
        
        # Ajustamos al consumo real de la factura
        factor_consumo = mes['consumo_total_kwh'] / df['perfil_base'].sum()
        df['consumo_kwh'] = df['perfil_base'] * factor_consumo
        
        # B) Perfil Solar (Campana de Gauss 08:00 - 19:00)
        df['perfil_solar'] = np.where(
            (df['hora_dia'] > 7) & (df['hora_dia'] < 20),
            np.sin((df['hora_dia'] - 7) * np.pi / 13),
            0
        )
        # Ajustamos al excedente real de la factura
        factor_solar = mes['excedente_total_kwh'] / df['perfil_solar'].sum() if df['perfil_solar'].sum() > 0 else 0
        df['solar_disponible_kwh'] = df['perfil_solar'] * factor_solar
        
        # C) Precios Horarios (Simplificación P1/P6 de la factura)
        # 00-08h: Valle (Precio P6) | 08-00h: Punta (Precio P1/P4 según mes)
        df['precio_compra'] = np.where(df['hora_dia'] < 8, mes['precio_valle'], mes['precio_punta'])
        df['es_hora_valle'] = df['hora_dia'] < 8
        
        # --- 2. SIMULACIÓN DE LA BATERÍA ---
        soc = 0.0 # Estado de carga (kWh)
        ahorro_acumulado_mes = 0.0
        
        # Listas para guardar datos de la gráfica (solo usamos un mes de ejemplo luego)
        historial_soc = []
        
        for i in range(len(df)):
            cons = df.loc[i, 'consumo_kwh']
            solar = df.loc[i, 'solar_disponible_kwh']
            precio_actual = df.loc[i, 'precio_compra']
            es_valle = df.loc[i, 'es_hora_valle']
            
            # --- ESTRATEGIA DE CARGA ---
            energia_entrada = 0.0
            coste_carga = 0.0
            
            # 1. Carga Solar (Prioridad Absoluta) -> Coste oportunidad = Precio venta excedente
            if solar > 0:
                espacio_libre = cap_bat - soc
                carga_solar = min(solar, espacio_libre, pot_bat)
                
                soc += carga_solar * np.sqrt(eficiencia) # Pérdida en la entrada
                coste_carga += carga_solar * mes['precio_venta_excedente'] 
                energia_entrada += carga_solar
            
            # 2. Carga de Red (Arbitraje) -> Solo en Valle y si hay margen económico
            # Solo cargamos si la batería no se ha llenado con sol y si el "spread" vale la pena
            if es_valle and energia_entrada == 0:
                espacio_libre = cap_bat - soc
                # Margen: Precio Punta vs (Precio Valle / Eficiencia)
                precio_descarga_efectivo = mes['precio_valle'] / eficiencia
                margen = mes['precio_punta'] - precio_descarga_efectivo
                
                if margen > 0.02 and espacio_libre > 0: # Solo si ganamos >2 céntimos/kWh
                    carga_red = min(espacio_libre, pot_bat)
                    soc += carga_red * np.sqrt(eficiencia)
                    coste_carga += carga_red * mes['precio_valle']
                    energia_entrada += carga_red

            # --- ESTRATEGIA DE DESCARGA ---
            ahorro_hora = 0.0
            
            # Descargamos solo en horas CARAS (No valle) para cubrir consumo
            if not es_valle and soc > 0 and cons > 0:
                # Energía necesaria para cubrir el consumo
                energia_necesaria_red = cons
                
                # Lo que la batería puede dar (limitado por potencia y carga actual)
                # OJO: soc está en DC. Para dar 1 kWh AC, necesito sacar 1/sqrt(eff) DC aprox.
                # Simplificamos: Energía AC disponible = SOC * sqrt(eff)
                energia_ac_disponible = soc * np.sqrt(eficiencia)
                
                descarga_ac_util = min(energia_necesaria_red, energia_ac_disponible, pot_bat)
                
                # Actualizamos SOC (restamos lo que sale en DC)
                soc_restar = descarga_ac_util / np.sqrt(eficiencia)
                soc -= soc_restar
                
                # Dinero ahorrado (lo que NO pagamos a la comercializadora)
                ahorro_hora = descarga_ac_util * precio_actual
            
            # Balance Neto de la Hora
            balance_hora = ahorro_hora - coste_carga
            ahorro_acumulado_mes += balance_hora
            historial_soc.append(soc)

        # Fin del mes
        resultados_mes.append({
            'Mes': nombre,
            'Ahorro_Eur': round(ahorro_acumulado_mes, 2),
            'Consumo_Total': int(mes['consumo_total_kwh']),
            'Precio_Punta': mes['precio_punta'],
            'Precio_Valle': mes['precio_valle']
        })
        ahorro_total += ahorro_acumulado_mes

    # --- 3. RESULTADOS Y VISUALIZACIÓN ---
    df_res = pd.DataFrame(resultados_mes)
    
    print("\nRESULTADOS POR PERIODO:")
    print(df_res[['Mes', 'Consumo_Total', 'Precio_Punta', 'Ahorro_Eur']].to_string(index=False))
    print("-" * 60)
    print(f"AHORRO TOTAL ({len(datos_facturas)} meses): {ahorro_total:,.2f} €")
    
    # Proyección anual simple (x3 si son 4 meses)
    factor_anual = 12 / len(datos_facturas)
    proyeccion = ahorro_total * factor_anual
    print(f"PROYECCIÓN AHORRO ANUAL:       {proyeccion:,.2f} €")
    
    roi_years = 30000 / proyeccion if proyeccion > 0 else 999
    print(f"Retorno Inversión (Est. 30k€):   {roi_years:.1f} años")
    print("-" * 60)

    # --- GENERAR GRÁFICA (COMPATIBLE CON DOCKER) ---
    plt.figure(figsize=(10, 6))
    plt.bar(df_res['Mes'], df_res['Ahorro_Eur'], color='#4CAF50', edgecolor='black')
    
    plt.title(f'Ahorro Estimado - Batería {cap_bat}kWh (Cliente: Bar de Jimmy)', fontsize=14)
    plt.ylabel('Ahorro Neto (€)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Añadir etiquetas de valor en las barras
    for i, v in enumerate(df_res['Ahorro_Eur']):
        plt.text(i, v + 1, f"{v:.0f}€", ha='center', fontweight='bold')

    # Guardado seguro en Docker
    output_dir = '/app/resultados'
    
    # Si no estamos en Docker (ej. ejecución local), guardamos en carpeta local
    if not os.path.exists('/app'):
        output_dir = 'resultados'
        
    os.makedirs(output_dir, exist_ok=True)
    ruta_fichero = os.path.join(output_dir, 'grafica_ahorro.png')
    
    plt.savefig(ruta_fichero)
    print(f"\n[INFO] Gráfica guardada exitosamente en: {ruta_fichero}")

# --- DATOS REALES DE LAS FACTURAS ---
datos_reales_cliente = [
    {
        'mes': 'Mar-Abr', # Factura Primavera (Excedente alto, consumo bajo)
        'consumo_total_kwh': 2955, 
        'excedente_total_kwh': 1940,
        'precio_valle': 0.092,  # P6 Real
        'precio_punta': 0.129,  # P4 (Punta relativa)
        'precio_venta_excedente': 0.10
    },
    {
        'mes': 'Abr-May', 
        'consumo_total_kwh': 3397, 
        'excedente_total_kwh': 1708,
        'precio_valle': 0.092, # Asumimos similar anterior
        'precio_punta': 0.130, 
        'precio_venta_excedente': 0.10
    },
    {
        'mes': 'May-Jun', # Empieza el calor
        'consumo_total_kwh': 5891, 
        'excedente_total_kwh': 1352,
        'precio_valle': 0.130, # P6 (Sube precio)
        'precio_punta': 0.172, # P3
        'precio_venta_excedente': 0.10
    },
    {
        'mes': 'Jun-Jul', # Verano a tope
        'consumo_total_kwh': 6563, 
        'excedente_total_kwh': 1399,
        'precio_valle': 0.131, # P6 Caro
        'precio_punta': 0.180, # P1 Muy caro
        'precio_venta_excedente': 0.10
    }
]

if __name__ == "__main__":
    # Ejecutamos la simulación
    simular_arbitraje_y_solar(datos_reales_cliente)