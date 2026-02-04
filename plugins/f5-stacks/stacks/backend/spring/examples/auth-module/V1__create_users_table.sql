-- V1__create_users_table.sql
-- Description: Create users, roles, and permissions tables for authentication

-- Create roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
);

-- Create role permissions table
CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission VARCHAR(100) NOT NULL,
    PRIMARY KEY (role_id, permission)
);

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip VARCHAR(50),
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    version BIGINT NOT NULL DEFAULT 0,

    CONSTRAINT chk_users_status CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'DELETED'))
);

-- Create user_roles junction table
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_email_verification_token ON users(email_verification_token) WHERE email_verification_token IS NOT NULL;
CREATE INDEX idx_users_password_reset_token ON users(password_reset_token) WHERE password_reset_token IS NOT NULL;
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE users IS 'User accounts for authentication';
COMMENT ON TABLE roles IS 'User roles for authorization';
COMMENT ON TABLE role_permissions IS 'Permissions assigned to roles';
COMMENT ON TABLE user_roles IS 'Junction table for user-role assignments';

-- Insert default roles
INSERT INTO roles (id, name, description) VALUES
    ('00000000-0000-0000-0000-000000000001', 'ADMIN', 'System administrator with full access'),
    ('00000000-0000-0000-0000-000000000002', 'MANAGER', 'Manager with elevated permissions'),
    ('00000000-0000-0000-0000-000000000003', 'USER', 'Standard user with basic permissions');

-- Insert role permissions
INSERT INTO role_permissions (role_id, permission) VALUES
    -- Admin permissions (all)
    ('00000000-0000-0000-0000-000000000001', 'user:read'),
    ('00000000-0000-0000-0000-000000000001', 'user:write'),
    ('00000000-0000-0000-0000-000000000001', 'user:delete'),
    ('00000000-0000-0000-0000-000000000001', 'product:read'),
    ('00000000-0000-0000-0000-000000000001', 'product:write'),
    ('00000000-0000-0000-0000-000000000001', 'product:delete'),
    ('00000000-0000-0000-0000-000000000001', 'order:read'),
    ('00000000-0000-0000-0000-000000000001', 'order:write'),
    -- Manager permissions
    ('00000000-0000-0000-0000-000000000002', 'user:read'),
    ('00000000-0000-0000-0000-000000000002', 'product:read'),
    ('00000000-0000-0000-0000-000000000002', 'product:write'),
    ('00000000-0000-0000-0000-000000000002', 'order:read'),
    ('00000000-0000-0000-0000-000000000002', 'order:write'),
    -- User permissions
    ('00000000-0000-0000-0000-000000000003', 'product:read'),
    ('00000000-0000-0000-0000-000000000003', 'order:read');

-- Insert demo admin user (password: Admin@123)
INSERT INTO users (id, email, password_hash, name, status, email_verified) VALUES
    ('10000000-0000-0000-0000-000000000001', 'admin@example.com',
     '$2a$10$N9qo8uLOickgx2ZMRZoMye.Fb/t9l6iJJO2O6KjKzBIJE.zNQlrze',
     'System Admin', 'ACTIVE', TRUE);

INSERT INTO user_roles (user_id, role_id) VALUES
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001');
