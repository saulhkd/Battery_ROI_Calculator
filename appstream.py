import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Simulador Baterías Industrial",
    page_icon="🔋",
    layout="wide"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    .big-font { font-size: 24px !important; font-weight: bold; color: #2E7D32; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE SIMULACIÓN (MOTOR MATEMÁTICO) ---
@st.cache_data # Cacheamos para que no recalcule si no cambias los inputs
def ejecutar_simulacion(datos_df, cap_bat, pot_bat, eficiencia, precio_excedente):
    
    resultados_mensuales = []
    detalle_horario_ejemplo = None # Guardaremos un mes para ver el detalle hora a hora
    ahorro_total = 0
    
    # Iteramos por cada fila del editor de datos
    for index, row in datos_df.iterrows():
        nombre = row['Mes']
        dias = 30
        horas_totales = dias * 24
        
        # 1. GENERAR PERFIL SINTÉTICO (Igual que en el script anterior)
        df = pd.DataFrame(index=range(horas_totales))
        df['hora_dia'] = df.index % 24
        
        # Perfil Consumo Hostelería 
        condiciones = [
            (df['hora_dia'] < 8),
            (df['hora_dia'] >= 8) & (df['hora_dia'] < 12),
            (df['hora_dia'] >= 12) & (df['hora_dia'] < 17),
            (df['hora_dia'] >= 17) & (df['hora_dia'] < 20),
            (df['hora_dia'] >= 20)
        ]
        pesos = [0.4, 0.8, 2.0, 0.8, 1.2] 
        df['perfil_base'] = np.select(condiciones, pesos)
        
        factor_cons = row['Consumo (kWh)'] / df['perfil_base'].sum()
        df['consumo_kwh'] = df['perfil_base'] * factor_cons
        
        # Perfil Solar
        df['perfil_solar'] = np.where(
            (df['hora_dia'] > 7) & (df['hora_dia'] < 20),
            np.sin((df['hora_dia'] - 7) * np.pi / 13), 0
        )
        factor_solar = row['Excedente (kWh)'] / df['perfil_solar'].sum() if df['perfil_solar'].sum() > 0 else 0
        df['solar_kwh'] = df['perfil_solar'] * factor_solar
        
        # Precios (Simulamos tarifa con discriminación horaria simple)
        df['precio_compra'] = np.where(df['hora_dia'] < 8, row['Precio Valle (€)'], row['Precio Punta (€)'])
        df['es_valle'] = df['hora_dia'] < 8
        
        # 2. SIMULACIÓN BATERÍA
        soc = 0.0
        ahorro_mes = 0.0
        lista_soc = []
        lista_ahorro_hora = []
        
        for i in range(len(df)):
            cons = df.loc[i, 'consumo_kwh']
            solar = df.loc[i, 'solar_kwh']
            precio_actual = df.loc[i, 'precio_compra']
            es_valle = df.loc[i, 'es_valle']
            
            energia_entrada = 0.0
            coste_carga = 0.0
            
            # A) Carga Solar
            if solar > 0:
                espacio = cap_bat - soc
                carga = min(solar, espacio, pot_bat)
                soc += carga * np.sqrt(eficiencia)
                coste_carga += carga * precio_excedente # Coste oportunidad
                energia_entrada += carga
            
            # B) Carga Red (Arbitraje)
            if es_valle and solar == 0:
                espacio = cap_bat - soc
                # Margen mínimo para operar (Spread)
                precio_salida_real = row['Precio Valle (€)'] / (eficiencia)
                margen = row['Precio Punta (€)'] - precio_salida_real
                
                if margen > 0.02 and espacio > 0: # Si ganamos >2 céntimos
                    carga = min(espacio, pot_bat)
                    soc += carga * np.sqrt(eficiencia)
                    coste_carga += carga * row['Precio Valle (€)']
                    energia_entrada += carga
            
            # C) Descarga (Ahorro)
            ahorro_bruto = 0.0
            if not es_valle and soc > 0 and cons > 0:
                energia_disponible_ac = soc * np.sqrt(eficiencia)
                descarga = min(cons, energia_disponible_ac, pot_bat)
                
                soc -= descarga / np.sqrt(eficiencia)
                ahorro_bruto = descarga * precio_actual
            
            balance = ahorro_bruto - coste_carga
            ahorro_mes += balance
            lista_soc.append(soc)
            lista_ahorro_hora.append(balance)
            
        resultados_mensuales.append({
            'Mes': nombre,
            'Ahorro (€)': round(ahorro_mes, 2),
            'Consumo Red (kWh)': int(row['Consumo (kWh)']),
            'Excedente FV (kWh)': int(row['Excedente (kWh)'])
        })
        ahorro_total += ahorro_mes
        
        # Guardamos el último mes completo para graficar detalle
        df['soc'] = lista_soc
        df['ahorro_acum'] = np.cumsum(lista_ahorro_hora)
        detalle_horario_ejemplo = df
        
    return pd.DataFrame(resultados_mensuales), ahorro_total, detalle_horario_ejemplo

# --- INTERFAZ DE USUARIO ---

# Sidebar: Configuración
with st.sidebar:
    st.header("⚙️ Configuración del Sistema")
    capacidad = st.number_input("Capacidad Batería (kWh)", value=100, step=10)
    potencia = st.number_input("Potencia Inversor (kW)", value=50, step=5)
    eficiencia = st.slider("Eficiencia Global (%)", 80, 100, 90) / 100
    
    st.divider()
    st.header("💰 Datos Económicos")
    inversion = st.number_input("Coste Instalación (€)", value=30000, step=1000)
    precio_excedente = st.number_input("Precio Venta Excedente (€/kWh)", value=0.10, format="%.3f")
    
    # st.info("💡 Consejo: Prueba a bajar el 'Precio Valle' en la tabla de datos a 0.05€ para simular una tarifa Indexada.")

# Título Principal
st.title("🔋 Simulador rentabilidad baterías **V2C Power**")
st.markdown("**Cliente:** ____________ | **Estrategia:** Solar + Arbitraje")

# Sección 1: Datos de Entrada (Editables)
st.subheader("1. Datos de facturación (Mensuales)")

# Datos iniciales (Cargados de tus facturas)
datos_iniciales = pd.DataFrame([
    {'Mes': '1', 'Consumo (kWh)': 2955, 'Excedente (kWh)': 1940, 'Precio Valle (€)': 0.092, 'Precio Punta (€)': 0.129},
    {'Mes': '2', 'Consumo (kWh)': 3397, 'Excedente (kWh)': 1708, 'Precio Valle (€)': 0.092, 'Precio Punta (€)': 0.130},
    {'Mes': '3', 'Consumo (kWh)': 5891, 'Excedente (kWh)': 1352, 'Precio Valle (€)': 0.130, 'Precio Punta (€)': 0.172},
    {'Mes': '4', 'Consumo (kWh)': 6563, 'Excedente (kWh)': 1399, 'Precio Valle (€)': 0.131, 'Precio Punta (€)': 0.180},
])

# Editor interactivo
df_input = st.data_editor(datos_iniciales, num_rows="dynamic", use_container_width=True)

# Botón de Cálculo
if st.button("🚀 Calcular rentabilidad", type="primary"):
    
    # Ejecutar lógica
    df_resultados, ahorro_total, df_detalle = ejecutar_simulacion(
        df_input, capacidad, potencia, eficiencia, precio_excedente
    )
    
    # Proyecciones
    meses_simulados = len(df_input)
    ahorro_anual_est = (ahorro_total / meses_simulados) * 12
    roi_years = inversion / ahorro_anual_est if ahorro_anual_est > 0 else 999
    
    st.divider()
    
    # Sección 2: KPIs Principales
    st.subheader("2. Resultados económicos")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Ahorro total (Periodo)", f"{ahorro_total:,.2f} €", delta="Simulado")
    col2.metric("Proyección ahorro anual", f"{ahorro_anual_est:,.2f} €", delta_color="normal")
    col3.metric("Retorno Inversión (ROI)", f"{roi_years:.1f} Años", delta=f"- Coste: {inversion/1000}k€", delta_color="inverse")
    
    if roi_years > 10:
        st.warning("⚠️ **Atención:** El retorno es superior a 10 años. Revisa si la diferencia entre Precio Valle y Punta es suficiente para el arbitraje. **Simula una tarifa Indexada (Valle ~0.05€).**")
    else:
        st.success("✅ **Proyecto viable:** El retorno está dentro de parámetros rentables.")

    # Sección 3: Gráficas
    st.subheader("3. Análisis Visual")
    
    tab1, tab2 = st.tabs(["📊 Ahorro Mensual", "📈 Detalle Operación (48h)"])
    
    with tab1:
        st.bar_chart(df_resultados, x="Mes", y="Ahorro (€)", color="#4CAF50")
        st.dataframe(df_resultados, use_container_width=True)
        
    with tab2:
        st.write("Visualización del comportamiento de la batería durante 2 días tipo (Verano/Alta demanda).")
        
        # Filtramos solo 48 horas del detalle para que se vea bien
        subset = df_detalle.iloc[240:288] # Unas 48h del medio del mes
        
        fig, ax1 = plt.subplots(figsize=(10, 4))
        
        # Eje Y1: Precios y SOC
        ax1.set_xlabel('Hora Simulada')
        ax1.set_ylabel('Carga Batería (kWh)', color='green')
        line1 = ax1.plot(subset['soc'], color='green', label='SOC Batería (kWh)', linewidth=2)
        ax1.tick_params(axis='y', labelcolor='green')
        ax1.set_ylim(0, capacidad * 1.1)
        
        # Eje Y2: Precios
        ax2 = ax1.twinx()
        ax2.set_ylabel('Precio Luz (€/kWh)', color='red')
        line2 = ax2.plot(subset['precio_compra'], color='red', linestyle='--', label='Precio Luz', alpha=0.5)
        ax2.tick_params(axis='y', labelcolor='red')
        
        # Relleno para visualizar zonas de carga/descarga
        ax2.fill_between(subset.index, 0, subset['precio_compra'], color='red', alpha=0.1)
        
        # Leyenda combinada
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        st.pyplot(fig)
        st.caption("Observa cómo la línea verde (Batería) sube cuando la línea roja punteada (Precio) es baja (Carga nocturna) o cuando hay sol, y baja cuando el precio es alto.")

else:
    st.info("Modifica los datos en la tabla de arriba y pulsa 'Calcular' para ver los resultados.")