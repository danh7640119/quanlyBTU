import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. Hàm vẽ bản đồ
def hien_thi_ban_do(df_loc):
    # Tọa độ trung tâm xã Bắc Tân Uyên (Bạn có thể chỉnh lại cho chuẩn tâm xã)
    center_lat = 11.12
    center_lon = 106.57
    
    # Tạo đối tượng bản đồ nền
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles='OpenStreetMap')

    # Duyệt qua từng dòng dữ liệu để vẽ điểm
    for i, row in df_loc.iterrows():
        try:
            # Tách tọa độ từ cột 'ViTri' (Dạng: 11.123, 106.456)
            coords = str(row['ViTri']).split(',')
            lat = float(coords[0])
            lon = float(coords[1])
            
            # Chọn màu sắc cho Icon dựa trên loại hình
            mau_sac = 'blue'
            if 'Công ty' in str(row['LinhVuc']):
                mau_sac = 'red'
            elif 'Hộ kinh doanh' in str(row['LinhVuc']):
                mau_sac = 'green'

            # Tạo nội dung hiển thị khi bấm vào điểm (Popup)
            noi_dung = f"""
                <div style='width:200px'>
                    <b>Tên: {row['TenCoSo']}</b><br>
                    Ấp: {row['Ap']}<br>
                    Lao động: {row['SoLaoDong']}<br>
                    Trạng thái: {row['TrangThai']}
                </div>
            """

            # Vẽ điểm lên bản đồ
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(noi_dung, max_width=300),
                tooltip=row['TenCoSo'], # Hiện tên khi di chuột qua
                icon=folium.Icon(color=mau_sac, icon='info-sign')
            ).add_to(m)
        except:
            continue # Bỏ qua nếu dòng đó bị lỗi tọa độ

    # Hiển thị bản đồ lên Streamlit
    st_folium(m, width=1200, height=600)

# --- PHẦN GIAO DIỆN CHÍNH ---
st.title("🗺️ BẢN ĐỒ QUẢN LÝ CƠ SỞ KINH DOANH")

# Giả sử df là dữ liệu bạn lấy từ API Google Sheet
# df = get_data_tu_api() 

# Gọi hàm hiển thị
# hien_thi_ban_do(df)
