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
│                      # IPC-Fipe, metas de inflação, IPCA 12 meses
├── taxas-de-juros/    # Selic, CDI, TR, meta Selic
└── taxas-de-cambio/   # USD, EUR, JPY, ... (universo dinâmico do PTAX)
```

Cada série:

```text
dados/v1/<categoria>/<serie>/
├── metadados.json          # descrição autoexplicativa da série
├── valores.json            # observações em ordem cronológica
├── somas-verificacao.json  # checksums SHA-256
└── anos/<ano>.json         # partição por ano (idêntica a valores.json)
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
<!-- sneffelz:generated:end -->
