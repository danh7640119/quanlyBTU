import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CẤU HÌNH ĐĂNG NHẬP TỪ SECRETS ---
def check_password():
    """Kiểm tra mật khẩu được lưu trong Secrets."""
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>HỆ THỐNG QUẢN LÝ ĐỊA BÀN</h2>", unsafe_allow_name=True)
        st.write("---")
        
        # Căn giữa ô nhập liệu
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password_input = st.text_input("Nhập mật khẩu truy cập:", type="password")
            btn_login = st.button("Xác nhận đăng nhập", use_container_width=True)
            
            if btn_login:
                # Lấy mật khẩu từ mục [credentials] trong Secrets
                try:
                    correct_password = st.secrets["credentials"]["password"]
                    if password_input == correct_password:
                        st.session_state["password_correct"] = True
                        st.rerun()
                    else:
                        st.error("❌ Mật khẩu không đúng. Vui lòng thử lại.")
                except KeyError:
                    st.error("⚠️ Lỗi: Chưa cấu hình mật khẩu trong mục Secrets của Streamlit!")
        return False
    return True

# --- 2. GIAO DIỆN SAU KHI ĐĂNG NHẬP THÀNH CÔNG ---
if check_password():
    # Hiển thị nút đăng xuất ở thanh bên
    if st.sidebar.button("Đăng xuất 🔓"):
        del st.session_state["password_correct"]
        st.rerun()

    # Hàm lấy dữ liệu (Sử dụng Cache để app chạy nhanh hơn)
    @st.cache_data(ttl=120) # Cập nhật dữ liệu mới mỗi 2 phút
    def load_data():
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
            client = gspread.authorize(creds)
            
            # THAY TÊN FILE SHEET CỦA BẠN VÀO ĐÂY
            sh = client.open("Tên_file_Google_Sheet_Của_Bạn")
            df = pd.DataFrame(sh.worksheet("ThongTin").get_all_records())
            return df
        except Exception as e:
            st.error(f"Lỗi kết nối: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        st.title("📍 Bản đồ Cơ sở Kinh doanh - Xã Bắc Tân Uyên")
        
        # Bộ lọc Ấp
        st.sidebar.markdown("---")
        list_ap = df['Ap'].unique().tolist()
        selected_ap = st.sidebar.multiselect("Lọc theo Ấp:", list_ap, default=list_ap)
        df_loc = df[df['Ap'].isin(selected_ap)]

        # --- 3. HIỂN THỊ BẢN ĐỒ ---
        # Tọa độ mặc định: Trung tâm huyện Bắc Tân Uyên
        # Bạn có thể lấy tọa độ chính xác của UBND xã dán vào đây
        BTU_LAT_LONG = [11.1684, 106.8406]
        
        m = folium.Map(location=BTU_LAT_LONG, zoom_start=14)

        for _, row in df_loc.iterrows():
            if pd.notnull(row['ViTri']):
                try:
                    # AppSheet lưu "11.123, 106.456" -> Tách ra số thực
                    lat, lon = map(float, str(row['ViTri']).split(','))
                    
                    # Màu sắc icon
                    color = "blue"
                    if "Công ty" in str(row['LinhVuc']): color = "red"
                    elif "Hộ kinh doanh" in str(row['LinhVuc']): color = "green"

                    popup_text = f"<b>{row['TenCoSo']}</b><br>Ấp: {row['Ap']}<br>Lao động: {row['SoLaoDong']}"
                    
                    folium.Marker(
                        [lat, lon],
                        popup=folium.Popup(popup_text, max_width=250),
                        tooltip=row['TenCoSo'],
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(m)
                except:
                    continue

        # Hiển thị bản đồ rộng toàn màn hình
        st_folium(m, width="100%", height=550)

        # Hiển thị bảng dữ liệu tóm tắt
        with st.expander("Xem danh sách chi tiết"):
            st.dataframe(df_loc, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu để hiển thị. Hãy dùng AppSheet để nhập điểm đầu tiên!")
