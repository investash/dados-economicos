# AGENTS.md — Dados Econômicos

Guia para agentes de IA (e humanos) que trabalham **somente com o dataset**
deste repositório. Não descreve a implementação interna de ferramentas de
sincronização — apenas o contrato e a integridade dos dados.

## O que é este repositório

Dataset público de dados econômicos oficiais do Brasil, derivado das APIs do
Banco Central do Brasil (SGS e PTAX/Olinda), usado como **fallback estático**
por sistemas consumidores. **Não é** a fonte primária — o BACEN é.

## Estrutura

```text
dados/v1/<categoria>/<serie>/
├── metadados.json          # autoexplicativo (identificador, nome, unidade,
│                           #   frequência, provedor, status, referências)
├── somas-verificacao.json  # SHA-256 de valores/metadados/anos (sem self-hash)
├── valores.json            # somente agregado-e-anual (mensal/anual)
└── anos/<ano>.json         # partições anuais; única representação no diário
manifesto.json              # catálogo completo e auto-descritivo
esquemas/v1/                # contratos formais (JSON Schema, nomes PT-BR)
scripts/validate_dataset.py # validador independente (stdlib; MIT)
```

Categorias: `inflacao`, `taxas-de-juros`, `taxas-de-cambio`.

## Contrato (schema v1)

* Datas econômicas: `YYYY-MM-DD` (ISO-8601).
* Valores: JSON number (nunca string); precisão decimal preservada da fonte.
* Câmbio: `cotacao-compra`, `cotacao-venda`, `paridade-compra`,
  `paridade-venda`, `data-hora-fonte` (boletim oficial de fechamento PTAX).
* Identificadores de máquina em PT-BR: lowercase, hífen, sem acentos
  (ex.: `taxas-de-cambio`, `ultima-observacao`).
* Registros em ordem cronológica; no máximo uma observação canônica por data.
* O contrato formal vive em `esquemas/v1/*.schema.json`.

## Fonte da verdade

**BACEN é autoritativo.** Em qualquer divergência, o valor oficial publicado
pelo BACEN vence. Nunca interpole, extrapole, estime, zere, copie valor
anterior ou invente observações — "preencher um gap" significa recuperar uma
observação oficial que existe na fonte.

## Integridade

* `agregado-e-anual` contém `valores.json`, que deve ser a concatenação exata
  de `anos/*.json`.
* `particionado-anual` contém apenas `anos/YYYY.json`; `valores.json` é
  proibido nesse layout.
* Checksums SHA-256 em `somas-verificacao.json` (nunca inclui a si mesmo).
* Uma observação local ausente na fonte não é removida automaticamente —
  isso é anomalia de integridade e exige investigação humana.
* Série cuja fonte parou de publicar é marcada `inativa` nos metadados; o
  histórico é preservado.

## Como validar

```bash
python3 scripts/validate_dataset.py .     # barreira de CI (stdlib, MIT)
```

Valida JSON, estrutura, tipos, datas, ordenação, duplicidades, a relação
aplicável entre agregado e partições, checksums, manifesto, metadados, README
gerenciado e ausência de dados legados na raiz.

## Processo de contribuição manual

1. Consulte a fonte oficial (BACEN) e colete evidência.
2. Altere apenas as séries com evidência; siga o
   [template de PR](.github/pull_request_template.md).
3. Recalcule `somas-verificacao.json` e atualize `manifesto.json` se
   necessário.
4. Rode o validador localmente antes de abrir o PR.
5. O CI revalida tudo de forma independente.

## O que pode mudar

* Observações novas/revisadas com evidência oficial; metadados descritivos;
  status de série; novos esquemas versionados (`dados/v2/` no futuro).

## O que NÃO pode mudar

* Contrato `v1` silenciosamente (breaking changes criam `dados/v2/`);
* dados inventados, interpolados ou arredondados arbitrariamente;
* remoção de história sem investigação humana;
* dados fora de `dados/v1/` (raiz é só para arquivos de contrato/leitura);
* timestamps de "verificação" em arquivos versionados (zero diff artificial).

## Como analisar inconsistência

1. Rode o validador.
2. Compare com a fonte oficial para a série/data em questão.
3. Verifique os checksums e a consistência valores↔anos.
4. Se for revisão oficial: registre o valor novo com evidência e siga o
   processo de contribuição. Se for anomalia: preserve o estado e reporte.
