import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RedisConnectionError(Exception):
    pass

class MockDatabase:
    def __init__(self):
        self.storage = {"iPhone 15": 100}

    def get_inventory(self, product_id):
        logging.info(f"[Database] Đang lấy tồn kho cho sản phẩm: {product_id}")
        return self.storage.get(product_id, None)

    def update_inventory(self, product_id, quantity):
        logging.info(f"[Database] Cập nhật tồn kho {product_id} thành {quantity}")
        self.storage[product_id] = quantity
        return quantity

class MockRedisCache:
    def __init__(self, ttl=60):
        self.cache = {}
        self.fail_mode = False
        self.ttl = ttl

    def get(self, product_id):
        if self.fail_mode:
            raise RedisConnectionError("Mất kết nối Redis khi đọc!")
        logging.info(f"[Redis Cache] Đọc cache cho sản phẩm: {product_id}")
        return self.cache.get(product_id, None)

    def set(self, product_id, quantity):
        if self.fail_mode:
            raise RedisConnectionError("Mất kết nối Redis khi ghi!")
        logging.info(f"[Redis Cache] Nạp cache cho sản phẩm {product_id} với số lượng {quantity} (TTL: {self.ttl}s)")
        self.cache[product_id] = quantity

    def evict(self, product_id):
        if self.fail_mode:
            raise RedisConnectionError("Mất kết nối Redis khi xóa cache!")
        if product_id in self.cache:
            logging.info(f"[Redis Cache] Xóa cache (evict) cho sản phẩm: {product_id}")
            del self.cache[product_id]

class InventoryService:
    def __init__(self, db: MockDatabase, cache: MockRedisCache):
        self.db = db
        self.cache = cache

    def get_product_inventory(self, product_id: str):
        if not product_id or not product_id.strip():
            raise ValueError("Product ID không được để trống")
        
        try:
            cached_qty = self.cache.get(product_id)
            if cached_qty is not None:
                logging.info(f"[Cache Hit] Sản phẩm {product_id} có sẵn trong cache: {cached_qty}")
                return {"productId": product_id, "quantity": cached_qty}
        except RedisConnectionError as e:
            logging.warning(f"[Fallback Warning] {e}. Chuyển hướng trực tiếp xuống Database.")

        logging.info(f"[Cache Miss] Không tìm thấy cache cho {product_id}, lấy từ DB.")
        db_qty = self.db.get_inventory(product_id)
        if db_qty is None:
            return None

        try:
            self.cache.set(product_id, db_qty)
        except RedisConnectionError as e:
            logging.warning(f"[Redis Error] Không thể nạp cache sau khi lấy từ DB: {e}")

        return {"productId": product_id, "quantity": db_qty}

    def update_product_inventory(self, product_id: str, new_quantity: int):
        if not product_id or not product_id.strip():
            raise ValueError("Product ID không được để trống")
        if new_quantity < 0:
            raise ValueError(f"Số lượng tồn kho không được âm: {new_quantity}")

        self.db.update_inventory(product_id, new_quantity)

        try:
            self.cache.evict(product_id)
        except RedisConnectionError as e:
            logging.error(f"[Redis Evict Error] Không thể xóa cache: {e}. TTL ngắn sẽ giúp tự động hết hạn dữ liệu cũ.")

        return {"productId": product_id, "quantity": new_quantity}

if __name__ == "__main__":
    db = MockDatabase()
    cache = MockRedisCache()
    service = InventoryService(db, cache)

    print("--- 1. Kiểm tra luồng đọc chuẩn (Cache Miss -> DB -> Cache Hit) ---")
    print(service.get_product_inventory("iPhone 15"))
    print(service.get_product_inventory("iPhone 15"))

    print("\n--- 2. Kiểm tra luồng ghi chuẩn (Cập nhật DB -> Xóa Cache) ---")
    print(service.update_product_inventory("iPhone 15", 95))
    print(service.get_product_inventory("iPhone 15"))

    print("\n--- 3. Kiểm tra tình huống nhập số lượng âm ---")
    try:
        service.update_product_inventory("iPhone 15", -10)
    except ValueError as e:
        logging.error(f"Bắt lỗi thành công: {e}")

    print("\n--- 4. Kiểm tra sự cố Redis khi đọc (Fallback xuống DB) ---")
    cache.fail_mode = True
    print(service.get_product_inventory("iPhone 15"))
