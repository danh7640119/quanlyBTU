import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Cấu hình trang
st.set_page_config(layout="wide", page_title="Bản đồ Xã Bắc Tân Uyên")

# Hàm đọc dữ liệu
def load_data():
    # DÁN CÁI LINK CSV BẠN LẤY Ở BƯỚC 1 VÀO ĐÂY
    url = "https://docs.google.com/spreadsheets/d/e/XXXXX/pub?output=csv"
    df = pd.read_csv(url)
    return df

st.title("📍 Hệ thống quản lý cơ sở kinh doanh - Xã Bắc Tân Uyên")

try:
    df = load_data()
    
    # Bộ lọc ở thanh bên
    st.sidebar.header("Bộ lọc")
    all_ap = df['Ap'].unique().tolist()
    selected_ap = st.sidebar.multiselect("Chọn Ấp", all_ap, default=all_ap)
    
    # Lọc dữ liệu
    df_filtered = df[df['Ap'].isin(selected_ap)]

    # Tạo bản đồ (Tọa độ trung tâm xã)
    m = folium.Map(location=[11.12, 106.57], zoom_start=13)

    for index, row in df_filtered.iterrows():
        if pd.notnull(row['ViTri']):
            try:
                lat, lon = map(float, str(row['ViTri']).split(','))
                
                # Màu sắc theo lĩnh vực
                color = "blue"
                if "Gỗ" in str(row['LinhVuc']): color = "red"
                elif "Dịch vụ" in str(row['LinhVuc']): color = "green"

                folium.Marker(
                    [lat, lon],
                    popup=f"<b>{row['TenCoSo']}</b><br>Ấp: {row['Ap']}<br>Lao động: {row['SoLaoDong']}",
                    tooltip=row['TenCoSo'],
                    icon=folium.Icon(color=color, icon="info-sign")
                ).add_to(m)
            except:
                continue

    # Hiển thị bản đồ
    st_folium(m, width=1000, height=500)
    
    # Hiển thị bảng dữ liệu
    st.subheader("Danh sách chi tiết")
    st.dataframe(df_filtered[['TenCoSo', 'Ap', 'DiaChi', 'SoLaoDong', 'TrangThai']])

except Exception as e:
    st.error(f"Đang chờ dữ liệu từ AppSheet... (Lỗi: {e})")
