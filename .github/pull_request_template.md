# Atualização manual de dados econômicos

Este template orienta contribuições **manuais** (humanos ou LLMs) ao dataset.
Pull requests automáticos gerados pelo Sneffelz têm corpo próprio.

## Fonte oficial

- [ ] Informe a fonte oficial consultada (BACEN — SGS e/ou PTAX/Olinda), com
      URLs dos endpoints usados.

## Séries modificadas

- [ ] Liste cada série (identificador) e o tipo de mudança:
      adição de observações, revisão de valores, correção de duplicidade,
      marcação de inativa, etc.

## Evidências

- [ ] Cole exemplos das respostas oficiais da fonte que justificam cada
      mudança (amostras pequenas, sem payloads gigantes).

## Validações executadas

- [ ] `python3 scripts/validate_dataset.py .` — sem erros.
- [ ] JSONs válidos, datas ISO-8601 em ordem cronológica, sem duplicidades.
- [ ] `valores.json` consistente com `anos/*.json`.
- [ ] Checksums (`somas-verificacao.json`) recalculados após a mudança.

## Revisões históricas

- [ ] Se houver mudança de valor em data já publicada, liste: série, data,
      valor anterior, valor oficial novo.

## Comandos executados

- [ ] Liste os comandos usados para gerar/validar a mudança.

## Motivo da alteração manual

- [ ] Explique por que a mudança foi feita manualmente (e não pelo Sneffelz).
