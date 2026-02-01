-- Database initialization for Load Planning System

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'operator' CHECK (role IN ('admin', 'operator')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    vehicle_type VARCHAR(50) NOT NULL,
    max_load DECIMAL(10, 2) NOT NULL,
    length DECIMAL(10, 2) NOT NULL,
    width DECIMAL(10, 2) NOT NULL,
    height DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cargo table
CREATE TABLE IF NOT EXISTS cargo (
    cargo_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    weight DECIMAL(10, 2) NOT NULL,
    length DECIMAL(10, 2) NOT NULL,
    width DECIMAL(10, 2) NOT NULL,
    height DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Load plans table
CREATE TABLE IF NOT EXISTS load_plans (
    plan_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    stability_score DECIMAL(5, 2),
    center_of_gravity_x DECIMAL(10, 2),
    center_of_gravity_y DECIMAL(10, 2),
    center_of_gravity_z DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cargo placements table
CREATE TABLE IF NOT EXISTS cargo_placements (
    placement_id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES load_plans(plan_id) ON DELETE CASCADE,
    cargo_id INTEGER REFERENCES cargo(cargo_id),
    position_x DECIMAL(10, 2) NOT NULL,
    position_y DECIMAL(10, 2) NOT NULL,
    position_z DECIMAL(10, 2) NOT NULL,
    rotation INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (name, email, password_hash, role) VALUES
('Admin User', 'admin@loadplan.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEQVAe', 'admin'),
('Operator User', 'operator@loadplan.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEQVAe', 'operator');
-- Password for both is: password123

INSERT INTO vehicles (vehicle_type, max_load, length, width, height) VALUES
('Box Truck', 5000.00, 6.00, 2.40, 2.60),
('Semi Trailer', 20000.00, 13.60, 2.48, 2.70),
('Van', 1500.00, 4.00, 1.80, 1.90),
('Container 20ft', 28000.00, 5.90, 2.35, 2.39),
('Container 40ft', 28600.00, 12.03, 2.35, 2.39);

INSERT INTO cargo (name, weight, length, width, height) VALUES
('Pallet A', 500.00, 1.20, 1.00, 1.50),
('Pallet B', 750.00, 1.20, 1.00, 1.80),
('Crate Heavy', 1200.00, 1.50, 1.20, 1.40),
('Box Light', 100.00, 0.60, 0.50, 0.50),
('Machinery', 2000.00, 2.00, 1.50, 1.60);

-- Create indexes for better performance
CREATE INDEX idx_load_plans_user ON load_plans(user_id);
CREATE INDEX idx_load_plans_vehicle ON load_plans(vehicle_id);
CREATE INDEX idx_cargo_placements_plan ON cargo_placements(plan_id);
