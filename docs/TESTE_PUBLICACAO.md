# Teste do site publicado

Endereço: https://bricioso.pythonanywhere.com/  
Verificação: sessão autenticada do administrador `fabricio`, em 26/10/2026 UTC. Os registros abaixo foram identificados com `[TESTE]`.

| Fluxo | Resultado observado |
| --- | --- |
| Cadastro | Trator, colheitadeira e pulverizador foram salvos. Modelo, marca e ano apareceram no relatório; marca e ano opcionais também funcionaram. |
| Manutenção | O trator apareceu com 15 h restantes; a colheitadeira, como vencida. Após operação e manutenção no diário do trator, seu aviso sumiu e o painel ainda contou apenas a colheitadeira como vencida. |
| Validação do horímetro | Operação com leitura menor que a atual foi recusada sem criar lançamento. A edição direta do horímetro de máquina com diário também foi recusada. |
| Diário e cálculos | Operação de 1235 a 1250 h, abastecimento de 45 L por R$ 270 e manutenção por R$ 150 foram gravados. O diário mostrou 15 h, 3,00 L/h registrados, R$ 420 em gastos e R$ 28/h. |
| Edição | Nome e consumo informado do trator foram atualizados; o relatório recalculou o diesel estimado para R$ 78/h. |
| Painel, relatório e auditoria | Painel exibiu 2 máquinas, 1 manutenção vencida e média estimada de R$ 123/h após a exclusão do pulverizador. O relatório e a auditoria refletiram os registros e a edição. |
| API | `GET /api/maquinas` autenticado retornou as três máquinas antes da exclusão. Sem sessão, a mesma rota retornou HTTP 401; páginas administrativas redirecionaram para `/login`. |
| Exclusão | O pulverizador de teste, sem histórico, foi excluído após confirmação. |

**Dados de demonstração que permanecem:** `[TESTE] Trator A revisado` (ID 1) e `[TESTE] Colheitadeira B` (ID 2), além dos três lançamentos no diário do trator. A conta `fabricio` já existia quando o teste começou.

**Limites do teste:** não digitamos a senha nem repetimos o login/cadastro de conta no navegador; não criamos usuários de equipe nem testamos seus perfis no site público. Essas rotas e permissões têm cobertura nos testes automatizados, executados no PythonAnywhere (16 testes aprovados). A API de escrita foi coberta pelos testes automatizados, não por requisições manuais na produção. O site publicado usa SQLite; a validação dos scripts e privilégios MariaDB de Banco de Dados II permanece pendente.
