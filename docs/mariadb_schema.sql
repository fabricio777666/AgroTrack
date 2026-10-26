-- Modelo físico proposto para a versão MariaDB do AgroTrack.
-- Execute em base vazia criada pelo administrador do banco.
CREATE TABLE IF NOT EXISTS fazendas (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS usuarios (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fazenda_id BIGINT UNSIGNED NOT NULL,
  nome VARCHAR(80) NOT NULL UNIQUE,
  senha_hash VARCHAR(255) NOT NULL,
  perfil ENUM('admin','operador','leitor') NOT NULL,
  CONSTRAINT fk_usuario_fazenda FOREIGN KEY (fazenda_id) REFERENCES fazendas(id),
  INDEX idx_usuario_fazenda (fazenda_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS maquinas (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fazenda_id BIGINT UNSIGNED NOT NULL,
  nome VARCHAR(120) NOT NULL,
  modelo VARCHAR(120) NOT NULL,
  marca VARCHAR(120) NOT NULL DEFAULT '',
  ano SMALLINT UNSIGNED,
  tipo ENUM('Trator','Colheitadeira','Pulverizador','Outro') NOT NULL,
  horimetro_atual DECIMAL(12,1) NOT NULL,
  consumo_diesel_litros_hora DECIMAL(12,2) NOT NULL,
  custo_diesel_litro DECIMAL(12,2) NOT NULL,
  ultima_manutencao_horimetro DECIMAL(12,1) NOT NULL,
  intervalo_manutencao_horas DECIMAL(12,1) NOT NULL,
  CONSTRAINT fk_maquina_fazenda FOREIGN KEY (fazenda_id) REFERENCES fazendas(id),
  CONSTRAINT ck_maquina_horas CHECK (horimetro_atual >= ultima_manutencao_horimetro AND ultima_manutencao_horimetro >= 0 AND intervalo_manutencao_horas > 0),
  CONSTRAINT ck_maquina_diesel CHECK (consumo_diesel_litros_hora >= 0 AND custo_diesel_litro >= 0),
  INDEX idx_maquina_fazenda (fazenda_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS registros (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  maquina_id BIGINT UNSIGNED NOT NULL,
  usuario_id BIGINT UNSIGNED NOT NULL,
  tipo ENUM('operacao','abastecimento','manutencao') NOT NULL,
  descricao VARCHAR(500) NOT NULL,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  horimetro_inicial DECIMAL(12,1),
  horimetro_final DECIMAL(12,1),
  litros DECIMAL(12,2),
  valor_total DECIMAL(14,2),
  CONSTRAINT fk_registro_maquina FOREIGN KEY (maquina_id) REFERENCES maquinas(id) ON DELETE RESTRICT,
  CONSTRAINT fk_registro_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
  INDEX idx_registro_maquina (maquina_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS auditoria (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fazenda_id BIGINT UNSIGNED,
  usuario_id BIGINT UNSIGNED,
  acao VARCHAR(80) NOT NULL,
  maquina_id BIGINT UNSIGNED,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_auditoria_fazenda (fazenda_id, id),
  CONSTRAINT fk_auditoria_fazenda FOREIGN KEY (fazenda_id) REFERENCES fazendas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DELIMITER //
-- Função exigida em Banco de Dados II: calcula horas até a manutenção.
CREATE OR REPLACE FUNCTION horas_ate_manutencao(
  p_atual DECIMAL(12,1), p_ultima DECIMAL(12,1), p_intervalo DECIMAL(12,1)
) RETURNS DECIMAL(12,1)
DETERMINISTIC NO SQL
BEGIN
  RETURN p_intervalo - (p_atual - p_ultima);
END//

-- Gatilho do servidor: impede lançamento atribuído a usuário de outra fazenda.
CREATE OR REPLACE TRIGGER registros_bi_mesma_fazenda
BEFORE INSERT ON registros FOR EACH ROW
BEGIN
  DECLARE v_fazenda_maquina BIGINT UNSIGNED;
  DECLARE v_fazenda_usuario BIGINT UNSIGNED;
  SELECT fazenda_id INTO v_fazenda_maquina FROM maquinas WHERE id = NEW.maquina_id;
  SELECT fazenda_id INTO v_fazenda_usuario FROM usuarios WHERE id = NEW.usuario_id;
  IF v_fazenda_maquina IS NULL OR v_fazenda_usuario IS NULL OR v_fazenda_maquina <> v_fazenda_usuario THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Máquina e usuário devem pertencer à mesma fazenda';
  END IF;
  IF NEW.tipo = 'operacao' AND (NEW.horimetro_final IS NULL OR NEW.horimetro_inicial IS NULL OR NEW.horimetro_final <= NEW.horimetro_inicial) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Horímetro final inválido';
  END IF;
END//
DELIMITER ;
