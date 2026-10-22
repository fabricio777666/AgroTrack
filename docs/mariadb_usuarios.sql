-- Executar com conta administradora do SERVIDOR MariaDB.
-- Trocar as senhas antes da execução; nunca salvar senhas reais neste arquivo.
-- Criar o banco separadamente: CREATE DATABASE agrotrack CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'agrotrack_admin'@'localhost' IDENTIFIED BY 'SUBSTITUIR_SENHA_ADMIN';
CREATE USER IF NOT EXISTS 'agrotrack_app'@'localhost' IDENTIFIED BY 'SUBSTITUIR_SENHA_APP';
GRANT ALL PRIVILEGES ON agrotrack.* TO 'agrotrack_admin'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON agrotrack.* TO 'agrotrack_app'@'localhost';
GRANT EXECUTE ON FUNCTION agrotrack.horas_ate_manutencao TO 'agrotrack_app'@'localhost';
-- A conta da aplicação não recebe CREATE, DROP, ALTER ou GRANT OPTION.
-- Validar com SHOW GRANTS FOR 'agrotrack_app'@'localhost';
