-- Rebrickable downloads schema v4
-- https://rebrickable.com/static/img/diagrams/downloads_schema_v4.svg

CREATE TABLE themes (
    id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    parent_id INT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_themes_parent FOREIGN KEY (parent_id) REFERENCES themes (id)
);

CREATE TABLE colors (
    id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    rgb VARCHAR(6) NOT NULL,
    is_trans BOOLEAN NOT NULL,
    num_parts BIGINT NOT NULL,
    num_sets BIGINT NOT NULL,
    y1 INT NULL,
    y2 INT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE part_categories (
    id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE parts (
    part_num VARCHAR(20) NOT NULL,
    name VARCHAR(250) NOT NULL,
    part_cat_id INT NOT NULL,
    part_material VARCHAR(50) NOT NULL,
    PRIMARY KEY (part_num),
    CONSTRAINT fk_parts_category FOREIGN KEY (part_cat_id) REFERENCES part_categories (id)
);

CREATE TABLE elements (
    element_id VARCHAR(10) NOT NULL,
    part_num VARCHAR(20) NOT NULL,
    color_id INT NOT NULL,
    design_id VARCHAR(10) NULL,
    PRIMARY KEY (element_id),
    CONSTRAINT fk_elements_part FOREIGN KEY (part_num) REFERENCES parts (part_num),
    CONSTRAINT fk_elements_color FOREIGN KEY (color_id) REFERENCES colors (id)
);

CREATE TABLE sets (
    set_num VARCHAR(20) NOT NULL,
    name VARCHAR(256) NOT NULL,
    year INT NOT NULL,
    theme_id INT NOT NULL,
    num_parts INT NOT NULL,
    img_url TEXT NOT NULL,
    PRIMARY KEY (set_num),
    CONSTRAINT fk_sets_theme FOREIGN KEY (theme_id) REFERENCES themes (id)
);

CREATE TABLE minifigs (
    fig_num VARCHAR(20) NOT NULL,
    name VARCHAR(256) NOT NULL,
    num_parts INT NOT NULL,
    img_url TEXT NOT NULL,
    PRIMARY KEY (fig_num)
);

-- set_num refers to either sets.set_num or minifigs.fig_num.
CREATE TABLE inventories (
    id INT NOT NULL,
    version INT NOT NULL,
    set_num VARCHAR(20) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE inventory_parts (
    inventory_id INT NOT NULL,
    part_num VARCHAR(20) NOT NULL,
    color_id INT NOT NULL,
    quantity INT NOT NULL,
    is_spare BOOLEAN NOT NULL,
    img_url TEXT NULL,
    PRIMARY KEY (inventory_id, part_num, color_id, is_spare),
    CONSTRAINT fk_inventory_parts_inventory FOREIGN KEY (inventory_id) REFERENCES inventories (id),
    CONSTRAINT fk_inventory_parts_part FOREIGN KEY (part_num) REFERENCES parts (part_num),
    CONSTRAINT fk_inventory_parts_color FOREIGN KEY (color_id) REFERENCES colors (id)
);

CREATE TABLE inventory_sets (
    inventory_id INT NOT NULL,
    set_num VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (inventory_id, set_num),
    CONSTRAINT fk_inventory_sets_inventory FOREIGN KEY (inventory_id) REFERENCES inventories (id),
    CONSTRAINT fk_inventory_sets_set FOREIGN KEY (set_num) REFERENCES sets (set_num)
);

CREATE TABLE inventory_minifigs (
    inventory_id INT NOT NULL,
    fig_num VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (inventory_id, fig_num),
    CONSTRAINT fk_inventory_minifigs_inventory FOREIGN KEY (inventory_id) REFERENCES inventories (id),
    CONSTRAINT fk_inventory_minifigs_fig FOREIGN KEY (fig_num) REFERENCES minifigs (fig_num)
);

CREATE TABLE part_relationships (
    rel_type VARCHAR(1) NOT NULL,
    child_part_num VARCHAR(20) NOT NULL,
    parent_part_num VARCHAR(20) NOT NULL,
    PRIMARY KEY (rel_type, child_part_num, parent_part_num),
    CONSTRAINT fk_part_relationships_child FOREIGN KEY (child_part_num) REFERENCES parts (part_num),
    CONSTRAINT fk_part_relationships_parent FOREIGN KEY (parent_part_num) REFERENCES parts (part_num)
);

CREATE TABLE part_mappings (
    part_num VARCHAR(20) NOT NULL,
    ext_system VARCHAR(10) NOT NULL,
    ext_id VARCHAR(30) NOT NULL,
    is_export_id BOOLEAN NOT NULL,
    is_import_id BOOLEAN NOT NULL,
    PRIMARY KEY (part_num, ext_system, ext_id),
    CONSTRAINT fk_part_mappings_part FOREIGN KEY (part_num) REFERENCES parts (part_num)
);

-- set_num refers to either sets.set_num or minifigs.fig_num.
-- Most rows in the catalog download are minifig ids, so this column has no foreign key.
CREATE TABLE set_mappings (
    set_num VARCHAR(20) NOT NULL,
    ext_system VARCHAR(10) NOT NULL,
    ext_id VARCHAR(30) NOT NULL,
    PRIMARY KEY (set_num, ext_system, ext_id)
);

CREATE TABLE color_mappings (
    id INT NOT NULL,
    ext_system VARCHAR(10) NOT NULL,
    ext_id INT NOT NULL,
    ext_descr TEXT NOT NULL,
    is_export_id BOOLEAN NOT NULL,
    is_import_id BOOLEAN NOT NULL,
    PRIMARY KEY (id, ext_system, ext_id),
    CONSTRAINT fk_color_mappings_color FOREIGN KEY (id) REFERENCES colors (id)
);
