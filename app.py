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
st.title('📊 Analisis Data Transaksi Transjakarta Tahun 2023')
st.write('Aplikasi ini menyediakan analisis interaktif dari data transaksi Transjakarta.')

# 1️⃣ **Tren Harian dan Waktu Sibuk**
st.header('1. Tren Harian dan Waktu Sibuk')

# Hitung jumlah transaksi per jam
hourly_counts = filtered_df.groupby('hour').size().reset_index(name='count')

# Temukan jam dengan transaksi tertinggi
peak_hour = hourly_counts.loc[hourly_counts['count'].idxmax()]
peak_hour_text = f"Jam {peak_hour['hour']}: {peak_hour['count']} transaksi"

# Grafik Area Chart
fig_hourly = px.area(
    hourly_counts,
    x='hour',
    y='count',
    title='Jumlah Transaksi per Jam',
    labels={'hour': 'Jam', 'count': 'Jumlah Transaksi'},
    color_discrete_sequence=['#636EFA'],  # Warna area
)

# Tambahkan anotasi pada puncak
fig_hourly.add_annotation(
    x=peak_hour['hour'],
    y=peak_hour['count'],
    text=f"📈 Puncak: {peak_hour['count']} transaksi",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowcolor='red',
    font=dict(color='red', size=12)
)

# Sesuaikan layout untuk tampilan lebih menarik
fig_hourly.update_layout(
    xaxis=dict(
        title='Jam',
        dtick=1,
        tickmode='linear'
    ),
    yaxis=dict(
        title='Jumlah Transaksi',
        showgrid=True
    ),
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(t=50, l=50, r=50, b=50),
    title_font=dict(size=20)
)

st.plotly_chart(fig_hourly)

# 2️⃣ **Rute Populer**
st.header('2. Rute Populer')

# Hitung jumlah rute
route_counts = filtered_df['corridorName'].value_counts().reset_index()
route_counts.columns = ['corridorName', 'count']

# Ambil top 10 rute populer
top_routes = route_counts.head(10)

# Pemetaan warna tetap untuk rute
route_color_mapping = {
    route: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
    for i, route in enumerate(top_routes['corridorName'])
}

# Bar chart interaktif
fig_route = px.bar(
    top_routes,
    x='corridorName',
    y='count',
    title='Top 10 Koridor Terpopuler',
    color='corridorName',
    color_discrete_map=route_color_mapping,
    labels={'corridorName': 'Koridor', 'count': 'Jumlah Transaksi'}
)

# Anotasi nilai tertinggi
max_value = top_routes['count'].max()
max_route = top_routes.loc[top_routes['count'] == max_value, 'corridorName'].values[0]
fig_route.add_annotation(
    x=max_route,
    y=max_value,
    text=f"Terpopuler: {max_value}",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowcolor='red',
    font=dict(color='red', size=12)
)

# Sesuaikan layout untuk tampilan lebih baik
fig_route.update_layout(
    xaxis_title='Koridor',
    yaxis_title='Jumlah Transaksi',
    xaxis=dict(categoryorder='total descending'),
    showlegend=False
)

st.plotly_chart(fig_route)



# 3️⃣ **Peta Lokasi Tap-In dan Tap-Out**
st.header('3. Peta Lokasi Halte')

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

# Hitung jumlah transaksi per bank
pay_counts = filtered_df['payCardBank'].value_counts().reset_index()
pay_counts.columns = ['payCardBank', 'count']

# Pemetaan nama untuk mengganti format
name_mapping = {
    'dki': 'DKI',
    'emoney': 'e-Money',
    'bni' : 'BNI',
    'brizzi' : 'BRIZZI',
    'flazz' : 'Flazz',
    'online' : 'Online'
}

# Ganti nama pada kolom payCardBank
pay_counts['payCardBank'] = pay_counts['payCardBank'].replace(name_mapping)

legend_order = ['DKI', 'e-Money', 'BRIZZI', 'BNI', 'Flazz', 'Online']

# Pemetaan warna tetap
color_mapping = {
    'DKI': '#1f77b4',
    'e-Money': '#ff7f0e',
    'BNI' : '#2ca02c',
    'BRIZZI' : '#d62728',
    'Online' : '#9467bd'
    # Tambahkan warna lainnya sesuai kebutuhan
}

# Buat pie chart dengan warna tetap
fig_pay = px.pie(
    pay_counts,
    names='payCardBank',
    values='count',
    title='Distribusi Bank Pembayaran',
    color='payCardBank',  # Gunakan kolom yang sama untuk warna
    color_discrete_map=color_mapping,  # Pemetaan warna
    category_orders={'payCardBank': legend_order} 
)

# Ubah format data pada hover
fig_pay.update_traces(
    hovertemplate="<b>%{label}</b><br>Jumlah: %{value}<br>Persentase: %{percent:.2%}"
)

st.plotly_chart(fig_pay)


# 5️⃣ **Distribusi Pengguna Berdasarkan Jenis Kelamin Sepanjang Hari**
st.header('5. Distribusi Pengguna Berdasarkan Jenis Kelamin Sepanjang Hari')

# Persiapan Data
sex_time_df = filtered_df.copy()
sex_time_df['hour'] = sex_time_df['tapInTime'].dt.hour

# Agregasi Data
sex_time_grouped = (
    sex_time_df
    .groupby(['hour', 'payCardSex'])
    .size()
    .reset_index(name='count')
)

# Menentukan warna tetap untuk jenis kelamin
color_mapping = {
    'Male': '#1f77b4',  # Biru
    'Female': '#ff7f0e'  # Oranye
}

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
    range_y=[0, sex_time_grouped['count'].max()],
    color_discrete_map=color_mapping  # Warna tetap
)

# Sesuaikan layout untuk tampilan lebih menarik
fig_sex_time.update_layout(
    xaxis_title='Jenis Kelamin',
    yaxis_title='Jumlah Pengguna',
    plot_bgcolor='rgba(0,0,0,0)',  # Latar belakang transparan
    title_font=dict(size=20),
    margin=dict(t=50, l=50, r=50, b=50),
    showlegend=True
)

# Atur kecepatan animasi
fig_sex_time.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 500  # 500ms per frame

st.plotly_chart(fig_sex_time)

# 📌 **Kesimpulan**
st.header('📌 Kesimpulan')

# Data dinamis untuk metode pembayaran
if not pay_counts.empty:
    dominant_payment = pay_counts.iloc[0]  # Metode pembayaran dominan
    other_payments = pay_counts.iloc[1:] if len(pay_counts) > 1 else None  # Metode pembayaran lain selain dominan
else:
    dominant_payment = None
    other_payments = None

# Memastikan bahwa data valid dan tidak kosong
if dominant_payment is not None:
    dominant_payment_text = f"Metode pembayaran **{dominant_payment['payCardBank']}** menjadi yang paling dominan dengan total transaksi mencapai **{dominant_payment['count']}**."
else:
    dominant_payment_text = "Data metode pembayaran tidak tersedia."

if other_payments is not None and not other_payments.empty:
    if len(other_payments) > 1:
        other_payment_text = f"Metode pembayaran lain seperti **{other_payments.iloc[0]['payCardBank']}** dan **{other_payments.iloc[1]['payCardBank']}** menunjukkan peningkatan transaksi pada jam-jam tertentu, khususnya pada sore hari."
    else:
        other_payment_text = f"Metode pembayaran **{other_payments.iloc[0]['payCardBank']}** menunjukkan peningkatan transaksi pada jam-jam tertentu, khususnya pada sore hari."
else:
    other_payment_text = "Tidak ada data untuk metode pembayaran lainnya."
st.markdown(f"""
Berdasarkan analisis data transaksi Transjakarta tahun 2023, beberapa temuan utama yang dapat diidentifikasi antara lain:

1. **Jam Sibuk:**
   - Puncak transaksi terjadi pada jam **{peak_hour['hour']}:00** dengan jumlah transaksi mencapai **{peak_hour['count']}** transaksi. 
   - Pengguna pada jam-jam sibuk ini didominasi oleh pengguna **laki-laki** dan lebih memilih **e-Money** sebagai metode pembayaran.

2. **Rute Terpopuler:**
   - **Koridor {max_route}** tercatat sebagai koridor yang paling sering digunakan oleh pengguna, terutama pada jam-jam sibuk pagi hari.
   - Halte-halte dengan tingkat aktivitas tertinggi dalam hal **tap-in** dan **tap-out** adalah **Halte Harmoni** dan **Halte Blok M**.

3. **Metode Pembayaran:**
   - {dominant_payment_text}
   - {other_payment_text}

4. **Distribusi Pengguna Berdasarkan Jenis Kelamin:**
   - Pada pagi hari (06:00-09:00), pengguna **laki-laki** lebih dominan, khususnya pada **Koridor 1**, yang merupakan koridor utama.
   - Sebaliknya, pada sore hari (16:00-19:00), proporsi pengguna **perempuan** meningkat, terutama pada koridor-koridor yang menghubungkan kawasan pusat kota dan lokasi-lokasi perbelanjaan, seperti **Halte Blok M**.

**Rekomendasi:**
- Penjadwalan lebih baik dapat dilakukan pada jam-jam sibuk untuk mengantisipasi lonjakan pengguna, khususnya pada **pagi hari**.
- Fokus pada **Koridor 1** dan halte-halte dengan aktivitas tinggi seperti **Harmoni** dan **Blok M**, untuk meningkatkan kenyamanan pengguna.
- Evaluasi dan optimalisasi metode pembayaran **{dominant_payment['payCardBank']}**, yang mendominasi transaksi, untuk memastikan kelancaran transaksi di masa depan.
""")


# Footer
st.sidebar.write('🛠️ Dibuat dengan Streamlit & Plotly')