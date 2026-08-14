#!/usr/bin/env python3
"""Validação por JSON Schema do dataset (Draft 2020-12).

* Valida os próprios schemas contra o metaschema Draft 2020-12;
* valida manifesto.json, metadados.json, valores.json, anos/*.json e
  somas-verificacao.json contra os schemas correspondentes.

JSON Schema não substitui as regras cross-file — o semantic validator
(validate_dataset.py) continua obrigatório.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "esquemas" / "v1"


def _ler(caminho: Path) -> object:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _validar_schemas(erros: list[str]) -> None:
    for schema_path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        try:
            schema = _ler(schema_path)
            Draft202012Validator(schema).check_schema(schema)
        except Exception as exc:
            erros.append(f"{schema_path.name}: schema inválido contra metaschema: {exc}")


def _validar_dados(raiz: Path, erros: list[str]) -> None:
    schemas: dict[str, Draft202012Validator] = {}
    for schema_path in SCHEMA_DIR.glob("*.schema.json"):
        try:
            schemas[schema_path.name] = Draft202012Validator(_ler(schema_path))
        except Exception:
            continue

    manifesto = raiz / "manifesto.json"
    if manifesto.is_file() and "manifesto.schema.json" in schemas:
        for err in schemas["manifesto.schema.json"].iter_errors(_ler(manifesto)):
            erros.append(f"manifesto.json: {err.message}")

    v1 = raiz / "dados" / "v1"
    if not v1.is_dir():
        return
    for categoria in ("inflacao", "taxas-de-juros", "taxas-de-cambio"):
        cat_dir = v1 / categoria
        if not cat_dir.is_dir():
            continue
        for serie_dir in sorted(cat_dir.iterdir()):
            prefixo = f"{categoria}/{serie_dir.name}"
            meta = serie_dir / "metadados.json"
            if meta.is_file() and "metadados-serie.schema.json" in schemas:
                for err in schemas["metadados-serie.schema.json"].iter_errors(_ler(meta)):
                    erros.append(f"{prefixo}/metadados.json: {err.message}")
            valores = serie_dir / "valores.json"
            if valores.is_file():
                nome_schema = "serie-cambio.schema.json" if categoria == "taxas-de-cambio" else "serie-escalar.schema.json"
                if nome_schema in schemas:
                    for err in schemas[nome_schema].iter_errors(_ler(valores)):
                        erros.append(f"{prefixo}/valores.json: {err.message}")
            somas = serie_dir / "somas-verificacao.json"
            if somas.is_file() and "somas-verificacao.schema.json" in schemas:
                for err in schemas["somas-verificacao.schema.json"].iter_errors(_ler(somas)):
                    erros.append(f"{prefixo}/somas-verificacao.json: {err.message}")
            anos = serie_dir / "anos"
            if anos.is_dir():
                for ano in sorted(anos.glob("*.json")):
                    nome_schema = "serie-cambio.schema.json" if categoria == "taxas-de-cambio" else "serie-escalar.schema.json"
                    if nome_schema in schemas:
                        for err in schemas[nome_schema].iter_errors(_ler(ano)):
                            erros.append(f"{prefixo}/anos/{ano.name}: {err.message}")


def main() -> int:
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    erros: list[str] = []
    _validar_schemas(erros)
    _validar_dados(raiz, erros)
    if not erros:
        print("JSON Schema: OK")
        return 0
    print(f"JSON Schema: {len(erros)} erro(s):", file=sys.stderr)
    for e in erros:
        print(f"  - {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
