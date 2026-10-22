# Conferência dos requisitos — 4º bimestre

Referência: AVA / Forma de Avaliação — Quarto Bimestre, atualização de 08/10/2026:
https://virtual.ifro.edu.br/ariquemes/mod/page/view.php?id=195831

## Implementado e validado localmente

- Cadastro de máquinas com CRUD, interface em Flask e API com GET/POST/PUT/DELETE.
- Validação no servidor: campos obrigatórios, tipos, números finitos, valores não negativos, intervalo positivo e coerência do horímetro.
- Login com senha armazenada em hash; contas sem senha padrão.
- Controle de acesso por perfil, inclusive nas rotas da API.
- Sessão com validade de 30 minutos, cookies HttpOnly/SameSite e Secure configurável para HTTPS.
- CSRF nos formulários e alterações pela API.
- Auditoria de login e alterações. Tela exclusiva para administrador. Não registra senhas nem tokens.
- Diário de operações, abastecimentos e manutenção; indicadores atualizados e histórico protegido contra exclusão da máquina.
- Cadastro público de fazenda com administrador próprio; leituras e alterações de máquinas, diário e auditoria são filtradas por fazenda.
- Layout revisto e teste de navegador em tela estreita (390 px).
- Testes automatizados em bancos descartáveis.

Controle de acesso, gerenciamento de sessão e auditoria são mecanismos candidatos à demonstração na disciplina de Segurança. A avaliação depende da documentação/demonstração à professora; a implementação local não comprova aprovação.

## Pendências que impedem declarar o projeto finalizado

### Banco de Dados II — prioridade alta

A aplicação ainda executa em SQLite. Os perfis admin/operador/leitor são usuários da APLICAÇÃO; eles não cumprem a exigência de dois usuários do SERVIDOR DE BANCO com permissões distintas. Foi escolhido MariaDB para o modelo físico: `docs/mariadb_schema.sql` contém as tabelas, uma função SQL e um gatilho; `docs/mariadb_usuarios.sql` define os dois usuários e os privilégios. Esses scripts ainda precisam ser executados, testados e integrados ao aplicativo.

É necessário executar MariaDB, migrar a persistência sem perder dados e comprovar:

- Usuário administrador do banco e usuário da aplicação com privilégios restritos à base do projeto.
- Pelo menos um procedimento ou função de banco.
- Pelo menos um gatilho (trigger) no banco. A auditoria atual é feita pelo Python; não é um trigger.
- Modelo lógico e físico final, scripts documentados, dump e teste de restauração.

Não substituir esses itens por nomes de funções Python. O banco do projeto foi copiado antes da migração de fazendas.

### Publicação e apresentação

- Publicar e testar o sistema completo na hospedagem; configurar HTTPS e os segredos.
- Inserir o link real do deploy no início do README.
- Preparar pitch e PDF em docs/, conforme a orientação final da professora.
- Regenerar as imagens PlantUML, corrigir modelos para representar as tabelas reais e incluir QR Code do sistema publicado.
- Preparar relatório no AVA com links verdadeiros do repositório e deploy.
- Conferir os critérios de Redes, ainda pendentes na página consultada.

### Processo e participação

- Conferir GitHub Projects, responsáveis e correspondência entre cartões e funcionalidades reais.
- Cada integrante deve compreender, desenvolver e registrar suas próprias contribuições. Não criar histórico artificial de commits.
- A atividade da sprint exige um incremento ainda não entregue pelo grupo. O diário é um candidato, mas essa escolha deve ser alinhada com a professora quando tratado como incremento alternativo.

## Limites desta versão

- Custo de diesel estimado e gastos registrados não incluem todos os custos operacionais.
- Sem lançamentos retroativos, correção de lançamentos ou desfazimento de manutenção. Essa evolução precisa preservar a trilha de auditoria e recalcular o horímetro com segurança.
- A primeira conta de cada fazenda pode ser criada na interface; ainda falta uma forma segura de convidar operadores/leitores e recuperar senha.
- Antes de exposição pública mais ampla, complementar a proteção de login contra tentativas repetidas e definir rotina de backup/restauração.
- Não foram verificados GitHub Projects, deploy, certificados ou todas as entregas de outras disciplinas nesta revisão do código local.
