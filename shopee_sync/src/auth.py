import hmac
import hashlib
import time
import json
import logging
from typing import Dict, Any, Optional
import requests
from pathlib import Path
from . import config

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("shopee_auth")

def generate_signature(path: str, timestamp: int, access_token: Optional[str] = None, shop_id: Optional[int] = None) -> str:
    """
    Tạo chữ ký số (signature) cho API Shopee V2 theo chuẩn HMAC-SHA256.
    """
    if config.MOCK_MODE:
        return "mock_signature_1234567890abcdef"
        
    partner_id = config.PARTNER_ID
    partner_key = config.PARTNER_KEY

    if access_token and shop_id:
        # Shop-level API
        message = f"{partner_id}{path}{timestamp}{access_token}{shop_id}"
    else:
        # Public API (OAuth, Token management...)
        message = f"{partner_id}{path}{timestamp}"

    sign = hmac.new(
        partner_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return sign

def get_auth_url() -> str:
    """
    Tạo đường dẫn đăng nhập ủy quyền của Shopee (Shop Authorization Link).
    """
    path = "/api/v2/shop/auth_partner"
    timestamp = int(time.time())
    sign = generate_signature(path, timestamp)
    
    # Ở chế độ Mock
    if config.MOCK_MODE:
        return f"https://partner.test-stable.shopeemobile.com{path}?partner_id={config.PARTNER_ID}&timestamp={timestamp}&sign={sign}&redirect={config.REDIRECT_URL} (MOCK MODE ENABLED)"

    # Build URL chính thức
    url = f"{config.SHOPEE_API_URL}{path}?partner_id={config.PARTNER_ID}&timestamp={timestamp}&sign={sign}&redirect={config.REDIRECT_URL}"
    return url

def load_tokens() -> Dict[str, Any]:
    """
    Đọc cặp token hiện tại từ file local.
    """
    if not config.TOKEN_FILE_PATH.exists():
        return {}
    try:
        with open(config.TOKEN_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Lỗi khi đọc file token: {e}")
        return {}

def save_tokens(access_token: str, refresh_token: str, expires_in: int) -> None:
    """
    Lưu cặp token và tính toán thời gian hết hạn cụ thể.
    """
    expire_time = int(time.time()) + expires_in
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expire_time": expire_time,
        "updated_at": int(time.time())
    }
    try:
        # Đảm bảo thư mục cha tồn tại
        config.TOKEN_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(config.TOKEN_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info("Đã lưu token thành công.")
    except Exception as e:
        logger.error(f"Lỗi khi ghi file token: {e}")

def fetch_tokens(auth_code: str, shop_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Đổi authorization code lấy access_token và refresh_token.
    """
    # Sử dụng shop_id từ config nếu không được truyền vào
    target_shop_id = shop_id or config.SHOP_ID

    if config.MOCK_MODE:
        logger.info("Chạy chế độ MOCK: Giả lập lấy token bằng auth_code")
        mock_access = "mock_access_token_xyz123"
        mock_refresh = "mock_refresh_token_abc789"
        # Mặc định Shopee access token sống 4 tiếng (14400s)
        save_tokens(mock_access, mock_refresh, 14400)
        return {
            "access_token": mock_access,
            "refresh_token": mock_refresh,
            "expires_in": 14400,
            "shop_id": target_shop_id,
            "message": "Thành công (Giả lập)"
        }

    path = "/api/v2/auth/token/get"
    timestamp = int(time.time())
    sign = generate_signature(path, timestamp)
    
    url = f"{config.SHOPEE_API_URL}{path}?partner_id={config.PARTNER_ID}&timestamp={timestamp}&sign={sign}"
    
    payload = {
        "code": auth_code,
        "partner_id": config.PARTNER_ID,
        "shop_id": target_shop_id
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        
        if "error" in res_data and res_data["error"]:
            raise Exception(f"Shopee API Error: {res_data.get('message', res_data['error'])}")
            
        access_token = res_data.get("access_token")
        refresh_token = res_data.get("refresh_token")
        expires_in = res_data.get("expires_in", 14400)
        
        if access_token and refresh_token:
            save_tokens(access_token, refresh_token, expires_in)
            return res_data
        else:
            raise Exception(f"Không nhận được tokens trong phản hồi: {res_data}")
            
    except Exception as e:
        logger.error(f"Lỗi khi lấy tokens từ Shopee: {e}")
        raise

def refresh_token() -> Dict[str, Any]:
    """
    Làm mới access_token bằng refresh_token.
    """
    tokens = load_tokens()
    current_refresh_token = tokens.get("refresh_token")
    if not current_refresh_token:
        raise Exception("Không tìm thấy refresh_token cục bộ. Vui lòng cấp quyền (auth) trước.")
        
    if config.MOCK_MODE:
        logger.info("Chạy chế độ MOCK: Giả lập refresh token")
        mock_access = f"mock_access_token_refreshed_{int(time.time())}"
        mock_refresh = f"mock_refresh_token_refreshed_{int(time.time())}"
        save_tokens(mock_access, mock_refresh, 14400)
        return {
            "access_token": mock_access,
            "refresh_token": mock_refresh,
            "expires_in": 14400
        }

    path = "/api/v2/auth/access_token/get"
    timestamp = int(time.time())
    sign = generate_signature(path, timestamp)
    
    url = f"{config.SHOPEE_API_URL}{path}?partner_id={config.PARTNER_ID}&timestamp={timestamp}&sign={sign}"
    
    payload = {
        "refresh_token": current_refresh_token,
        "partner_id": config.PARTNER_ID,
        "shop_id": config.SHOP_ID
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        
        if "error" in res_data and res_data["error"]:
            raise Exception(f"Shopee API Error: {res_data.get('message', res_data['error'])}")
            
        access_token = res_data.get("access_token")
        refresh_token_new = res_data.get("refresh_token")
        expires_in = res_data.get("expires_in", 14400)
        
        if access_token and refresh_token_new:
            save_tokens(access_token, refresh_token_new, expires_in)
            return res_data
        else:
            raise Exception(f"Không nhận được tokens trong phản hồi: {res_data}")
            
    except Exception as e:
        logger.error(f"Lỗi khi refresh token: {e}")
        raise

def get_valid_access_token() -> str:
    """
    Lấy access_token hợp lệ. Tự động refresh nếu token sắp hết hạn (còn dưới 5 phút).
    """
    tokens = load_tokens()
    if not tokens:
        if config.MOCK_MODE:
            # Tự động lấy mock token nếu chưa có trong mock mode
            fetch_tokens("mock_code")
            tokens = load_tokens()
        else:
            raise Exception("Không tìm thấy thông tin xác thực. Hãy gọi shopee_get_auth_url và nhập code trước.")

    access_token = tokens.get("access_token")
    expire_time = tokens.get("expire_time", 0)
    
    # Kiểm tra xem token còn hạn trên 300 giây (5 phút) không
    if time.time() + 300 > expire_time:
        logger.info("Access token sắp hết hạn hoặc đã hết hạn. Bắt đầu làm mới tự động...")
        try:
            res = refresh_token()
            access_token = res.get("access_token")
        except Exception as e:
            logger.error(f"Không thể tự động làm mới token: {e}")
            # Nếu refresh thất bại nhưng vẫn còn token cũ, trả về token cũ như giải pháp tình thế
            if access_token:
                logger.warning("Sử dụng access token cũ mặc dù đã hết hạn.")
                return access_token
            raise
            
    return access_token
