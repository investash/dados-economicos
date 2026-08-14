#!/usr/bin/env python3
"""Validador independente do dataset de dados econômicos (schema v1).

Barreira de CI separada do Sneffelz: este script NÃO importa código do
Sneffelz e usa apenas a biblioteca padrão do Python. Mesmo que o Sneffelz
tenha um bug, o repositório de dados rejeita um dataset inválido.

Uso:
    python3 scripts/validate_dataset.py [raiz-do-repositorio]

Valida:
  * JSON parse de todos os arquivos (NaN/Infinity rejeitados — JSON estrito);
  * estrutura de diretórios (dados/v1/<categoria>/<serie>/);
  * campos e tipos obrigatórios de metadados.json e manifesto.json;
  * datas ISO-8601, ordenação cronológica e ausência de duplicidades;
  * storage frequency-aware:
      agregado-e-anual  → valores.json OBRIGATÓRIO + anos/ concatenação == valores;
      particionado-anual→ valores.json PROIBIDO; histórico reconstruído dos anos/;
  * primeira/ultima-observacao dos metadados == primeira/última real dos dados;
  * manifesto ↔ filesystem BIDIRECIONAL (sem série órfã, sem entrada órfã);
  * checksums SHA-256 respeitando a estratégia de storage (sem self-hash);
  * markers gerenciados do README;
  * ausência de dados legados na raiz.

Exit code: 0 = válido; 1 = inválido (com lista de erros no stderr).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "v1"
CATEGORIAS = ("inflacao", "taxas-de-juros", "taxas-de-cambio")
ARQUIVOS_SERIE = {"metadados.json", "valores.json", "somas-verificacao.json", "anos"}
ARQUIVOS_RAIZ = {
    ".git",
    ".github",
    "AGENTS.md",
    "CODE_OF_CONDUCT.md",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "NOTICE.md",
    "README.md",
    "SECURITY.md",
    "docs",
    "esquemas",
    "manifesto.json",
    "scripts",
    "dados",
    ".gitignore",
    # projeto do validador independente
    "pyproject.toml",
    "uv.lock",
    "tests",
}
ARMAZENAMENTO_AGREGADO = "agregado-e-anual"
ARMAZENAMENTO_PARTICIONADO = "particionado-anual"
README_INICIO = "<!-- sneffelz:generated:start -->"
README_FIM = "<!-- sneffelz:generated:end -->"
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_estrito(texto: str, origem: str) -> object:
    """json.loads com rejeição explícita de NaN/Infinity/-Infinity."""
    try:
        return json.loads(
            texto,
            parse_constant=lambda c: _constante_invalida(c, origem),  # type: ignore[arg-type]
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"{origem}: JSON inválido: {exc}") from exc
    except _ConstanteInvalida as exc:
        raise ValueError(f"{origem}: {exc}") from exc


class _ConstanteInvalida(ValueError):
    pass


def _constante_invalida(constante: str, origem: str) -> object:
    raise _ConstanteInvalida(
        f"{origem}: constante não-JSON proibida: {constante}"
    )


class Validator:
    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz
        self.erros: list[str] = []
        self.series: list[str] = []

    def run(self) -> bool:
        self._validar_raiz()
        self._validar_manifesto()
        self._validar_readme()
        self._validar_series()
        self._validar_manifesto_filesystem()
        return not self.erros

    def _erro(self, mensagem: str) -> None:
        self.erros.append(mensagem)

    def _ler_json(self, caminho: Path, origem: str) -> object:
        try:
            texto = caminho.read_text(encoding="utf-8")
        except OSError as exc:
            self._erro(f"{origem}: não foi possível ler: {exc}")
            return None
        try:
            return _parse_estrito(texto, origem)
        except ValueError as exc:
            self._erro(str(exc))
            return None

    # ------------------------------------------------------------ raiz

    def _validar_raiz(self) -> None:
        if not self.raiz.is_dir():
            self._erro(f"raiz não encontrada: {self.raiz}")
            return
        for item in self.raiz.iterdir():
            if item.name not in ARQUIVOS_RAIZ:
                self._erro(f"item inesperado na raiz: {item.name}")

        v1 = self.raiz / "dados" / SCHEMA_VERSION
        if not v1.is_dir():
            self._erro(f"dados/{SCHEMA_VERSION} não encontrado")
        for categoria in CATEGORIAS:
            if not (v1 / categoria).is_dir():
                self._erro(f"categoria ausente: dados/{SCHEMA_VERSION}/{categoria}")

        for legado in ("ipca", "ipca-15", "igp-m", "inpc", "metas-de-inflacao.json"):
            if (self.raiz / legado).exists():
                self._erro(
                    f"dado legado na raiz (deve ficar em dados/{SCHEMA_VERSION}/): {legado}"
                )

    # --------------------------------------------------------- manifesto

    def _validar_manifesto(self) -> None:
        caminho = self.raiz / "manifesto.json"
        if not caminho.is_file():
            self._erro("manifesto.json ausente")
            return
        payload = self._ler_json(caminho, "manifesto.json")
        if not isinstance(payload, dict):
            self._erro("manifesto.json: deve ser um objeto")
            return
        if payload.get("versao-schema") != SCHEMA_VERSION:
            self._erro(f"manifesto.json: versao-schema deve ser {SCHEMA_VERSION}")
        if not isinstance(payload.get("series"), list):
            self._erro("manifesto.json: campo 'series' ausente ou inválido")
            return
        vistos: dict[str, str] = {}
        for serie in payload["series"]:
            if not isinstance(serie, dict):
                self._erro("manifesto.json: item de series deve ser objeto")
                continue
            for campo in (
                "identificador",
                "caminho",
                "metadados",
                "somas-verificacao",
                "status",
                "categoria",
                "armazenamento",
                "agregado-disponivel",
            ):
                if campo not in serie:
                    self._erro(f"manifesto.json: série sem campo '{campo}'")
            status = serie.get("status")
            if status not in ("ativa", "inativa"):
                self._erro(f"manifesto.json: status inválido {status!r}")
            arm = serie.get("armazenamento")
            if arm not in (ARMAZENAMENTO_AGREGADO, ARMAZENAMENTO_PARTICIONADO):
                self._erro(f"manifesto.json: armazenamento inválido {arm!r}")
            identificador = serie.get("identificador")
            caminho_serie = serie.get("caminho")
            if isinstance(identificador, str):
                if identificador in vistos:
                    self._erro(
                        f"manifesto.json: identificador duplicado: {identificador}"
                    )
                vistos[identificador] = "identificador"
            if isinstance(caminho_serie, str):
                if caminho_serie in vistos:
                    self._erro(f"manifesto.json: caminho duplicado: {caminho_serie}")
                vistos[caminho_serie] = "caminho"

    def _validar_manifesto_filesystem(self) -> None:
        """Prova bidirecional: cada série física está no manifesto e vice-versa."""
        caminho = self.raiz / "manifesto.json"
        if not caminho.is_file():
            return
        payload = self._ler_json(caminho, "manifesto.json")
        if not isinstance(payload, dict) or not isinstance(payload.get("series"), list):
            return

        v1 = self.raiz / "dados" / SCHEMA_VERSION
        no_manifesto: set[str] = set()
        for serie in payload["series"]:
            if not isinstance(serie, dict):
                continue
            rel = serie.get("caminho")
            if not isinstance(rel, str):
                continue
            no_manifesto.add(rel)
            base = v1 / rel
            if not base.is_dir():
                self._erro(f"manifesto.json: caminho não existe no filesystem: {rel}")
                continue
            if (base / "metadados.json").is_file():
                meta = self._ler_json(base / "metadados.json", f"{rel}/metadados.json")
                if isinstance(meta, dict):
                    if meta.get("identificador") != serie.get("identificador"):
                        self._erro(
                            f"manifesto.json: identificador do manifesto "
                            f"({serie.get('identificador')!r}) difere dos metadados "
                            f"({meta.get('identificador')!r}) para {rel}"
                        )
                    if meta.get("categoria") != serie.get("categoria"):
                        self._erro(
                            f"manifesto.json: categoria do manifesto difere dos "
                            f"metadados para {rel}"
                        )
                    meta_arm = meta.get("armazenamento")
                    manifesto_arm = serie.get("armazenamento")
                    if meta_arm != manifesto_arm:
                        self._erro(
                            f"manifesto.json: armazenamento do manifesto "
                            f"({manifesto_arm!r}) difere dos metadados ({meta_arm!r}) "
                            f"para {rel}"
                        )
            else:
                self._erro(f"manifesto.json: metadados.json ausente para {rel}")
            if not (base / "somas-verificacao.json").is_file():
                self._erro(f"manifesto.json: somas-verificacao.json ausente para {rel}")

        # cada série física presente no manifesto
        if not v1.is_dir():
            return
        for categoria in CATEGORIAS:
            cat_dir = v1 / categoria
            if not cat_dir.is_dir():
                continue
            for serie_dir in sorted(cat_dir.iterdir()):
                if not serie_dir.is_dir():
                    continue
                rel = f"{categoria}/{serie_dir.name}"
                if rel not in no_manifesto:
                    self._erro(f"série órfã no filesystem (ausente do manifesto): {rel}")

    # ------------------------------------------------------------ README

    def _validar_readme(self) -> None:
        caminho = self.raiz / "README.md"
        if not caminho.is_file():
            self._erro("README.md ausente")
            return
        texto = caminho.read_text(encoding="utf-8")
        if README_INICIO not in texto or README_FIM not in texto:
            self._erro("README.md sem markers gerenciados sneffelz")
            return
        if texto.index(README_INICIO) > texto.index(README_FIM):
            self._erro("README.md: markers gerenciados fora de ordem")

    # ------------------------------------------------------------ séries

    def _validar_series(self) -> None:
        v1 = self.raiz / "dados" / SCHEMA_VERSION
        if not v1.is_dir():
            return
        for categoria in CATEGORIAS:
            cat_dir = v1 / categoria
            if not cat_dir.is_dir():
                continue
            for serie_dir in sorted(cat_dir.iterdir()):
                if not serie_dir.is_dir():
                    self._erro(f"{categoria}/{serie_dir.name}: não é diretório")
                    continue
                self.series.append(serie_dir.name)
                self._validar_serie(serie_dir, categoria)

    def _validar_serie(self, base: Path, categoria: str) -> None:
        prefixo = f"{categoria}/{base.name}"
        for item in base.iterdir():
            if item.name not in ARQUIVOS_SERIE:
                self._erro(f"{prefixo}: arquivo inesperado {item.name}")

        metadados = self._ler_json(base / "metadados.json", f"{prefixo}/metadados.json")
        if not isinstance(metadados, dict):
            if metadados is None:
                self._erro(f"{prefixo}: metadados.json ausente ou ilegível")
            else:
                self._erro(f"{prefixo}/metadados.json: deve ser um objeto")
            return

        self._validar_metadados(metadados, prefixo)

        armazenamento = metadados.get("armazenamento")
        if armazenamento not in (ARMAZENAMENTO_AGREGADO, ARMAZENAMENTO_PARTICIONADO):
            self._erro(
                f"{prefixo}/metadados.json: armazenamento deve ser "
                f"{ARMAZENAMENTO_AGREGADO} ou {ARMAZENAMENTO_PARTICIONADO}"
            )
            return

        valores_path = base / "valores.json"
        if armazenamento == ARMAZENAMENTO_AGREGADO:
            if not valores_path.is_file():
                self._erro(f"{prefixo}: valores.json OBRIGATÓRIO (agregado-e-anual)")
                return
            valores = self._ler_json(valores_path, f"{prefixo}/valores.json")
            if not isinstance(valores, list):
                self._erro(f"{prefixo}/valores.json: deve ser uma lista")
                return
            if not valores:
                self._erro(f"{prefixo}/valores.json: lista vazia")
                return
            self._validar_registros(valores, f"{prefixo}/valores.json")
        else:
            if valores_path.is_file():
                self._erro(
                    f"{prefixo}: valores.json PROIBIDO (particionado-anual); "
                    f"histórico vive em anos/"
                )
                valores = None
            else:
                valores = None

        observacoes = self._validar_anos(base, prefixo, armazenamento)
        if observacoes is not None and armazenamento == ARMAZENAMENTO_AGREGADO:
            if observacoes != valores:
                self._erro(f"{prefixo}: anos/*.json não correspondem a valores.json")
        elif observacoes is not None:
            # particionado: ordem global e duplicidade entre partições
            datas = [o.get("data") for o in observacoes]
            if datas != sorted(datas):
                self._erro(f"{prefixo}: registros fora de ordem cronológica entre partições")
            if len(set(datas)) != len(datas):
                self._erro(f"{prefixo}: datas duplicadas entre partições")

        self._validar_checksums(base, prefixo, armazenamento)
        self._validar_metadata_dados(metadados, observacoes, prefixo)

    def _validar_registros(self, registros: list, origem: str) -> None:
        """Valida cada registro e a ordem/duplicidade no agregado."""
        datas: list[str] = []
        for i, item in enumerate(registros):
            self._validar_registro(item, i, origem)
            if isinstance(item, dict) and isinstance(item.get("data"), str):
                datas.append(item["data"])
        if datas != sorted(datas):
            self._erro(f"{origem}: registros fora de ordem cronológica")
        if len(set(datas)) != len(datas):
            self._erro(f"{origem}: datas duplicadas")

    def _validar_registro(self, item: object, i: int, origem: str) -> None:
        if not isinstance(item, dict) or "data" not in item:
            self._erro(f"{origem}: registro {i} inválido")
            return
        data = item["data"]
        if not isinstance(data, str) or not DATA_ISO.match(data):
            self._erro(f"{origem}: data inválida no registro {i}")
            return
        try:
            ano, mes, dia = (int(p) for p in data.split("-"))
            _ = __import__("datetime").date(ano, mes, dia)
        except ValueError:
            self._erro(f"{origem}: data inexistente {data!r}")
            return
        if "valor" in item:
            valor = item["valor"]
            if not isinstance(valor, (int, float)):
                self._erro(f"{origem}: valor não numérico no registro {i}")
        else:
            for campo in (
                "cotacao-compra",
                "cotacao-venda",
                "paridade-compra",
                "paridade-venda",
                "data-hora-fonte",
            ):
                if campo not in item:
                    self._erro(f"{origem}: campo '{campo}' ausente no registro {i}")
                elif (
                    campo != "data-hora-fonte"
                    and not isinstance(item[campo], (int, float))
                ):
                    self._erro(f"{origem}: '{campo}' não numérico no registro {i}")

    def _validar_anos(
        self, base: Path, prefixo: str, armazenamento: str
    ) -> list[dict] | None:
        anos_dir = base / "anos"
        if not anos_dir.is_dir():
            self._erro(f"{prefixo}: diretório anos/ ausente")
            return None
        arquivos = sorted(anos_dir.glob("*.json"))
        if not arquivos:
            self._erro(f"{prefixo}: anos/ sem partições")
            return None
        combinado: list[dict] = []
        for arquivo in arquivos:
            nome = arquivo.name
            if not re.fullmatch(r"\d{4}\.json", nome):
                self._erro(f"{prefixo}/anos/: nome deve ser estritamente YYYY.json — {nome}")
                continue
            payload = self._ler_json(arquivo, f"{prefixo}/anos/{nome}")
            if payload is None:
                return None
            if not isinstance(payload, list):
                self._erro(f"{prefixo}/anos/{nome}: deve ser uma lista")
                return None
            for i, item in enumerate(payload):
                self._validar_registro(item, i, f"{prefixo}/anos/{nome}")
                if isinstance(item, dict) and isinstance(item.get("data"), str):
                    if item["data"][:4] != nome[:4]:
                        self._erro(
                            f"{prefixo}/anos/{nome}: registro de {item['data']} "
                            f"fora do ano do arquivo"
                        )
                    combinado.append(item)
        if armazenamento == ARMAZENAMENTO_PARTICIONADO and not combinado:
            self._erro(f"{prefixo}: particionado-anual sem nenhuma observação")
        return combinado

    def _validar_metadata_dados(
        self, meta: dict, observacoes: list[dict] | None, prefixo: str
    ) -> None:
        """primeira/ultima-observacao dos metadados == primeira/última real."""
        if not observacoes:
            return
        primeira = meta.get("primeira-observacao")
        ultima = meta.get("ultima-observacao")
        datas = [o["data"] for o in observacoes if isinstance(o, dict) and isinstance(o.get("data"), str)]
        if not datas:
            return
        real_primeira = min(datas)
        real_ultima = max(datas)
        if primeira is not None and primeira != real_primeira:
            self._erro(
                f"{prefixo}/metadados.json: primeira-observacao ({primeira!r}) "
                f"≠ primeira real ({real_primeira})"
            )
        if ultima is not None and ultima != real_ultima:
            self._erro(
                f"{prefixo}/metadados.json: ultima-observacao ({ultima!r}) "
                f"≠ última real ({real_ultima})"
            )

    def _validar_metadados(self, meta: dict, prefixo: str) -> None:
        obrigatorios = (
            "identificador",
            "nome",
            "descricao",
            "categoria",
            "provedor",
            "moeda",
            "frequencia",
            "unidade",
            "status",
            "versao-schema",
            "referencia-oficial",
            "ultima-alteracao-dados",
            "versao-sneffelz",
            "armazenamento",
            "particionamento",
            "agregado-disponivel",
        )
        for campo in obrigatorios:
            if campo not in meta:
                self._erro(f"{prefixo}/metadados.json: campo obrigatório ausente: {campo}")
        if meta.get("versao-schema") != SCHEMA_VERSION:
            self._erro(f"{prefixo}/metadados.json: versao-schema deve ser {SCHEMA_VERSION}")
        if meta.get("provedor") != "BACEN":
            self._erro(f"{prefixo}/metadados.json: provedor deve ser BACEN")
        if meta.get("frequencia") not in ("diaria", "mensal", "anual"):
            self._erro(f"{prefixo}/metadados.json: frequencia inválida")
        if meta.get("status") not in ("ativa", "inativa"):
            self._erro(f"{prefixo}/metadados.json: status inválido")
        if meta.get("particionamento") != "anual":
            self._erro(f"{prefixo}/metadados.json: particionamento deve ser anual")
        if meta.get("agregado-disponivel") not in (True, False):
            self._erro(f"{prefixo}/metadados.json: agregado-disponivel deve ser booleano")
        arm = meta.get("armazenamento")
        if arm == ARMAZENAMENTO_AGREGADO:
            if meta.get("frequencia") == "diaria":
                self._erro(
                    f"{prefixo}/metadados.json: agregado-e-anual exige frequência "
                    f"mensal ou anual"
                )
            if meta.get("agregado-disponivel") is not True:
                self._erro(
                    f"{prefixo}/metadados.json: agregado-e-anual exige "
                    f"agregado-disponivel=true"
                )
        elif arm == ARMAZENAMENTO_PARTICIONADO:
            if meta.get("frequencia") != "diaria":
                self._erro(
                    f"{prefixo}/metadados.json: particionado-anual exige frequência diária"
                )
            if meta.get("agregado-disponivel") is not False:
                self._erro(
                    f"{prefixo}/metadados.json: particionado-anual exige "
                    f"agregado-disponivel=false"
                )
        for campo in ("primeira-observacao", "ultima-observacao", "ultima-alteracao-dados"):
            valor = meta.get(campo)
            if valor is not None and not isinstance(valor, str):
                self._erro(f"{prefixo}/metadados.json: {campo} deve ser string ou null")
        for campo in ("codigo-sgs",):
            valor = meta.get(campo)
            if valor is not None and not isinstance(valor, int):
                self._erro(f"{prefixo}/metadados.json: {campo} deve ser inteiro ou null")

    # --------------------------------------------------------- checksums

    def _validar_checksums(self, base: Path, prefixo: str, armazenamento: str) -> None:
        caminho = base / "somas-verificacao.json"
        if not caminho.is_file():
            self._erro(f"{prefixo}: somas-verificacao.json ausente")
            return
        payload = self._ler_json(caminho, f"{prefixo}/somas-verificacao.json")
        if not isinstance(payload, dict) or payload.get("algoritmo") != "sha256":
            self._erro(f"{prefixo}/somas-verificacao.json: algoritmo deve ser sha256")
            return
        arquivos = payload.get("arquivos")
        if not isinstance(arquivos, dict):
            self._erro(f"{prefixo}/somas-verificacao.json: campo 'arquivos' inválido")
            return
        if "somas-verificacao.json" in arquivos:
            self._erro(f"{prefixo}/somas-verificacao.json: autorreferência proibida")
        for rel, esperado in arquivos.items():
            if not isinstance(esperado, str) or not re.fullmatch(r"[a-f0-9]{64}", esperado):
                self._erro(f"{prefixo}/somas-verificacao.json: hash inválido para {rel}")
                continue
            caminho_arquivo = base / rel
            if not caminho_arquivo.is_file():
                self._erro(f"{prefixo}: checksum referencia arquivo inexistente: {rel}")
                continue
            real = _sha256_streaming(caminho_arquivo)
            if real != esperado:
                self._erro(f"{prefixo}: checksum de {rel} não confere")
        # checksums órfãos: arquivos esperados sem hash (conforme storage)
        esperados: set[str] = {"metadados.json"}
        if armazenamento == ARMAZENAMENTO_AGREGADO:
            esperados.add("valores.json")
        if (base / "anos").is_dir():
            esperados.update(f"anos/{f.name}" for f in (base / "anos").glob("*.json"))
        for esperado in sorted(esperados):
            if esperado not in arquivos:
                self._erro(f"{prefixo}: checksum ausente para {esperado}")
        # checksums extras indesejados: valores.json num particionado
        if armazenamento == ARMAZENAMENTO_PARTICIONADO and "valores.json" in arquivos:
            self._erro(f"{prefixo}: checksum de valores.json proibido (particionado-anual)")


def _sha256_streaming(caminho: Path) -> str:
    digest = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            digest.update(bloco)
    return digest.hexdigest()


def main() -> int:
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    validator = Validator(raiz)
    ok = validator.run()
    if ok:
        print(f"OK: {len(validator.series)} série(s) íntegras em dados/{SCHEMA_VERSION}")
        return 0
    print(f"FALHA: {len(validator.erros)} erro(s):", file=sys.stderr)
    for erro in validator.erros:
        print(f"  - {erro}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
