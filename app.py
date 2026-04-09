import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    layout="wide", 
    page_title="Hệ thống quản lý Bắc Tân Uyên",
    page_icon="📍"
)

# --- 2. HÀM KIỂM TRA ĐĂNG NHẬP ---
def check_password():
    """Kiểm tra mật khẩu từ mục [credentials] trong Secrets."""
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>HỆ THỐNG QUẢN LÝ ĐỊA BÀN</h2>", unsafe_allow_html=True)
        st.write("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("Vui lòng đăng nhập để truy cập dữ liệu xã Bắc Tân Uyên")
            password_input = st.text_input("Mật khẩu:", type="password")
            if st.button("Xác nhận đăng nhập", use_container_width=True):
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
        st.title("📍 Bản đồ Cơ sở Kinh doanh - Bắc Tân Uyên")
        
        # --- BỘ LỌC TẠI SIDEBAR ---
        st.sidebar.header("Bộ lọc tìm kiếm")
        
        # Lọc theo Ấp
        if 'Ap' in df.columns:
            list_ap = sorted(df['Ap'].unique().tolist())
            selected_ap = st.sidebar.multiselect("Chọn Ấp:", list_ap, default=list_ap)
            df_loc = df[df['Ap'].isin(selected_ap)]
        else:
            df_loc = df

        # --- 4. HIỂN THỊ BẢN ĐỒ FOLIUM ---
        # Tọa độ mặc định trung tâm xã Bắc Tân Uyên (vùng UBND xã)
        BTU_CENTER = [11.1684, 106.8406]
        
        m = folium.Map(location=BTU_CENTER, zoom_start=14, control_scale=True)

        for _, row in df_loc.iterrows():
            # Kiểm tra cột ViTri (tọa độ từ AppSheet)
            vitri = row.get('ViTri')
            if pd.notnull(vitri) and vitri != "":
                try:
                    lat, lon = map(float, str(vitri).split(','))
                    
                    # Phân màu theo Lĩnh vực
                    color = "blue"
                    linh_vuc = str(row.get('LinhVuc', '')).lower()
                    if "công ty" in linh_vuc: color = "red"
                    elif "hộ kinh doanh" in linh_vuc: color = "green"

                    popup_content = f"""
                        <div style='min-width: 150px; font-family: sans-serif;'>
                            <b style='color: #1E3A8A;'>{row.get('TenCoSo', 'N/A')}</b><br>
                            <b>Ấp:</b> {row.get('Ap', 'N/A')}<br>
                            <b>Lao động:</b> {row.get('SoLaoDong', 0)}<br>
                            <hr style='margin: 5px 0;'>
                            <b>Trạng thái:</b> {row.get('TrangThai', 'N/A')}
                        </div>
                    """
                    
                    folium.Marker(
                        [lat, lon],
                        popup=folium.Popup(popup_content, max_width=300),
                        tooltip=row.get('TenCoSo', 'Xem chi tiết'),
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(m)
                except:
                    continue

        # Hiển thị bản đồ
        st_folium(m, width="100%", height=550, returned_objects=[])

        # --- 5. BẢNG DỮ LIỆU CHI TIẾT ---
        with st.expander("📊 Xem danh sách dữ liệu chi tiết"):
            st.dataframe(df_loc, use_container_width=True, hide_index=True)
            
    else:
        st.warning("⚠️ Không có dữ liệu để hiển thị. Kiểm tra lại tên Sheet 'ThongTin' hoặc quyền của Service Account.")
