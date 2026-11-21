-- ==========================================================
-- Smart Expense Tracker Database Schema
-- Database: MySQL
-- ==========================================================

CREATE DATABASE IF NOT EXISTS `smart_expense_tracker`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `smart_expense_tracker`;

-- Disable foreign key checks while resetting/creating
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `currency` VARCHAR(10) NOT NULL DEFAULT '$',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Categories Table
CREATE TABLE IF NOT EXISTS `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL,
    `type` ENUM('expense', 'income') NOT NULL DEFAULT 'expense',
    `icon` VARCHAR(50) NOT NULL DEFAULT 'tag',
    `color` VARCHAR(20) NOT NULL DEFAULT '#8B5CF6',
    `user_id` INT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_categories_user` FOREIGN KEY (`user_id`)
        REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Expenses Table
CREATE TABLE IF NOT EXISTS `expenses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `category_id` INT NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `expense_date` DATE NOT NULL,
    `description` VARCHAR(255) DEFAULT NULL,
    `payment_method` VARCHAR(50) NOT NULL DEFAULT 'Cash',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_expenses_user` FOREIGN KEY (`user_id`)
        REFERENCES `users`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_expenses_category` FOREIGN KEY (`category_id`)
        REFERENCES `categories`(`id`) ON DELETE RESTRICT,
    INDEX `idx_expense_user_date` (`user_id`, `expense_date`),
    INDEX `idx_expense_user_cat` (`user_id`, `category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Incomes Table
CREATE TABLE IF NOT EXISTS `incomes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `source` VARCHAR(100) NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `income_date` DATE NOT NULL,
    `description` VARCHAR(255) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_incomes_user` FOREIGN KEY (`user_id`)
        REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_income_user_date` (`user_id`, `income_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Budgets Table
CREATE TABLE IF NOT EXISTS `budgets` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `category_id` INT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `month` TINYINT NOT NULL,
    `year` SMALLINT NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_budgets_user` FOREIGN KEY (`user_id`)
        REFERENCES `users`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_budgets_category` FOREIGN KEY (`category_id`)
        REFERENCES `categories`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_user_cat_month_year` (`user_id`, `category_id`, `month`, `year`),
    INDEX `idx_budget_user_time` (`user_id`, `month`, `year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- Seed Default Expense Categories (Global, user_id IS NULL)
INSERT INTO `categories` (`name`, `type`, `icon`, `color`, `user_id`)
SELECT 'Food', 'expense', 'utensils', '#F59E0B', NULL
WHERE NOT EXISTS (SELECT 1 FROM `categories` WHERE `name` = 'Food' AND `user_id` IS NULL);

INSERT INTO `categories` (`name`, `type`, `icon`, `color`, `user_id`)
SELECT 'Shopping', 'expense', 'shopping-bag', '#EC4899', NULL
WHERE NOT EXISTS (SELECT 1 FROM `categories` WHERE `name` = 'Shopping' AND `user_id` IS NULL);

INSERT INTO `categories` (`name`, `type`, `icon`, `color`, `user_id`)
SELECT 'Travel', 'expense', 'plane', '#3B82F6', NULL
WHERE NOT EXISTS (SELECT 1 FROM `categories` WHERE `name` = 'Travel' AND `user_id` IS NULL);

INSERT INTO `categories` (`name`, `type`, `icon`, `color`, `user_id`)
SELECT 'Education', 'expense', 'graduation-cap', '#8B5CF6', NULL
WHERE NOT EXISTS (SELECT 1 FROM `categories` WHERE `name` = 'Education' AND `user_id` IS NULL);

INSERT INTO `categories` (`name`, `type`, `icon`, `color`, `user_id`)
SELECT 'Entertainment', 'expense', 'film', '#6366F1', NULL
WHERE NOT EXISTS (SELECT 1 FROM `categories` WHERE `name` = 'Entertainment' AND `user_id` IS NULL);

INSERT INTO `categories` (`name`, `type`, `icon`, `color`, `user_id`)
SELECT 'Bills', 'expense', 'receipt', '#EF4444', NULL
WHERE NOT EXISTS (SELECT 1 FROM `categories` WHERE `name` = 'Bills' AND `user_id` IS NULL);

INSERT INTO `categories` (`name`, `type`, `icon`, `color`, `user_id`)
SELECT 'Healthcare', 'expense', 'heart-pulse', '#10B981', NULL
WHERE NOT EXISTS (SELECT 1 FROM `categories` WHERE `name` = 'Healthcare' AND `user_id` IS NULL);

INSERT INTO `categories` (`name`, `type`, `icon`, `color`, `user_id`)
SELECT 'Others', 'expense', 'folder', '#64748B', NULL
WHERE NOT EXISTS (SELECT 1 FROM `categories` WHERE `name` = 'Others' AND `user_id` IS NULL);
