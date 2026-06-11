import re

with open("drive_debug.html", "r", encoding="utf-8") as f:
    html = f.read()

# Lọc các ID bắt đầu bằng 1 và có độ dài đúng 33 ký tự
candidates = re.findall(r'"(1[a-zA-Z0-9_-]{32})"', html)

image_ids = []
for cid in candidates:
    if cid not in image_ids:
        image_ids.append(cid)

print(f"Tim thay {len(image_ids)} file IDs:")
for img_id in image_ids:
    print(f"- {img_id}")
