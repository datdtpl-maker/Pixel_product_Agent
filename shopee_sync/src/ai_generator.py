import os
import re
import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("ai_generator")

# Các từ cấm trên Shopee Việt Nam (đặc biệt đối với Mỹ phẩm & TPCN) và từ thay thế
BANNED_WORDS_MAP = {
    r"\bđặc trị\b": "hỗ trợ giảm",
    r"\btrị dứt điểm\b": "hỗ trợ giảm cải thiện",
    r"\bdứt điểm\b": "cải thiện hiệu quả",
    r"\bchữa khỏi\b": "hỗ trợ cải thiện",
    r"\bthuốc trị\b": "sản phẩm hỗ trợ",
    r"\bthuốc\b": "viên uống", # Dành cho thực phẩm chức năng như Zicum
    r"\b100%\b": "hoàn toàn",
    r"\btuyệt đối\b": "tối ưu",
    r"\btốt nhất\b": "chất lượng cao",
    r"\bsố 1\b": "hàng đầu",
    r"\bsố một\b": "hàng đầu"
}

def clean_banned_words(text: str) -> str:
    """
    Hậu kiểm quét sạch các từ cấm Shopee khỏi văn bản để đảm bảo an toàn tuyệt đối.
    """
    cleaned = text
    for pattern, replacement in BANNED_WORDS_MAP.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned

def generate_shopee_content(product_title: str, insight_name: str, api_key: str) -> Dict[str, str]:
    """
    Tự động nhận diện loại API key (OpenAI hay Gemini) để sinh Tiêu đề và Mô tả sản phẩm tối ưu,
    tuân thủ nghiêm ngặt chính sách của Shopee VN.
    """
    if not api_key:
        logger.warning("Không tìm thấy API Key. Sử dụng nội dung fallback mặc định.")
        return generate_fallback_content(product_title, insight_name)

    # Xây dựng prompt viết bài Shopee chuẩn SEO & Marketing chuyên nghiệp
    prompt = f"""
Bạn là chuyên gia tối ưu nội dung bán hàng (Copywriter SEO) xuất sắc trên các sàn TMĐT (Shopee, Lazada, TikTok Shop) tại Việt Nam.
Hãy viết nội dung bán hàng cực kỳ thuyết phục và chuẩn SEO cho sản phẩm sau:
- Tên sản phẩm gốc: "{product_title}"
- Insight khách hàng mục tiêu cần bám sát: "{insight_name}"

QUY TẮC PHÙ HỢP CHÍNH SÁCH SÀN TMĐT (TUYỆT ĐỐI TUÂN THỦ):
Để tránh bị khóa sản phẩm hoặc quét lỗi vi phạm ngành hàng Sức Khỏe & Làm Đẹp, bạn BẮT BUỘC phải tuân thủ:
1. KHÔNG dùng các từ khẳng định y khoa, chữa bệnh như: "đặc trị", "trị mụn", "điều trị", "dứt điểm", "trị dứt điểm", "chữa khỏi", "thuốc" (đây là thực phẩm chức năng, không phải thuốc).
2. THAY THẾ bằng các từ an toàn chuẩn thương mại điện tử: "hỗ trợ giảm mụn", "giúp cải thiện da mụn", "chăm sóc da mụn", "viên uống bổ sung", "hiệu quả", "cân bằng dầu nhờn".
3. TUYỆT ĐỐI KHÔNG dùng từ nói quá: "100%", "tốt nhất", "số 1", "cam kết hoàn tiền", "vĩnh viễn".
4. KHÔNG chèn số điện thoại, link website, zalo hay thông tin liên hệ ngoài Shopee để tránh lỗi điều hướng khách hàng.

PHONG CÁCH VIẾT & CẤU TRÚC NỘI DUNG CHUYÊN NGHIỆP:
- **Ngắn gọn, dễ đọc, không lan man:** Dùng các câu ngắn, từ ngữ gãy gọn, trực diện. Tránh văn phong hoa mỹ sáo rỗng. Khách hàng chủ yếu đọc trên điện thoại nên nội dung cần phân đoạn rõ ràng bằng khoảng trắng.
- **Bám sát Insight:** Phần mở đầu phải đánh trúng tâm lý, hoàn cảnh của nhóm khách hàng có insight "{insight_name}".
- **Emoji tinh tế:** Sử dụng emoji làm điểm nhấn sạch sẽ (ví dụ: 🍀, ⭐, 💊, 📦), không lạm dụng quá nhiều gây rối mắt.

Cấu trúc bài viết gồm các phần phân tách rõ ràng:
1. **Tiêu đề sản phẩm (Title):**
   - Lồng ghép tên sản phẩm gốc và từ khóa phụ hướng tới Insight: "{insight_name}".
   - Chuẩn SEO, kích thích click, ngắn gọn và KHÔNG QUÁ 120 ký tự.
2. **Hook (Mở đầu):** 2-3 câu ngắn đánh thẳng vào nỗi đau/mong muốn của nhóm khách hàng theo insight "{insight_name}".
3. **Ưu điểm nổi bật (Giải pháp):** 3-4 gạch đầu dòng ngắn gọn nêu lý do vì sao sản phẩm này giải quyết được vấn đề của họ.
4. **Thông tin chi tiết & Thành phần:** Ghi rõ hàm lượng kẽm gluconate và công dụng bổ sung đề kháng.
5. **Hướng dẫn sử dụng & Liều dùng** (ngắn gọn, trực quan).
6. **Cam kết dịch vụ từ Shop** (đóng gói kỹ, hàng chính hãng, hỗ trợ nhanh).

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (CHỈ TRẢ VỀ JSON):
Trả về kết quả ở định dạng JSON duy nhất, không kèm theo bất kỳ văn bản giải thích nào khác ngoài JSON. Cấu trúc JSON như sau:
{{
  "title": "Tiêu đề tối ưu Shopee (<120 ký tự, chuẩn SEO)",
  "description": "Mô tả sản phẩm chi tiết chuyên nghiệp chuẩn SEO"
}}
"""

    # Phát hiện loại API key
    is_openai = api_key.startswith("sk-")
    
    if is_openai:
        # Triển khai gọi OpenAI API
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional Shopee VN copywriter. You must reply with a valid JSON object matching the requested schema. Do not write anything outside the JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"}
        }
        
        try:
            logger.info(f"Đang gửi yêu cầu tới OpenAI (gpt-4o-mini) cho sản phẩm '{product_title}'...")
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            response.raise_for_status()
            
            result_json = response.json()
            raw_text = result_json["choices"][0]["message"]["content"].strip()
            
            data = json.loads(raw_text)
            title = clean_banned_words(data.get("title", product_title))
            description = clean_banned_words(data.get("description", ""))
            
            if len(title) > 120:
                title = title[:117] + "..."
                
            logger.info("Sinh nội dung bằng OpenAI thành công!")
            return {
                "title": title,
                "description": description
            }
        except Exception as e:
            logger.error(f"Lỗi khi gọi OpenAI API: {e}. Sử dụng fallback.")
            return generate_fallback_content(product_title, insight_name)
            
    else:
        # Triển khai gọi Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            logger.info(f"Đang gửi yêu cầu tới Gemini cho sản phẩm '{product_title}'...")
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            response.raise_for_status()
            
            result_json = response.json()
            raw_text = result_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Làm sạch các ký tự markdown nếu AI vô tình trả về
            if raw_text.startswith("```"):
                match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw_text)
                if match:
                    raw_text = match.group(1).strip()
                    
            data = json.loads(raw_text)
            title = clean_banned_words(data.get("title", product_title))
            description = clean_banned_words(data.get("description", ""))
            
            if len(title) > 120:
                title = title[:117] + "..."
                
            logger.info("Sinh nội dung bằng Gemini thành công!")
            return {
                "title": title,
                "description": description
            }
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini API: {e}. Sử dụng fallback.")
            return generate_fallback_content(product_title, insight_name)

def generate_fallback_content(product_title: str, insight_name: str) -> Dict[str, str]:
    """
    Sinh nội dung mặc định (fallback) khi không có API Key hoặc bị lỗi kết nối.
    """
    title = f"{product_title} - Hỗ Trợ Giảm Mụn, Sáng Da (Bản {insight_name})"
    if len(title) > 120:
        title = title[:117] + "..."
        
    # Tạo mô tả mẫu
    description = f"""✨ {product_title} (Phiên bản chuyên biệt dành cho: {insight_name}) ✨

Chào mừng bạn đến với gian hàng chính hãng! Chúng tôi tự hào mang đến sản phẩm viên uống bổ sung kẽm chất lượng cao, an toàn và hiệu quả hàng đầu cho làn da của bạn.

🍀 ĐỐI TƯỢNG SỬ DỤNG PHÙ HỢP:
- Sản phẩm được tối ưu cho nhóm đối tượng: {insight_name}.
- Người gặp các vấn đề về da dầu mụn, da dễ nổi mụn do các tác nhân môi trường, nội tiết hoặc stress.
- Người cần bổ sung kẽm tăng cường sức đề kháng cho cơ thể.

⭐ CÔNG DỤNG VÀ ƯU ĐIỂM NỔI BẬT:
- Hỗ trợ làm dịu làn da bị tổn thương do mụn, hỗ trợ giảm mụn và giúp cải thiện tình trạng dầu nhờn trên da.
- Bổ sung hàm lượng kẽm thiết yếu cho hệ miễn dịch khỏe mạnh.
- Giúp cải thiện nhanh chóng các vùng da mụn, tăng sinh tế bào da khỏe mạnh.

💊 HƯỚNG DẪN SỬ DỤNG:
- Uống trực tiếp sau bữa ăn để cơ thể hấp thu tốt nhất.
- Liều lượng: Sử dụng theo hướng dẫn chi tiết trên bao bì hoặc chỉ định của chuyên gia sức khỏe.

📦 HƯỚNG DẪN BẢO QUẢN:
- Bảo quản nơi khô ráo, thoáng mát dưới 30°C.
- Tránh ánh nắng mặt trời trực tiếp. Để xa tầm tay trẻ em.

👉 CAM KẾT TỪ SHOP:
- Sản phẩm chính hãng 100%, rõ ràng xuất xứ.
- Đóng gói cẩn thận, bảo mật thông tin đơn hàng. Giao hàng nhanh chóng toàn quốc."""

    return {
        "title": title,
        "description": description
    }

def moderate_and_fix_shopee_description(description: str, api_key: str) -> str:
    """
    Sử dụng AI để kiểm duyệt và chỉnh sửa mô tả sản phẩm, loại bỏ các từ vi phạm chính sách Shopee
    nhưng vẫn giữ nguyên cấu trúc định dạng gốc (headings, lists, callouts...).
    """
    if not api_key:
        logger.warning("Không tìm thấy API Key để chạy kiểm duyệt AI. Sử dụng cơ chế lọc regex cơ bản.")
        return clean_banned_words(description)
        
    prompt = f"""Bạn là một chuyên gia kiểm duyệt và tối ưu nội dung sản phẩm trên sàn TMĐT Shopee Việt Nam.
Nhiệm vụ của bạn là kiểm duyệt và chỉnh sửa lại mô tả sản phẩm dưới đây sao cho:
1. KHÔNG vi phạm chính sách bán hàng của Shopee Việt Nam (đặc biệt trong ngành hàng Sức Khỏe & Sắc Đẹp / Mỹ phẩm / Thực phẩm chức năng).
2. KHÔNG dùng các từ khẳng định y khoa, chữa bệnh như: "đặc trị", "trị mụn", "điều trị", "dứt điểm", "trị dứt điểm", "chữa khỏi", "thuốc". Hãy thay thế bằng các từ an toàn như: "hỗ trợ giảm mụn", "giúp cải thiện da mụn", "chăm sóc da mụn", "sản phẩm bổ sung", "hiệu quả", "cải thiện". (Sản phẩm này là thực phẩm bảo vệ sức khỏe hoặc mỹ phẩm).
3. KHÔNG sử dụng từ ngữ nói quá, phóng đại: "100%", "tốt nhất", "số 1", "cam kết hoàn tiền", "vĩnh viễn", "tuyệt đối". Hãy thay thế bằng từ nhẹ nhàng hơn (ví dụ: "chất lượng cao", "hàng đầu", "tối ưu", "cải thiện tối đa").
4. KHÔNG chèn số điện thoại, link website ngoài, link mạng xã hội, zalo, v.v. (nếu có, hãy xóa bỏ chúng).
5. GIỮ NGUYÊN HOÀN TOÀN CẤU TRÚC ĐỊNH DẠNG gốc của văn bản mô tả (bao gồm các emoji đầu dòng, các tiêu đề dạng viết hoa, thụt lề bằng dấu gạch ngang, callout dạng 💡, quotes dạng >, các dòng trống phân đoạn). Hãy chỉ sửa đổi câu chữ bên trong để tuân thủ chính sách Shopee.

Nội dung mô tả sản phẩm gốc:
\"\"\"
{description}
\"\"\"

Hãy trả về CHỈ nội dung mô tả đã được chỉnh sửa sạch sẽ và tuân thủ chính sách. Không trả về bất kỳ văn bản giới thiệu nào khác ở đầu hoặc ở cuối. Không bao quanh câu trả lời bằng markdown code blocks (như ```)."""

    is_openai = api_key.startswith("sk-")
    
    if is_openai:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional Shopee VN content moderator. You must return only the corrected description text without any markdown wrappers, code blocks or introductory text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        }
        
        try:
            logger.info("Đang kiểm duyệt mô tả sản phẩm bằng OpenAI...")
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            response.raise_for_status()
            result_json = response.json()
            raw_text = result_json["choices"][0]["message"]["content"].strip()
            
            # Xóa markdown code block wrapper nếu AI tự thêm
            if raw_text.startswith("```"):
                match = re.search(r"```(?:[a-zA-Z0-9_-]+)?\s*([\s\S]+?)\s*```", raw_text)
                if match:
                    raw_text = match.group(1).strip()
            
            # Vẫn chạy thêm clean_banned_words để đảm bảo an toàn tuyệt đối
            return clean_banned_words(raw_text)
        except Exception as e:
            logger.error(f"Lỗi khi gọi OpenAI để kiểm duyệt: {e}. Sử dụng lọc regex.")
            return clean_banned_words(description)
            
    else:
        # Gọi Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        
        try:
            logger.info("Đang kiểm duyệt mô tả sản phẩm bằng Gemini...")
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            response.raise_for_status()
            result_json = response.json()
            raw_text = result_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            if raw_text.startswith("```"):
                match = re.search(r"```(?:[a-zA-Z0-9_-]+)?\s*([\s\S]+?)\s*```", raw_text)
                if match:
                    raw_text = match.group(1).strip()
                    
            return clean_banned_words(raw_text)
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini để kiểm duyệt: {e}. Sử dụng lọc regex.")
            return clean_banned_words(description)

# Bản đồ phân loại ngành hàng Shopee Việt Nam và các từ khóa đặc trưng (dành cho Dược mỹ phẩm GSV)
CATEGORIES_MAP: Dict[str, Dict[str, Any]] = {
    "HEALTH_SUPPLEMENT": {
        "id": 101543,
        "name": "Sức khỏe > Thực phẩm chức năng > Thực phẩm bổ sung",
        "keywords": ["kẽm", "zinc", "vitamin", "viên uống", "bổ sung", "đề kháng", "collagen", "thực phẩm chức năng", "thảo dược", "sâm", "bổ gan", "bổ não", "xương khớp", "giảm cân", "tăng cân", "chất xơ", "dinh dưỡng", "acid amin", "axit amin"]
    },
    "SERUM": {
        "id": 11035552,
        "name": "Sắc đẹp > Chăm sóc da mặt > Tinh chất dưỡng da",
        "keywords": ["serum", "tinh chất dưỡng da", "tinh chất", "ampoule", "essence"]
    },
    "CLEANSER": {
        "id": 11035550,
        "name": "Sắc đẹp > Chăm sóc da mặt > Sữa rửa mặt",
        "keywords": ["sữa rửa mặt", "gel rửa mặt", "cleanser", "foaming cleanser"]
    },
    "MOISTURIZER": {
        "id": 11035554,
        "name": "Sắc đẹp > Chăm sóc da mặt > Kem dưỡng ẩm",
        "keywords": ["kem dưỡng ẩm", "gel dưỡng ẩm", "kem dưỡng", "moisturizer", "cream"]
    },
    "SKINCARE": {
        "id": 11035544,
        "name": "Sắc đẹp > Chăm sóc da mặt",
        "keywords": ["tẩy trang", "toner", "nước hoa hồng", "mặt nạ", "kem chống nắng", "trị mụn", "tẩy tế bào chết", "mỹ phẩm", "chăm sóc da", "kem thoa", "bôi ngoài", "dưỡng ẩm"]
    },
    "BATH_BODY": {
        "id": 11035609,
        "name": "Sắc đẹp > Tắm & Chăm sóc cơ thể",
        "keywords": ["sữa tắm", "dưỡng thể", "lăn khử mùi", "tẩy tế bào chết body", "soap", "xà phòng", "dưỡng ẩm body", "kem tay"]
    },
    "HAIRCARE": {
        "id": 11035609,
        "name": "Sắc đẹp > Chăm sóc tóc",
        "keywords": ["dầu gội", "dầu xả", "dưỡng tóc", "serum tóc", "ủ tóc", "thuốc nhuộm", "rụng tóc", "gàu", "da đầu"]
    },
    "MEDICAL_DEVICE": {
        "id": 11036394,
        "name": "Sức khỏe > Thiết bị y tế",
        "keywords": ["khẩu trang", "đo huyết áp", "nhiệt kế", "băng dán", "y tế", "thiết bị y tế", "hỗ trợ y tế", "băng gạc", "găng tay y tế"]
    },
    "BABY": {
        "id": 11035567,
        "name": "Mẹ & Bé",
        "keywords": ["sữa bột", "tã", "bỉm", "đồ chơi trẻ em", "bình sữa", "cho bé", "tắm bé", "sơ sinh", "trẻ nhỏ"]
    },
    "DEFAULT_HEALTH": {
        "id": 11035610,
        "name": "Sức khỏe > Khác",
        "keywords": []
    }
}

def remove_vietnamese_tones(input_str: str) -> str:
    """Loại bỏ dấu tiếng Việt để hỗ trợ so khớp từ khóa không dấu."""
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẬheadingẬẸẹẺẻẼẽẾếỀềỂểỄễỆệỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s2 = u'AAAAEEEIIOOOOUYaaaaeeeiioooouyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    
    # Tạo map chuyển đổi
    char_map = {ord(c1): c2 for c1, c2 in zip(s1, s2)}
    return input_str.translate(char_map)

def classify_product_category(title: str, description: str, api_key: str = None) -> int:
    """
    Tự động phân tích tên và mô tả sản phẩm để chọn ra mã danh mục (Category ID) Shopee Việt Nam chính xác.
    Sử dụng kết hợp Rule-based (so khớp từ khóa) và AI-based làm fallback.
    """
    logger.info(f"Bắt đầu phân loại danh mục cho sản phẩm: '{title}'")
    
    # 1. Chuẩn bị chuỗi text để so khớp (chuyển sang lowercase và loại bỏ dấu)
    full_text = f"{title} {description}".lower()
    text_no_tones = remove_vietnamese_tones(full_text)
    
    # 2. Bước 1: Quy tắc từ khóa (Rule-based)
    scores = {}
    for cat_key, cat_info in CATEGORIES_MAP.items():
        if cat_key == "DEFAULT_HEALTH":
            continue
        
        score = 0
        for keyword in cat_info["keywords"]:
            # So khớp cả có dấu và không dấu
            kw_lower = keyword.lower()
            kw_no_tones = remove_vietnamese_tones(kw_lower)
            
            # Đếm số lượng xuất hiện của từ khóa
            # Sử dụng regex word boundary để tránh khớp một phần từ (ví dụ "kẽm" khớp trong "kẽm...")
            pattern = rf"\b{re.escape(kw_lower)}\b"
            pattern_no_tones = rf"\b{re.escape(kw_no_tones)}\b"
            
            score += len(re.findall(pattern, full_text))
            score += len(re.findall(pattern_no_tones, text_no_tones))
            
        if score > 0:
            scores[cat_key] = score
            
    # Nếu tìm thấy danh mục khớp và có một danh mục vượt trội rõ rệt
    if scores:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_cat, best_score = sorted_scores[0]
        logger.info(f"Phân loại bằng Quy tắc từ khóa thành công: {best_cat} (Điểm số: {best_score})")
        return CATEGORIES_MAP[best_cat]["id"]
        
    # 3. Bước 2: Phân loại bằng AI (nếu quy tắc từ khóa không khớp)
    if not api_key:
        logger.warning("Không tìm thấy API Key để chạy phân loại AI. Sử dụng danh mục mặc định Sức khỏe.")
        # Fallback đặc biệt: nếu tiêu đề có chứa chữ liên quan đến y tế/sức khỏe
        return CATEGORIES_MAP["DEFAULT_HEALTH"]["id"]
        
    # Rút ngắn mô tả để tiết kiệm token
    short_desc = description[:250].strip()
    
    prompt = f"""Bạn là một chuyên gia phân loại danh mục ngành hàng sản phẩm trên sàn TMĐT Shopee Việt Nam.
Hãy phân tích sản phẩm sau đây:
- Tiêu đề: "{title}"
- Mô tả tóm tắt: "{short_desc}"

Nhiệm vụ của bạn là phân loại sản phẩm này vào MỘT TRONG CÁC khóa danh mục dưới đây:
1. HEALTH_SUPPLEMENT: Sức khỏe > Thực phẩm chức năng > Thực phẩm bổ sung (bao gồm vitamin, kẽm, viên uống bổ sung, tăng đề kháng, collagen, bổ gan, bổ não, hỗ trợ xương khớp, hỗ trợ giảm cân/tăng cân...)
2. SERUM: Sắc đẹp > Chăm sóc da mặt > Tinh chất dưỡng da / Serum
3. CLEANSER: Sắc đẹp > Chăm sóc da mặt > Sữa rửa mặt / Gel rửa mặt
4. MOISTURIZER: Sắc đẹp > Chăm sóc da mặt > Kem dưỡng ẩm / Gel dưỡng ẩm
5. SKINCARE: Sắc đẹp > Chăm sóc da mặt (chung cho các sản phẩm khác như tẩy trang, mặt nạ, toner, kem chống nắng, kem trị mụn thoa ngoài...)
6. BATH_BODY: Sắc đẹp > Tắm & Chăm sóc cơ thể (sữa tắm, dưỡng thể, lăn khử mùi, xà phòng...)
7. HAIRCARE: Sắc đẹp > Chăm sóc tóc (dầu gội, dầu xả, dưỡng tóc, ủ tóc...)
8. MEDICAL_DEVICE: Sức khỏe > Thiết bị y tế (khẩu trang y tế, máy đo huyết áp, nhiệt kế...)
9. BABY: Mẹ & Bé (tã bỉm, sữa bột, đồ dùng trẻ em...)
10. DEFAULT_HEALTH: Các sản phẩm sức khỏe khác hoặc không thuộc nhóm nào ở trên.

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:
Chỉ trả về duy nhất chuỗi ký tự là tên khóa danh mục viết hoa (ví dụ: HEALTH_SUPPLEMENT hoặc SERUM hoặc CLEANSER). Tuyệt đối không viết thêm bất kỳ từ ngữ giải thích nào khác ở đầu hoặc ở cuối. Không bao quanh bằng markdown hay dấu nháy.
"""

    is_openai = api_key.startswith("sk-")
    
    if is_openai:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a Shopee VN category classification bot. You must only output the exact category key name."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1
        }
        
        try:
            logger.info("Đang gọi OpenAI để phân loại danh mục sản phẩm...")
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            result_json = response.json()
            raw_text = result_json["choices"][0]["message"]["content"].strip().upper()
            
            # Làm sạch nếu AI trả về linh tinh
            for cat_key in CATEGORIES_MAP.keys():
                if cat_key in raw_text:
                    logger.info(f"AI OpenAI phân loại sản phẩm thuộc danh mục: {cat_key}")
                    return CATEGORIES_MAP[cat_key]["id"]
        except Exception as e:
            logger.error(f"Lỗi khi gọi OpenAI để phân loại: {e}")
            
    else:
        # Gọi Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1
            }
        }
        
        try:
            logger.info("Đang gọi Gemini để phân loại danh mục sản phẩm...")
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            result_json = response.json()
            raw_text = result_json["candidates"][0]["content"]["parts"][0]["text"].strip().upper()
            
            for cat_key in CATEGORIES_MAP.keys():
                if cat_key in raw_text:
                    logger.info(f"AI Gemini phân loại sản phẩm thuộc danh mục: {cat_key}")
                    return CATEGORIES_MAP[cat_key]["id"]
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini để phân loại: {e}")

    # 4. Fallback mặc định
    logger.info("Sử dụng danh mục mặc định: Sức khỏe > Khác")
    return CATEGORIES_MAP["DEFAULT_HEALTH"]["id"]

