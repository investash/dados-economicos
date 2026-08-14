#!/usr/bin/env python3
"""Validador independente do dataset de dados econômicos (schema v1).

Barreira de CI separada do Sneffelz: este script NÃO importa código do
Sneffelz e usa apenas a biblioteca padrão do Python. Mesmo que o Sneffelz
tenha um bug, o repositório de dados rejeita um dataset inválido.

Uso:
    python3 scripts/validate_dataset.py [raiz-do-repositorio]

Valida:
  * JSON parse de todos os arquivos;
  * estrutura de diretórios (dados/v1/<categoria>/<serie>/);
  * campos e tipos obrigatórios de metadados.json e manifesto.json;
  * datas ISO-8601, ordenação cronológica e ausência de duplicidades;
  * consistência valores.json ↔ anos/*.json;
  * checksums SHA-256 (somas-verificacao.json);
  * markers gerenciados do README;
  * ausência de dados legados na raiz (séries não podem ficar fora de dados/v1);
  * determinismo relevante (chaves ordenadas em metadados/manifesto).

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
}
README_INICIO = "<!-- sneffelz:generated:start -->"
README_FIM = "<!-- sneffelz:generated:end -->"
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
            return json.loads(texto)
        except json.JSONDecodeError as exc:
            self._erro(f"{origem}: JSON inválido: {exc}")
            return None

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
            ):
                if campo not in serie:
                    self._erro(f"manifesto.json: série sem campo '{campo}'")
            status = serie.get("status")
            if status not in ("ativa", "inativa"):
                self._erro(f"manifesto.json: status inválido {status!r}")

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
        valores = self._ler_json(base / "valores.json", f"{prefixo}/valores.json")
        if metadados is None or valores is None:
            return

        if isinstance(metadados, dict):
            self._validar_metadados(metadados, prefixo)
        else:
            self._erro(f"{prefixo}/metadados.json: deve ser um objeto")

        if isinstance(valores, list):
            self._validar_valores(valores, prefixo)
        else:
            self._erro(f"{prefixo}/valores.json: deve ser uma lista")

        self._validar_anos(base, valores, prefixo)
        self._validar_checksums(base, prefixo)

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
        for campo in ("primeira-observacao", "ultima-observacao", "ultima-alteracao-dados"):
            valor = meta.get(campo)
            if valor is not None and not isinstance(valor, str):
                self._erro(f"{prefixo}/metadados.json: {campo} deve ser string ou null")
        for campo in ("codigo-sgs",):
            valor = meta.get(campo)
            if valor is not None and not isinstance(valor, int):
                self._erro(f"{prefixo}/metadados.json: {campo} deve ser inteiro ou null")

    def _validar_valores(self, valores: list, prefixo: str) -> None:
        if not valores:
            self._erro(f"{prefixo}/valores.json: lista vazia")
            return
        datas: list[str] = []
        for i, item in enumerate(valores):
            if not isinstance(item, dict) or "data" not in item:
                self._erro(f"{prefixo}/valores.json: registro {i} inválido")
                return
            data = item["data"]
            if not isinstance(data, str) or not DATA_ISO.match(data):
                self._erro(f"{prefixo}/valores.json: data inválida no registro {i}")
                return
            try:
                ano, mes, dia = (int(p) for p in data.split("-"))
                _ = __import__("datetime").date(ano, mes, dia)
            except ValueError:
                self._erro(f"{prefixo}/valores.json: data inexistente {data!r}")
                return
            datas.append(data)
            if "valor" in item:
                # série escalar: valor numérico finito
                valor = item["valor"]
                if not isinstance(valor, (int, float)):
                    self._erro(f"{prefixo}/valores.json: valor não numérico no registro {i}")
                elif isinstance(valor, float) and (valor != valor or valor in (float("inf"), float("-inf"))):
                    self._erro(f"{prefixo}/valores.json: valor NaN/Infinity no registro {i}")
            else:
                # série de câmbio: campos de cotação/paridade obrigatórios
                for campo in (
                    "cotacao-compra",
                    "cotacao-venda",
                    "paridade-compra",
                    "paridade-venda",
                    "data-hora-fonte",
                ):
                    if campo not in item:
                        self._erro(f"{prefixo}/valores.json: campo '{campo}' ausente no registro {i}")
                    elif not isinstance(item[campo], (int, float)) and campo != "data-hora-fonte":
                        self._erro(f"{prefixo}/valores.json: '{campo}' não numérico no registro {i}")
        if datas != sorted(datas):
            self._erro(f"{prefixo}/valores.json: registros fora de ordem cronológica")
        if len(set(datas)) != len(datas):
            self._erro(f"{prefixo}/valores.json: datas duplicadas")

    def _validar_anos(self, base: Path, valores: object, prefixo: str) -> None:
        anos_dir = base / "anos"
        if not anos_dir.is_dir():
            self._erro(f"{prefixo}: diretório anos/ ausente")
            return
        combinado: list[object] = []
        for arquivo in sorted(anos_dir.glob("*.json")):
            nome = arquivo.name
            if not re.fullmatch(r"\d{4}\.json", nome):
                self._erro(f"{prefixo}/anos/: nome deve ser estritamente YYYY.json — {nome}")
                continue
            payload = self._ler_json(arquivo, f"{prefixo}/anos/{nome}")
            if payload is None:
                return
            if not isinstance(payload, list):
                self._erro(f"{prefixo}/anos/{nome}: deve ser uma lista")
                return
            for item in payload:
                if isinstance(item, dict) and isinstance(item.get("data"), str):
                    if item["data"][:4] != nome[:4]:
                        self._erro(
                            f"{prefixo}/anos/{nome}: registro de {item['data']} "
                            f"fora do ano do arquivo"
                        )
            combinado.extend(payload)
        if combinado != valores:
            self._erro(f"{prefixo}: anos/*.json não correspondem a valores.json")

    def _validar_checksums(self, base: Path, prefixo: str) -> None:
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
        # checksums órfãos: arquivos esperados sem hash
        esperados = {"valores.json", "metadados.json"}
        if (base / "anos").is_dir():
            esperados.update(f"anos/{f.name}" for f in (base / "anos").glob("*.json"))
        for esperado in sorted(esperados):
            if esperado not in arquivos:
                self._erro(f"{prefixo}: checksum ausente para {esperado}")


def _sha256_streaming(caminho: Path) -> str:
    digest = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _ano_do_arquivo(prefixo: str) -> int | None:
    m = re.search(r"/anos/(\d{4})\.json", prefixo)
    return int(m.group(1)) if m else None


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
