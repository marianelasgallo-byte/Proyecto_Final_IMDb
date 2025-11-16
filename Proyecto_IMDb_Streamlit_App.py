import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import io
import datetime
import matplotlib.pyplot as plt

# ReportLab (PDF)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader


# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title='IMDb: Análisis de películas', layout='wide')
DATA_FILENAME = 'imdb_5000.csv'
MIN_YEAR = 1950
MAX_YEAR = 2025


# ==============================
# CARGA Y LIMPIEZA DE DATOS
# ==============================
@st.cache_data
def load_and_clean(path):
    df = pd.read_csv(path)

    df = df.loc[:, ~df.columns.duplicated()]  
    df.columns = [c.strip() for c in df.columns]

    col_map = {}
    for c in df.columns:
        low = c.lower()
        if 'movie_title' in low or low == "title":
            col_map[c] = 'title'
        if 'title_year' in low:
            col_map[c] = 'year'
        if 'genres' in low:
            col_map[c] = 'genres'
        if 'imdb_score' in low:
            col_map[c] = 'rating'
        if 'num_voted_users' in low:
            col_map[c] = 'votes'
        if 'duration' in low:
            col_map[c] = 'duration'
        if 'director_name' in low:
            col_map[c] = 'director'
        if 'country' in low:
            col_map[c] = 'country'

    df = df.rename(columns=col_map)

    keep = ['title','year','genres','rating','votes','duration','director','country']
    df = df[[c for c in keep if c in df.columns]]

    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    df['votes'] = pd.to_numeric(df.get('votes', 0), errors='coerce').fillna(0).astype(int)
    df['genres'] = df['genres'].fillna('Unknown')

    df = df[(df['year'] >= MIN_YEAR) & (df['year'] <= MAX_YEAR)]

    df['decade'] = (df['year'] // 10) * 10

    df['genres_list'] = df['genres'].astype(str).str.split('|')
    df = df.explode('genres_list')
    df['genre'] = df['genres_list'].str.strip()

    return df.reset_index(drop=True)


# ==============================
# PLOTLY → PNG usando Matplotlib (SIN KALEIDO)
# ==============================
def plotly_to_png(fig):
    buf = io.BytesIO()
    plt.figure(figsize=(6,4))

    for trace in fig.data:
        if trace.type == "bar":
            plt.bar(trace.x, trace.y)
        elif trace.type == "scatter":
            plt.plot(trace.x, trace.y)
        elif trace.type == "histogram":
            plt.hist(trace.x)

    plt.title(fig.layout.title.text if fig.layout.title.text else "")
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf


# ==============================
# GENERACIÓN DEL PDF
# ==============================
def generate_pdf_report(fig1, fig2, fig3, fig4):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # convertir figuras
    img1 = ImageReader(plotly_to_png(fig1))
    img2 = ImageReader(plotly_to_png(fig2))
    img3 = ImageReader(plotly_to_png(fig3))
    img4 = ImageReader(plotly_to_png(fig4))

    c.drawString(30, height - 40, "Informe del Proyecto IMDb")

    c.drawImage(img1, 30, height - 300, width=550, preserveAspectRatio=True)
    c.showPage()

    c.drawImage(img2, 30, height - 300, width=550, preserveAspectRatio=True)
    c.showPage()

    c.drawImage(img3, 30, height - 300, width=550, preserveAspectRatio=True)
    c.showPage()

    c.drawImage(img4, 30, height - 300, width=550, preserveAspectRatio=True)
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


# ==============================
# STREAMLIT LAYOUT
# ==============================
st.title('IMDb: Análisis de películas y ratings (1950-2025)')

st.sidebar.header('Carga de datos y filtros')
uploaded = st.sidebar.file_uploader('Sube tu archivo CSV (imdb_5000.csv)', type=['csv'])

if uploaded is None and not os.path.exists(DATA_FILENAME):
    st.sidebar.info('Si no subes archivo, la app buscará imdb_5000.csv en la carpeta actual.')

csv_path = uploaded if uploaded else (DATA_FILENAME if os.path.exists(DATA_FILENAME) else None)

if not csv_path:
    st.warning('Sube el CSV o coloca imdb_5000.csv en la carpeta de la app.')
    st.stop()

with st.spinner('Cargando y limpiando datos...'):
    df = load_and_clean(csv_path)

# Filtros
years = df['year'].astype(int)
min_year = int(max(MIN_YEAR, years.min()))
max_year = int(min(MAX_YEAR, years.max()))
year_range = st.sidebar.slider('Rango de años', min_value=min_year, max_value=max_year, value=(1950, max_year))

unique_genres = sorted(df['genre'].unique())
selected_genres = st.sidebar.multiselect('Géneros (filtrar)', options=unique_genres)

df_filtered = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]
if selected_genres:
    df_filtered = df_filtered[df_filtered['genre'].isin(selected_genres)]

menu = st.sidebar.radio('Sección', ['Exploración', 'Visualizaciones', 'Conclusiones'])


# ==============================
# EXPLORACIÓN
# ==============================
if menu == 'Exploración':
    st.header('1) Exploración del dataset')

    st.subheader('Primeras filas')
    st.dataframe(df_filtered.head(20))

    st.subheader('Estadísticas rápidas')
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Películas (filtradas)', len(df_filtered))
    col2.metric('Rating promedio', f"{df_filtered['rating'].mean():.2f}")
    col3.metric('Mediana votos', f"{df_filtered['votes'].median():.0f}")
    col4.metric('Años cubiertos', f"{df_filtered['year'].min()} - {df_filtered['year'].max()}")

    st.subheader('Conteos por género (top 20)')
    genre_counts = df_filtered['genre'].value_counts().head(20).reset_index()
    genre_counts.columns = ['genre', 'count']
    fig_gc = px.bar(genre_counts, x='count', y='genre', orientation='h')
    st.plotly_chart(fig_gc)


# ==============================
# VISUALIZACIONES
# ==============================
elif menu == 'Visualizaciones':
    st.header("2) Visualizaciones")

    st.subheader('Distribución de ratings')
    fig_hist = px.histogram(df_filtered, x='rating', nbins=30)
    st.plotly_chart(fig_hist)

    st.subheader('Películas por año')
    movies_per_year = df_filtered.groupby('year').size().reset_index(name='count')
    fig_year = px.line(movies_per_year, x='year', y='count', markers=True)
    st.plotly_chart(fig_year)

    st.subheader('Top géneros')
    top_genres = df_filtered['genre'].value_counts().reset_index()
    top_genres.columns = ['genre', 'count']
    fig_gen = px.bar(top_genres.head(20), x='count', y='genre', orientation='h')
    st.plotly_chart(fig_gen)

    st.subheader('Rating promedio por década (por género)')
    rbd = df_filtered.groupby(['genre','decade'])['rating'].mean().reset_index()
    fig_rbd = px.line(rbd, x='decade', y='rating', color='genre', markers=True)
    st.plotly_chart(fig_rbd)


# ==============================
# CONCLUSIONES + EXPORTAR PDF
# ==============================
elif menu == 'Conclusiones':
    st.header("3) Conclusiones")

    st.subheader("Hallazgos principales")

    top_gen = df_filtered['genre'].value_counts().head(5)
    st.write(top_gen)

    top_gen_rating = (
        df_filtered.groupby('genre')['rating']
        .mean()
        .sort_values(ascending=False)
        .head(5)
    )
    st.write(top_gen_rating)

    st.markdown("### Conclusiones automáticas")
    st.write(f"""
    - El género con más películas es **{top_gen.index[0]}**.  
    - El mejor rating promedio lo tiene **{top_gen_rating.index[0]}** (**{top_gen_rating.iloc[0]:.2f}**).  
    - Rating promedio general: **{df_filtered['rating'].mean():.2f}**.  
    - Total de películas filtradas: **{len(df_filtered)}**.
    """)

    # Gráficos para el PDF
    fig_hist = px.histogram(df_filtered, x='rating', nbins=30)
    movies_per_year = df_filtered.groupby('year').size().reset_index(name='count')
    fig_year = px.line(movies_per_year, x='year', y='count', markers=True)
    top_gen2 = df_filtered['genre'].value_counts().reset_index()
    top_gen2.columns = ['genre', 'count']
    fig_gen = px.bar(top_gen2.head(20), x='count', y='genre', orientation='h')
    rbd = df_filtered.groupby(['genre','decade'])['rating'].mean().reset_index()
    fig_rbd = px.line(rbd, x='decade', y='rating', color='genre', markers=True)

    st.markdown("### 📄 Exportar reporte en PDF")

    pdf_buffer = generate_pdf_report(fig_hist, fig_year, fig_gen, fig_rbd)

    st.download_button(
        label="Descargar PDF",
        data=pdf_buffer,
        file_name="Informe_IMDb.pdf",
        mime="application/pdf"
    )
