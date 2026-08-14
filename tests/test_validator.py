"""Testes do validador independente do dataset (sem Sneffelz)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from validate_dataset import Validator  # noqa: E402


def _escrever_serie_valida(v1: Path, categoria: str, identificador: str) -> Path:
    serie = v1 / categoria / identificador
    serie.mkdir(parents=True)
    (serie / "anos").mkdir()
    payload = [{"data": "2026-01-01", "valor": 0.33}]
    (serie / "valores.json").write_text(json.dumps(payload), encoding="utf-8")
    (serie / "anos" / "2026.json").write_text(json.dumps(payload), encoding="utf-8")
    (serie / "metadados.json").write_text(
        json.dumps(
            {
                "identificador": identificador,
                "nome": identificador,
                "descricao": "d",
                "categoria": categoria,
                "provedor": "BACEN",
                "instituicao-responsavel": None,
                "codigo-sgs": 433,
                "moeda": "BRL",
                "frequencia": "mensal",
                "unidade": "%",
                "status": "ativa",
                "versao-schema": "v1",
                "referencia-oficial": "https://",
                "primeira-observacao": "2026-01-01",
                "ultima-observacao": "2026-01-01",
                "ultima-alteracao-dados": "2026-08-13",
                "versao-sneffelz": "2.0.0",
            }
        ),
        encoding="utf-8",
    )
    from validate_dataset import _sha256_streaming

    arquivos = {
        "valores.json": _sha256_streaming(serie / "valores.json"),
        "metadados.json": _sha256_streaming(serie / "metadados.json"),
        "anos/2026.json": _sha256_streaming(serie / "anos" / "2026.json"),
    }
    (serie / "somas-verificacao.json").write_text(
        json.dumps({"algoritmo": "sha256", "arquivos": arquivos}), encoding="utf-8"
    )
    return serie


@pytest.fixture()
def raiz(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    (r / "dados" / "v1" / "inflacao").mkdir(parents=True)
    (r / "dados" / "v1" / "taxas-de-juros").mkdir()
    (r / "dados" / "v1" / "taxas-de-cambio").mkdir()
    (r / "manifesto.json").write_text(
        json.dumps(
            {"versao-schema": "v1", "descricao": "d", "series": [], "categorias": {}}
        ),
        encoding="utf-8",
    )
    (r / "README.md").write_text(
        "<!-- sneffelz:generated:start -->\nx\n<!-- sneffelz:generated:end -->\n",
        encoding="utf-8",
    )
    return r


class TestSemanticValidator:
    def test_dataset_valido_passa(self, raiz: Path) -> None:
        _escrever_serie_valida(raiz / "dados" / "v1", "inflacao", "ipca")
        assert Validator(raiz).run()

    def test_nan_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_valida(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "valores.json").write_text(
            json.dumps([{"data": "2026-01-01", "valor": float("nan")}]), encoding="utf-8"
        )
        assert not Validator(raiz).run()

    def test_infinity_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_valida(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "valores.json").write_text(
            json.dumps([{"data": "2026-01-01", "valor": float("inf")}]), encoding="utf-8"
        )
        assert not Validator(raiz).run()

    def test_ano_do_registro_deve_bater_com_nome(self, raiz: Path) -> None:
        serie = _escrever_serie_valida(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "anos" / "2025.json").write_text(
            json.dumps([{"data": "2026-01-01", "valor": 0.33}]), encoding="utf-8"
        )
        assert not Validator(raiz).run()

    def test_nome_nao_yyyy_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_valida(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "anos" / "extra.json").write_text("[]", encoding="utf-8")
        assert not Validator(raiz).run()

    def test_checksum_orfao_detectado(self, raiz: Path) -> None:
        serie = _escrever_serie_valida(raiz / "dados" / "v1", "inflacao", "ipca")
        from validate_dataset import _sha256_streaming

        arquivos = json.loads((serie / "somas-verificacao.json").read_text())
        del arquivos["arquivos"]["metadados.json"]
        (serie / "somas-verificacao.json").write_text(
            json.dumps(arquivos), encoding="utf-8"
        )
        assert not Validator(raiz).run()

    def test_cambio_valida_campos(self, raiz: Path) -> None:
        serie = raiz / "dados" / "v1" / "taxas-de-cambio" / "usd"
        serie.mkdir(parents=True)
        (serie / "anos").mkdir()
        payload = [
            {
                "data": "2026-01-01",
                "cotacao-compra": 5.1,
                "cotacao-venda": 5.11,
                "paridade-compra": 1.0,
                "paridade-venda": 1.0,
                "data-hora-fonte": "x",
            }
        ]
        (serie / "valores.json").write_text(json.dumps(payload), encoding="utf-8")
        (serie / "anos" / "2026.json").write_text(json.dumps(payload), encoding="utf-8")
        (serie / "metadados.json").write_text(
            json.dumps(
                {
                    "identificador": "usd",
                    "nome": "Dólar",
                    "descricao": "d",
                    "categoria": "taxas-de-cambio",
                    "provedor": "BACEN",
                    "instituicao-responsavel": None,
                    "codigo-sgs": None,
                    "moeda": "USD",
                    "frequencia": "diaria",
                    "unidade": "BRL",
                    "status": "ativa",
                    "versao-schema": "v1",
                    "referencia-oficial": "https://",
                    "primeira-observacao": "2026-01-01",
                    "ultima-observacao": "2026-01-01",
                    "ultima-alteracao-dados": "2026-08-13",
                    "versao-sneffelz": "2.0.0",
                    "tipo-serie": "cambio",
                    "paridade-contra-usd": True,
                }
            ),
            encoding="utf-8",
        )
        from validate_dataset import _sha256_streaming

        arquivos = {
            "valores.json": _sha256_streaming(serie / "valores.json"),
            "metadados.json": _sha256_streaming(serie / "metadados.json"),
            "anos/2026.json": _sha256_streaming(serie / "anos" / "2026.json"),
        }
        (serie / "somas-verificacao.json").write_text(
            json.dumps({"algoritmo": "sha256", "arquivos": arquivos}), encoding="utf-8"
        )
        assert Validator(raiz).run()


class TestJsonSchema:
    def test_schemas_validos_contra_metaschema(self, raiz: Path) -> None:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from validate_schemas import _validar_schemas

        erros: list[str] = []
        _validar_schemas(erros)
        assert erros == []

    def test_dados_validos_contra_schemas(self, raiz: Path) -> None:
        _escrever_serie_valida(raiz / "dados" / "v1", "inflacao", "ipca")
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from validate_schemas import _validar_dados

        erros: list[str] = []
        _validar_dados(raiz, erros)
        assert erros == []

    def test_script_cli_exit_zero(self, raiz: Path) -> None:
        _escrever_serie_valida(raiz / "dados" / "v1", "inflacao", "ipca")
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        r = subprocess.run(
            [sys.executable, str(scripts / "validate_schemas.py"), str(raiz)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
