import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
from folium.plugins import MarkerCluster

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    layout="wide",
    page_title="Địa bàn BTU",
    page_icon="📍"
)

# Thêm CSS để tối ưu hóa bố cục
st.markdown("""
    <style>
        /* Có thể thêm CSS tùy chỉnh ở đây nếu cần */
    </style>
""", unsafe_allow_html=True)

# --- 2. HÀM KIỂM TRA ĐĂNG NHẬP ---
def check_password():
    """Kiểm tra mật khẩu từ mục [credentials] trong Secrets."""
    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>CƠ SỞ KINH DOANH BTU</h1>", unsafe_allow_html=True)
        st.write("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("Vui lòng đăng nhập để truy cập dữ liệu")
            with st.form("login_form"):
                password_input = st.text_input("Mật khẩu:", type="password")
                submit = st.form_submit_button("Xác nhận đăng nhập", use_container_width=True)
                if submit:
                    try:
                        if password_input == st.secrets["credentials"]["password"]:
                            st.session_state["password_correct"] = True
                            st.rerun()
                        else:
                            st.error("❌ Mật khẩu không chính xác!")
                    except KeyError:
                        st.error("⚠️ Lỗi: Chưa cấu hình 'password' trong Secrets!")
                        return False
        return False
    return True

# --- 3. CHƯƠNG TRÌNH CHÍNH ---
if check_password():
    # Nút đăng xuất tại Sidebar
    if st.sidebar.button("Đăng xuất 🔓"):
        del st.session_state["password_correct"]
        st.rerun()

    # Hàm tải dữ liệu từ Google Sheets API
    @st.cache_data(ttl=300)
    def load_data():
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes
            )
            client = gspread.authorize(creds)
            sh = client.open("MAP_BTU")
            worksheet = sh.worksheet("ThongTin")
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Lỗi kết nối dữ liệu: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        st.markdown("<h2 style='text-align: center;'>CƠ SỞ KINH DOANH BTU</h2>", unsafe_allow_html=True)
        st.write("---")

        # --- BỘ LỌC TẠI SIDEBAR ---
        st.sidebar.header("Bộ lọc tìm kiếm")
        
        if 'Ap' in df.columns:
            list_ap = sorted(df['Ap'].unique().tolist())
            selected_ap = st.sidebar.multiselect("Chọn Ấp:", list_ap, default=list_ap)
            df_loc = df[df['Ap'].isin(selected_ap)]
        else:
            df_loc = df

        search_query = st.sidebar.text_input("🔍 Tìm tên cơ sở:")
        if search_query:
            df_loc = df_loc[df_loc['TenCoSo'].str.contains(search_query, case=False, na=False)]

        # --- TỔNG HỢP SỐ LIỆU ---
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns([1.5, 2, 1, 1])
        with col_metric1:
            st.metric("Tổng số cơ sở:", len(df_loc))
        with col_metric2:
            so_lao_dong_safe = pd.to_numeric(df_loc['SoLaoDong'], errors='coerce').fillna(0)
            st.metric("Lao động địa phương:", f"{int(so_lao_dong_safe.sum()):,} người")
        with col_metric3:
            st.metric("Công ty:", len(df_loc[df_loc['LinhVuc'].str.contains("Công ty", case=False, na=False)]))
        with col_metric4:
            st.metric("Hộ KD:", len(df_loc[df_loc['LinhVuc'].str.contains("Hộ kinh doanh", case=False, na=False)]))

        st.write("---")

        # --- 4. HIỂN THỊ BẢN ĐỒ FOLIUM (Hiển thị to rõ phía trên) ---
        st.subheader("Bản đồ địa bàn")
        BTU_CENTER = [11.115307, 106.842750]
        m = folium.Map(
            location=BTU_CENTER,
            zoom_start=14,
            control_scale=True,
            tiles='OpenStreetMap'
        )

        marker_cluster = MarkerCluster().add_to(m)
        coords_list = []

        for _, row in df_loc.iterrows():
            vitri = row.get('ViTri')
            if pd.notnull(vitri) and vitri != "":
                try:
                    lat, lon = map(float, str(vitri).split(','))
                    coords_list.append([lat, lon])
                    
                    color = "blue"
                    linh_vuc = str(row.get('LinhVuc', '')).lower()
                    if "công ty" in linh_vuc:
                        color = "red"
                    elif "hộ kinh doanh" in linh_vuc:
                        color = "green"

                    # Tạo link Google Maps chỉ đường
                    google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

                    popup_content = f"""
                    <div style="font-family: Arial; font-size: 14px;">
                        <h4 style="margin-top: 0;">{row.get('TenCoSo', 'N/A')}</h4>
                        <b>Lĩnh Vực:</b> {row.get('LinhVuc', 'N/A')}<br>
                        <b>Ấp:</b> {row.get('Ap', 'N/A')}<br>
                        <b>Số Lao Động:</b> {row.get('SoLaoDong', 0)}<br>
                        <b>Trạng thái:</b> {row.get('TrangThai', 'N/A')}<br><br>
                        <a href="{google_maps_url}" target="_blank" style="background-color: #4285F4; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">📍 Chỉ đường đến đây</a>
                    </div>
                    """
                    
                    folium.Marker(
                        [lat, lon],
                        popup=folium.Popup(popup_content, max_width=350),
                        tooltip=row.get('TenCoSo', 'Xem chi tiết'),
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(marker_cluster)
                except:
                    continue

        if coords_list:
            min_lat = min(coord[0] for coord in coords_list)
            max_lat = max(coord[0] for coord in coords_list)
            min_lon = min(coord[1] for coord in coords_list)
            max_lon = max(coord[1] for coord in coords_list)
            m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

        # Hiển thị bản đồ full width
        st_folium(m, width="100%", height=600, returned_objects=[])

        st.write("---")

        # --- 5. BẢNG DỮ LIỆU CHI TIẾT (Đưa xuống dưới bản đồ) ---
        st.subheader("Bảng dữ liệu cơ sở")
        cols_to_display = ['TenCoSo', 'LinhVuc', 'Ap', 'SoLaoDong']
        
        if all(col in df_loc.columns for col in cols_to_display):
            # Hiển thị bảng full width ở dưới
            st.dataframe(
                df_loc[cols_to_display],
                use_container_width=True,
                hide_index=True,
                height=400
            )
        else:
            st.warning("⚠️ Không tìm thấy đầy đủ các cột: TenCoSo, LinhVuc, Ap, SoLaoDong")

    else:
        st.markdown("<h2 style='text-align: center;'>CƠ SỞ KINH DOANH BTU</h2>", unsafe_allow_html=True)
        st.warning("⚠️ Không có dữ liệu để hiển thị. Kiểm tra lại tên Sheet 'ThongTin' hoặc quyền của Service Account.")

    # Chú giải màu sắc ở sidebar
    with st.sidebar:
        st.write("---")
        st.subheader("Chú giải bản đồ")
        st.markdown("""
        - 🔴 : Công ty
        - 🟢 : Hộ kinh doanh
        - 🔵 : Lĩnh vực khác
        """)
