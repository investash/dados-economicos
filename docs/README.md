# Dados Econômicos — Documentação

## Fonte dos dados

Todas as séries são derivadas das APIs públicas do **Banco Central do Brasil**:

* **SGS** (Sistema Gerenciador de Séries Temporais):
  `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{id}/dados?formato=json`
* **PTAX/Olinda** (taxas de câmbio):
  `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata`

A fonte primária para consumidores é o **BACEN**. Este repositório é um
fallback estático.

## Estrutura

```text
dados/v1/<categoria>/<serie>/
├── metadados.json          # contrato autoexplicativo (inclui armazenamento)
├── valores.json            # presente em séries mensais/anuais (agregado)
├── somas-verificacao.json  # SHA-256 (streaming) dos arquivos da série
└── anos/<ano>.json         # partição anual
```

### Storage strategy

* Séries **mensais/anuais** (`inflacao`, juros mensais): `agregado-e-anual`
  (`valores.json` + `anos/`).
* Séries **diárias** (SELIC, CDI, TR, PTAX): `particionado-anual` (apenas
  `anos/`; `agregado-disponivel: false` nos metadados).

O consumidor descobre o layout pelos campos `armazenamento`,
`particionamento` e `agregado-disponivel` do `metadados.json` — sem
conhecimento interno do gerador.

## Validação

* `scripts/validate_dataset.py` — regras semânticas cross-file (JSON, datas,
  ordem, duplicidade, valores↔anos, checksums, manifesto, estrutura).
* `scripts/validate_schemas.py` — JSON Schema Draft 2020-12 contra
  `esquemas/v1/*.schema.json`.

Ambos rodam no CI com `uv run --frozen`.

## Licenciamento

Ver `LICENSE.md` (ODbL para dados) e `LICENSE` (MIT para scripts/esquemas).
Atribuição: `NOTICE.md`.
