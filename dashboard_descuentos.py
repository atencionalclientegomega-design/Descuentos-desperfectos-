import re
import streamlit as st
import pandas as pd
import plotly.express as px


# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Dashboard Descuentos Estéticos",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# ESTILOS CSS
# ============================================================

st.markdown("""
<style>

    .stApp {
        background-color: #F5F7FA;
    }

    .titulo-dashboard {
        font-size: 30px;
        font-weight: 700;
        color: #1F3556;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitulo-dashboard {
        font-size: 17px;
        color: #6B7280;
        text-align: center;
        margin-bottom: 25px;
    }

    .kpi-card {
        background-color: white;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
        border: 1px solid #E5E7EB;
        min-height: 140px;
    }

    .kpi-title {
        font-size: 14px;
        color: #6B7280;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #1F3556;
    }

    .kpi-subtitle {
        font-size: 12px;
        color: #9CA3AF;
        margin-top: 5px;
    }

   .section-title {
    background-color: #1F3556;
    color: white;
    padding: 10px;
    border-radius: 8px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 15px;
}

    .info-box {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        text-align: center;
        margin-bottom: 10px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNCIÓN PARA LIMPIAR TEXTO Y CARACTERES DE EXCEL
# ============================================================

def limpiar_texto(valor):
    if pd.isna(valor):
        return valor
    texto = str(valor)
    texto = re.sub(r'_x[0-9a-fA-F]{4}_', '', texto)
    return texto.replace('\r', '').replace('\n', '').strip()


# ============================================================
# FUNCIÓN PARA CONVERTIR NÚMEROS
# ============================================================

def convertir_numero(valor):

    if pd.isna(valor):
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    valor = str(valor).strip()

    valor = valor.replace("$", "")
    valor = valor.replace("%", "")
    valor = valor.replace(" ", "")

    try:
        if "," in valor and "." in valor:
            if valor.rfind(",") > valor.rfind("."):
                valor = valor.replace(".", "")
                valor = valor.replace(",", ".")
            else:
                valor = valor.replace(",", "")
        elif "," in valor:
            valor = valor.replace(",", ".")

        return float(valor)
    except:
        return 0.0


# ============================================================
# CARGAR Y UNIFICAR DATOS HISTÓRICOS
# ============================================================

@st.cache_data
def cargar_datos():

    archivo = "historico_descuentos.xlsx"

    try:
        hojas = pd.read_excel(
            archivo,
            sheet_name=None
        )
    except Exception as e:
        st.error(
            f"Error al leer el archivo Excel: {e}"
        )
        st.stop()

    lista_dataframes = []

    for nombre_hoja, df_mes in hojas.items():

        df_mes.columns = (
            df_mes.columns
            .astype(str)
            .str.strip()
        )

        df_mes = df_mes.dropna(how="all")
        df_mes["Periodo"] = f"{nombre_hoja} 2026"

        if "Cliente" in df_mes.columns:
            df_mes = df_mes[
                ~df_mes["Cliente"]
                .astype(str)
                .str.upper()
                .str.contains("TOTAL", na=False)
            ]

        if "Código Producto" in df_mes.columns:
            df_mes = df_mes[
                df_mes["Código Producto"]
                .astype(str)
                .str.strip()
                .str.upper()
                != "CÓDIGO PRODUCTO"
            ]

            df_mes = df_mes[
                df_mes["Código Producto"].notna()
            ]

        lista_dataframes.append(df_mes)

    if not lista_dataframes:
        st.error(
            "No se encontraron datos en las pestañas."
        )
        st.stop()

    # 1. Crear 'df' unificando los meses
    df = pd.concat(
        lista_dataframes,
        ignore_index=True
    )

    # 2. Limpieza de sufijos y caracteres especiales en columnas de texto
    columnas_texto = df.select_dtypes(include=['object']).columns
    for col in columnas_texto:
        df[col] = df[col].apply(limpiar_texto)

    # 3. Conversión de columnas numéricas
    columnas_numericas = [
        "Despachado",
        "Precio Facturado",
        "Precio Negociado",
        "Ajuste Und",
        "Total Ajuste",
        "Descuento"
    ]

    for columna in columnas_numericas:
        if columna in df.columns:
            df[columna] = (
                df[columna]
                .apply(convertir_numero)
            )

    if "Despachado" in df.columns:
        df = df[
            df["Despachado"] > 0
        ]

    df = df.reset_index(drop=True)

    return df


# ============================================================
# CARGAR DATAFRAME
# ============================================================

df = cargar_datos()

# ============================================================
# FILTROS HISTÓRICOS
# ============================================================

if "Periodo" not in df.columns:
    st.error(
        "No se encontró la columna 'Periodo' en el archivo historico_descuentos.xlsx"
    )
    st.stop()

df["Periodo"] = (
    df["Periodo"]
    .astype(str)
    .str.strip()
)

periodos = sorted(
    df["Periodo"]
    .dropna()
    .unique()
)


# ============================================================
# PANEL DE FILTROS
# ============================================================

st.markdown(r"### 📍 ")


filtro1, filtro2, filtro3, filtro4, filtro5 = st.columns(5)


# ------------------------------------------------------------
# FILTRO PERÍODO
# ------------------------------------------------------------

with filtro1:
    periodo_seleccionado = st.selectbox(
        "📅 Período",
        ["Todos"] + list(periodos)
    )


# ------------------------------------------------------------
# FILTRO NIVEL
# ------------------------------------------------------------

with filtro2:
    niveles = sorted(
        df["Nivel"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    nivel_seleccionado = st.selectbox(
        "🚦 Nivel",
        ["Todos"] + list(niveles)
    )


# ------------------------------------------------------------
# FILTRO PRODUCTO
# ------------------------------------------------------------

with filtro3:
    productos_filtro = sorted(
        df["Código Producto"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    producto_seleccionado = st.selectbox(
        "📦 Producto",
        ["Todos"] + list(productos_filtro)
    )


# ------------------------------------------------------------
# FILTRO CLIENTE
# ------------------------------------------------------------

with filtro4:
    clientes = sorted(
        df["Cliente"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    cliente_seleccionado = st.selectbox(
        "🏢 Cliente",
        ["Todos"] + list(clientes)
    )


# ------------------------------------------------------------
# FILTRO COMERCIAL
# ------------------------------------------------------------

with filtro5:
    if "Comercial" in df.columns:
        comerciales = sorted(
            [c for c in df["Comercial"].dropna().astype(str).str.strip().unique() if c]
        )
    else:
        comerciales = []

    comercial_seleccionado = st.selectbox(
        "👤 Comercial",
        ["Todos"] + list(comerciales)
    )


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()

if periodo_seleccionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Periodo"] == periodo_seleccionado
    ]

if nivel_seleccionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Nivel"]
        .astype(str)
        .str.strip()
        == nivel_seleccionado
    ]

if producto_seleccionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Código Producto"]
        .astype(str)
        .str.strip()
        == producto_seleccionado
    ]

if cliente_seleccionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Cliente"]
        .astype(str)
        .str.strip()
        == cliente_seleccionado
    ]

if comercial_seleccionado != "Todos" and "Comercial" in df_filtrado.columns:
    df_filtrado = df_filtrado[
        df_filtrado["Comercial"]
        .astype(str)
        .str.strip()
        == comercial_seleccionado
    ]


# ============================================================
# USAR DATA FILTRADA EN TODO EL DASHBOARD
# ============================================================

df = df_filtrado.copy()


# ============================================================
# VALIDAR COLUMNAS NECESARIAS
# ============================================================

columnas_requeridas = [
    "Despachado",
    "Total Ajuste",
    "Descuento",
    "Nivel",
    "Código Producto"
]

columnas_faltantes = [
    columna
    for columna in columnas_requeridas
    if columna not in df.columns
]

if columnas_faltantes:
    st.error(
        "Faltan las siguientes columnas en el Excel: "
        + ", ".join(columnas_faltantes)
    )
    st.write("Columnas encontradas:")
    st.write(df.columns.tolist())
    st.stop()


# ============================================================
# LIMPIAR NIVEL
# ============================================================

df["Nivel"] = (
    df["Nivel"]
    .astype(str)
    .str.strip()
    .str.title()
)


# ============================================================
# CLASIFICACIÓN DE DESCUENTOS
# ============================================================

df["Tipo Descuento"] = df["Descuento"].apply(
    lambda x:
    "Excepción (>7%)"
    if x > 7
    else "Regular (≤7%)"
)


# ============================================================
# KPIs PRINCIPALES
# ============================================================

total_productos = int(
    df["Despachado"].sum()
)

total_descuento = float(
    df["Total Ajuste"].sum()
)

total_casos = len(df)


# ============================================================
# CASOS DE EXCEPCIÓN
# ============================================================

excepciones = df[
    df["Descuento"] > 7
].copy()

total_excepciones = len(excepciones)

productos_excepcion = int(
    excepciones["Despachado"].sum()
)

descuento_excepciones = float(
    excepciones["Total Ajuste"].sum()
)

porcentaje_excepciones = (
    total_excepciones
    / total_casos
    * 100
    if total_casos > 0
    else 0
)


# ============================================================
# IMPACTO DEL DESCUENTO
# ============================================================

if "Precio Facturado" in df.columns:
    valor_facturado_total = (
        df["Precio Facturado"]
        * df["Despachado"]
    ).sum()
else:
    valor_facturado_total = 0

porcentaje_impacto = (
    total_descuento
    / valor_facturado_total
    * 100
    if valor_facturado_total > 0
    else 0
)


# ============================================================
# HEADER
# ============================================================

if periodo_seleccionado == "Todos":
    titulo_periodo = "Histórico General"
else:
    titulo_periodo = periodo_seleccionado

st.markdown(
    f"""
    <div class="titulo-dashboard">
        Cierre de Descuentos por Desperfecto Estético
    </div>

    <div class="subtitulo-dashboard">
        {titulo_periodo}
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# KPIs SUPERIORES
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)


def tarjeta_kpi(titulo, valor, subtitulo):
    html = f"""
<div class="kpi-card">
<div class="kpi-title">{titulo}</div>
<div class="kpi-value">{valor}</div>
<div class="kpi-subtitle">{subtitulo}</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


with col1:
    tarjeta_kpi(
        "📦 Productos con Descuento",
        f"{total_productos:,.0f}",
        "unidades procesadas"
    )

with col2:
    tarjeta_kpi(
        "💰 Total Descuento Aplicado",
        f"${total_descuento:,.2f}",
        "USD"
    )

with col3:
    tarjeta_kpi(
        "🚨 Casos de Excepción",
        f"{total_excepciones}",
        "descuentos mayores a 7%"
    )

with col4:
    tarjeta_kpi(
        "📋 Casos Registrados",
        f"{total_casos}",
        "registros procesados"
    )

with col5:
    tarjeta_kpi(
        "📊 Impacto del Descuento",
        f"{porcentaje_impacto:.2f}%",
        "sobre valor facturado"
    )


# ============================================================
# PRIMERA FILA DE ANÁLISIS
# ============================================================

col1, col2, col3 = st.columns([1, 1.8, 1])


# ============================================================
# NIVEL DE AFECTACIÓN
# ============================================================

with col1:

    st.markdown(
        '<div class="section-title">NIVEL DE AFECTACIÓN</div>',
        unsafe_allow_html=True
    )

    nivel_data = (
        df.groupby("Nivel")
        .agg(
            Casos=("Nivel", "count"),
            Productos=("Despachado", "sum"),
            Descuento=("Total Ajuste", "sum")
        )
        .reset_index()
    )

    fig_nivel = px.pie(
        nivel_data,
        values="Casos",
        names="Nivel",
        hole=0.55
    )

    fig_nivel.update_layout(
        height=350,
        margin=dict(
            t=20,
            b=20,
            l=20,
            r=20
        )
    )

    st.plotly_chart(
        fig_nivel,
        use_container_width=True
    )


# ============================================================
# DETALLE DE CLIENTES POR ZONA / REGISTROS FILTRADOS
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">DETALLE DE DESCUENTOS POR CLIENTE Y ZONA</div>',
        unsafe_allow_html=True
    )

    e1, e2, e3 = st.columns(3)

    with e1:
        total_clientes_unicos = df["Cliente"].nunique() if "Cliente" in df.columns else 0
        st.metric(
            "Clientes Afectados",
            total_clientes_unicos
        )

    with e2:
        st.metric(
            "Total Casos",
            total_casos
        )

    with e3:
        st.metric(
            "Monto Total",
            f"${total_descuento:,.2f}"
        )

    columnas_deseadas = [
        "Comercial",
        "Cliente",
        "Nro. Nota",
        "Código Producto",
        "Despachado",
        "Descuento",
        "Total Ajuste",
        "Nivel"
    ]

    columnas_disponibles = [
        columna
        for columna in columnas_deseadas
        if columna in df.columns
    ]

    if not df.empty:
        df_mostrar = df[columnas_disponibles].copy()
        
        # Formatear la vista de números para mayor claridad
        if "Descuento" in df_mostrar.columns:
            df_mostrar["Descuento"] = df_mostrar["Descuento"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
        if "Total Ajuste" in df_mostrar.columns:
            df_mostrar["Total Ajuste"] = df_mostrar["Total Ajuste"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "")

        st.dataframe(
            df_mostrar,
            use_container_width=True,
            height=260
        )
    else:
        st.info(
            "No se encontraron registros de clientes para la selección actual."
        )


# ============================================================
# DISTRIBUCIÓN REGULAR VS EXCEPCIÓN
# ============================================================

with col3:

    st.markdown(
        '<div class="section-title">DISTRIBUCIÓN DE DESCUENTOS</div>',
        unsafe_allow_html=True
    )

    distribucion = (
        df.groupby("Tipo Descuento")
        .size()
        .reset_index(name="Casos")
    )

    fig_distribucion = px.pie(
        distribucion,
        values="Casos",
        names="Tipo Descuento",
        hole=0.55
    )

    fig_distribucion.update_layout(
        height=350,
        margin=dict(
            t=20,
            b=20,
            l=20,
            r=20
        )
    )

    st.plotly_chart(
        fig_distribucion,
        use_container_width=True
    )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# SEGUNDA FILA
# ============================================================

col1, col2 = st.columns(2)


# ============================================================
# PRODUCTOS CON MAYOR DESCUENTO
# ============================================================

with col1:

    st.markdown(
        '<div class="section-title">PRODUCTOS CON MAYOR IMPACTO ECONÓMICO</div>',
        unsafe_allow_html=True
    )

    productos = (
        df.groupby("Código Producto")
        .agg(
            Productos_Afectados=("Despachado", "sum"),
            Total_Descuento=("Total Ajuste", "sum")
        )
        .reset_index()
    )

    productos["% Participación"] = (
        productos["Total_Descuento"]
        / total_descuento
        * 100
        if total_descuento > 0
        else 0
    )

    productos = productos.sort_values(
        by="Total_Descuento",
        ascending=False
    )

    productos = productos.rename(
        columns={
            "Código Producto": "Producto",
            "Productos_Afectados": "Unidades Afectadas",
            "Total_Descuento": "Total Descuento"
        }
    )

    productos_display = productos.copy()

    productos_display["Total Descuento"] = (
        productos_display["Total Descuento"]
        .map(lambda x: f"${x:,.2f}")
    )

    productos_display["% Participación"] = (
        productos_display["% Participación"]
        .map(lambda x: f"{x:.2f}%")
    )

    st.dataframe(
        productos_display.head(10),
        use_container_width=True,
        height=350
    )


# ============================================================
# RESUMEN POR NIVEL
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">RESUMEN POR NIVEL DE AFECTACIÓN</div>',
        unsafe_allow_html=True
    )

    resumen_nivel = (
        df.groupby("Nivel")
        .agg(
            Casos=("Nivel", "count"),
            Productos=("Despachado", "sum"),
            Descuento=("Total Ajuste", "sum")
        )
        .reset_index()
    )

    resumen_nivel["% Participación"] = (
        resumen_nivel["Descuento"]
        / total_descuento
        * 100
        if total_descuento > 0
        else 0
    )

    resumen_display = resumen_nivel.copy()

    resumen_display["Descuento"] = (
        resumen_display["Descuento"]
        .map(lambda x: f"${x:,.2f}")
    )

    resumen_display["% Participación"] = (
        resumen_display["% Participación"]
        .map(lambda x: f"{x:.2f}%")
    )

    st.dataframe(
        resumen_display,
        use_container_width=True,
        height=350
    )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# TERCERA FILA - DESCUENTO POR PRODUCTO
# ============================================================

st.markdown(
    '<div class="section-title">TOP 10 PRODUCTOS CON MAYOR DESCUENTO ACUMULADO</div>',
    unsafe_allow_html=True
)

top_productos_grafico = (
    productos
    .head(10)
    .sort_values(
        by="Total Descuento",
        ascending=True
    )
)

fig_productos = px.bar(
    top_productos_grafico,
    x="Total Descuento",
    y="Producto",
    orientation="h",
    text="Total Descuento"
)

fig_productos.update_traces(
    texttemplate="$%{text:,.2f}",
    textposition="outside"
)

fig_productos.update_layout(
    height=450,
    xaxis_title="Total Descuento (USD)",
    yaxis_title="Producto",
    margin=dict(
        t=20,
        b=20,
        l=20,
        r=60
    )
)

st.plotly_chart(
    fig_productos,
    use_container_width=True
)


# ============================================================
# FOOTER - RESUMEN EJECUTIVO
# ============================================================

st.divider()

st.markdown(
    """
    ### 📌 Resumen Ejecutivo
    """
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📦 Unidades con Descuento",
        f"{total_productos:,.0f}"
    )

with col2:
    st.metric(
        "💰 Impacto Económico",
        f"${total_descuento:,.2f}"
    )

with col3:
    st.metric(
        "🚨 Productos en Excepción",
        f"{productos_excepcion:,.0f}"
    )

with col4:
    if total_productos > 0:
        promedio_producto = (
            total_descuento
            / total_productos
        )
    else:
        promedio_producto = 0

    st.metric(
        "💵 Descuento Promedio por Unidad",
        f"${promedio_producto:,.2f}"
    )
    