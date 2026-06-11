import os
import time
import logging
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from . import config
from . import auth

logger = logging.getLogger("shopee_client")

def _send_request(method: str, path: str, query_params: Optional[Dict[str, Any]] = None, payload: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Hàm helper nội bộ để ký và gửi HTTP request đến Shopee API.
    """
    access_token = auth.get_valid_access_token()
    timestamp = int(time.time())
    
    # Tạo signature dựa trên việc có access_token và shop_id
    sign = auth.generate_signature(path, timestamp, access_token, config.SHOP_ID)
    
    # Query parameters bắt buộc cho mỗi request
    params = {
        "partner_id": config.PARTNER_ID,
        "shop_id": config.SHOP_ID,
        "timestamp": timestamp,
        "sign": sign,
        "access_token": access_token
    }
    if query_params:
        params.update(query_params)
        
    url = f"{config.SHOPEE_API_URL}{path}"
    
    headers = {}
    if not files:
        headers["Content-Type"] = "application/json"
        
    try:
        logger.info(f"Đang gửi {method} request tới {path}...")
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method.upper() == "POST":
            if files:
                response = requests.post(url, params=params, files=files, headers=headers)
            else:
                response = requests.post(url, params=params, json=payload, headers=headers)
        else:
            raise ValueError(f"Không hỗ trợ HTTP Method: {method}")
            
        res_data = response.json()
        
        # Kiểm tra lỗi từ phía Shopee API
        if "error" in res_data and res_data["error"]:
            err_msg = res_data.get("message", res_data["error"])
            logger.error(f"Lỗi phản hồi từ Shopee API ({path}): {err_msg}")
            raise Exception(f"Shopee API Error [{path}]: {err_msg}")
            
        return res_data
        
    except Exception as e:
        logger.error(f"Lỗi kết nối khi gọi Shopee API ({path}): {e}")
        raise

def get_logistic_channels() -> List[Dict[str, Any]]:
    """
    Lấy danh sách các đơn vị vận chuyển (Logistic Channels) được cấu hình cho shop.
    """
    if config.MOCK_MODE:
        logger.info("Chạy chế độ MOCK: Trả về danh sách đơn vị vận chuyển giả lập")
        return [
            {"logistic_id": 50001, "logistic_name": "SPX Express", "enabled": True, "preferred": True},
            {"logistic_id": 50002, "logistic_name": "Giao Hàng Nhanh (GHN)", "enabled": True, "preferred": False},
            {"logistic_id": 50003, "logistic_name": "Viettel Post", "enabled": False, "preferred": False},
            {"logistic_id": 50004, "logistic_name": "Giao Hàng Tiết Kiệm (GHTK)", "enabled": True, "preferred": False}
        ]
        
    path = "/api/v2/logistics/get_channel_list"
    res = _send_request("GET", path)
    return res.get("response", {}).get("channel_list", [])

def get_categories(language: str = "vi") -> List[Dict[str, Any]]:
    """
    Lấy toàn bộ cây danh mục ngành hàng Shopee (Categories).
    """
    if config.MOCK_MODE:
        logger.info("Chạy chế độ MOCK: Trả về danh mục ngành hàng giả lập")
        return [
            {"category_id": 100001, "parent_category_id": 0, "original_category_name": "Thời Trang Nam", "display_category_name": "Thời Trang Nam", "has_child": True},
            {"category_id": 100002, "parent_category_id": 100001, "original_category_name": "Áo Thun Nam", "display_category_name": "Áo Thun Nam", "has_child": False},
            {"category_id": 100003, "parent_category_id": 0, "original_category_name": "Thiết Bị Điện Tử", "display_category_name": "Thiết Bị Điện Tử", "has_child": True},
            {"category_id": 100004, "parent_category_id": 100003, "original_category_name": "Điện Thoại Di Động", "display_category_name": "Điện Thoại Di Động", "has_child": False},
            {"category_id": 100005, "parent_category_id": 0, "original_category_name": "Nhà Cửa & Đời Sống", "display_category_name": "Nhà Cửa & Đời Sống", "has_child": True},
            {"category_id": 100006, "parent_category_id": 100005, "original_category_name": "Trang Trí Nhà Cửa", "display_category_name": "Trang Trí Nhà Cửa", "has_child": False}
        ]
        
    path = "/api/v2/product/get_category"
    res = _send_request("GET", path, query_params={"language": language})
    return res.get("response", {}).get("category_list", [])

def get_attributes(category_id: int, language: str = "vi") -> List[Dict[str, Any]]:
    """
    Lấy thông tin các thuộc tính (Attributes) yêu cầu của một Category.
    """
    if config.MOCK_MODE:
        logger.info(f"Chạy chế độ MOCK: Trả về danh sách thuộc tính giả lập cho danh mục {category_id}")
        return [
            {
                "attribute_id": 20001,
                "original_attribute_name": "Thương hiệu",
                "display_attribute_name": "Thương hiệu",
                "is_mandatory": True, # Bắt buộc
                "attribute_type": "DROP_DOWN_TYPE",
                "attribute_value_list": [{"value_id": 0, "original_value_name": "No Brand", "display_value_name": "No Brand"}]
            },
            {
                "attribute_id": 20002,
                "original_attribute_name": "Chất liệu",
                "display_attribute_name": "Chất liệu",
                "is_mandatory": False,
                "attribute_type": "FREE_TEXT_TYPE",
                "attribute_value_list": []
            },
            {
                "attribute_id": 20003,
                "original_attribute_name": "Xuất xứ",
                "display_attribute_name": "Xuất xứ",
                "is_mandatory": False,
                "attribute_type": "DROP_DOWN_TYPE",
                "attribute_value_list": [
                    {"value_id": 301, "original_value_name": "Việt Nam", "display_value_name": "Việt Nam"},
                    {"value_id": 302, "original_value_name": "Trung Quốc", "display_value_name": "Trung Quốc"}
                ]
            }
        ]
        
    path = "/api/v2/product/get_attributes"
    res = _send_request("GET", path, query_params={"category_id": category_id, "language": language})
    return res.get("response", {}).get("attribute_list", [])

def upload_image(file_path_or_url: str) -> Dict[str, Any]:
    """
    Tải ảnh lên Shopee CDN. Chấp nhận file path cục bộ hoặc URL ảnh từ web.
    """
    if config.MOCK_MODE:
        logger.info(f"Chạy chế độ MOCK: Giả lập upload hình ảnh: {file_path_or_url}")
        # Sinh ID giả lập
        import hashlib
        img_id = f"mock_img_hash_{hashlib.md5(file_path_or_url.encode()).hexdigest()}"
        return {
            "image_id": img_id,
            "image_url": f"https://cf.shopee.vn/file/{img_id}"
        }

    path = "/api/v2/product/upload_image"
    
    # Kiểm tra xem đây là URL hay đường dẫn file cục bộ
    if file_path_or_url.startswith(("http://", "https://")):
        try:
            logger.info(f"Tải ảnh từ URL để chuẩn bị upload lên Shopee: {file_path_or_url}")
            response = requests.get(file_path_or_url, timeout=15)
            response.raise_for_status()
            file_name = Path(file_path_or_url).name or "downloaded_image.jpg"
            image_content = response.content
        except Exception as e:
            logger.error(f"Không thể tải ảnh từ URL: {e}")
            raise Exception(f"Lỗi khi tải ảnh từ URL trước khi đăng Shopee: {e}")
    else:
        file_path = Path(file_path_or_url)
        if not file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file hình ảnh cục bộ: {file_path_or_url}")
        file_name = file_path.name
        with open(file_path, "rb") as f:
            image_content = f.read()

    # Chuẩn bị gửi multipart/form-data
    files = {
        "image": (file_name, image_content, "image/jpeg")
    }
    
    res = _send_request("POST", path, files=files)
    
    image_info = res.get("response", {}).get("image_info", {})
    return {
        "image_id": image_info.get("image_id"),
        "image_url": image_info.get("image_url_list", [None])[0]
    }

def add_product(
    item_name: str,
    description: str,
    original_price: float,
    normal_stock: int,
    category_id: int,
    image_id_list: List[str],
    weight: float,
    package_length: int = 10,
    package_width: int = 10,
    package_height: int = 10,
    logistic_ids: Optional[List[int]] = None,
    brand_name: str = "No Brand",
    attributes: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Đăng sản phẩm mới lên gian hàng Shopee.
    """
    # Xử lý Logistics mặc định nếu không được chỉ định
    # Nếu chạy real, ta sẽ tự động lấy danh sách channel được bật để điền nếu không truyền vào
    if not logistic_ids:
        if config.MOCK_MODE:
            logistic_ids = [50001]
        else:
            try:
                channels = get_logistic_channels()
                logistic_ids = [ch["logistic_id"] for ch in channels if ch.get("enabled")]
                if not logistic_ids:
                    raise Exception("Không tìm thấy đơn vị vận chuyển nào được bật trên shop.")
            except Exception as e:
                logger.error(f"Lỗi khi tự động cấu hình logistics: {e}")
                raise

    # Chuẩn bị logistic info payload
    logistic_info = []
    for lid in logistic_ids:
        logistic_info.append({
            "logistic_id": lid,
            "enabled": True
        })

    # Brand cấu trúc
    brand_payload = {
        "brand_id": 0, # 0 nghĩa là No Brand/Thương hiệu tự do
        "original_brand_name": brand_name
    }

    # Build Payload gửi Shopee
    payload = {
        "item_name": item_name,
        "description": description,
        "original_price": original_price,
        "normal_stock": normal_stock,
        "category_id": category_id,
        "brand": brand_payload,
        "weight": weight,
        "dimension": {
            "package_length": package_length,
            "package_width": package_width,
            "package_height": package_height
        },
        "logistic_info": logistic_info,
        "image": {
            "image_id_list": image_id_list
        }
    }

    # Thêm attributes nếu có
    if attributes:
        payload["attribute_list"] = attributes

    if config.MOCK_MODE:
        logger.info(f"Chạy chế độ MOCK: Giả lập đăng sản phẩm '{item_name}'")
        import random
        mock_item_id = random.randint(100000000, 999999999)
        return {
            "item_id": mock_item_id,
            "status": "NORMAL",
            "message": "Sản phẩm đã được tạo thành công (Chế độ giả lập)",
            "payload_sent": payload
        }

    path = "/api/v2/product/add_item"
    res = _send_request("POST", path, payload=payload)
    
    item_info = res.get("response", {})
    return {
        "item_id": item_info.get("item_id"),
        "status": "NORMAL",
        "message": "Thành công",
        "raw_response": res
    }
