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
    /* Ẩn tiêu đề mặc định và khoảng trống thừa */
    .stApp > header {display: none;}
    .reportview-container .main .block-container{padding-top: 1rem; padding-right: 1rem; padding-left: 1rem; padding-bottom: 1rem;}
    
    /* Điều chỉnh kích thước bản đồ để chiếm tối đa */
    .element-container iframe {
        height: 80vh !important;
    }
    
    /* Thiết kế popup đẹp hơn */
    .leaflet-popup-content-wrapper {
        border-radius: 8px;
        box-shadow: 0 3px 14px rgba(0,0,0,0.4);
    }
    .leaflet-popup-content {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. HÀM KIỂM TRA ĐĂNG NHẬP ---
def check_password():
    """Kiểm tra mật khẩu từ mục [credentials] trong Secrets."""
    if "password_correct" not in st.session_state:
        # Tiêu đề chính như trong ảnh
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>CƠ SỞ KINH DOANH BTU</h2>", unsafe_allow_html=True)
        st.write("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("Vui lòng đăng nhập để truy cập dữ liệu")
            with st.form("login_form"):
                password_input = st.text_input("Mật khẩu:", type="password")
                submit = st.form_submit_button("Xác nhận đăng nhập", use_container_width=True)
                if submit:
                    try:
                        # So khớp mật khẩu với thông tin trong Secrets
                        if password_input == st.secrets["credentials"]["password"]:
                            st.session_state["password_correct"] = True
                            st.rerun()
                        else:
                            st.error("❌ Mật khẩu không chính xác!")
                    except KeyError:
                        st.error("⚠️ Lỗi: Chưa cấu hình 'password' trong Secrets!")
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
            # THÊM QUYỀN DRIVE ĐỂ TRÁNH LỖI 403
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], 
                scopes=scopes
            )
            client = gspread.authorize(creds)
            
            # MỞ FILE VỚI TÊN CHÍNH XÁC LÀ MAP_BTU
            sh = client.open("MAP_BTU") 
            worksheet = sh.worksheet("ThongTin")
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Lỗi kết nối dữ liệu: {e}")
            return pd.DataFrame()

    df = load_data()

    if not df.empty:
        # Tiêu đề chính như trong ảnh
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>CƠ SỞ KINH DOANH BTU</h2>", unsafe_allow_html=True)
        
        # --- BỘ LỌC TẠI SIDEBAR ---
        st.sidebar.header("Bộ lọc tìm kiếm")
        
        # Lọc theo Ấp
        if 'Ap' in df.columns:
            list_ap = sorted(df['Ap'].unique().tolist())
            selected_ap = st.sidebar.multiselect("Chọn Ấp:", list_ap, default=list_ap)
            df_loc = df[df['Ap'].isin(selected_ap)]
        else:
            df_loc = df

        # Thêm thanh tìm kiếm theo tên cơ sở
        search_query = st.sidebar.text_input("🔍 Tìm tên cơ sở:")
        if search_query:
            df_loc = df_loc[df_loc['TenCoSo'].str.contains(search_query, case=False, na=False)]

        # --- TỔNG HỢP SỐ LIỆU ---
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns([1.5, 2, 1, 1])
        with col_metric1:
            st.metric("Tổng số cơ sở:", len(df_loc))
        with col_metric2:
            # Chuyển đổi cột SoLaoDong sang kiểu số, lỗi sẽ biến thành NaN, sau đó thay NaN bằng 0
            so_lao_dong_safe = pd.to_numeric(df_loc['SoLaoDong'], errors='coerce').fillna(0)
            # Hiển thị metric với dữ liệu đã xử lý
            st.metric("Lao động địa phương:", f"{int(so_lao_dong_safe.sum()):,} người")
        with col_metric3:
            st.metric("Công ty:", len(df_loc[df_loc['LinhVuc'].str.contains("Công ty", case=False, na=False)]))
        with col_metric4:
            st.metric("Hộ KD:", len(df_loc[df_loc['LinhVuc'].str.contains("Hộ kinh doanh", case=False, na=False)]))

        # Giao diện Map-centric (Bản đồ lớn, bảng dữ liệu bên phải)
        map_col, data_col = st.columns([2, 1])

        # --- 4. HIỂN THỊ BẢN ĐỒ FOLIUM ---
        with map_col:
            # Tọa độ mặc định trung tâm xã Bắc Tân Uyên
            BTU_CENTER = [11.1684, 106.8406]
            
            # Cấu hình bản đồ
            m = folium.Map(
                location=BTU_CENTER, 
                zoom_start=14, 
                control_scale=True,
                tiles='OpenStreetMap'
            )

            # Thêm MarkerCluster để gom nhóm điểm
            marker_cluster = MarkerCluster().add_to(m)

            coords_list = []

            for _, row in df_loc.iterrows():
                # Kiểm tra cột ViTri (tọa độ từ AppSheet)
                vitri = row.get('ViTri')
                if pd.notnull(vitri) and vitri != "":
                    try:
                        lat, lon = map(float, str(vitri).split(','))
                        coords_list.append([lat, lon])
                        
                        # Phân màu theo Lĩnh vực
                        color = "blue"
                        linh_vuc = str(row.get('LinhVuc', '')).lower()
                        if "công ty" in linh_vuc: color = "red"
                        elif "hộ kinh doanh" in linh_vuc: color = "green"

                        # Popup nội dung chi tiết
                        popup_content = f"""
                            <div style='min-width: 180px;'>
                                <p style='margin: 0; padding-bottom: 5px; color: #1E3A8A; font-weight: bold; font-size: 14px;'>{row.get('TenCoSo', 'N/A')}</p>
                                <p style='margin: 0;'><b>Lĩnh Vực:</b> {row.get('LinhVuc', 'N/A')}</p>
                                <p style='margin: 0;'><b>Ấp:</b> {row.get('Ap', 'N/A')}</p>
                                <p style='margin: 0;'><b>Số Lao Động:</b> {row.get('SoLaoDong', 0)}</p>
                                <hr style='margin: 7px 0;'>
                                <p style='margin: 0;'><b>Trạng thái:</b> {row.get('TrangThai', 'N/A')}</p>
                            </div>
                        """
                        
                        folium.Marker(
                            [lat, lon],
                            popup=folium.Popup(popup_content, max_width=300),
                            tooltip=row.get('TenCoSo', 'Xem chi tiết'),
                            icon=folium.Icon(color=color, icon='info-sign')
                        ).add_to(marker_cluster) # Add to cluster instead of map directly
                    except:
                        continue

            # Tự động căn chỉnh bản đồ nếu có điểm
            if coords_list:
                # Tính toán biên (bounding box) cho các điểm đang hiển thị
                min_lat = min(coord[0] for coord in coords_list)
                max_lat = max(coord[0] for coord in coords_list)
                min_lon = min(coord[1] for coord in coords_list)
                max_lon = max(coord[1] for coord in coords_list)
                
                # Căn chỉnh bản đồ cho vừa khít các điểm
                m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

            # Hiển thị bản đồ
            st_folium(m, width="100%", height=700, returned_objects=[])

        # --- 5. BẢNG DỮ LIỆU CHI TIẾT bên phải ---
        with data_col:
            st.subheader("Bảng dữ liệu cơ sở")
            
            # Chỉ hiển thị các cột cần thiết để giống trong ảnh
            cols_to_display = ['TenCoSo', 'LinhVuc', 'Ap', 'SoLaoDong']
            if all(col in df_loc.columns for col in cols_to_display):
                # Sử dụng pagination (phân trang)
                rows_per_page = st.slider("Cơ sở/trang:", min_value=10, max_value=100, value=20)
                
                # Hiển thị bảng
                st.dataframe(
                    df_loc[cols_to_display], 
                    use_container_width=True, 
                    hide_index=True,
                    height=600 # Chiều cao tương đương bản đồ
                )
                
            else:
                st.warning("⚠️ Không tìm thấy đầy đủ các cột: TenCoSo, LinhVuc, Ap, SoLaoDong")
            
    else:
        # Tiêu đề chính như trong ảnh (vẫn hiển thị khi không có dữ liệu)
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>CƠ SỞ KINH DOANH BTU</h2>", unsafe_allow_html=True)
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
