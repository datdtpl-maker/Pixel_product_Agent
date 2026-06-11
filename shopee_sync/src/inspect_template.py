import json
import pandas as pd
from pathlib import Path

def inspect():
    template_path = r"C:\Users\datdt\Downloads\import_template_VN.xlsx"
    # Đọc file không chỉ định header để lấy toàn bộ các hàng trên cùng
    df = pd.read_excel(template_path, header=None)
    
    # Lấy 5 dòng đầu tiên để phân tích tiêu đề và định dạng
    first_rows = df.head(5).values.tolist()
    
    # Lấy thông tin về số lượng cột và kích thước
    shape = df.shape
    
    result = {
        "shape": shape,
        "first_5_rows": first_rows
    }
    
    output_path = Path(__file__).resolve().parent.parent / "template_structure.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
        
    print(f"Đã xuất cấu trúc file mẫu sang: {output_path}")

if __name__ == "__main__":
    inspect()
