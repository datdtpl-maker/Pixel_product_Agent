import json
import logging
from . import config
from . import auth
from . import shopee_client

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_local")

def run_tests():
    logger.info("=== BẮT ĐẦU CHẠY THỬ NGHIỆM LOCAL (MOCK MODE) ===")
    
    # 1. Đọc thông tin cấu hình
    logger.info("1. Đọc cấu hình hiện tại:")
    summary = config.get_config_summary()
    logger.info(json.dumps(summary, indent=2))
    
    if not config.MOCK_MODE:
        logger.warning("Cảnh báo: Đang tắt MOCK_MODE. Quá trình kiểm thử này sẽ gọi trực tiếp đến API Shopee thật.")
    else:
        logger.info("MOCK_MODE=True được kích hoạt. Tiến hành giả lập các request.")
        
    # 2. Kiểm tra sinh Auth URL
    logger.info("\n2. Kiểm tra sinh URL đăng nhập Shopee:")
    auth_url = auth.get_auth_url()
    logger.info(f"Auth URL: {auth_url}")
    
    # 3. Thử đổi Token
    logger.info("\n3. Kiểm tra cấp token đầu tiên bằng auth_code:")
    tokens_res = auth.fetch_tokens("mock_auth_code_123456")
    logger.info(f"Kết quả lấy Token: {json.dumps(tokens_res, indent=2)}")
    
    # 4. Lấy danh mục ngành hàng
    logger.info("\n4. Kiểm tra lấy danh mục Shopee:")
    categories = shopee_client.get_categories()
    logger.info(f"Số lượng danh mục trả về: {len(categories)}")
    logger.info(f"Danh mục đầu tiên: {json.dumps(categories[0], ensure_ascii=False)}")
    
    # 5. Lấy đơn vị vận chuyển
    logger.info("\n5. Kiểm tra lấy đơn vị vận chuyển:")
    channels = shopee_client.get_logistic_channels()
    logger.info(f"Đơn vị vận chuyển đang bật: {[ch['logistic_name'] for ch in channels if ch['enabled']]}")
    
    # 6. Upload ảnh
    logger.info("\n6. Kiểm tra tải ảnh lên Shopee CDN:")
    img_res = shopee_client.upload_image("https://example.com/sanpham_demo.jpg")
    logger.info(f"Ảnh upload thành công: {json.dumps(img_res, indent=2)}")
    
    # 7. Đăng sản phẩm
    logger.info("\n7. Kiểm tra đăng sản phẩm mới:")
    item_res = shopee_client.add_product(
        item_name="Áo thun nam Cotton basic thoáng mát",
        description="Áo thun nam chất liệu 100% cotton tự nhiên mềm mại, co giãn tốt, thấm hút mồ hôi hiệu quả. Thiết kế trẻ trung năng động phù hợp mặc đi chơi, đi làm.",
        original_price=129000.0,
        normal_stock=150,
        category_id=100002,
        image_id_list=[img_res["image_id"]],
        weight=0.2,
        logistic_ids=[50001, 50002],
        brand_name="No Brand"
    )
    logger.info(f"Kết quả đăng sản phẩm: {json.dumps(item_res, ensure_ascii=False, indent=2)}")
    
    logger.info("\n=== TẤT CẢ CÁC BƯỚC KHỞI CHẠY KIỂM THỬ THÀNH CÔNG ===")

if __name__ == "__main__":
    run_tests()
