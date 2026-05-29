CREATE TABLE IF NOT EXISTS lecturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor VARCHAR(50),
    deteccion TINYINT(1),
    estado VARCHAR(20),
    timestamp_esp BIGINT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);