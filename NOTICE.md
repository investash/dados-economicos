# NOTICE

## Proveniência dos dados

Este repositório redistribui dados econômicos oficiais publicados pelo
**Banco Central do Brasil (BACEN)** por meio de suas APIs públicas:

* **SGS** (Sistema Gerenciador de Séries Temporais):
  `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{id}/dados?formato=json`
* **PTAX/Olinda** (taxas de câmbio):
  `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata`

## Atribuição

Os dados são de autoria e responsabilidade do Banco Central do Brasil, das
instituições que os calculam (ex.: IBGE, FGV, FIPE, CMN, Copom) e são
divulgados pelo BACEN. A consulta oficial e a documentação das séries estão
disponíveis nos portais do BACEN.

## Licença

As séries SGS e PTAX são disponibilizadas pelo BACEN sob a licença
**Open Data Commons Open Database License (ODbL)**
(`dadosabertos.bcb.gov.br`). Este repositório redistribui os dados sob a
mesma licença aplicável da fonte. Consulte `LICENSE.md` para o texto da
licença.

## Escopos

* `dados/` — dados econômicos (ODbL, conforme a fonte).
* `esquemas/`, `scripts/` — contratos e ferramentas de validação (MIT).
* `docs/`, `README.md`, `AGENTS.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` —
  documentação e textos do projeto: sem licença formal de código aplicável;
  o conteúdo é fornecido para conveniência e atribuição (veja acima).

## Observação

Este repositório é um **fallback estático** para consumidores. A fonte
primária é o BACEN; em caso de divergência, o valor oficial publicado pelo
BACEN prevalece.
