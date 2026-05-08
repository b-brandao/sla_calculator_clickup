import os
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# ---------- Configuração da página ----------
st.set_page_config(
    page_title="Dashboard ClickUp - Incidentes",
    page_icon="📊",
    layout="wide",
)

DEFAULT_FILE = os.getenv("OUTPUT_FILE", "tasks_export.xlsx")

# ---------- Funções utilitárias ----------
@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    df = pd.read_excel(file, dtype={"sla_horas_uteis": str})

    # Conversões de data
    for col in ["date_created", "date_updated"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Coluna SLA em horas (decimal) para gráficos
    def hhmmss_to_hours(s):
        try:
            if pd.isna(s) or s == "":
                return 0.0
            h, m, sec = s.split(":")
            return int(h) + int(m) / 60 + int(sec) / 3600
        except Exception:
            return 0.0

    if "sla_horas_uteis" in df.columns:
        df["sla_horas_decimal"] = df["sla_horas_uteis"].apply(hhmmss_to_hours)
    else:
        df["sla_horas_decimal"] = 0.0

    return df


def kpi_card(col, label, value, help_text=None):
    col.metric(label, value, help=help_text)


# ---------- Sidebar ----------
st.sidebar.title("⚙️ Configurações")

uploaded = st.sidebar.file_uploader("Carregue o arquivo XLSX", type=["xlsx"])
file_to_load = uploaded if uploaded else (DEFAULT_FILE if os.path.exists(DEFAULT_FILE) else None)

if file_to_load is None:
    st.warning("📂 Faça o upload de um arquivo .xlsx ou gere o `tasks_export.xlsx` rodando `python main.py`.")
    st.stop()

df = load_data(file_to_load)

if df.empty:
    st.info("Arquivo vazio.")
    st.stop()

# ---------- Filtros ----------
st.sidebar.subheader("🔍 Filtros")

def multiselect_filter(df, col, label):
    if col not in df.columns:
        return df
    options = sorted([x for x in df[col].dropna().unique() if str(x).strip() != ""])
    if not options:
        return df
    selected = st.sidebar.multiselect(label, options, default=options)
    return df[df[col].isin(selected)]

df_f = df.copy()
df_f = multiselect_filter(df_f, "status", "Status")
df_f = multiselect_filter(df_f, "priority", "Prioridade")
df_f = multiselect_filter(df_f, "cf_SQUAD", "Squad")
df_f = multiselect_filter(df_f, "cf_Cliente", "Cliente")
df_f = multiselect_filter(df_f, "cf_Categoria Incidente", "Categoria Incidente")
df_f = multiselect_filter(df_f, "cf_Origem Incidente", "Origem Incidente")

# Faixa de SLA
if "sla_horas_decimal" in df_f.columns and not df_f.empty:
    sla_max = float(df_f["sla_horas_decimal"].max() or 0)
    sla_range = st.sidebar.slider(
        "SLA (horas úteis)",
        min_value=0.0,
        max_value=max(sla_max, 1.0),
        value=(0.0, max(sla_max, 1.0)),
        step=1.0,
    )
    df_f = df_f[(df_f["sla_horas_decimal"] >= sla_range[0]) & (df_f["sla_horas_decimal"] <= sla_range[1])]

# ---------- Cabeçalho ----------
st.title("📊 Dashboard ClickUp - Incidentes em Aberto")
st.caption(f"Última atualização do arquivo: {datetime.fromtimestamp(os.path.getmtime(file_to_load)).strftime('%d/%m/%Y %H:%M') if isinstance(file_to_load, str) else 'arquivo enviado'}")

# ---------- KPIs ----------
col1, col2, col3, col4 = st.columns(4)
total = len(df_f)
sla_medio = df_f["sla_horas_decimal"].mean() if total else 0
sla_max_v = df_f["sla_horas_decimal"].max() if total else 0
acima_24h = (df_f["sla_horas_decimal"] > 24).sum()

kpi_card(col1, "Total de Tasks", f"{total}")
kpi_card(col2, "SLA Médio (h úteis)", f"{sla_medio:.1f}h")
kpi_card(col3, "SLA Máximo (h úteis)", f"{sla_max_v:.1f}h")
kpi_card(col4, "Tasks > 24h úteis", f"{acima_24h}")

st.divider()

# ---------- Gráficos ----------
g1, g2 = st.columns(2)

with g1:
    st.subheader("Tasks por Status")
    if "status" in df_f.columns:
        s = df_f["status"].value_counts().reset_index()
        s.columns = ["status", "qtd"]
        fig = px.bar(s, x="status", y="qtd", text="qtd", color="status")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Qtd")
        st.plotly_chart(fig, use_container_width=True)

with g2:
    st.subheader("Tasks por Prioridade")
    if "priority" in df_f.columns:
        p = df_f["priority"].fillna("sem prioridade").value_counts().reset_index()
        p.columns = ["priority", "qtd"]
        fig = px.pie(p, names="priority", values="qtd", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

g3, g4 = st.columns(2)

with g3:
    st.subheader("Tasks por Squad")
    if "cf_SQUAD" in df_f.columns:
        sq = df_f["cf_SQUAD"].fillna("Sem squad").value_counts().reset_index()
        sq.columns = ["squad", "qtd"]
        fig = px.bar(sq, x="qtd", y="squad", orientation="h", text="qtd", color="squad")
        fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="Qtd")
        st.plotly_chart(fig, use_container_width=True)

with g4:
    st.subheader("Tasks por Cliente (Top 10)")
    if "cf_Cliente" in df_f.columns:
        cl = df_f["cf_Cliente"].fillna("Não informado").value_counts().head(10).reset_index()
        cl.columns = ["cliente", "qtd"]
        fig = px.bar(cl, x="qtd", y="cliente", orientation="h", text="qtd")
        fig.update_layout(yaxis_title="", xaxis_title="Qtd")
        st.plotly_chart(fig, use_container_width=True)

g5, g6 = st.columns(2)

with g5:
    st.subheader("Categoria de Incidente")
    if "cf_Categoria Incidente" in df_f.columns:
        c = df_f["cf_Categoria Incidente"].fillna("Não informado").value_counts().reset_index()
        c.columns = ["categoria", "qtd"]
        fig = px.bar(c, x="categoria", y="qtd", text="qtd", color="categoria")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Qtd")
        st.plotly_chart(fig, use_container_width=True)

with g6:
    st.subheader("Origem do Incidente")
    if "cf_Origem Incidente" in df_f.columns:
        o = df_f["cf_Origem Incidente"].fillna("Não informado").value_counts().reset_index()
        o.columns = ["origem", "qtd"]
        fig = px.pie(o, names="origem", values="qtd", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

st.subheader("⏱️ Distribuição de SLA (horas úteis)")
if "sla_horas_decimal" in df_f.columns and not df_f.empty:
    fig = px.histogram(df_f, x="sla_horas_decimal", nbins=20, title="")
    fig.update_layout(xaxis_title="Horas úteis", yaxis_title="Qtd de tasks")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("📈 Evolução de Criação das Tasks")
if "date_created" in df_f.columns and df_f["date_created"].notna().any():
    tmp = df_f.copy()
    tmp["data"] = tmp["date_created"].dt.date
    serie = tmp.groupby("data").size().reset_index(name="qtd")
    fig = px.line(serie, x="data", y="qtd", markers=True)
    fig.update_layout(xaxis_title="Data de criação", yaxis_title="Qtd de tasks")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Tabela ----------
st.divider()
st.subheader("📋 Detalhamento das Tasks")

cols_to_show = [
    "id", "name", "status", "priority",
    "cf_SQUAD", "cf_Cliente", "cf_Categoria Incidente",
    "cf_Origem Incidente", "cf_Sprint",
    "date_created", "date_updated",
    "sla_horas_uteis", "url",
]
cols_existing = [c for c in cols_to_show if c in df_f.columns]

st.dataframe(
    df_f[cols_existing],
    use_container_width=True,
    hide_index=True,
    column_config={
        "url": st.column_config.LinkColumn("Abrir no ClickUp"),
    },
)

# ---------- Download ----------
st.download_button(
    label="⬇️ Baixar dados filtrados (CSV)",
    data=df_f[cols_existing].to_csv(index=False).encode("utf-8-sig"),
    file_name="tasks_filtradas.csv",
    mime="text/csv",
)

if st.sidebar.button("🔄 Atualizar dados do ClickUp"):
    from main import main as run_export
    run_export()
    st.cache_data.clear()
    st.rerun()