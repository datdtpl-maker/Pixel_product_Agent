import re
import json

def find():
    with open("drive_debug.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    output_lines = []
    output_lines.append(f"Kich thuoc file HTML: {len(html)} bytes")
    
    folder_id = "1ztw4v6uiZirjkZT4PBXn2EDsHNWitTe5"
    if folder_id in html:
        output_lines.append("Tim thay Folder ID trong HTML!")
        positions = [m.start() for m in re.finditer(folder_id, html)]
        output_lines.append(f"Folder ID xuat hien o {len(positions)} vi tri.")
        
        pos = positions[0]
        start = max(0, pos - 200)
        end = min(len(html), pos + 300)
        output_lines.append("\n--- Cau truc xung quanh Folder ID ---")
        output_lines.append(html[start:end])
    else:
        output_lines.append("Khong tim thay Folder ID trong HTML. Co the trang yeu cau render JS dong.")
        
    # Ghi ra file
    with open("find_results.txt", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(output_lines))

if __name__ == "__main__":
    find()
