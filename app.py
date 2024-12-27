import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static

# Load dataset
@st.cache_data
def load_data():
    file_path = 'dfTransjakarta180kRows.csv'
    df = pd.read_csv(file_path)
    df['tapInTime'] = pd.to_datetime(df['tapInTime'])
    df['tapOutTime'] = pd.to_datetime(df['tapOutTime'])
    df['hour'] = df['tapInTime'].dt.hour
    return df

df = load_data()

# Sidebar
st.sidebar.title('🔍 Filter Data')
selected_day = st.sidebar.selectbox('Pilih Hari', df['tapInTime'].dt.day_name().unique())
corridor_options = ['Semua Koridor'] + list(df['corridorName'].dropna().unique())
selected_corridor = st.sidebar.selectbox('Pilih Koridor', corridor_options)
selected_bank = st.sidebar.multiselect('Pilih Bank', df['payCardBank'].unique())

# Filter data berdasarkan pilihan sidebar
filtered_df = df.copy()
if selected_day:
    filtered_df = filtered_df[filtered_df['tapInTime'].dt.day_name() == selected_day]
if selected_corridor and selected_corridor != 'Semua Koridor':
    filtered_df = filtered_df[filtered_df['corridorName'] == selected_corridor]
if selected_bank:
    filtered_df = filtered_df[filtered_df['payCardBank'].isin(selected_bank)]

# Halaman Utama
st.title('📊 Analisis Data Transaksi Transjakarta')
st.write('Aplikasi ini menyediakan analisis interaktif dari data transaksi Transjakarta.')

# 1️⃣ **Tren Harian dan Waktu Sibuk**
st.header('1. Tren Harian dan Waktu Sibuk')
hourly_counts = filtered_df.groupby('hour').size().reset_index(name='count')
fig_hourly = px.line(hourly_counts, x='hour', y='count', title='Jumlah Transaksi per Jam')
st.plotly_chart(fig_hourly)

# 2️⃣ **Rute Populer**
st.header('2. Rute Populer')
route_counts = filtered_df['corridorName'].value_counts().reset_index()
route_counts.columns = ['corridorName', 'count']
fig_route = px.bar(route_counts.head(10), x='corridorName', y='count', title='Top 10 Koridor Terpopuler')
st.plotly_chart(fig_route)

# 3️⃣ **Peta Lokasi Tap-In dan Tap-Out**
st.header('3. Peta Lokasi Tap-In dan Tap-Out')

# Filter lokasi yang valid
valid_locations = filtered_df.dropna(subset=['tapInStopsLat', 'tapInStopsLon', 'tapOutStopsLat', 'tapOutStopsLon'])
map_center = [valid_locations['tapInStopsLat'].mean(), valid_locations['tapInStopsLon'].mean()]
m = folium.Map(location=map_center, zoom_start=12)

for _, row in valid_locations.head(100).iterrows():
    folium.Marker([row['tapInStopsLat'], row['tapInStopsLon']], popup='Tap-In').add_to(m)
    folium.Marker([row['tapOutStopsLat'], row['tapOutStopsLon']], popup='Tap-Out').add_to(m)

folium_static(m)

# 4️⃣ **Pembayaran dan Moda Transportasi**
st.header('4. Pembayaran dan Moda Transportasi')
pay_counts = filtered_df['payCardBank'].value_counts().reset_index()
pay_counts.columns = ['payCardBank', 'count']
fig_pay = px.pie(pay_counts, names='payCardBank', values='count', title='Distribusi Bank Pembayaran')
st.plotly_chart(fig_pay)

# 5️⃣ **Distribusi Pengguna Berdasarkan Jenis Kelamin Sepanjang Hari**
st.header('5. Distribusi Pengguna Berdasarkan Jenis Kelamin Sepanjang Hari')

# Persiapan Data
sex_time_df = filtered_df.copy()
sex_time_df['hour'] = sex_time_df['tapInTime'].dt.hour

# Agregasi Data
sex_time_grouped = (sex_time_df
                    .groupby(['hour', 'payCardSex'])
                    .size()
                    .reset_index(name='count'))

# Grafik Bar Chart Animasi
fig_sex_time = px.bar(
    sex_time_grouped,
    x='payCardSex',
    y='count',
    animation_frame='hour',
    animation_group='payCardSex',
    color='payCardSex',
    title='Distribusi Pengguna Berdasarkan Jenis Kelamin Sepanjang Hari',
    labels={'count': 'Jumlah Pengguna', 'payCardSex': 'Jenis Kelamin'},
    range_y=[0, sex_time_grouped['count'].max()]
)

fig_sex_time.update_layout(
    xaxis_title='Jenis Kelamin',
    yaxis_title='Jumlah Pengguna',
    showlegend=True
)

st.plotly_chart(fig_sex_time)

# **Kesimpulan**
st.header('Kesimpulan')
st.write("""
- Koridor tertentu lebih populer pada jam sibuk.
- Pembayaran didominasi oleh kartu dari bank tertentu.
- Tren transaksi menunjukkan lonjakan signifikan di waktu tertentu.
""")

# Footer
st.sidebar.write('🛠️ Dibuat dengan Streamlit & Plotly')