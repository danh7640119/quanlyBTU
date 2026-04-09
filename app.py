import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Quản lý Cơ sở Kinh doanh", layout="wide")

# CSS để tùy chỉnh giao diện giống hình mẫu (Dark mode nhẹ, bảng gọn gàng)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    /* Tối ưu hiển thị bảng trên mobile */
    @media (max-width: 600px) {
        .stDataFrame { font-size: 10px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. MÔ PHỎNG DỮ LIỆU (Thay bằng pd.read_csv hoặc sheet của bạn) ---
@st.cache_data
def load_data():
    data = {
        'Tên Cơ Sở': ['Công ty ABC', 'Cơ sở Suối Sâu', 'Ấp Đất Cuốc', 'Xưởng Gỗ Thành Tâm', 'Tiệm KD Tổng Hợp'],
        'Lĩnh Vực': ['Sản xuất Gỗ', 'Nông nghiệp', 'Dịch vụ', 'Sản xuất Gỗ', 'Bán lẻ'],
        'Địa Chỉ': ['Bắc Tân Uyên', 'Suối Sâu', 'Đất Cuốc', 'Bắc Tân Uyên', 'Bắc Tân Uyên'],
        'Số Lao Động': [45, 12, 8, 25, 3],
        'Lat': [11.15, 11.16, 11.14, 11.155, 11.145],
        'Lon': [106.85, 106.86, 106.84, 106.855, 106.845],
        'Ghi Chú': ['Đang hoạt động', 'Mới thành lập', 'Đạt chuẩn', 'Cần kiểm tra', 'Đạt chuẩn']
    }
    return pd.DataFrame(data)

df = load_data()

# --- 2. PHẦN HEADER & THỐNG KÊ NHANH ---
st.title("📊 KẾT QUẢ ĐIỀU TRA CƠ SỞ KINH DOANH XÃ")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Tổng số điểm", len(df))
col_m2.metric("Lao động địa phương", df['Số Lao Động'].sum())
col_m3.metric("Công ty", len(df[df['Lĩnh Vực'].str.contains('Sản xuất')]))
col_m4.metric("Hộ KD", len(df[df['Lĩnh Vực'].str.contains('Bán lẻ|Dịch vụ')]))

st.divider()

# --- 3. BẢN ĐỒ VÀ DANH SÁCH ---
col_left, col_right = st.columns([6, 4])

with col_left:
    st.subheader("📍 Bản đồ phân bố")
    # Khởi tạo bản đồ tại trung tâm dữ liệu
    m = folium.Map(location=[df['Lat'].mean(), df['Lon'].mean()], zoom_start=13, tiles='OpenStreetMap')
    
    # Thêm Marker cho từng cơ sở
    for i, row in df.iterrows():
        # Nội dung khi bấm vào marker (Popup)
        popup_html = f"""
            <div style="width:200px">
                <h4 style="margin-bottom:5px;">{row['Tên Cơ Sở']}</h4>
                <b>Lĩnh vực:</b> {row['Lĩnh Vực']}<br>
                <b>Lao động:</b> {row['Số Lao Động']}<br>
                <b>Địa chỉ:</b> {row['Địa Chỉ']}<br>
                <hr>
                <p style="font-size:12px; color:gray;">{row['Ghi Chú']}</p>
            </div>
        """
        folium.Marker(
            [row['Lat'], row['Lon']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=row['Tên Cơ Sở'],
            icon=folium.Icon(color='red' if row['Số Lao Động'] > 20 else 'blue', icon='info-sign')
        ).add_to(m)
    
    # Hiển thị bản đồ
    st_data = st_folium(m, width="100%", height=450)

with col_right:
    st.subheader("📋 Chi tiết dữ liệu")
    # Ô tìm kiếm nhanh
    search = st.text_input("🔍 Tìm tên cơ sở...", "")
    filtered_df = df[df['Tên Cơ Sở'].str.contains(search, case=False)]
    
    # Bảng hiển thị (Ẩn các cột tọa độ cho gọn)
    show_df = filtered_df.drop(columns=['Lat', 'Lon'])
    st.dataframe(show_df, use_container_width=True, height=400)

# --- 4. TỐI ƯU KHI BẤM CHỌN (SIDEBAR HOẶC BOTTOM) ---
# Nếu người dùng click vào bản đồ, hiển thị thông tin chi tiết bên dưới
if st_data['last_object_clicked_popup']:
    st.info(f"📍 Đang xem chi tiết: {st_data['last_object_clicked_popup']}")
