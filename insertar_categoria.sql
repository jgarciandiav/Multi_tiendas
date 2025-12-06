-- Primero: eliminar datos existentes (opcional, para reiniciar)
DELETE FROM tienda_categoria;
DELETE FROM sqlite_sequence WHERE name = 'tienda_categoria';

-- Reiniciar autoincrement (solo SQLite)
-- En PostgreSQL: usa TRUNCATE y RESTART IDENTITY
-- En MySQL: ALTER TABLE ... AUTO_INCREMENT = 1

-- Insertar CATEGORÍAS PRINCIPALES (padre = NULL)
INSERT INTO tienda_categoria (id, nombre, descripcion, padre_id) VALUES
(1, 'Electrodomésticos y Artículos del hogar', 'Productos para el hogar y electrodomésticos', NULL),
(2, 'Dulces y Regalos', 'Dulces, confituras y artículos de regalo', NULL),
(3, 'Juguetes', 'Juguetes para todas las edades', NULL);

-- Insertar SUBCATEGORÍAS (padre_id = id de la categoría principal)
INSERT INTO tienda_categoria (nombre, descripcion, padre_id) VALUES
-- Subcategorías de "Electrodomésticos y Artículos del hogar" (id=1)
('Electrodomésticos', 'Lavadoras, refrigeradoras, cocinas, etc.', 1),
('Artículos de hogar', 'Utensilios, decoración, limpieza, etc.', 1),

-- Subcategorías de "Dulces y Regalos" (id=2)
('Dulces', 'Chocolates, caramelos, galletas, etc.', 2),
('Confituras', 'Mermeladas, jaleas, dulces tradicionales', 2),
('Regalos', 'Artículos para regalo: peluches, cajas, etc.', 2),

-- Subcategorías de "Juguetes" (id=3)
('Juguetes', 'Juguetes educativos, de acción, de construcción', 3);