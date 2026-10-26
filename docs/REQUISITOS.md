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

## Publicação verificada em 26/10/2026

- https://bricioso.pythonanywhere.com/ abre o login do AgroTrack por HTTPS; `/cadastro` abre o formulário de nova fazenda.
- A conta gratuita `bricioso` usa SQLite em `/home/bricioso/agrotrack-data/agrotrack.db`, fora do repositório; o arquivo foi observado no servidor.
- O servidor foi configurado com Python 3.13, ambiente virtual, chave secreta fora do Git e redirecionamento obrigatório para HTTPS. Os 16 testes automatizados passaram no console da hospedagem.
- Ainda falta exercitar um cadastro e login reais pelo endereço público. A validade da hospedagem gratuita precisa ser renovada no painel mensalmente.

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

- Testar cadastro, login e lançamentos reais no endereço público com uma conta criada pela equipe.
- Preparar pitch e PDF em docs/, conforme a orientação final da professora.
- Regenerar as imagens PlantUML, corrigir modelos para representar as tabelas reais e incluir QR Code do sistema publicado.
- Preparar relatório no AVA com links verdadeiros do repositório e deploy.
- Conferir os critérios de Redes, ainda pendentes na página consultada.

### Processo e participação

- Manter o GitHub Projects atualizado: issues #1 e #2 com Eduardo; #3 e #4 com Fabricio. Conferir cada critério de aceitação antes de fechar os cartões.
- Cada integrante deve compreender, desenvolver e registrar suas próprias contribuições. Não criar histórico artificial de commits.
- A atividade da sprint exige um incremento ainda não entregue pelo grupo. O diário é um candidato, mas essa escolha deve ser alinhada com a professora quando tratado como incremento alternativo.

## Limites desta versão

- Custo de diesel estimado e gastos registrados não incluem todos os custos operacionais.
- Sem lançamentos retroativos, correção de lançamentos ou desfazimento de manutenção. Essa evolução precisa preservar a trilha de auditoria e recalcular o horímetro com segurança.
- A primeira conta de cada fazenda pode ser criada na interface; ainda falta uma forma segura de convidar operadores/leitores e recuperar senha.
- Antes de exposição pública mais ampla, complementar a proteção de login contra tentativas repetidas e definir rotina de backup/restauração.
- O GitHub Projects e os responsáveis foram conferidos em 25/10/2026. A publicação, a página de login e o cadastro foram verificados em 26/10/2026; o fluxo completo com conta real e as entregas das outras disciplinas ainda precisam de verificação.
