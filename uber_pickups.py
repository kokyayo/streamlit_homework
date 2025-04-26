import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime
import plotly.express as px

st.title('Uber pickups in NYC')

DATE_COLUMN = 'date/time'
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
            'streamlit-demo-data/uber-raw-data-sep14.csv.gz')

@st.cache_data
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data

data_load_state = st.text('Loading data...')
data = load_data(10000)
data_load_state.text("Done! (using st.cache_data)")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

st.subheader('Number of pickups by hour')
hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0,24))[0]
st.bar_chart(hist_values)

# Some number in the range 0-23
hour_to_filter = st.slider('hour', 0, 23, 17)
filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]

st.subheader('Map of all pickups at %s:00' % hour_to_filter)
st.map(filtered_data)



# 3D Map
st.subheader("3D Map of Pickups by Location")

# ดึงวันที่ที่มีข้อมูลจริง
available_dates = sorted(data['date/time'].dt.date.unique())
min_date = min(available_dates)
max_date = max(available_dates)

# เลือกวัน
selected_date = st.date_input(
    "เลือกวันที่",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

# เลือกโหมดการกรองเวลา
time_mode = st.radio("เลือกเวลา", ["ทุกเวลา", "เลือกเวลาเดียว", "เลือกช่วงเวลา"])

# เงื่อนไขการกรองตามโหมด
if time_mode == "ทุกเวลา":
    filtered = data[data['date/time'].dt.date == selected_date]
    time_text = "ทุกเวลา"

elif time_mode == "เลือกเวลาเดียว":
    selected_hour = st.selectbox("เลือกเวลาเดียว", range(24), format_func=lambda x: f"{x:02d}:00")
    filtered = data[
        (data['date/time'].dt.date == selected_date) &
        (data['date/time'].dt.hour == selected_hour)
    ]
    time_text = f"{selected_hour:02d}:00"

elif time_mode == "เลือกช่วงเวลา":
    start_hour, end_hour = st.slider(
        "เลือกช่วงเวลา",
        0, 23, (8, 11),
        format="%02d:00"
    )
    filtered = data[
        (data['date/time'].dt.date == selected_date) &
        (data['date/time'].dt.hour >= start_hour) &
        (data['date/time'].dt.hour <= end_hour)
    ]
    time_text = f"{start_hour:02d}:00 - {end_hour:02d}:00"

# แสดงข้อมูลที่กรองแล้ว
st.write(f"พบข้อมูล {len(filtered)} รายการในวันที่ {selected_date} เวลา: {time_text}")

# คำนวณตำแหน่งกลางของแผนที่
midpoint = (filtered["lat"].mean(), filtered["lon"].mean()) if len(filtered) else (40.7128, -74.0060)

# แสดง 3D Map
st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/dark-v10",
    initial_view_state=pdk.ViewState(
        latitude=midpoint[0],
        longitude=midpoint[1],
        zoom=11,
        pitch=40,
    ),
    layers=[
        pdk.Layer(
            "HexagonLayer",
            data=filtered,
            get_position='[lon, lat]',
            radius=100,
            elevation_scale=25,
            pickable=True,
            extruded=True,
            coverage=0.6,
            opacity=0.5
        )
    ],
    tooltip={"text": "จำนวน Pickup ณ จุดนี้"}
))

# วาดกราฟด้วย plotly
# เตรียมข้อมูล
if not filtered.empty:
    # เพิ่มคอลัมน์ชั่วโมง
    filtered['hour'] = filtered['date/time'].dt.hour

    # นับจำนวน pickup ต่อชั่วโมง
    pickups_per_hour = filtered.groupby('hour').size().reset_index(name='pickups')

    # สร้างกราฟ bar chart
    fig = px.bar(
        pickups_per_hour,
        x='hour',
        y='pickups',
        labels={'hour': 'ชั่วโมง', 'pickups': 'จำนวน Pickup'},
        title=f'จำนวน Uber Pickups แบ่งตามเวลา วันที่ {selected_date}',
        text='pickups'
    )

    fig.update_layout(
        xaxis=dict(dtick=1),
        yaxis_title="จำนวน Pickup",
        xaxis_title="เวลา (0-23)",
        plot_bgcolor='rgba(0,0,0,0)',
        bargap=0.2
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ไม่มีข้อมูล pickup ในช่วงเวลาที่เลือก")

# เช็กว่า session_state มีตัวแปร x หรือยัง
if "x" not in st.session_state:
    st.session_state.x = 0  # เริ่มต้น x = 0

# แสดงข้อความ
st.write(f"This page has run {st.session_state.x} times.")

# ปุ่มสำหรับเพิ่มค่า x
if st.button("Click to increase"):
    st.session_state.x += 1  # เพิ่มค่า x ทีละ 1