"""Monta e envia a edição do dia de O Compilado.

    python edicao.py                        monta e envia agora
    python edicao.py --aguardar-ate 08:00   espera dar 8h antes de varrer (é o que o GitHub Actions usa)
    python edicao.py --previa saida.html    só gera o HTML: não envia e não mexe no estado
    python edicao.py --forcar               envia mesmo se a edição de hoje já saiu
    python edicao.py --reenviar 2026-10-16  reenvia uma edição arquivada, igualzinha, sem mexer no estado
"""
import argparse
import os
import re
import sys
import time
from datetime import datetime, timedelta
from html import unescape

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from compilado import envio, estado, fontes, jornal, ranking  # noqa: E402
from compilado.config import FUSO, HF_DIAS, HF_DIAS_SEMANA, PASTA_EDICOES  # noqa: E402

ESPERA_MAXIMA = timedelta(minutes=90)


def agora():
    return datetime.now(FUSO)


def aguarda(hhmm):
    h, m = map(int, hhmm.split(":"))
    alvo = agora().replace(hour=h, minute=m, second=0, microsecond=0)
    falta = alvo - agora()
    if timedelta(0) < falta <= ESPERA_MAXIMA:
        print(f"Aguardando até {hhmm} ({int(falta.total_seconds())}s)…", flush=True)
        time.sleep(falta.total_seconds())


def reenvia(dia):
    """Rodar de novo não serve pra isso: os papers da edição já contam como enviados, então sairia outra."""
    with open(os.path.join(PASTA_EDICOES, f"{dia}.html"), encoding="utf-8") as f:
        html = f.read()
    titulo = re.search(r"<title>(.*?)</title>", html, re.S)
    assunto = unescape(titulo.group(1)) if titulo else f"O Compilado · {dia}"
    texto = "Esta edição de O Compilado é em HTML. Abra num leitor de e-mail com HTML ativado."
    destino = envio.envia(assunto, html, texto)
    print(f"Edição de {dia} reenviada para {destino}.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aguardar-ate", metavar="HH:MM")
    ap.add_argument("--previa", metavar="ARQUIVO.html")
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--reenviar", metavar="AAAA-MM-DD")
    args = ap.parse_args()

    if args.reenviar:
        return reenvia(args.reenviar)

    est = estado.carrega()
    hoje = agora().date()
    if estado.ja_saiu_hoje(est, hoje) and not (args.forcar or args.previa):
        print(f"A edição de {hoje:%d/%m} já saiu (nº {est['numero']}). Nada a fazer.")
        return 0
    if args.aguardar_ate:
        aguarda(args.aguardar_ate)

    hora = agora().strftime("%H:%M")
    avisos = []
    try:
        arxiv = fontes.arxiv()
    except Exception as e:
        arxiv = []
        avisos.append(f"arXiv fora do ar na hora da varredura ({e}); esta edição só tem o Hugging Face.")
    hf_semana, erros_hf = fontes.hugging_face(hoje, HF_DIAS_SEMANA)
    if len(erros_hf) == HF_DIAS_SEMANA:
        avisos.append("Hugging Face fora do ar na hora da varredura.")
    if not arxiv and len(erros_hf) == HF_DIAS_SEMANA:
        print("As duas fontes falharam:", *avisos, sep="\n  ", file=sys.stderr)
        return 1

    limite_recentes = (hoje - timedelta(days=HF_DIAS - 1)).isoformat()
    hf_recentes = [p for p in hf_semana if p["data_hf"] >= limite_recentes]
    edicao = ranking.monta(arxiv, hf_recentes, hf_semana, est["enviados"])
    numero = est["numero"] + 1
    assunto, html, texto = jornal.renderiza(edicao, numero, hoje, hora, avisos)
    print(f"{assunto}\n  arXiv: {len(arxiv)} novos · HF: {len(hf_recentes)} recentes, {len(hf_semana)} na semana")

    if args.previa:
        with open(args.previa, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Prévia salva em {args.previa} (nada foi enviado).")
        return 0

    destino = envio.envia(assunto, html, texto)
    print(f"Enviado para {destino} às {agora():%H:%M:%S}.")
    os.makedirs(PASTA_EDICOES, exist_ok=True)
    with open(os.path.join(PASTA_EDICOES, f"{hoje.isoformat()}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    estado.registra(est, hoje, ranking.papers_da_edicao(edicao))
    estado.salva(est)
    return 0


if __name__ == "__main__":
    sys.exit(main())
