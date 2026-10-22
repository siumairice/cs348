CREATE DATABASE IF NOT EXISTS lego_sets;
USE lego_sets;

CREATE TABLE IF NOT EXISTS themes (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INT NULL,
    FOREIGN KEY (parent_id) REFERENCES themes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sets (
    set_num VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    year INT NOT NULL,
    theme_id INT NULL,
    num_parts INT NULL,
    img_url VARCHAR(512) NULL,
    FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE SET NULL
);
