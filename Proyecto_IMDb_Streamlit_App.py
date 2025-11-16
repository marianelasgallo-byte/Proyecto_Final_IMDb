import streamlit as st
DATA_FILENAME = "imdb_5000.csv"

import pandas as pd
import numpy as np
import plotly.express as px
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title='IMDb: Análisis de películas', layout='wide')
DATA_FILENAME = 'imdb_5000.csv'  # nombre esperado del archivo CSV
MIN_YEAR = 1950
MAX_YEAR = 2025

# ----------------------------
# Utilidades de limpieza y preparación
# ----------------------------
@st.cache_data
def load_and_clean(path):
    # Leer CSV
    df = pd.read_csv(path)

    # FIX 1: eliminar columnas duplicadas (causa de tu error)
    df = df.loc[:, ~df.columns.duplicated()]

    # Normalizar nombres
    df.columns = [c.strip() for c in df.columns]

    # Mapear columnas (dataset movie_metadata.csv)
    col_map = {}
    for c in df.columns:
        low = c.lower()
        if 'movie_title' in low:
            col_map[c] = 'title'
        if 'title' == low:
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

    # Mantener solo lo relevante
    keep = ['title','year','genres','rating','votes','duration','director','country']
    df = df[[c for c in keep if c in df.columns]]

    # Convertir tipos
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')

    if 'rating' in df.columns:
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

    if 'votes' in df.columns:
        df['votes'] = pd.to_numeric(df['votes'], errors='coerce').fillna(0).astype(int)

    df['genres'] = df['genres'].fillna('Unknown')

    # Año realista
    df = df[(df['year'] >= MIN_YEAR) & (df['year'] <= MAX_YEAR)]

    # Década
    df['decade'] = (df['year'] // 10) * 10

    # Separar géneros: en este dataset vienen con "|"
    df['genres_list'] = df['genres'].astype(str).str.split('|')
    df = df.explode('genres_list')

    df['genre'] = df['genres_list'].str.strip()
    df = df.drop(columns=['genres_list'])

    # Reset index
    df = df.reset_index(drop=True)

    return df

# ----------------------------
# Función para generar un PDF simple con hallazgos y capturas
# ----------------------------

def generate_pdf_report(df_filtered, out_filename='informe_proyecto.pdf'):
    """Genera un PDF simple con título, fecha y algunos hallazgos básicos.
    Para incluir gráficos, la app los guarda como PNGs y los inserta aquí si existen.
    """
    c = canvas.Canvas(out_filename, pagesize=letter)
    width, height = letter

    title = 'Proyecto: Análisis de Películas y Ratings en IMDb'
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width/2, height-72, title)

    subtitle = f'Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    c.setFont('Helvetica', 10)
    c.drawCentredString(width/2, height-90, subtitle)

    text_y = height - 120
    c.setFont('Helvetica-Bold', 12)
    c.drawString(72, text_y, 'Resumen de métricas')
    text_y -= 18

    c.setFont('Helvetica', 10)
    # Ejemplos de métricas simples
    n_movies = len(df_filtered)
    avg_rating = df_filtered['rating'].mean() if 'rating' in df_filtered.columns else 0
    median_votes = df_filtered['votes'].median() if 'votes' in df_filtered.columns else 0

    c.drawString(72, text_y, f'Películas en el dataset filtrado: {n_movies}')
    text_y -= 14
    c.drawString(72, text_y, f'Rating promedio (IMDb): {avg_rating:.2f}')
    text_y -= 14
    c.drawString(72, text_y, f'Votos mediana: {int(median_votes)}')
    text_y -= 24

    # Añadir imágenes de gráficos si existen (nombres fijos esperados)
    expected_images = ['hist_rating.png', 'movies_per_year.png', 'genre_counts.png', 'rating_by_decade.png']
    for img in expected_images:
        if os.path.exists(img):
            # reducir y posicionar
            try:
                c.drawImage(img, 72, text_y-200, width=width-144, height=160, preserveAspectRatio=True)
                text_y -= 180
            except Exception:
                pass

    c.showPage()
    c.save()
    return out_filename

# ----------------------------
# Video script (plantilla)
# ----------------------------
VIDEO_SCRIPT = '''
Guion sugerido para video (7-12 min). Graba en cámara según indicado.

0:00 - 0:20 Presentación personal y título del proyecto.
0:20 - 0:50 Problema y objetivo: analizar películas y ratings en IMDb (1950-2025).
0:50 - 1:40 Datos usados: origen (Kaggle - imdb_5000), columnas principales y limpieza realizada.
1:40 - 3:00 Mostrar la sección Exploración del dashboard: primeras filas, conteos y distribución básica.
3:00 - 6:00 Mostrar y explicar 3-4 visualizaciones (histograma de ratings, películas por año, top géneros, rating por género por década). Indicar insights clave en cada visual.
6:00 - 7:00 Conclusiones principales: géneros con mejor rating, cambios por década, limitaciones del análisis.
7:00 - 7:30 Herramientas empleadas y pasos reproducibles para ejecutar la app.
7:30 - 8:00 Problemas enfrentados y cómo se resolvieron.
8:00 - 8:30 Cierre y agradecimientos.

Notas: adapta tiempos para llegar a 7-12 minutos. Muestra la pantalla con el dashboard en acción y habla mientras navegas por filtros.
'''

# ----------------------------
# Streamlit layout: 3 secciones
# ----------------------------

st.title('IMDb: Análisis de películas y ratings (1950-2025)')

# Carga de datos
st.sidebar.header('Carga de datos y filtros')
uploaded = st.sidebar.file_uploader('Sube tu archivo CSV (imdb_5000.csv)', type=['csv'])

if uploaded is None and not os.path.exists(DATA_FILENAME):
    st.sidebar.info('Si no subes archivo, la app buscará imdb_5000.csv en la carpeta actual.')

csv_path = None
if uploaded is not None:
    csv_path = uploaded
elif os.path.exists(DATA_FILENAME):
    csv_path = DATA_FILENAME

if csv_path is None:
    st.warning('Sube el CSV o coloca imdb_5000.csv en la carpeta de la app para continuar.')
    st.stop()

with st.spinner('Cargando y limpiando datos...'):
    df = load_and_clean(csv_path)

# Sidebar: filtros
years = df['year'].dropna().astype(int)
min_year = int(max(MIN_YEAR, years.min()))
max_year = int(min(MAX_YEAR, years.max()))

year_range = st.sidebar.slider('Rango de años', min_value=min_year, max_value=max_year, value=(1950, max_year))

unique_genres = sorted(df['genre'].dropna().unique().tolist())
selected_genres = st.sidebar.multiselect('Géneros (filtrar)', options=unique_genres, default=None)

# Aplicar filtros
df_filtered = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]
if selected_genres:
    df_filtered = df_filtered[df_filtered['genre'].isin(selected_genres)]

# Layout por secciones
menu = st.sidebar.radio('Sección', ['Exploración', 'Visualizaciones', 'Conclusiones'])

# ----- Exploración -----
if menu == 'Exploración':
    st.header('1) Exploración del dataset')
    st.subheader('Muestra de datos (primeras filas)')
    st.dataframe(df_filtered.head(20))

    st.subheader('Estadísticas rápidas')
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Películas (filtradas)', len(df_filtered))
    col2.metric('Rating promedio', f"{df_filtered['rating'].mean():.2f}")
    col3.metric('Mediana votos', f"{int(df_filtered['votes'].median() if 'votes' in df_filtered else 0)}")
    col4.metric('Años cubiertos', f"{df_filtered['year'].min()} - {df_filtered['year'].max()}")

    st.subheader('Conteos por género (top 20)')
    genre_counts = df_filtered['genre'].value_counts().nlargest(20).reset_index()
    genre_counts.columns = ['genre', 'count']
    fig_gc = px.bar(genre_counts.sort_values('count'), x='count', y='genre', orientation='h', labels={'count':'Cantidad','genre':'Género'}, title='Top géneros')
    st.plotly_chart(fig_gc, use_container_width=True)

# ----- Visualizaciones -----
elif menu == 'Visualizaciones':
    st.header('2) Visualizaciones')

    # Visualización 1: Histograma de ratings
    st.subheader('Distribución de ratings (IMDb)')
    fig_hist = px.histogram(df_filtered, x='rating', nbins=30, title='Histograma de ratings IMDb', labels={'rating':'Rating IMDb'})
    st.plotly_chart(fig_hist, use_container_width=True)
    fig_hist.write_image('hist_rating.png')

    # Visualización 2: Películas por año
    st.subheader('Películas por año')
    movies_per_year = df_filtered.groupby('year').size().reset_index(name='count')
    fig_year = px.line(movies_per_year, x='year', y='count', markers=True, title='Películas por año')
    st.plotly_chart(fig_year, use_container_width=True)
    fig_year.write_image('movies_per_year.png')

    # Visualización 3: Top géneros (barras)
    st.subheader('Top géneros')
    top_genres = df_filtered['genre'].value_counts().reset_index()
    top_genres.columns = ['genre', 'count']
    fig_gen = px.bar(top_genres.head(20), x='count', y='genre', orientation='h', title='Top géneros por cantidad')
    st.plotly_chart(fig_gen, use_container_width=True)
    fig_gen.write_image('genre_counts.png')

    # Visualización 4: Rating promedio por género por década
    st.subheader('Rating promedio por género por década')
    # Agrupar por genre y decade
    rbd = df_filtered.groupby(['genre','decade'])['rating'].mean().reset_index()

    # Selección de géneros para visualizar (limitar a 8 por defecto para evitar saturación)
    genres_to_plot = st.multiselect('Elige géneros para la serie temporal (máx 8)', options=sorted(rbd['genre'].unique()), default=sorted(rbd['genre'].unique())[:6])
    if genres_to_plot:
        rbd_plot = rbd[rbd['genre'].isin(genres_to_plot)]
        fig_rbd = px.line(rbd_plot, x='decade', y='rating', color='genre', markers=True, title='Rating promedio por década (por género)', labels={'decade':'Década','rating':'Rating promedio'})
        st.plotly_chart(fig_rbd, use_container_width=True)
        fig_rbd.write_image('rating_by_decade.png')
    else:
        st.info('Selecciona al menos un género para ver la serie temporal por década.')

    st.markdown('**Sugerencia:** usa el filtro de géneros en la barra lateral para explorar cómo cambian las visualizaciones.')

# ----- Conclusiones -----
elif menu == 'Conclusiones':
    st.header("3) Conclusiones")

    st.write("""
    En esta sección se presentan conclusiones automáticas basadas en los datos filtrados. 
    El objetivo es resumir los principales patrones observados en el análisis.
    """)

    # --- Hallazgos automáticos ---
    st.subheader("Hallazgos principales")

    # Top 5 géneros por cantidad
    st.markdown("### 🎬 Top 5 géneros con más películas")
    top_genres = df_filtered['genre'].value_counts().head(5)
    st.write(top_genres)

    # Top 5 géneros por rating promedio
    st.markdown("### ⭐ Top 5 géneros con mejor rating promedio")
    top_genres_rating = (
        df_filtered.groupby('genre')['rating']
        .mean()
        .sort_values(ascending=False)
        .head(5)
    )
    st.write(top_genres_rating)

    # Conclusiones generadas automáticamente
    st.markdown("### 📝 Conclusiones automáticas")
    conclusion_text = f"""
    - El género con mayor cantidad de películas en el dataset filtrado es **{top_genres.index[0]}**.
    - El género con mejor rating promedio es **{top_genres_rating.index[0]}**, con un promedio de **{top_genres_rating.iloc[0]:.2f}**.
    - El rating promedio general del conjunto filtrado es **{df_filtered['rating'].mean():.2f}**.
    - La cantidad de películas en el período seleccionado es **{len(df_filtered)}**.
    """

    st.write(conclusion_text)

    # Exportar PDF
    st.markdown("### 📄 Exportar reporte en PDF")
    if st.button("Generar PDF"):
        generate_pdf_report(df_filtered, out_filename='informe_proyecto.pdf')
        st.success("PDF generado correctamente. Se guardó como informe_proyecto.pdf.")
