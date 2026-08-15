# Política de Segurança

## Escopo

Este repositório contém **dados econômicos públicos** do Banco Central do
Brasil, esquemas de contrato (JSON Schema) e scripts públicos de validação
(rodados no CI). A segurança relevante aqui é:

1. **Integridade dos dados**: nenhum dado pode ser alterado sem passar pelo
   CI de validação (semântico + JSON Schema) e pela revisão humana.
2. **Cadeia de suprimento dos scripts**: dependências Python do validador
   são mínimas (`jsonschema`, `pytest`) e rastreadas por `uv.lock`.

## Reportando problemas

Este é um projeto pequeno mantido pela organização investash. Para reportar
uma vulnerabilidade:

* Abra uma **issue privada** no GitHub (se você tem acesso ao repositório),
  descrevendo o problema sem expor dados sensíveis;
* ou envie um e-mail para o mantenedor listado no perfil da organização
  `investash`.

Esperamos responder em até **7 dias úteis** com um plano de correção.

## Práticas adotadas

* `main` é protegida: PRs obrigatórios com revisão humana (CODEOWNERS).
* CI executa: validação semântica, validação JSON Schema (Draft 2020-12),
  testes do validador e rejeição de dados legados na raiz.
* `uv.lock` fixa as dependências dos scripts; `uv run --frozen` no CI.
* Segredos não devem existir neste repositório; se um segredo for exposto
  acidentalmente, rotacione-o imediatamente e reporte.

## Dados

Os dados são públicos e derivados do BACEN (fonte primária). Divergências
devem ser reportadas como issues normais com a evidência da fonte oficial.
