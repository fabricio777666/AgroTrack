# Pitch AgroTrack — roteiro de 3 a 5 minutos

Esta apresentação descreve a versão local. Não atribua resultados medidos ou endereço público antes de verificá-los.

**Apresentadores e equipe atual:** Fabricio Marques da Cunha e Eduardo Fernandes Silva. Sugestão de divisão: Fabricio apresenta os slides 1 a 4; Eduardo, os slides 5 a 7 e a demonstração.

## 1. AgroTrack (25 s)
**Na tela:** AgroTrack — o controle da frota começa pelos dados. Apresentação: Fabricio Marques da Cunha e Eduardo Fernandes Silva. Fotografia ilustrativa.

**Fala:** “Nosso projeto é o AgroTrack, uma aplicação web para organizar as informações das máquinas agrícolas e dar mais clareza aos custos e à manutenção.”

## 2. O problema (35 s)
**Na tela:** Registros dispersos dificultam saber quanto uma máquina consome, quando precisa de manutenção e o que aconteceu com ela.

**Fala:** “No uso diário, o horímetro, os abastecimentos e os gastos podem ficar em planilhas ou anotações separadas. Isso dificulta acompanhar cada máquina e perceber a hora certa de agir.”

## 3. A solução (40 s)
**Na tela:** Cadastro da frota → diário de bordo → indicadores e alertas.

**Fala:** “O AgroTrack reúne cadastro, operações, abastecimentos e manutenções. Com consumo e preço do diesel, calcula uma estimativa de gasto por hora. Com o horímetro, mostra quando o intervalo de manutenção venceu.”

## 4. Como funciona (40 s)
**Na tela:** Operador no navegador → aplicação Flask → banco de dados. Administrador, operador e leitor têm permissões diferentes. Cada fazenda tem seus próprios dados.

**Fala:** “A interface conversa com a aplicação Flask, que valida os dados, controla o acesso e registra o histórico. Cada fazenda fica separada, e cada perfil pode executar apenas as ações permitidas.”

## 5. Demonstração real (70 s)
**Na tela:** Capturas reais do painel, do cadastro e do diário. Inserir QR Code apenas quando houver endereço público testado.

**Demonstração:** Entrar; mostrar um alerta de manutenção no painel; abrir a máquina; registrar uma operação ou abastecimento em base de demonstração; mostrar a atualização do relatório. Usar dados fictícios, nunca o banco pessoal.

## 6. Segurança e banco (35 s)
**Na tela:** Senhas em hash, sessão, perfis, proteção dos formulários, auditoria. Banco MariaDB: modelo, usuários com permissões, rotina SQL e gatilho.

**Fala:** “Além das funções principais, protegemos o acesso com senha armazenada em hash, sessão, validação e uma trilha de auditoria. Para a disciplina de banco, os scripts de MariaDB estão preparados; ainda precisamos executá-los e validá-los no servidor.”

## 7. Fechamento (25 s)
**Na tela:** Mais clareza para acompanhar a frota. Demonstração e perguntas.

**Fala:** “O resultado é uma visão mais organizada da frota e dos seus custos. Podemos mostrar o funcionamento local agora e responder às perguntas.”

**Duração prevista:** 4 min 30 s. Ensaiar com cronômetro e ajustar a demonstração ao tempo disponível.
