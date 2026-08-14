"""Testes do validador independente do dataset (sem Sneffelz)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from validate_dataset import (  # noqa: E402
    ARMAZENAMENTO_AGREGADO,
    ARMAZENAMENTO_PARTICIONADO,
    Validator,
    _sha256_streaming,
)


def _metadados(
    identificador: str,
    categoria: str,
    *,
    frequencia: str = "mensal",
    armazenamento: str = ARMAZENAMENTO_AGREGADO,
    primeira: str = "2026-01-01",
    ultima: str = "2026-01-01",
    tipo: str = "escalar",
    moeda: str = "BRL",
) -> dict:
    return {
        "identificador": identificador,
        "nome": identificador,
        "descricao": "d",
        "categoria": categoria,
        "provedor": "BACEN",
        "instituicao-responsavel": None,
        "codigo-sgs": 433 if tipo == "escalar" else None,
        "moeda": moeda,
        "frequencia": frequencia,
        "unidade": "%",
        "status": "ativa",
        "versao-schema": "v1",
        "referencia-oficial": "https://",
        "primeira-observacao": primeira,
        "ultima-observacao": ultima,
        "ultima-alteracao-dados": "2026-08-13",
        "versao-sneffelz": "2.0.0",
        "tipo-serie": tipo,
        "armazenamento": armazenamento,
        "particionamento": "anual",
        "agregado-disponivel": armazenamento == ARMAZENAMENTO_AGREGADO,
    }


def _checksums(serie: Path, *relativos: str) -> None:
    arquivos = {rel: _sha256_streaming(serie / rel) for rel in relativos}
    (serie / "somas-verificacao.json").write_text(
        json.dumps({"algoritmo": "sha256", "arquivos": arquivos}), encoding="utf-8"
    )


def _escrever_serie_agregada(v1: Path, categoria: str, identificador: str) -> Path:
    serie = v1 / categoria / identificador
    serie.mkdir(parents=True)
    (serie / "anos").mkdir()
    payload = [{"data": "2026-01-01", "valor": 0.33}]
    (serie / "valores.json").write_text(json.dumps(payload), encoding="utf-8")
    (serie / "anos" / "2026.json").write_text(json.dumps(payload), encoding="utf-8")
    (serie / "metadados.json").write_text(
        json.dumps(_metadados(identificador, categoria)), encoding="utf-8"
    )
    _checksums(serie, "valores.json", "metadados.json", "anos/2026.json")
    return serie


def _escrever_serie_particionada(v1: Path, identificador: str = "usd") -> Path:
    serie = v1 / "taxas-de-cambio" / identificador
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
    (serie / "anos" / "2026.json").write_text(json.dumps(payload), encoding="utf-8")
    (serie / "metadados.json").write_text(
        json.dumps(
            _metadados(
                identificador,
                "taxas-de-cambio",
                frequencia="diaria",
                armazenamento=ARMAZENAMENTO_PARTICIONADO,
                tipo="cambio",
                moeda="USD",
            )
        ),
        encoding="utf-8",
    )
    _checksums(serie, "metadados.json", "anos/2026.json")
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


def _manifesto_valido(v1: Path) -> dict:
    series = []
    for categoria in ("inflacao", "taxas-de-juros", "taxas-de-cambio"):
        for serie_dir in sorted((v1 / categoria).iterdir()):
            if not serie_dir.is_dir():
                continue
            meta = json.loads((serie_dir / "metadados.json").read_text(encoding="utf-8"))
            series.append(
                {
                    "identificador": serie_dir.name,
                    "nome": serie_dir.name,
                    "categoria": categoria,
                    "caminho": f"{categoria}/{serie_dir.name}",
                    "descricao": "d",
                    "frequencia": meta["frequencia"],
                    "unidade": "%",
                    "moeda": meta["moeda"],
                    "provedor": "BACEN",
                    "status": "ativa",
                    "armazenamento": meta["armazenamento"],
                    "particionamento": "anual",
                    "agregado-disponivel": meta["agregado-disponivel"],
                    "primeira-observacao": meta["primeira-observacao"],
                    "ultima-observacao": meta["ultima-observacao"],
                    "ultima-alteracao-dados": meta["ultima-alteracao-dados"],
                    "metadados": f"{categoria}/{serie_dir.name}/metadados.json",
                    "somas-verificacao": f"{categoria}/{serie_dir.name}/somas-verificacao.json",
                }
            )
    return {
        "versao-schema": "v1",
        "descricao": "d",
        "categorias": {"inflacao": {"identificador": "inflacao", "series": ["ipca"]}},
        "series": series,
    }


class TestSemanticValidator:
    def test_dataset_valido_passa(self, raiz: Path) -> None:
        _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        (raiz / "manifesto.json").write_text(
            json.dumps(_manifesto_valido(raiz / "dados" / "v1")), encoding="utf-8"
        )
        assert Validator(raiz).run()

    def test_particionado_valido_passa(self, raiz: Path) -> None:
        _escrever_serie_particionada(raiz / "dados" / "v1")
        (raiz / "manifesto.json").write_text(
            json.dumps(_manifesto_valido(raiz / "dados" / "v1")), encoding="utf-8"
        )
        assert Validator(raiz).run()

    def test_particionado_com_valores_json_e_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_particionada(raiz / "dados" / "v1")
        (serie / "valores.json").write_text("[]", encoding="utf-8")
        assert not Validator(raiz).run()

    def test_agregado_sem_valores_json_e_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "valores.json").unlink()
        assert not Validator(raiz).run()

    def test_combinacao_impossivel_storage_frequencia(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        meta = json.loads((serie / "metadados.json").read_text(encoding="utf-8"))
        meta["frequencia"] = "diaria"
        (serie / "metadados.json").write_text(json.dumps(meta), encoding="utf-8")
        _checksums(serie, "valores.json", "metadados.json", "anos/2026.json")
        assert not Validator(raiz).run()

    def test_nan_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "valores.json").write_text(
            json.dumps([{"data": "2026-01-01", "valor": float("nan")}]), encoding="utf-8"
        )
        _checksums(serie, "valores.json", "metadados.json", "anos/2026.json")
        assert not Validator(raiz).run()

    def test_infinity_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "valores.json").write_text(
            json.dumps([{"data": "2026-01-01", "valor": float("inf")}]), encoding="utf-8"
        )
        _checksums(serie, "valores.json", "metadados.json", "anos/2026.json")
        assert not Validator(raiz).run()

    def test_nan_cambio_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_particionada(raiz / "dados" / "v1")
        payload = json.loads((serie / "anos" / "2026.json").read_text(encoding="utf-8"))
        payload[0]["cotacao-compra"] = float("nan")
        (serie / "anos" / "2026.json").write_text(json.dumps(payload), encoding="utf-8")
        _checksums(serie, "metadados.json", "anos/2026.json")
        assert not Validator(raiz).run()

    def test_ano_do_registro_deve_bater_com_nome(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "anos" / "2025.json").write_text(
            json.dumps([{"data": "2026-01-01", "valor": 0.33}]), encoding="utf-8"
        )
        _checksums(serie, "valores.json", "metadados.json", "anos/2025.json")
        assert not Validator(raiz).run()

    def test_nome_nao_yyyy_rejeitado(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        (serie / "anos" / "extra.json").write_text("[]", encoding="utf-8")
        assert not Validator(raiz).run()

    def test_checksum_orfao_detectado(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        arquivos = json.loads((serie / "somas-verificacao.json").read_text())
        del arquivos["arquivos"]["metadados.json"]
        (serie / "somas-verificacao.json").write_text(
            json.dumps(arquivos), encoding="utf-8"
        )
        assert not Validator(raiz).run()

    def test_checksum_valores_proibido_no_particionado(self, raiz: Path) -> None:
        serie = _escrever_serie_particionada(raiz / "dados" / "v1")
        arquivos = json.loads((serie / "somas-verificacao.json").read_text())
        arquivos["arquivos"]["valores.json"] = "0" * 64
        (serie / "somas-verificacao.json").write_text(
            json.dumps(arquivos), encoding="utf-8"
        )
        assert not Validator(raiz).run()

    def test_cambio_valida_campos(self, raiz: Path) -> None:
        serie = _escrever_serie_particionada(raiz / "dados" / "v1")
        payload = json.loads((serie / "anos" / "2026.json").read_text(encoding="utf-8"))
        del payload[0]["cotacao-venda"]
        (serie / "anos" / "2026.json").write_text(json.dumps(payload), encoding="utf-8")
        _checksums(serie, "metadados.json", "anos/2026.json")
        assert not Validator(raiz).run()

    def test_metadados_ultima_observacao_desatualizada(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        payload = [
            {"data": "2026-01-01", "valor": 0.33},
            {"data": "2026-02-01", "valor": 0.34},
        ]
        (serie / "valores.json").write_text(json.dumps(payload), encoding="utf-8")
        (serie / "anos" / "2026.json").write_text(json.dumps(payload), encoding="utf-8")
        _checksums(serie, "valores.json", "metadados.json", "anos/2026.json")
        assert not Validator(raiz).run()  # ultima-observacao=2026-01-01 ≠ real 2026-02-01

    def test_ordem_entre_particoes_validada(self, raiz: Path) -> None:
        serie = _escrever_serie_particionada(raiz / "dados" / "v1")
        (serie / "anos" / "2025.json").write_text(
            json.dumps(
                [
                    {
                        "data": "2025-12-01",
                        "cotacao-compra": 4.0,
                        "cotacao-venda": 4.0,
                        "paridade-compra": 1.0,
                        "paridade-venda": 1.0,
                        "data-hora-fonte": "x",
                    }
                ]
            ),
            encoding="utf-8",
        )
        meta = json.loads((serie / "metadados.json").read_text(encoding="utf-8"))
        meta["primeira-observacao"] = "2025-12-01"
        (serie / "metadados.json").write_text(json.dumps(meta), encoding="utf-8")
        _checksums(serie, "metadados.json", "anos/2025.json", "anos/2026.json")
        (raiz / "manifesto.json").write_text(
            json.dumps(_manifesto_valido(raiz / "dados" / "v1")), encoding="utf-8"
        )
        assert Validator(raiz).run()  # 2025 < 2026: ordem global ok

    def test_ordem_fora_entre_particoes_rejeitada(self, raiz: Path) -> None:
        serie = _escrever_serie_particionada(raiz / "dados" / "v1")
        payload = json.loads((serie / "anos" / "2026.json").read_text(encoding="utf-8"))
        payload[0]["data"] = "2026-01-02"
        (serie / "anos" / "2026.json").write_text(json.dumps(payload), encoding="utf-8")
        (serie / "anos" / "2025.json").write_text(
            json.dumps(
                [
                    {
                        "data": "2026-01-01",
                        "cotacao-compra": 4.0,
                        "cotacao-venda": 4.0,
                        "paridade-compra": 1.0,
                        "paridade-venda": 1.0,
                        "data-hora-fonte": "x",
                    }
                ]
            ),
            encoding="utf-8",
        )
        _checksums(serie, "metadados.json", "anos/2025.json", "anos/2026.json")
        assert not Validator(raiz).run()  # 2026-01-01 em 2025.json: fora do ano

    def test_root_allowlist_aceita_pyproject(self, raiz: Path) -> None:
        _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        (raiz / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        (raiz / "uv.lock").write_text("", encoding="utf-8")
        (raiz / "tests").mkdir()
        (raiz / "manifesto.json").write_text(
            json.dumps(_manifesto_valido(raiz / "dados" / "v1")), encoding="utf-8"
        )
        assert Validator(raiz).run()

    def test_root_arquivo_estranho_rejeitado(self, raiz: Path) -> None:
        (raiz / "estranho.bin").write_bytes(b"x")
        assert not Validator(raiz).run()

    def test_serie_orfã_no_filesystem_detectada(self, raiz: Path) -> None:
        serie = _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        (raiz / "manifesto.json").write_text(
            json.dumps(
                {
                    "versao-schema": "v1",
                    "descricao": "d",
                    "categorias": {},
                    "series": [],  # série física fora do manifesto
                }
            ),
            encoding="utf-8",
        )
        assert not Validator(raiz).run()

    def test_entrada_orfã_no_manifesto_detectada(self, raiz: Path) -> None:
        _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        manifesto = _manifesto_valido(raiz / "dados" / "v1")
        manifesto["series"].append(
            {
                "identificador": "fantasma",
                "nome": "x",
                "categoria": "inflacao",
                "caminho": "inflacao/fantasma",
                "descricao": "d",
                "frequencia": "mensal",
                "unidade": "%",
                "moeda": "BRL",
                "provedor": "BACEN",
                "status": "ativa",
                "armazenamento": "agregado-e-anual",
                "particionamento": "anual",
                "agregado-disponivel": True,
                "primeira-observacao": None,
                "ultima-observacao": None,
                "ultima-alteracao-dados": None,
                "metadados": "inflacao/fantasma/metadados.json",
                "somas-verificacao": "inflacao/fantasma/somas-verificacao.json",
            }
        )
        (raiz / "manifesto.json").write_text(json.dumps(manifesto), encoding="utf-8")
        assert not Validator(raiz).run()

    def test_identificador_duplicado_no_manifesto(self, raiz: Path) -> None:
        _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        manifesto = _manifesto_valido(raiz / "dados" / "v1")
        manifesto["series"].append(dict(manifesto["series"][0]))
        (raiz / "manifesto.json").write_text(json.dumps(manifesto), encoding="utf-8")
        assert not Validator(raiz).run()

    def test_categoria_divergente_manifesto_vs_metadados(self, raiz: Path) -> None:
        _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        manifesto = _manifesto_valido(raiz / "dados" / "v1")
        manifesto["series"][0]["categoria"] = "taxas-de-juros"
        (raiz / "manifesto.json").write_text(json.dumps(manifesto), encoding="utf-8")
        assert not Validator(raiz).run()


class TestJsonSchema:
    def test_schemas_validos_contra_metaschema(self, raiz: Path) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from validate_schemas import _validar_schemas

        erros: list[str] = []
        _validar_schemas(erros)
        assert erros == []

    def test_dados_validos_contra_schemas(self, raiz: Path) -> None:
        _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from validate_schemas import _validar_dados

        erros: list[str] = []
        _validar_dados(raiz, erros)
        assert erros == []

    def test_dados_particionado_validos_contra_schemas(self, raiz: Path) -> None:
        _escrever_serie_particionada(raiz / "dados" / "v1")
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from validate_schemas import _validar_dados

        erros: list[str] = []
        _validar_dados(raiz, erros)
        assert erros == []

    def test_script_cli_exit_zero(self, raiz: Path) -> None:
        _escrever_serie_agregada(raiz / "dados" / "v1", "inflacao", "ipca")
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        r = subprocess.run(
            [sys.executable, str(scripts / "validate_schemas.py"), str(raiz)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
