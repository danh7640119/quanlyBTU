import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- CẤU HÌNH GIAO DIỆN CHUẨN ---
st.set_page_config(page_title="KẾT QUẢ ĐIỀU TRA", layout="wide")

# CSS để ép giao diện giống hình (Bảng bên phải, Map bên trái, Metrics nằm dưới)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 5px; }
    /* Tối ưu cho mobile */
    @media (max-width: 768px) {
        .stColumn { width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. DỮ LIỆU (Dựa trên thông tin trong hình) ---
def load_data():
    data = {
        'STT': range(1, 13),
        'Tên Cơ Sở': ['Công ty ABC', 'Công ty ABC', 'Công ty ABC', 'Ấp Đất Cuốc', 'Ấp Đất Cuốc', 'Ấp Đất Cuốc', 'Ấp Đất Cuốc', 'Ấp Đất Cuốc', 'Ấp Đất Cuốc', 'Ấp - Suối Sâu', 'Ấp - Suối Sâu', 'Ấp - Suối Sâu'],
        'Lĩnh Vực': ['Hỗ', 'Sản xuất Gỗ', 'Sản xuất Gỗ', 'Ấp', 'Sản xuất Gỗ', 'Đất Cuốc', 'Đất Cuốc', 'Sản xuất Gỗ', 'Đất Cuốc', 'Đất Cuốc', 'Đất Cuốc', 'Đất Cuốc'],
        'Công ty': [12, 12, 12, 12, 12, 12, 12, 12, 13, 4, 12, 12],
        'Số Lao Động': [33, 23, 18, 15, 15, 8, 6, 10, 4, 45, 3, 2],
        'Lat': [11.155, 11.156, 11.157, 11.150, 11.149, 11.148, 11.147, 11.146, 11.145, 11.160, 11.161, 11.162],
        'Lon': [106.850, 106.851, 106.852, 106.840, 106.841, 106.842, 106.843, 106.844, 106.845, 106.860, 106.861, 106.862],
        'Anh': ['https://via.placeholder.com/150'] * 12 # Thay link ảnh thật vào đây
    }
    return pd.DataFrame(data)

df = load_data()

# --- 2. TIÊU ĐỀ ---
st.subheader("KẾT QUẢ ĐIỀU TRA CƠ SỞ KINH DOANH XÃ BẮC TÂN UYÊN")

# --- 3. BỐ CỤC CHÍNH (MAP & TABLE) ---
col_map, col_table = st.columns([6, 4])

with col_map:
    # Khởi tạo bản đồ
    m = folium.Map(location=[11.15, 106.85], zoom_start=14, tiles='cartodbpositron')
    
    for i, row in df.iterrows():
        # HTML cho Popup giống hệt trong ảnh (Có ảnh, Tiêu đề, Nội dung)
        popup_content = f"""
            <div style="width:180px; font-family: sans-serif;">
                <b style="font-size:14px;">Tên Cơ Sở:</b> {row['Tên Cơ Sở']}<br>
                <b>Lĩnh Vực:</b> {row['Lĩnh Vực']}<br>
                <b>Ấp:</b> {row['Tên Cơ Sở'].split(' - ')[-1]}<br>
                <b>Số Lao Động:</b> {row['Số Lao Động']}<br>
                <img src="{row['Anh']}" width="100%" style="margin-top:10px; border-radius:5px;">
            </div>
        """
        folium.Marker(
            [row['Lat'], row['Lon']],
            popup=folium.Popup(popup_content, max_width=200),
            icon=folium.Icon(color='red' if 'Gỗ' in row['Lĩnh Vực'] else 'blue', icon='home')
        ).add_to(m)
    
    st_folium(m, width="100%", height=500)

with col_table:
    # Hiển thị bảng dữ liệu rút gọn như trong ảnh
    st.dataframe(
        df[['Tên Cơ Sở', 'Lĩnh Vực', 'Công ty', 'Số Lao Động']], 
        height=500, 
        use_container_width=True,
        hide_index=True
    )

# --- 4. THANH THỐNG KÊ (DƯỚI CÙNG - METRICS) ---
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Tổng số điểm", "34")
with m2:
    st.metric("Lao động địa phương", "210")
with m3:
    st.metric("Công ty", "12")
with m4:
    st.metric("Hộ KD", "22")

# --- 5. TỐI ƯU MOBILE (XỬ LÝ KHI CLICK) ---
# Khi bấm vào 1 dòng trong bảng, bản đồ có thể tự động focus (tùy chọn thêm)
st.info("💡 Trên điện thoại: Bấm vào các điểm màu trên bản đồ để xem thông tin chi tiết và ảnh cơ sở.")
