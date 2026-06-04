import streamlit as st
from datetime import datetime
from calendar import monthrange
import pandas as pd
import base64
import json
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client

# Configuración de página
st.set_page_config(
    page_title="Billetera Personal | Dashboard Financiero",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CONFIGURACIÓN DE SUPABASE (NUEVAS CREDENCIALES) ====================
SUPABASE_URL = "https://eyrnidrglgktlxohpuyp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5cm5pZHJnbGdrdGx4b2hwdXlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1OTU1MzMsImV4cCI6MjA5NjE3MTUzM30.lmsUIODUM-6o_ao2x5tHtlJb3_yMQ5NHWZMZMJQUwFs"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()
USUARIO_ACTUAL = "usuario_principal"

# ==================== FUNCIONES DE BASE DE DATOS ====================
def guardar_ingreso_en_db(ingreso):
    try:
        data = {
            "usuario": USUARIO_ACTUAL,
            "nombre": ingreso["nombre"],
            "monto": ingreso["monto"],
            "fecha": ingreso["fecha"],
            "fecha_display": ingreso["fecha_display"],
            "descripcion": ingreso.get("descripcion", ""),
            "mes": ingreso["mes"],
            "año": ingreso["año"],
            "timestamp": ingreso["timestamp"]
        }
        supabase.table("ingresos").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def guardar_gasto_en_db(gasto):
    try:
        data = {
            "usuario": USUARIO_ACTUAL,
            "nombre": gasto["nombre"],
            "monto": gasto["monto"],
            "fecha": gasto["fecha"],
            "fecha_display": gasto["fecha_display"],
            "descripcion": gasto.get("descripcion", ""),
            "mes": gasto["mes"],
            "año": gasto["año"],
            "timestamp": gasto["timestamp"]
        }
        supabase.table("gastos").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def guardar_movilidad_en_db(movilidad):
    try:
        data = {
            "usuario": USUARIO_ACTUAL,
            "monto": movilidad["monto"],
            "fecha": movilidad["fecha"],
            "fecha_display": movilidad["fecha_display"],
            "detalle": movilidad.get("detalle", ""),
            "mes": movilidad["mes"],
            "año": movilidad["año"],
            "timestamp": movilidad["timestamp"]
        }
        supabase.table("movilidad").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def cargar_ingresos_desde_db(mes, año):
    try:
        response = supabase.table("ingresos").select("*").eq("usuario", USUARIO_ACTUAL).eq("mes", mes).eq("año", año).execute()
        return response.data
    except Exception as e:
        return []

def cargar_gastos_desde_db(mes, año):
    try:
        response = supabase.table("gastos").select("*").eq("usuario", USUARIO_ACTUAL).eq("mes", mes).eq("año", año).execute()
        return response.data
    except Exception as e:
        return []

def cargar_movilidad_desde_db(mes, año):
    try:
        response = supabase.table("movilidad").select("*").eq("usuario", USUARIO_ACTUAL).eq("mes", mes).eq("año", año).execute()
        return response.data
    except Exception as e:
        return []

def guardar_configuracion_en_db():
    try:
        existing = supabase.table("configuracion").select("*").eq("usuario", USUARIO_ACTUAL).execute()
        data = {
            "usuario": USUARIO_ACTUAL,
            "meta_ahorro_porcentaje": st.session_state.meta_ahorro_porcentaje,
            "gastos_fijos_config": json.dumps(st.session_state.gastos_fijos_config),
            "ingresos_referencia_config": json.dumps(st.session_state.ingresos_referencia_config),
            "updated_at": datetime.now().isoformat()
        }
        if existing.data:
            supabase.table("configuracion").update(data).eq("usuario", USUARIO_ACTUAL).execute()
        else:
            supabase.table("configuracion").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar configuración: {e}")
        return False

def cargar_configuracion_desde_db():
    try:
        response = supabase.table("configuracion").select("*").eq("usuario", USUARIO_ACTUAL).execute()
        if response.data:
            config = response.data[0]
            st.session_state.meta_ahorro_porcentaje = config.get("meta_ahorro_porcentaje", 20)
            st.session_state.gastos_fijos_config = json.loads(config.get("gastos_fijos_config", "{}"))
            st.session_state.ingresos_referencia_config = json.loads(config.get("ingresos_referencia_config", "{}"))
            return True
        return False
    except Exception as e:
        return False

def cargar_todos_los_datos(mes, año):
    with st.spinner("Cargando datos..."):
        st.session_state.ingresos_registrados = cargar_ingresos_desde_db(mes, año)
        st.session_state.gastos_registrados = cargar_gastos_desde_db(mes, año)
        st.session_state.movilidad_registros = cargar_movilidad_desde_db(mes, año)

# ==================== INICIALIZACIÓN DE ESTADO ====================
if 'gastos_fijos_config' not in st.session_state:
    st.session_state.gastos_fijos_config = {
        "Dentista": {"monto": 150.0, "dia": 15, "activo": True},
        "Servicios": {"monto": 105.0, "dia": 15, "activo": True},
        "Universidad": {"monto": 530.0, "dia": 27, "activo": True},
        "Alimentación": {"monto": 100.0, "dia": 30, "activo": True}
    }

if 'ingresos_referencia_config' not in st.session_state:
    st.session_state.ingresos_referencia_config = {
        "Ingreso quincena": {"monto": 500.0, "dia": 15, "activo": True},
        "Ingreso fin de mes": {"monto": 829.0, "dia": 30, "activo": True}
    }

if 'meta_ahorro_porcentaje' not in st.session_state:
    st.session_state.meta_ahorro_porcentaje = 20

if 'ingresos_registrados' not in st.session_state:
    st.session_state.ingresos_registrados = []
if 'gastos_registrados' not in st.session_state:
    st.session_state.gastos_registrados = []
if 'movilidad_registros' not in st.session_state:
    st.session_state.movilidad_registros = []

# ==================== FUNCIONES DE NEGOCIO ====================
def get_gastos_fijos_activos():
    return {k: v for k, v in st.session_state.gastos_fijos_config.items() if v["activo"]}

def get_ingresos_referencia_activos():
    return {k: v for k, v in st.session_state.ingresos_referencia_config.items() if v["activo"]}

def calcular_total_ingresos_referencia():
    return sum(v["monto"] for v in get_ingresos_referencia_activos().values())

def calcular_meta_ahorro():
    total_ingresos_ref = calcular_total_ingresos_referencia()
    return total_ingresos_ref * (st.session_state.meta_ahorro_porcentaje / 100)

def get_ingresos_del_mes(mes, año):
    return [i for i in st.session_state.ingresos_registrados 
            if i.get("mes") == mes and i.get("año") == año]

def get_gastos_del_mes(mes, año):
    gastos = []
    for g in st.session_state.gastos_registrados:
        if g.get("mes") == mes and g.get("año") == año:
            gastos.append(g)
    for m in st.session_state.movilidad_registros:
        if m.get("mes") == mes and m.get("año") == año:
            gastos.append({
                "nombre": "Movilidad",
                "monto": m["monto"],
                "fecha": m["fecha"],
                "descripcion": m.get("detalle", ""),
                "categoria": "Movilidad"
            })
    return gastos

def calcular_ahorro_mes(mes, año):
    ingresos = get_ingresos_del_mes(mes, año)
    gastos = get_gastos_del_mes(mes, año)
    total_ingresos = sum(i["monto"] for i in ingresos)
    total_gastos = sum(g["monto"] for g in gastos)
    return total_ingresos - total_gastos, total_ingresos, total_gastos

def calcular_ahorro_acumulado():
    all_months = set()
    for i in st.session_state.ingresos_registrados:
        all_months.add((i.get("año"), i.get("mes")))
    for g in st.session_state.gastos_registrados:
        all_months.add((g.get("año"), g.get("mes")))
    for m in st.session_state.movilidad_registros:
        all_months.add((m.get("año"), m.get("mes")))
    
    ahorro_por_mes = []
    meses_lista = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    for año, mes in sorted(all_months):
        ingresos = sum(i["monto"] for i in st.session_state.ingresos_registrados 
                      if i.get("mes") == mes and i.get("año") == año)
        gastos = 0
        for g in st.session_state.gastos_registrados:
            if g.get("mes") == mes and g.get("año") == año:
                gastos += g["monto"]
        for m in st.session_state.movilidad_registros:
            if m.get("mes") == mes and m.get("año") == año:
                gastos += m["monto"]
        ahorro = ingresos - gastos
        nombre_mes = meses_lista[mes - 1]
        ahorro_por_mes.append({
            "mes": nombre_mes,
            "año": año,
            "ahorro": ahorro,
            "periodo": f"{nombre_mes} {año}"
        })
    return ahorro_por_mes

def get_proximos_referencias(mes, año, dia_actual):
    eventos = []
    ultimo_dia = monthrange(año, mes)[1]
    
    for nombre, ingreso in get_ingresos_referencia_activos().items():
        if ingreso["dia"] >= dia_actual and ingreso["dia"] <= ultimo_dia:
            eventos.append({
                "nombre": nombre,
                "monto": ingreso["monto"],
                "dia": ingreso["dia"],
                "tipo": "ingreso"
            })
    
    for nombre, gasto in get_gastos_fijos_activos().items():
        if gasto["dia"] >= dia_actual and gasto["dia"] <= ultimo_dia:
            eventos.append({
                "nombre": nombre,
                "monto": gasto["monto"],
                "dia": gasto["dia"],
                "tipo": "gasto"
            })
    
    return sorted(eventos, key=lambda x: x["dia"])

# ==================== SELECTOR DE MES (SIDEBAR) ====================
meses_lista = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
mes_actual = datetime.now().month - 1
mes_seleccionado = st.sidebar.selectbox("Seleccionar Mes", meses_lista, index=mes_actual, key="selector_mes")
mes_num = meses_lista.index(mes_seleccionado) + 1
año_actual = datetime.now().year

# Sidebar
st.sidebar.markdown("---")
if st.sidebar.button("Sincronizar datos", use_container_width=True, key="btn_sincronizar"):
    cargar_todos_los_datos(mes_num, año_actual)
    st.sidebar.success("Datos sincronizados")

if st.sidebar.button("Guardar configuración", use_container_width=True, key="btn_guardar_config"):
    guardar_configuracion_en_db()
    st.sidebar.success("Configuración guardada")

st.sidebar.markdown("---")
st.sidebar.caption(f"Usuario: {USUARIO_ACTUAL}")
st.sidebar.caption("Los datos se guardan en la nube")

# Cargar datos al iniciar
if 'datos_iniciales_cargados' not in st.session_state:
    cargar_configuracion_desde_db()
    cargar_todos_los_datos(mes_num, año_actual)
    st.session_state.datos_iniciales_cargados = True

hoy = datetime.now()
dia_actual = hoy.day
fecha_actual_str = hoy.strftime("%d/%m/%Y %H:%M")

# ==================== HEADER ====================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<h1 style='text-align: center;'>BILLETERA PERSONAL</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>{mes_seleccionado} {año_actual} · {fecha_actual_str}</p>", unsafe_allow_html=True)
st.divider()

# ==================== TABS ====================
tab_movilidad, tab_gastos, tab_calendario, tab_resumen, tab_analisis, tab_ingresos, tab_configuracion, tab_exportar = st.tabs([
    "MOVILIDAD", "GASTOS", "CALENDARIO", "RESUMEN", "ANALISIS", "INGRESOS", "CONFIGURACION", "EXPORTAR"
])

# ==================== TAB: MOVILIDAD ====================
with tab_movilidad:
    st.subheader("Registrar Movilidad")
    
    col1, col2 = st.columns(2)
    with col1:
        mov_monto = st.number_input("Monto (S/)", min_value=0.0, step=5.0, format="%.2f", key="mov_monto")
        mov_detalle = st.text_input("Detalle", placeholder="Ej: Bus, Taxi", key="mov_detalle")
    with col2:
        st.caption(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    if st.button("Registrar Movilidad", use_container_width=True, key="btn_movilidad"):
        if mov_monto > 0:
            ahora = datetime.now()
            nuevo = {
                "monto": mov_monto,
                "fecha": ahora.strftime("%Y-%m-%d %H:%M:%S"),
                "fecha_display": ahora.strftime("%d/%m/%Y %H:%M"),
                "detalle": mov_detalle,
                "mes": ahora.month,
                "año": ahora.year,
                "timestamp": ahora.timestamp()
            }
            if guardar_movilidad_en_db(nuevo):
                st.session_state.movilidad_registros.append(nuevo)
                st.success(f"Movilidad registrada: -S/ {mov_monto:.2f}")
                st.rerun()
        else:
            st.error("Monto inválido")
    
    st.divider()
    st.subheader("Historial de Movilidad")
    movilidad = [m for m in st.session_state.movilidad_registros if m.get("mes") == mes_num and m.get("año") == año_actual]
    if movilidad:
        total = sum(m["monto"] for m in movilidad)
        st.metric("Total Movilidad", f"S/ {total:,.2f}")
        for m in sorted(movilidad, key=lambda x: x.get("timestamp", 0), reverse=True):
            col1, col2 = st.columns([3, 1])
            col1.write(f"**Movilidad**")
            col1.caption(m.get('fecha_display'))
            col1.caption(m.get('detalle', ''))
            col2.write(f"-S/ {m['monto']:.2f}")
            st.divider()
    else:
        st.info("Sin registros de movilidad")

# ==================== TAB: GASTOS ====================
with tab_gastos:
    st.subheader("Registrar Gasto")
    
    col1, col2 = st.columns(2)
    with col1:
        gasto_nombre = st.selectbox("Concepto", list(get_gastos_fijos_activos().keys()) + ["Otro gasto"], key="gasto_selectbox")
        gasto_monto = st.number_input("Monto (S/)", min_value=0.0, step=50.0, format="%.2f", key="gasto_number")
    with col2:
        gasto_desc = st.text_input("Descripción", placeholder="Opcional", key="gasto_text")
        st.caption(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    if st.button("Registrar Gasto", use_container_width=True, key="btn_gasto"):
        if gasto_monto > 0:
            ahora = datetime.now()
            nuevo = {
                "nombre": gasto_nombre,
                "monto": gasto_monto,
                "fecha": ahora.strftime("%Y-%m-%d %H:%M:%S"),
                "fecha_display": ahora.strftime("%d/%m/%Y %H:%M"),
                "descripcion": gasto_desc,
                "mes": ahora.month,
                "año": ahora.year,
                "timestamp": ahora.timestamp()
            }
            if guardar_gasto_en_db(nuevo):
                st.session_state.gastos_registrados.append(nuevo)
                st.success(f"Gasto registrado: -S/ {gasto_monto:.2f}")
                st.rerun()
        else:
            st.error("Monto inválido")
    
    st.divider()
    st.subheader("Historial de Gastos")
    gastos = [g for g in st.session_state.gastos_registrados if g.get("mes") == mes_num and g.get("año") == año_actual]
    if gastos:
        total = sum(g["monto"] for g in gastos)
        st.metric("Total Gastos", f"S/ {total:,.2f}")
        for g in sorted(gastos, key=lambda x: x.get("timestamp", 0), reverse=True):
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{g['nombre']}**")
            col1.caption(g.get('fecha_display'))
            col2.write(f"-S/ {g['monto']:.2f}")
            st.divider()
    else:
        st.info("Sin gastos registrados")

# ==================== TAB: CALENDARIO ====================
with tab_calendario:
    st.subheader("Calendario de Referencia")
    st.write("**INGRESOS PROGRAMADOS**")
    for nombre, ingreso in get_ingresos_referencia_activos().items():
        col1, col2, col3 = st.columns([1, 3, 1])
        col1.write(f"**Día {ingreso['dia']}**")
        col2.write(nombre)
        col3.write(f"+ S/{ingreso['monto']}")
    st.divider()
    st.write("**GASTOS PROGRAMADOS**")
    for nombre, gasto in get_gastos_fijos_activos().items():
        col1, col2, col3 = st.columns([1, 3, 1])
        col1.write(f"**Día {gasto['dia']}**")
        col2.write(nombre)
        col3.write(f"- S/{gasto['monto']}")

# ==================== TAB: RESUMEN ====================
with tab_resumen:
    ahorro_mes, ingresos_mes, gastos_mes = calcular_ahorro_mes(mes_num, año_actual)
    meta_ahorro_soles = calcular_meta_ahorro()
    total_ingresos_ref = calcular_total_ingresos_referencia()
    porcentaje_ahorro = (ahorro_mes / total_ingresos_ref * 100) if total_ingresos_ref > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("INGRESOS", f"S/ {ingresos_mes:,.2f}")
    with col2:
        st.metric("GASTOS", f"S/ {gastos_mes:,.2f}", delta_color="inverse")
    with col3:
        st.metric("AHORRO", f"S/ {ahorro_mes:,.2f}", delta_color="normal" if ahorro_mes >= 0 else "inverse")
    with col4:
        st.metric("PORCENTAJE", f"{porcentaje_ahorro:.0f}%")
    
    st.divider()
    
    ahorro_acumulado_lista = calcular_ahorro_acumulado()
    ahorro_total = sum(a["ahorro"] for a in ahorro_acumulado_lista)
    st.metric("AHORRO ACUMULADO", f"S/ {ahorro_total:,.2f}")
    
    if ahorro_acumulado_lista:
        df_acumulado = pd.DataFrame(ahorro_acumulado_lista)
        fig = px.bar(
            df_acumulado, 
            x="periodo", 
            y="ahorro",
            title="Evolución del Ahorro",
            color="ahorro",
            color_continuous_scale=["#ff2b2b", "#09ab3b"]
        )
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader(f"META DE AHORRO ({st.session_state.meta_ahorro_porcentaje}%)")
    if meta_ahorro_soles > 0:
        progreso = min(100, (ahorro_mes / meta_ahorro_soles) * 100)
        st.progress(progreso / 100)
        st.caption(f"S/ {ahorro_mes:,.2f} de S/ {meta_ahorro_soles:,.2f}")
    
    if ahorro_mes < 0:
        st.warning("Tus gastos superan tus ingresos")
    elif ahorro_mes < meta_ahorro_soles and ingresos_mes > 0:
        st.info(f"Te faltan S/ {meta_ahorro_soles - ahorro_mes:.2f} para alcanzar la meta")
    elif ahorro_mes >= meta_ahorro_soles and ingresos_mes > 0:
        st.success("Meta de ahorro alcanzada")
    
    st.divider()
    st.subheader("Distribución de Gastos")
    gastos_lista = get_gastos_del_mes(mes_num, año_actual)
    if gastos_lista:
        grupos = {}
        for g in gastos_lista:
            cat = g.get('nombre', 'Otros')
            grupos[cat] = grupos.get(cat, 0) + g['monto']
        for cat, monto in grupos.items():
            col1, col2 = st.columns([3, 1])
            col1.write(f"• {cat}")
            col2.write(f"S/ {monto:,.2f}")
    else:
        st.info("Sin gastos registrados")

# ==================== TAB: ANALISIS ====================
with tab_analisis:
    st.subheader("Análisis Financiero")
    if st.button("Generar Análisis", use_container_width=True, key="btn_analisis"):
        ahorro_mes, ingresos_mes, gastos_mes = calcular_ahorro_mes(mes_num, año_actual)
        ahorro_total = sum(a["ahorro"] for a in calcular_ahorro_acumulado())
        meta = calcular_meta_ahorro()
        if ingresos_mes == 0 and gastos_mes == 0:
            st.info("Sin datos este mes. Registra tus transacciones.")
        elif ingresos_mes == 0:
            st.warning(f"Gastos registrados: S/ {gastos_mes:.2f} · Sin ingresos registrados")
        elif ahorro_mes >= meta:
            st.success(f"Excelente gestión. Ahorro del mes: S/ {ahorro_mes:.2f} · Ahorro acumulado: S/ {ahorro_total:.2f}")
        elif ahorro_mes > 0:
            st.info(f"Ahorro del mes: S/ {ahorro_mes:.2f} · Faltan S/ {meta - ahorro_mes:.2f} para la meta · Acumulado: S/ {ahorro_total:.2f}")
        else:
            st.warning(f"Exceso de gastos: S/ {abs(ahorro_mes):.2f} · Ahorro acumulado: S/ {ahorro_total:.2f}")

# ==================== TAB: INGRESOS ====================
with tab_ingresos:
    st.subheader("Registrar Ingreso")
    
    col1, col2 = st.columns(2)
    with col1:
        ingreso_nombre = st.selectbox("Concepto", list(get_ingresos_referencia_activos().keys()) + ["Bono", "Horas extra", "Otro ingreso"], key="ingreso_selectbox")
        ingreso_monto = st.number_input("Monto (S/)", min_value=0.0, step=50.0, format="%.2f", key="ingreso_number")
    with col2:
        ingreso_desc = st.text_input("Descripción", placeholder="Opcional", key="ingreso_text")
        st.caption(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    if st.button("Registrar Ingreso", use_container_width=True, key="btn_ingreso"):
        if ingreso_monto > 0:
            ahora = datetime.now()
            nuevo = {
                "nombre": ingreso_nombre,
                "monto": ingreso_monto,
                "fecha": ahora.strftime("%Y-%m-%d %H:%M:%S"),
                "fecha_display": ahora.strftime("%d/%m/%Y %H:%M"),
                "descripcion": ingreso_desc,
                "mes": ahora.month,
                "año": ahora.year,
                "timestamp": ahora.timestamp()
            }
            if guardar_ingreso_en_db(nuevo):
                st.session_state.ingresos_registrados.append(nuevo)
                st.success(f"Ingreso registrado: +S/ {ingreso_monto:.2f}")
                st.rerun()
        else:
            st.error("Monto inválido")
    
    st.divider()
    st.subheader("Historial de Ingresos")
    ingresos = get_ingresos_del_mes(mes_num, año_actual)
    if ingresos:
        total = sum(i["monto"] for i in ingresos)
        st.metric("Total Ingresos", f"S/ {total:,.2f}")
        for i in sorted(ingresos, key=lambda x: x.get("timestamp", 0), reverse=True):
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{i['nombre']}**")
            col1.caption(i.get('fecha_display'))
            col2.write(f"+S/ {i['monto']:.2f}")
            st.divider()
    else:
        st.info("Sin ingresos registrados")

# ==================== TAB: CONFIGURACION ====================
with tab_configuracion:
    st.subheader("Configuración")
    
    st.write("**META DE AHORRO**")
    nueva_meta = st.slider("Porcentaje (%)", 5, 50, st.session_state.meta_ahorro_porcentaje, key="meta_slider")
    if nueva_meta != st.session_state.meta_ahorro_porcentaje:
        st.session_state.meta_ahorro_porcentaje = nueva_meta
        guardar_configuracion_en_db()
        st.rerun()
    
    st.divider()
    st.write("**INGRESOS DE REFERENCIA**")
    for nombre, ingreso in list(st.session_state.ingresos_referencia_config.items()):
        with st.expander(nombre):
            col1, col2, col3 = st.columns(3)
            with col1:
                nuevo_monto = st.number_input("Monto", value=float(ingreso["monto"]), step=50.0, format="%.2f", key=f"ing_monto_{nombre}")
            with col2:
                nuevo_dia = st.number_input("Día", value=int(ingreso["dia"]), min_value=1, max_value=31, key=f"ing_dia_{nombre}")
            with col3:
                activo = st.checkbox("Activo", value=ingreso["activo"], key=f"ing_activo_{nombre}")
            if nuevo_monto != ingreso["monto"] or nuevo_dia != ingreso["dia"] or activo != ingreso["activo"]:
                st.session_state.ingresos_referencia_config[nombre] = {"monto": nuevo_monto, "dia": nuevo_dia, "activo": activo}
                guardar_configuracion_en_db()
                st.rerun()
    
    st.divider()
    st.write("**GASTOS FIJOS**")
    with st.expander("Agregar nuevo gasto fijo"):
        nuevo_nombre = st.text_input("Nombre", key="nuevo_gasto_nombre")
        col1, col2 = st.columns(2)
        with col1:
            nuevo_monto = st.number_input("Monto", min_value=0.0, step=50.0, format="%.2f", key="nuevo_gasto_monto")
        with col2:
            nuevo_dia = st.number_input("Día", min_value=1, max_value=31, value=15, key="nuevo_gasto_dia")
        if st.button("Agregar", key="btn_agregar_gasto"):
            if nuevo_nombre and nuevo_monto > 0 and nuevo_nombre not in st.session_state.gastos_fijos_config:
                st.session_state.gastos_fijos_config[nuevo_nombre] = {"monto": nuevo_monto, "dia": nuevo_dia, "activo": True}
                guardar_configuracion_en_db()
                st.rerun()
    
    for nombre, gasto in list(st.session_state.gastos_fijos_config.items()):
        with st.expander(f"{'Activo: ' if gasto['activo'] else 'Inactivo: '}{nombre}"):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                nuevo_monto = st.number_input("Monto", value=float(gasto["monto"]), step=50.0, format="%.2f", key=f"gas_monto_{nombre}")
            with col2:
                nuevo_dia = st.number_input("Día", value=int(gasto["dia"]), min_value=1, max_value=31, key=f"gas_dia_{nombre}")
            with col3:
                activo = st.checkbox("Activo", value=gasto["activo"], key=f"gas_activo_{nombre}")
            with col4:
                if st.button("Eliminar", key=f"del_{nombre}"):
                    del st.session_state.gastos_fijos_config[nombre]
                    guardar_configuracion_en_db()
                    st.rerun()
            if nuevo_monto != gasto["monto"] or nuevo_dia != gasto["dia"] or activo != gasto["activo"]:
                st.session_state.gastos_fijos_config[nombre] = {"monto": nuevo_monto, "dia": nuevo_dia, "activo": activo}
                guardar_configuracion_en_db()
                st.rerun()

# ==================== TAB: EXPORTAR ====================
with tab_exportar:
    st.subheader("Exportar Datos")
    
    if st.button("Exportar a CSV", use_container_width=True, key="btn_csv"):
        ahorro_mes, ingresos_mes, gastos_mes = calcular_ahorro_mes(mes_num, año_actual)
        ahorro_total = sum(a["ahorro"] for a in calcular_ahorro_acumulado())
        datos = {
            "Concepto": ["Mes", "Ingresos", "Gastos", "Ahorro del Mes", "Ahorro Acumulado"],
            "Valor": [f"{mes_seleccionado} {año_actual}", f"S/ {ingresos_mes:.2f}", f"S/ {gastos_mes:.2f}", f"S/ {ahorro_mes:.2f}", f"S/ {ahorro_total:.2f}"]
        }
        df = pd.DataFrame(datos)
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        st.markdown(f"[Descargar CSV](data:file/csv;base64,{b64})")
    
    st.divider()
    st.subheader("Estado de la Base de Datos")
    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos", len(st.session_state.ingresos_registrados))
    col2.metric("Gastos", len(st.session_state.gastos_registrados))
    col3.metric("Movilidad", len(st.session_state.movilidad_registros))

# ==================== FOOTER ====================
st.divider()
st.caption("Billetera Personal · Datos guardados en la nube con Supabase")
