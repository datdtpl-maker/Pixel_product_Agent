import re

def extract():
    with open("drive_debug.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    # Tìm các đoạn AF_initDataCallback
    callbacks = re.findall(r'AF_initDataCallback\(\{key:\s*\'ds:\d+\',[^\)]+\}\);', html)
    
    output_lines = [f"Tim thay {len(callbacks)} khoi callback."]
    
    for i, cb in enumerate(callbacks):
        # Chỉ lấy 500 ký tự đầu tiên của mỗi callback để tránh log quá dài
        output_lines.append(f"\n--- Callback {i} ---")
        output_lines.append(cb[:1000] + "...")
        
    with open("callbacks_extracted.txt", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(output_lines))

if __name__ == "__main__":
    extract()
