-- Создание схемы
CREATE SCHEMA IF NOT EXISTS banks;
SET search_path TO banks;

-- Таблица пользователей
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    birth_date DATE,
    registration_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    user_type VARCHAR(20) DEFAULT 'customer',
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица заказов
CREATE TABLE orders (
    order_id VARCHAR(20) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(30),
    shipping_address TEXT NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(12,2) GENERATED ALWAYS AS (total_amount - discount_amount + tax_amount) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    CHECK (total_amount >= 0),
    CHECK (discount_amount >= 0),
    CHECK (tax_amount >= 0)
);