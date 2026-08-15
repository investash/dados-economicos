# Dados Econômicos

Dados econômicos oficiais do Brasil, sincronizados a partir das APIs públicas
do **Banco Central do Brasil (BACEN)** — SGS (séries temporais) e
PTAX/Olinda (câmbio) — e disponibilizados aqui como **fallback estático** para
sistemas consumidores.

## Como consumir

**Fonte primária:** consulte o BACEN diretamente.

**Fallback:** use este repositório quando a fonte oficial estiver indisponível
ou deixar de ser pública.

### Exemplos

**curl** (IPCA mensal — SGS 433):

```bash
# Fonte primária (BACEN)
curl "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json"

# Fallback estático (este repositório)
curl "https://raw.githubusercontent.com/investash/dados-economicos/main/dados/v1/inflacao/ipca/valores.json"
```

**Python:**

```python
import json
import urllib.request

with urllib.request.urlopen(
    "https://raw.githubusercontent.com/investash/dados-economicos/main/dados/v1/inflacao/ipca/valores.json"
) as r:
    valores = json.load(r)
```

**JavaScript:**

```js
const valores = await fetch(
  "https://raw.githubusercontent.com/investash/dados-economicos/main/dados/v1/inflacao/ipca/valores.json"
).then((r) => r.json());
```

## Estrutura

```text
dados/v1/
├── inflacao/          # IPCA, IPCA-15, INPC, IGP-M, IGP-DI, IPC-Brasil, IPC-M,
│                      # IPC-Fipe, metas de inflação
├── taxas-de-juros/    # Selic, CDI, TR, meta Selic
└── taxas-de-cambio/   # EUR e USD (catálogo publicado atual)
```

O snapshot atual contém **17 séries**. `ipca-12-meses` não integra este
snapshot.

Há duas estratégias de armazenamento, declaradas em `metadados.json`:

```text
# agregado-e-anual (mensal/anual)
dados/v1/<categoria>/<serie>/
├── metadados.json          # descrição autoexplicativa da série
├── valores.json            # observações em ordem cronológica
├── somas-verificacao.json  # checksums SHA-256
└── anos/<ano>.json         # partição por ano (idêntica a valores.json)

# particionado-anual (diária)
dados/v1/<categoria>/<serie>/
├── metadados.json
├── somas-verificacao.json
└── anos/<ano>.json         # única representação das observações; sem valores.json
```

Descubra o catálogo completo em [`manifesto.json`](manifesto.json) — ele é a
fonte de verdade para programas e LLMs. Os contratos formais estão em
[`esquemas/v1/`](esquemas/v1/).

## Licenciamento

Os dados são redistribuídos sob a licença aplicável da fonte oficial (BACEN —
SGS e PTAX: **ODbL**). Veja [`NOTICE.md`](NOTICE.md) para atribuição e
proveniência. Os scripts públicos de validação (`scripts/`) são **MIT**.

## Integridade e manutenção

* O repositório é atualizado pelo **Sneffelz** (PRs automáticos com revisão
  humana obrigatória de `@rgiaviti`).
* Toda PR é validada pelo CI independente (`scripts/validate_dataset.py`),
  que não depende do Sneffelz.
* Contribuições manuais seguem o [template de PR](.github/pull_request_template.md).
* A fonte da verdade é o BACEN: em caso de divergência, o valor oficial vence.

<!-- sneffelz:generated:start -->
## Séries disponíveis

| Identificador | Nome | Categoria | Frequência | Unidade | Provedor | Última observação | Última alteração dos dados |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `igp-di` | Índice geral de preços - disponibilidade interna (IGP-DI) | inflacao | mensal | % a.m. | BACEN | 2026-07-01 | 2026-08-14 |
| `igp-m` | Índice geral de preços - mercado (IGP-M) | inflacao | mensal | % a.m. | BACEN | 2026-07-01 | 2026-08-14 |
| `inpc` | Índice nacional de preços ao consumidor (INPC) | inflacao | mensal | % a.m. | BACEN | 2026-07-01 | 2026-08-14 |
| `ipc-brasil` | Índice de preços ao consumidor - Brasil (IPC-Br) | inflacao | mensal | % a.m. | BACEN | 2026-07-01 | 2026-08-14 |
| `ipc-m` | Índice de preços ao consumidor - mercado (IPC-M) | inflacao | mensal | % a.m. | BACEN | 2026-07-01 | 2026-08-14 |
| `ipc-sp` | Índice de preços ao consumidor - São Paulo (IPC-Fipe) | inflacao | mensal | % a.m. | BACEN | 2026-07-01 | 2026-08-14 |
| `ipca` | Índice nacional de preços ao consumidor-amplo (IPCA) | inflacao | mensal | % a.m. | BACEN | 2026-07-01 | 2026-08-14 |
| `ipca-15` | Índice nacional de preços ao consumidor-15 (IPCA-15) | inflacao | mensal | % a.m. | BACEN | 2026-07-01 | 2026-08-14 |
| `metas-de-inflacao` | Meta para inflação | inflacao | anual | % | BACEN | 2026-01-01 | 2026-08-14 |
| `eur` | Euro | taxas-de-cambio | diaria | BRL | BACEN | 2026-08-14 | 2026-08-14 |
| `usd` | Dólar dos Estados Unidos | taxas-de-cambio | diaria | BRL | BACEN | 2026-08-14 | 2026-08-14 |
| `cdi-acumulada-no-mes` | Taxa de juros - CDI acumulada no mês | taxas-de-juros | mensal | % a.m. | BACEN | 2026-08-01 | 2026-08-14 |
| `cdi-diaria` | Taxa de juros - CDI | taxas-de-juros | diaria | % a.d. | BACEN | 2026-08-13 | 2026-08-14 |
| `selic-diaria` | Taxa de juros - Selic | taxas-de-juros | diaria | % a.d. | BACEN | 2026-08-13 | 2026-08-14 |
| `selic-mensal` | Taxa de juros - Selic acumulada no mês | taxas-de-juros | mensal | % a.m. | BACEN | 2026-08-01 | 2026-08-14 |
| `selic-meta-anual` | Taxa de juros - Meta Selic definida pelo Copom | taxas-de-juros | diaria | % a.a. | BACEN | 2026-08-14 | 2026-08-14 |
| `tr-mensal` | Taxa referencial (TR) | taxas-de-juros | diaria | % a.m. | BACEN | 2026-08-13 | 2026-08-14 |
<!-- sneffelz:generated:end -->
