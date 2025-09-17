import streamlit as st
import pandas as pd
import pyodbc
import datetime
import io

# =================== KẾT NỐI DATABASE ===================
def get_connection():
    return pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=LEDINHHUY\SQLEXPRESS;"
        r"DATABASE=QLNhanVien;"
        r"Trusted_Connection=yes;"
    )

def get_danh_sach_cham_cong():
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.datetime.now().date()

    cursor.execute("""
        SELECT c.MaChamCong, n.MaNV, n.HoTen, c.NgayLamViec, c.GioVao, c.GioRa,
               ISNULL(c.TrangThai, N'Chưa chấm công') as TrangThai
        FROM NhanVien n
        LEFT JOIN ChamCong c ON n.MaNV = c.MaNV AND c.NgayLamViec = ?
        ORDER BY n.MaNV
    """, (today,))

    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame.from_records(
        rows,
        columns=["Mã CC", "Mã NV", "Họ tên", "Ngày làm việc", "Giờ vào", "Giờ ra", "Trạng thái"]
    )
    return df

# =================== GIAO DIỆN STREAMLIT ===================
st.title("📋 Bảng chấm công")

# Hiển thị bảng
df = get_danh_sach_cham_cong()
st.dataframe(df)

# ===== Nút tải về Excel =====
if not df.empty:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="ChamCong")

    st.download_button(
        label="📥 Xuất Excel",
        data=buffer,
        file_name="ChamCong.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
