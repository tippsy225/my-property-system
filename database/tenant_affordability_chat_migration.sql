-- Tenant affordability and accepted-tenant chat migration
-- Run this after importing your base Zimlet/RentIQ database.

ALTER TABLE tenant_applications
  ADD COLUMN employment_position VARCHAR(50) NULL,
  ADD COLUMN number_of_dependents INT DEFAULT 0,
  ADD COLUMN current_monthly_rent DECIMAL(12,2) DEFAULT 0,
  ADD COLUMN household_notes TEXT NULL,
  ADD COLUMN affordability_status VARCHAR(40) NULL,
  ADD COLUMN affordability_comment TEXT NULL;

CREATE TABLE IF NOT EXISTS messages (
  message_id INT AUTO_INCREMENT PRIMARY KEY,
  sender_id INT NOT NULL,
  receiver_id INT NOT NULL,
  message_text TEXT NOT NULL,
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_read TINYINT(1) DEFAULT 0,
  FOREIGN KEY (sender_id) REFERENCES users(user_id),
  FOREIGN KEY (receiver_id) REFERENCES users(user_id)
);
