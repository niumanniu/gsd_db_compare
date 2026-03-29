-- DB Compare 测试数据初始化脚本
-- 用于初始化两个 MySQL 测试数据源

-- 创建测试数据库
CREATE DATABASE IF NOT EXISTS db_source1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS db_source2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建测试用户
CREATE USER IF NOT EXISTS 'dbuser'@'%' IDENTIFIED BY 'dbpassword123';
GRANT ALL PRIVILEGES ON db_source1.* TO 'dbuser'@'%';
GRANT ALL PRIVILEGES ON db_source2.* TO 'dbuser'@'%';
FLUSH PRIVILEGES;

-- 在 db_source1 中创建测试表
USE db_source1;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 产品表
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock INT NOT NULL DEFAULT 0,
    category_id INT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sku (sku),
    INDEX idx_category (category_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    shipping_address VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_order_no (order_no),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 订单明细表
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入测试数据
INSERT INTO users (username, email, password_hash, status) VALUES
('admin', 'admin@example.com', 'hashed_password_1', 1),
('user1', 'user1@example.com', 'hashed_password_2', 1),
('user2', 'user2@example.com', 'hashed_password_3', 1);

INSERT INTO products (name, sku, price, stock, category_id, description, is_active) VALUES
('iPhone 15 Pro', 'APPL-IP15P-001', 7999.00, 100, 1, 'Apple iPhone 15 Pro 256GB', TRUE),
('MacBook Pro 14', 'APPL-MBP14-001', 12999.00, 50, 1, 'Apple MacBook Pro 14 inch M3', TRUE),
('AirPods Pro 2', 'APPL-APP2-001', 1899.00, 200, 2, 'Apple AirPods Pro 2nd Gen', TRUE),
('iPad Air', 'APPL-IPAD-001', 4799.00, 80, 1, 'Apple iPad Air 5th Gen', TRUE);

INSERT INTO orders (order_no, user_id, total_amount, status, shipping_address) VALUES
('ORD-2024-001', 1, 9898.00, 'completed', '北京市朝阳区 xx 街道 1 号'),
('ORD-2024-002', 2, 1899.00, 'shipped', '上海市浦东新区 xx 路 2 号'),
('ORD-2024-003', 1, 4799.00, 'pending', '北京市朝阳区 xx 街道 1 号');

INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
(1, 1, 1, 7999.00, 7999.00),
(1, 3, 1, 1899.00, 1899.00),
(2, 3, 1, 1899.00, 1899.00),
(3, 4, 1, 4799.00, 4799.00);

-- 在 db_source2 中创建测试表 (结构略有不同，用于比对测试)
USE db_source2;

-- 用户表 (添加了 phone 字段)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_status (status),
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 产品表 (添加了 weight 字段)
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock INT NOT NULL DEFAULT 0,
    weight DECIMAL(8,3),
    category_id INT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sku (sku),
    INDEX idx_category (category_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 订单表 (结构相同)
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    shipping_address VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_order_no (order_no),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 订单明细表 (结构相同)
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 额外的配置表 (仅 db_source2 有)
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string',
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入测试数据到 db_source2
INSERT INTO users (username, email, password_hash, phone, status) VALUES
('admin', 'admin@example.com', 'hashed_password_1', '13800138000', 1),
('user1', 'user1@example.com', 'hashed_password_2', '13900139000', 1),
('user3', 'user3@example.com', 'hashed_password_4', '13700137000', 1);

INSERT INTO products (name, sku, price, stock, weight, category_id, description, is_active) VALUES
('iPhone 15 Pro', 'APPL-IP15P-001', 7999.00, 100, 0.187, 1, 'Apple iPhone 15 Pro 256GB', TRUE),
('MacBook Pro 14', 'APPL-MBP14-001', 12999.00, 50, 1.550, 1, 'Apple MacBook Pro 14 inch M3', TRUE),
('AirPods Pro 2', 'APPL-APP2-001', 1899.00, 200, 0.056, 2, 'Apple AirPods Pro 2nd Gen', TRUE),
('iPad Air', 'APPL-IPAD-001', 4799.00, 80, 0.461, 1, 'Apple iPad Air 5th Gen', TRUE),
('Apple Watch S9', 'APPL-AWS9-001', 2999.00, 150, 0.038, 3, 'Apple Watch Series 9', TRUE);

INSERT INTO orders (order_no, user_id, total_amount, status, shipping_address) VALUES
('ORD-2024-001', 1, 9898.00, 'completed', '北京市朝阳区 xx 街道 1 号'),
('ORD-2024-004', 3, 2999.00, 'pending', '广州市天河区 xx 路 3 号');

INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
(1, 1, 1, 7999.00, 7999.00),
(1, 3, 1, 1899.00, 1899.00),
(2, 5, 1, 2999.00, 2999.00);

INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('site_name', 'DB Compare Test', 'string', '站点名称'),
('version', '2.0.0', 'string', '系统版本'),
('maintenance_mode', 'false', 'boolean', '维护模式');
