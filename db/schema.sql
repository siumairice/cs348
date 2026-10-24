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

CREATE TABLE IF NOT EXISTS colors (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rgb CHAR(6) NOT NULL,
    is_trans TINYINT(1) NOT NULL,
    num_parts INT NULL,
    num_sets INT NULL,
    y1 INT NULL,
    y2 INT NULL
);

CREATE TABLE IF NOT EXISTS part_categories (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS parts (
    part_num VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    part_cat_id INT NULL,
    part_material VARCHAR(255) NULL,
    FOREIGN KEY (part_cat_id) REFERENCES part_categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS minifigs (
    fig_num VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    num_parts INT NULL,
    img_url VARCHAR(512) NULL
);

CREATE TABLE IF NOT EXISTS color_mappings (
    id INT PRIMARY KEY,
    ext_system VARCHAR(50) NOT NULL,
    ext_id VARCHAR(100) NOT NULL,
    ext_descr VARCHAR(255) NULL,
    is_export_id TINYINT(1) NOT NULL,
    is_import_id TINYINT(1) NOT NULL
);

CREATE TABLE IF NOT EXISTS elements (
    element_id VARCHAR(32) PRIMARY KEY,
    part_num VARCHAR(32) NOT NULL,
    color_id INT NOT NULL,
    design_id VARCHAR(32) NULL,
    FOREIGN KEY (part_num) REFERENCES parts(part_num),
    FOREIGN KEY (color_id) REFERENCES colors(id)
);

CREATE TABLE IF NOT EXISTS inventories (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    set_num VARCHAR(32) NOT NULL,
    FOREIGN KEY (set_num) REFERENCES sets(set_num) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS inventory_minifigs (
    inventory_id INT NOT NULL,
    fig_num VARCHAR(32) NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (inventory_id, fig_num),
    FOREIGN KEY (inventory_id) REFERENCES inventories(id) ON DELETE CASCADE,
    FOREIGN KEY (fig_num) REFERENCES minifigs(fig_num)
);

CREATE TABLE IF NOT EXISTS inventory_parts (
    inventory_id INT NOT NULL,
    part_num VARCHAR(32) NOT NULL,
    color_id INT NOT NULL,
    quantity INT NOT NULL,
    is_spare TINYINT(1) NOT NULL,
    img_url VARCHAR(512) NULL,
    PRIMARY KEY (inventory_id, part_num, color_id, is_spare),
    FOREIGN KEY (inventory_id) REFERENCES inventories(id) ON DELETE CASCADE,
    FOREIGN KEY (part_num) REFERENCES parts(part_num),
    FOREIGN KEY (color_id) REFERENCES colors(id),
    INDEX idx_inventory_parts_part_color (part_num, color_id)
);

CREATE TABLE IF NOT EXISTS inventory_sets (
    inventory_id INT NOT NULL,
    set_num VARCHAR(32) NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (inventory_id, set_num),
    FOREIGN KEY (inventory_id) REFERENCES inventories(id) ON DELETE CASCADE,
    FOREIGN KEY (set_num) REFERENCES sets(set_num)
);

CREATE TABLE IF NOT EXISTS part_mappings (
    part_num VARCHAR(32) NOT NULL,
    ext_system VARCHAR(50) NOT NULL,
    ext_id VARCHAR(100) NOT NULL,
    is_export_id TINYINT(1) NOT NULL,
    is_import_id TINYINT(1) NOT NULL,
    PRIMARY KEY (part_num, ext_system, ext_id),
    FOREIGN KEY (part_num) REFERENCES parts(part_num) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS part_relationships (
    rel_type CHAR(1) NOT NULL,
    child_part_num VARCHAR(32) NOT NULL,
    parent_part_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (rel_type, child_part_num, parent_part_num),
    FOREIGN KEY (child_part_num) REFERENCES parts(part_num) ON DELETE CASCADE,
    FOREIGN KEY (parent_part_num) REFERENCES parts(part_num) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS set_mappings (
    set_num VARCHAR(32) NOT NULL,
    ext_system VARCHAR(50) NOT NULL,
    ext_id VARCHAR(100) NOT NULL,
    PRIMARY KEY (set_num, ext_system, ext_id),
    FOREIGN KEY (set_num) REFERENCES sets(set_num) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_parts (
    user_id INT UNSIGNED NOT NULL,
    part_num VARCHAR(32) NOT NULL,
    color_id INT NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (user_id, part_num, color_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (part_num) REFERENCES parts(part_num),
    FOREIGN KEY (color_id) REFERENCES colors(id)
);

CREATE TABLE IF NOT EXISTS user_completed_sets (
    user_id INT UNSIGNED NOT NULL,
    set_num VARCHAR(32) NOT NULL,
    completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, set_num),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (set_num) REFERENCES sets(set_num) ON DELETE CASCADE
);
