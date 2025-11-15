import streamlit as st
import pandas as pd
import os
from datetime import date
import altair as alt

# --- Configuración de Archivos de Datos ---
DATA_FILE_LECHE = 'data_leche.csv'
DATA_FILE_GASOLINA = 'data_gasolina.csv'
DATA_FILE_GANADO = 'data_ganado.csv'

# =================================================================
# 1. FUNCIONES DE CARGA Y GUARDADO OPTIMIZADAS CON CACHÉ
# =================================================================

# Usamos @st.cache_data para que Streamlit solo lea el archivo CSV una vez,
# a menos que se fuerce la limpieza del caché (cache_data.clear()).

@st.cache_data(show_spinner=False)
def load_data_leche():
    if os.path.exists(DATA_FILE_LECHE):
        # Asegurar la columna de fecha
        df = pd.read_csv(DATA_FILE_LECHE, parse_dates=['Fecha'])
        return df
    else:
        return pd.DataFrame(columns=[
            'Fecha', 'ID_Lote', 'Vol_Entregado', 'Vol_Pesado', 'Vol_Vendido',
            'Perdida_Pesaje', 'Perdida_Venta', 'Perdida_Total'
        ])

@st.cache_data(show_spinner=False)
def load_data_gasolina():
    if os.path.exists(DATA_FILE_GASOLINA):
        # Asegurar la columna de fecha
        df = pd.read_csv(DATA_FILE_GASOLINA, parse_dates=['Fecha'])
        return df
    else:
        return pd.DataFrame(columns=[
            'Fecha', 'ID_Ruta', 'Litros_Cargados', 'Costo_Litro',
            'Km_Recorridos', 'Gasto_Total', 'Eficiencia_Km_Litro'
        ])

@st.cache_data(show_spinner=False)
def load_data_ganado():
    if os.path.exists(DATA_FILE_GANADO):
        # Asegurar la columna de fecha
        df = pd.read_csv(DATA_FILE_GANADO, parse_dates=['Fecha'])
        return df
    else:
        return pd.DataFrame(columns=[
            'Fecha', 'ID_Animal', 'Nombre_Animal', 'Raza', 'Litros_Pesados'
        ])

# Función para guardar datos, limpiar el caché y forzar la recarga
def save_data_and_rerun(df, filename):
    df.to_csv(filename, index=False)
    
    # Limpiar el caché específico
    if filename == DATA_FILE_LECHE:
        load_data_leche.clear()
    elif filename == DATA_FILE_GASOLINA:
        load_data_gasolina.clear()
    elif filename == DATA_FILE_GANADO:
        load_data_ganado.clear()
        
    st.experimental_rerun()

# --- Carga Inicial de DataFrames (usando las funciones con caché) ---
df_leche = load_data_leche()
df_gasolina = load_data_gasolina()
df_ganado = load_data_ganado()

# --- Diseño de la Aplicación con Streamlit ---
st.set_page_config(layout="wide", page_title="App Interna Agroindustrial")
st.title("🥛 Asistente de Control Operativo Agroindustrial")
st.markdown("---")

# Crea las pestañas
tab_leche, tab_ganado, tab_gasolina = st.tabs([
    "🥛 Trazabilidad de la Leche",
    "🐄 Inventario de Ganado",
    "⛽ Control de Combustible"
])

# =================================================================
# MÓDULO 1: TRAZABILIDAD DE LA LECHE
# =================================================================
with tab_leche:
    st.header("Análisis de Pérdidas de Leche por Trazabilidad")

    # --- Formulario de Registro ---
    with st.form("registro_leche"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_registro = st.date_input("Fecha de Registro", date.today())
            id_lote = st.text_input("ID o Nombre del Lote/Ruta", key="id_lote_leche")

        with col2:
            vol_entregado = st.number_input("1. Volumen ENTREGADO (Litros)", min_value=0.0, format="%.2f")
            vol_pesado = st.number_input("2. Volumen PESADO (Litros)", min_value=0.0, format="%.2f")
            vol_vendido = st.number_input("3. Volumen VENDIDO (Litros)", min_value=0.0, format="%.2f")

        submitted = st.form_submit_button("Registrar Lote y Calcular Pérdidas")

        if submitted:
            if vol_pesado > vol_entregado or vol_vendido > vol_pesado:
                st.error("🚨 Error de datos: El volumen pesado no puede ser mayor al entregado, ni el vendido mayor al pesado.")
            elif id_lote == "":
                st.error("🚨 El ID o Nombre del Lote es obligatorio.")
            else:
                # Ya no se necesita 'global df_leche' aquí porque df_leche se está reasignando
                # en el nivel superior y se pasa a la función de guardado. 
                # Simplemente creamos una copia local para la modificación.
                df_leche_local = df_leche.copy()

                perdida_pesaje = vol_entregado - vol_pesado
                perdida_venta = vol_pesado - vol_vendido
                perdida_total = vol_entregado - vol_vendido

                new_row = pd.DataFrame([{
                    # Convertir a datetime para asegurar la compatibilidad con el DF
                    'Fecha': pd.to_datetime(fecha_registro), 
                    'ID_Lote': id_lote,
                    'Vol_Entregado': vol_entregado,
                    'Vol_Pesado': vol_pesado,
                    'Vol_Vendido': vol_vendido,
                    'Perdida_Pesaje': perdida_pesaje,
                    'Perdida_Venta': perdida_venta,
                    'Perdida_Total': perdida_total
                }])

                df_leche_nuevo = pd.concat([df_leche_local, new_row], ignore_index=True)
                save_data_and_rerun(df_leche_nuevo, DATA_FILE_LECHE)

                st.success(f"✅ Lote **{id_lote}** registrado con éxito.")

                st.subheader("Resultados de Pérdida para este Lote")
                colA, colB, colC = st.columns(3)
                colA.metric("Pérdida 1 (Entrega → Pesaje)", f"{perdida_pesaje:.2f} Litros", delta_color="inverse")
                colB.metric("Pérdida 2 (Pesaje → Venta)", f"{perdida_venta:.2f} Litros", delta_color="inverse")
                colC.metric("Pérdida TOTAL", f"{perdida_total:.2f} Litros", delta_color="inverse")

    st.markdown("---")

    # --- Sección de Reportes y Gráficos ---
    if not df_leche.empty:
        st.subheader("📊 Análisis de Tendencia de Pérdidas Totales")

        # Asegurar que 'Fecha' es el tipo correcto para Altair
        df_chart = df_leche.copy()
        df_chart['Fecha'] = pd.to_datetime(df_chart['Fecha'])
        df_chart_grouped = df_chart.groupby(df_chart['Fecha'].dt.date)['Perdida_Total'].sum().reset_index()
        df_chart_grouped['Fecha'] = pd.to_datetime(df_chart_grouped['Fecha']) # Volver a convertir para Altair

        chart = alt.Chart(df_chart_grouped).mark_line(point=True).encode(
            x=alt.X('Fecha', title='Fecha'),
            y=alt.Y('Perdida_Total', title='Pérdida Total (Litros)'),
            tooltip=['Fecha', alt.Tooltip('Perdida_Total', format='.2f')]
        ).properties(
            title='Pérdida Total de Leche a lo largo del Tiempo'
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

        st.subheader("Historial Detallado de Lotes Registrados")
        columnas_mostrar = ['Fecha', 'ID_Lote', 'Vol_Entregado', 'Vol_Pesado', 'Vol_Vendido',
                            'Perdida_Pesaje', 'Perdida_Venta', 'Perdida_Total']

        df_leche_display = df_leche.reset_index().rename(columns={'index': 'ID_Fila'})
        st.dataframe(df_leche_display[['ID_Fila'] + columnas_mostrar].sort_values(by='Fecha', ascending=False), use_container_width=True)

        # --- Sección de Borrado ---
        st.markdown("### 🗑️ Borrar Registros")

        rows_to_delete = st.multiselect(
            "Selecciona el ID de Fila(s) a eliminar del historial de Leche:",
            options=df_leche_display['ID_Fila'].tolist(),
            key='delete_leche_key'
        )

        if st.button("Eliminar Registros Seleccionados (Leche)", key='btn_delete_leche'):
            if rows_to_delete:
                indices_to_delete = df_leche_display[df_leche_display['ID_Fila'].isin(rows_to_delete)].index

                df_leche_nuevo = df_leche.drop(indices_to_delete, axis=0).reset_index(drop=True)

                st.warning(f"Se eliminaron {len(rows_to_delete)} registro(s) de leche.")
                save_data_and_rerun(df_leche_nuevo, DATA_FILE_LECHE)
            else:
                st.info("No hay filas seleccionadas para eliminar.")

    else:
        st.info("Aún no hay datos de trazabilidad de leche registrados.")


# =================================================================
# MÓDULO 2: INVENTARIO DE GANADO
# =================================================================
with tab_ganado:
    st.header("🐄 Registro de Producción Individual de Ganado")

    tab_registro_ganado, tab_analisis_ganado, tab_borrado_ganado = st.tabs(["Registro Diario", "Análisis de Productividad", "🗑️ Borrar Datos"])

    with tab_registro_ganado:
        with st.form("registro_ganado"):
            colG1, colG2 = st.columns(2)

            with colG1:
                fecha_pesaje = st.date_input("Fecha de Pesaje", date.today(), key="fecha_pesaje")
                id_animal = st.text_input("ID Único del Animal (Tatuaje/Chip)", key="id_animal")

            with colG2:
                last_name = ""
                last_raza = 'Holstein'
                if id_animal and not df_ganado.empty:
                    animal_data = df_ganado[df_ganado['ID_Animal'] == id_animal]
                    if not animal_data.empty:
                        # Aseguramos que tomamos la última raza y nombre registrados
                        last_name = animal_data['Nombre_Animal'].iloc[-1] if 'Nombre_Animal' in animal_data.columns else ""
                        last_raza = animal_data['Raza'].iloc[-1] if 'Raza' in animal_data.columns else 'Holstein'

                raza_options = ['Holstein', 'Jersey', 'Pardo Suizo', 'Gyr', 'Otra']
                raza_index = raza_options.index(last_raza) if last_raza in raza_options else 4

                nombre_animal = st.text_input("Nombre del Animal", value=last_name, key="nombre_animal")
                raza_animal = st.selectbox("Raza del Animal", options=raza_options, index=raza_index, key="raza_animal")

            litros_pesados = st.number_input("Litros de Leche Pesados Hoy", min_value=0.0, format="%.2f", key="litros_pesados")

            submitted_ganado = st.form_submit_button("Registrar Pesaje del Animal")

            if submitted_ganado:
                if id_animal == "":
                    st.error("🚨 El ID Único del Animal es obligatorio.")
                else:
                    df_ganado_local = df_ganado.copy()

                    new_row_ganado = pd.DataFrame([{
                        'Fecha': pd.to_datetime(fecha_pesaje),
                        'ID_Animal': id_animal,
                        'Nombre_Animal': nombre_animal,
                        'Raza': raza_animal,
                        'Litros_Pesados': litros_pesados
                    }])

                    df_ganado_nuevo = pd.concat([df_ganado_local, new_row_ganado], ignore_index=True)
                    save_data_and_rerun(df_ganado_nuevo, DATA_FILE_GANADO)

                    st.success(f"✅ Pesaje de **{nombre_animal}** ({id_animal}) registrado con éxito.")

    with tab_analisis_ganado:
        st.subheader("Historial y Productividad Media")
        if not df_ganado.empty:

            produccion_media = df_ganado.groupby('ID_Animal').agg(
                Nombre=('Nombre_Animal', 'last'),
                Raza=('Raza', 'last'),
                Total_Pesado=('Litros_Pesados', 'sum'),
                Promedio_Diario=('Litros_Pesados', 'mean'),
                Total_Registros=('Litros_Pesados', 'count')
            ).reset_index().sort_values(by='Promedio_Diario', ascending=False)

            st.markdown("### 📈 Top 10 Productores (Promedio Diario)")

            chart_ganado = alt.Chart(produccion_media.head(10)).mark_bar().encode(
                x=alt.X('Promedio_Diario', title='Promedio Diario (Litros)'),
                y=alt.Y('Nombre', sort='-x', title='Animal'),
                color='Raza',
                tooltip=['Nombre', 'Raza', alt.Tooltip('Promedio_Diario', format='.2f')]
            ).properties(
                title='Productividad Promedio por Animal (Top 10)'
            )
            st.altair_chart(chart_ganado, use_container_width=True)

            produccion_media['Promedio_Diario'] = produccion_media['Promedio_Diario'].map('{:.2f} L'.format)
            produccion_media['Total_Pesado'] = produccion_media['Total_Pesado'].map('{:.2f} L'.format)

            st.markdown("---")
            st.subheader("Tabla de Productividad")
            st.dataframe(produccion_media, use_container_width=True)

        else:
            st.info("Aún no hay datos de pesaje individual de ganado registrados.")

    with tab_borrado_ganado:
        st.subheader("🗑️ Borrar Registros de Pesaje Individual")
        if not df_ganado.empty:
            df_ganado_display = df_ganado.reset_index().rename(columns={'index': 'ID_Fila'})

            st.dataframe(df_ganado_display[['ID_Fila', 'Fecha', 'ID_Animal', 'Nombre_Animal', 'Litros_Pesados']].sort_values(by='Fecha', ascending=False), use_container_width=True)

            rows_to_delete_ganado = st.multiselect(
                "Selecciona el ID de Fila(s) a eliminar del historial de Ganado:",
                options=df_ganado_display['ID_Fila'].tolist(),
                key='delete_ganado_key'
            )

            if st.button("Eliminar Registros Seleccionados (Ganado)", key='btn_delete_ganado'):
                if rows_to_delete_ganado:
                    indices_to_delete_ganado = df_ganado_display[df_ganado_display['ID_Fila'].isin(rows_to_delete_ganado)].index

                    df_ganado_nuevo = df_ganado.drop(indices_to_delete_ganado, axis=0).reset_index(drop=True)

                    st.warning(f"Se eliminaron {len(rows_to_delete_ganado)} registro(s) de ganado.")
                    save_data_and_rerun(df_ganado_nuevo, DATA_FILE_GANADO)
                else:
                    st.info("No hay filas seleccionadas para eliminar.")
        else:
            st.info("No hay datos para borrar.")

# =================================================================
# MÓDULO 3: CONTROL DE COMBUSTIBLE
# =================================================================
with tab_gasolina:
    st.header("⛽ Registro y Verificación de Consumo de Combustible")

    tab_registro_gasolina, tab_analisis_gasolina, tab_borrado_gasolina = st.tabs(["Registro de Carga", "Análisis de Eficiencia", "🗑️ Borrar Datos"])

    with tab_registro_gasolina:
        with st.form("registro_gasolina"):
            st.subheader("Datos de Carga de Combustible")

            colG1, colG2, colG3 = st.columns(3)
            with colG1:
                fecha_gasolina = st.date_input("Fecha de Carga", date.today(), key="fecha_gasolina")
                id_ruta = st.text_input("ID o Nombre de la Ruta/Lote", key="id_ruta_key")

            with colG2:
                litros_cargados = st.number_input("Litros Cargados", min_value=0.0, format="%.2f", key="litros_cargados")
                km_recorridos = st.number_input("Kilómetros Recorridos", min_value=0.0, format="%.2f", key="km_recorridos")

            with colG3:
                costo_litro = st.number_input("Costo por Litro (Moneda local)", min_value=0.0, format="%.2f", key="costo_litro")

                gasto_total_calc = litros_cargados * costo_litro
                st.markdown(f"**Gasto Total Estimado:** **${gasto_total_calc:.2f}**")


            submitted_gasolina = st.form_submit_button("Registrar Consumo y Calcular Eficiencia")

            if submitted_gasolina:
                if id_ruta == "":
                    st.error("🚨 El ID de la Ruta es obligatorio para el seguimiento.")
                elif km_recorridos == 0 and litros_cargados > 0:
                     st.error("🚨 Los Kilómetros Recorridos deben ser mayores a cero para calcular la eficiencia si se cargó combustible.")
                elif litros_cargados == 0 and km_recorridos > 0:
                     st.error("🚨 Se requiere cargar litros para calcular la eficiencia del recorrido.")
                else:
                    gasto_total = litros_cargados * costo_litro
                    # Manejar división por cero en caso de que litros_cargados sea 0 (aunque el form ya tiene min_value)
                    eficiencia = km_recorridos / litros_cargados if litros_cargados > 0 else 0

                    df_gasolina_local = df_gasolina.copy()

                    new_row_gasolina = pd.DataFrame([{
                        'Fecha': pd.to_datetime(fecha_gasolina),
                        'ID_Ruta': id_ruta,
                        'Litros_Cargados': litros_cargados,
                        'Costo_Litro': costo_litro,
                        'Km_Recorridos': km_recorridos,
                        'Gasto_Total': gasto_total,
                        'Eficiencia_Km_Litro': eficiencia
                    }])

                    df_gasolina_nuevo = pd.concat([df_gasolina_local, new_row_gasolina], ignore_index=True)
                    save_data_and_rerun(df_gasolina_nuevo, DATA_FILE_GASOLINA)

                    st.success(f"✅ Consumo para la Ruta **{id_ruta}** registrado con éxito.")

                    st.subheader("Métricas Clave de la Ruta")
                    colE1, colE2 = st.columns(2)
                    colE1.metric(
                        "Gasto Total",
                        f"${gasto_total:.2f}",
                        "Costo total del viaje"
                    )
                    colE2.metric(
                        "Eficiencia (Km/Litro)",
                        f"{eficiencia:.2f} Km/L",
                        "Métrica de control para evitar robo"
                    )

    with tab_analisis_gasolina:
        st.subheader("📊 Análisis de Eficiencia por Ruta")
        if not df_gasolina.empty:
            
            # Asegurar que 'Fecha' es el tipo correcto para Altair
            df_chart = df_gasolina.copy()
            df_chart['Fecha'] = pd.to_datetime(df_chart['Fecha'])

            st.markdown("### Tendencia de Eficiencia (Km/L) por Carga")
            chart_gas = alt.Chart(df_chart).mark_line(point=True).encode(
                x=alt.X('Fecha', title='Fecha de Carga'),
                y=alt.Y('Eficiencia_Km_Litro', title='Eficiencia (Km/Litro)'),
                color='ID_Ruta',
                tooltip=['Fecha', 'ID_Ruta', alt.Tooltip('Eficiencia_Km_Litro', format='.2f')]
            ).properties(
                title='Eficiencia de Combustible a lo largo del Tiempo'
            ).interactive()

            st.altair_chart(chart_gas, use_container_width=True)

            st.markdown("---")
            st.subheader("Historial Detallado de Consumo")
            columnas_mostrar_gas = ['Fecha', 'ID_Ruta', 'Litros_Cargados', 'Costo_Litro',
                                    'Km_Recorridos', 'Gasto_Total', 'Eficiencia_Km_Litro']
            st.dataframe(df_gasolina[columnas_mostrar_gas].sort_values(by='Fecha', ascending=False), use_container_width=True)
        else:
            st.info("Aún no hay datos de consumo de combustible registrados.")

    with tab_borrado_gasolina:
        st.subheader("🗑️ Borrar Registros de Combustible")
        if not df_gasolina.empty:
            df_gasolina_display = df_gasolina.reset_index().rename(columns={'index': 'ID_Fila'})

            st.dataframe(df_gasolina_display[['ID_Fila', 'Fecha', 'ID_Ruta', 'Gasto_Total', 'Eficiencia_Km_Litro']].sort_values(by='Fecha', ascending=False), use_container_width=True)

            rows_to_delete_gasolina = st.multiselect(
                "Selecciona el ID de Fila(s) a eliminar del historial de Combustible:",
                options=df_gasolina_display['ID_Fila'].tolist(),
                key='delete_gasolina_key'
            )

            if st.button("Eliminar Registros Seleccionados (Combustible)", key='btn_delete_gasolina'):
                if rows_to_delete_gasolina:
                    indices_to_delete_gasolina = df_gasolina_display[df_gasolina_display['ID_Fila'].isin(rows_to_delete_gasolina)].index

                    df_gasolina_nuevo = df_gasolina.drop(indices_to_delete_gasolina, axis=0).reset_index(drop=True)

                    st.warning(f"Se eliminaron {len(rows_to_delete_gasolina)} registro(s) de combustible.")
                    save_data_and_rerun(df_gasolina_nuevo, DATA_FILE_GASOLINA)
                else:
                    st.info("No hay filas seleccionadas para eliminar.")
        else:
            st.info("No hay datos para borrar.")
