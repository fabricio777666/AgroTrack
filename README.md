# AgroTrack

**Sistema publicado:** https://bricioso.pythonanywhere.com/ — crie a conta da sua fazenda para entrar. O site usa SQLite na conta gratuita do PythonAnywhere; a etapa de MariaDB exigida em Banco de Dados II continua pendente.

Diário de bordo e acompanhamento dos gastos de maquinário agrícola.

Tratores e colheitadeiras precisam de controle das horas de uso, do combustível e das manutenções. O AgroTrack reúne esses lançamentos por máquina e avisa quando o intervalo de manutenção por horímetro é atingido.

## Integrantes

- Fabricio Marques da Cunha
- Eduardo Fernandes Silva

Ian Gustavo Sanajiotto Dias e Hiago Rafael Fernandes do Amaral contribuíram em etapas anteriores e permanecem identificados no histórico e nos diagramas de sua autoria. A equipe atual é formada por Fabricio e Eduardo.

### Contribuições da equipe atual

| Integrante | Trabalho registrado no histórico |
| --- | --- |
| Eduardo | Estruturou a base da aplicação com rotas, banco, páginas e estilos ([commit 2e4bbbe](https://github.com/fabricio777666/AgroTrack/commit/2e4bbbe)); trabalhou no registro de uso das máquinas ([commit 5400040](https://github.com/fabricio777666/AgroTrack/commit/5400040), [commit 72be655](https://github.com/fabricio777666/AgroTrack/commit/72be655)) e no [fluxograma de manutenção](https://github.com/fabricio777666/AgroTrack/pull/8). |
| Fabricio | Evoluiu o cadastro ([commit 472679b](https://github.com/fabricio777666/AgroTrack/commit/472679b)); integrou autenticação, diário, separação entre fazendas, documentação e testes ([commit 57ff17b](https://github.com/fabricio777666/AgroTrack/commit/57ff17b)); preparou o pitch ([commit d888de7](https://github.com/fabricio777666/AgroTrack/commit/d888de7)) e a execução automática dos testes ([commit aaa4b7e](https://github.com/fabricio777666/AgroTrack/commit/aaa4b7e)). |

Esses links mostram partes verificáveis do trabalho de cada um. A quantidade de commits, isoladamente, não mede o esforço nem substitui a revisão das alterações.

## Organização no GitHub

O [Kanban do AgroTrack](https://github.com/users/fabricio777666/projects/2) acompanha as tarefas. As issues abertas estão distribuídas assim:

| Responsável | Issues | Próxima entrega verificável |
| --- | --- | --- |
| Eduardo | [#1 — cadastro de máquinas](https://github.com/fabricio777666/AgroTrack/issues/1), [#2 — horímetro](https://github.com/fabricio777666/AgroTrack/issues/2) | Conferir os critérios de aceitação e completar o que faltar, com testes. |
| Fabricio | [#3 — combustível](https://github.com/fabricio777666/AgroTrack/issues/3), [#4 — manutenção](https://github.com/fabricio777666/AgroTrack/issues/4) | Conferir os critérios de aceitação e completar o que faltar, com testes. |

Para cada entrega, o responsável cria uma branch a partir da `main`, registra commits descritivos com sua própria conta e abre um pull request ligado à issue. O outro integrante revisa antes da integração. Uma issue só vai para **Done** quando seus critérios forem verificados. O histórico anterior permanece intacto e preserva os créditos de quem participou em cada etapa.

## Funcionalidades implementadas

- Cadastro, consulta, edição e exclusão de máquinas sem histórico.
- Diário por máquina: operações, abastecimentos e manutenções concluídas.
- Operações avançam o horímetro; manutenção reinicia a contagem do alerta.
- Histórico preservado: máquinas com lançamentos não podem ser excluídas. Nelas, o horímetro e a última manutenção só mudam pelo diário.
- Painel de frota e estimativa de gasto de diesel por hora.
- Resumo dos gastos e horas efetivamente lançados no diário.
- Login, perfis de acesso, sessão com validade de 30 minutos, proteção CSRF e auditoria.
- Cadastro de fazendas com dados separados; cada nova fazenda recebe seu administrador, que pode adicionar operadores e leitores em **Equipe**.
- API do cadastro de máquinas com GET, POST, PUT e DELETE.
- Modelo, marca e ano da máquina no cadastro e no relatório.
- Média de litros abastecidos por hora de operação lançada, por máquina, no diário e no relatório. Essa média depende de registros do mesmo período e não mede o consumo exato do tanque.

## Executar localmente

No terminal da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m flask --app app criar-usuario --nome fabricio --perfil admin
.\.venv\Scripts\python -m flask --app app run
```

A criação solicita uma senha de pelo menos 12 caracteres, com confirmação. Não há senha padrão. Abra http://127.0.0.1:5000 e entre com a conta criada. Uma nova fazenda pode usar **Criar conta** na tela de login. O administrador dessa fazenda pode adicionar seus operadores e leitores na tela **Equipe**. O comando do terminal cria contas para a fazenda inicial (ID 1).

| Perfil | Permissões |
|---|---|
| Administrador | Consultar, cadastrar, editar, lançar no diário, excluir máquinas sem histórico e consultar auditoria |
| Operador | Consultar, cadastrar, editar e lançar no diário |
| Leitor | Consultar máquinas, indicadores e histórico |

O arquivo `agrotrack.db` existente é preservado. Na inicialização, as tabelas e colunas necessárias são acrescentadas sem apagar máquinas; os dados antigos passam para a fazenda inicial. O banco usa caminho absoluto relativo ao projeto, independentemente da pasta do terminal. Antes de usar com dados importantes, mantenha uma cópia de segurança do arquivo original. O arquivo de dados foi retirado do controle de versão, permanecendo no computador.

Uma base nova começa vazia. Somente para demonstração, pode-se executar:

```powershell
.\.venv\Scripts\python -m flask --app app dados-exemplo
```

Esse comando só insere os exemplos se não houver máquinas. Os exemplos não são inseridos automaticamente no início da aplicação.

## Como lançar no diário

1. Cadastre a máquina com o horímetro e o histórico de manutenção iniciais.
2. Abra **Diário** no relatório ou no painel.
3. Para uma operação, informe o horímetro final e a descrição. O início é o horímetro atual salvo no sistema.
4. Para abastecimento, informe litros e valor total pago.
5. Para manutenção concluída, informe a descrição e o valor total. O serviço é registrado no horímetro atual.

Os lançamentos recebem a data atual do servidor (UTC). Não há lançamento retroativo ou edição/exclusão de histórico nesta versão. Valide os valores antes de registrar.

### Entender os custos

- **Diesel estimado por hora** = consumo cadastrado em L/h × preço cadastrado em R$/L.
- **Gastos registrados por hora** = total dos abastecimentos e manutenções lançados ÷ horas de operações lançadas.
- Sem horas lançadas, o segundo indicador não é calculado.
- Não se trata de custo operacional completo: depreciação, mão de obra, seguros e outros gastos não estão incluídos. Os gastos e horas devem se referir ao mesmo acompanhamento para a média ser útil.

## API de máquinas

A API utiliza a mesma sessão de login do navegador. Faça login por `/login`, obtenha o token em `GET /api/csrf` e envie-o no cabeçalho `X-CSRF-Token` nas alterações. Não envie credenciais ou tokens em URLs.

| Método e caminho | Resultado |
|---|---|
| GET /api/maquinas | Lista as máquinas e indicadores |
| GET /api/maquinas/ID | Consulta uma máquina |
| POST /api/maquinas | Cadastra; retorna 201 e Location |
| PUT /api/maquinas/ID | Atualiza o cadastro completo |
| DELETE /api/maquinas/ID | Exclui máquina sem histórico; retorna 204 |

POST e PUT recebem JSON com `nome`, `modelo`, `tipo`, `horimetro_atual`, `consumo_diesel_litros_hora`, `custo_diesel_litro`, `ultima_manutencao_horimetro` e `intervalo_manutencao_horas`. `marca` e `ano` são opcionais. Tipos aceitos: Trator, Colheitadeira, Pulverizador e Outro. Os formulários HTML usam POST; a API implementa PUT/DELETE explicitamente. As permissões são verificadas no servidor em ambos os caminhos.

## Testes

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Os testes criam bancos temporários; não alteram os dados do projeto. Cobrem CRUD, cálculos, erros, CSRF, perfis, expiração de sessão, auditoria, diário e separação entre fazendas.

## Publicação e requisitos acadêmicos

O site foi publicado na conta `bricioso` do PythonAnywhere em 26/10/2026. O login e o formulário de criação de fazenda abriram por HTTPS, o arquivo SQLite foi criado no servidor e os 16 testes passaram no ambiente Python 3.13 hospedado. O envio de um cadastro real pelo endereço público ainda não foi testado. Consulte [o checklist do quarto bimestre](docs/REQUISITOS.md).

O [roteiro do pitch](docs/PITCH.md) e as [capturas reais da demonstração](docs/pitch-assets/) estão preparados. Para Banco de Dados II, há um [modelo físico MariaDB](docs/mariadb_schema.sql) com função e gatilho e um [script de usuários do banco](docs/mariadb_usuarios.sql). Esses scripts ainda precisam ser executados e testados em um servidor MariaDB; o aplicativo publicado e o local continuam usando SQLite.

Na conta gratuita do PythonAnywhere, é preciso entrar no painel e clicar em **Run until 1 month from today** antes do vencimento exibido na aba **Web**. Na publicação inicial, a data indicada foi 26/11/2026.

Na hospedagem:

- Instale as dependências e configure a entrada WSGI com `from app import app as application`.
- Defina `AGROTRACK_ENV=production`, `SECRET_KEY` longa e aleatória, e `AGROTRACK_HTTPS=1` quando servido em HTTPS.
- `AGROTRACK_DATABASE` permite escolher outro caminho para o arquivo SQLite.
- O comando `flask run` é para desenvolvimento local. Use o servidor da hospedagem em produção.
- Nunca publique o segredo, o arquivo de banco ou as credenciais. Há chave local em `instance/`, ignorada pelo Git. O banco local foi retirado do índice do Git após uma cópia segura; arquivos antigos no histórico do repositório ainda exigem cuidado se contiverem dados sensíveis.

## Arquitetura

- Contexto C4 — responsável original: Fabricio Marques da Cunha. [Fonte](contexto.puml) e [imagem](contexto.png).
- Contêiner C4 — responsável original: Hiago Rafael Fernandes do Amaral. [Fonte](conteiner.puml) e [imagem](conteiner.png).
- Banco — responsável original: Ian Gustavo Sanajiotto Dias. [Fonte atualizada da implementação](banco.puml). A imagem `banco.png` é do modelo anterior e deve ser regenerada antes da apresentação.
- Fluxograma de manutenção — responsável original: Eduardo Fernandes Silva. [Fonte](fluxo_manutencao.puml) e [imagem](fluxo_manutencao.png).

Revisar e regenerar os diagramas para a entrega final, incluindo autenticação, diário e auditoria. A revisão assistida não substitui a autoria e a participação individual exigidas na disciplina.
