"""Monta o e-mail com cara de jornal: HTML (estilos inline, que é o que cliente
de e-mail respeita) e uma versão em texto puro pra quem não renderiza HTML."""
from html import escape

from . import resumo

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

SERIF = "Georgia,'Times New Roman',Times,serif"
SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
TINTA, APAGADO, PAPEL, FUNDO, VERMELHO, FIO = "#1b1a17", "#625c53", "#fbf8f1", "#e9e2d3", "#9b1c1c", "#d6ccb8"


def data_extenso(d):
    return f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"


def _assinatura(p, max_nomes=3):
    a = p["autores"]
    if not a:
        nomes = ""
    elif len(a) <= max_nomes:
        nomes = a[0] if len(a) == 1 else ", ".join(a[:-1]) + " e " + a[-1]
    else:
        nomes = ", ".join(a[:max_nomes]) + f" e mais {len(a) - max_nomes}"
    partes = [f"Por {nomes}" if nomes else "", p.get("org") or ""]
    return " · ".join(x for x in partes if x)


def _chapeu(p):
    """A linha pequena acima do título."""
    partes = []
    if p["categorias"]:
        partes.append(" · ".join(p["categorias"][:3]))
    if p.get("votos"):
        partes.append(f"{p['votos']} votos no Hugging Face")
    if p.get("periodico"):
        partes.append("aceito: " + p["periodico"][:60])
    return " — ".join(partes)


def _links(p):
    itens = [("Ler no arXiv →", p["link"]), ("PDF", p["pdf"])]
    if p.get("codigo"):
        estrelas = f" ★{p['estrelas']}" if p.get("estrelas") else ""
        itens.append((f"Código{estrelas}", p["codigo"]))
    if p.get("votos") is not None:
        itens.append(("Discussão no HF", f"https://huggingface.co/papers/{p['id']}"))
    a = [f'<a href="{escape(u)}" style="color:{VERMELHO};text-decoration:none;font-weight:bold;">{escape(t)}</a>'
         for t, u in itens]
    return f'<p style="margin:10px 0 0;font-family:{SANS};font-size:12px;letter-spacing:.3px;">' + " &nbsp;·&nbsp; ".join(a) + "</p>"


def _pequeno(texto, cor=APAGADO, margem="0 0 6px"):
    return (f'<p style="margin:{margem};font-family:{SANS};font-size:11px;letter-spacing:1.4px;'
            f'text-transform:uppercase;color:{cor};">{escape(texto)}</p>')


def _em_uma_frase(p, tamanho=16):
    if not p.get("tldr"):
        return ""
    return (f'<p style="margin:0 0 10px;font-family:{SERIF};font-size:{tamanho}px;line-height:1.45;'
            f'font-style:italic;color:{TINTA};">{escape(p["tldr"])}</p>')


def _manchete(p):
    corpo = escape(p["resumo"])
    capitular = (f'<span style="float:left;font-family:{SERIF};font-size:54px;line-height:46px;'
                 f'padding:5px 8px 0 0;color:{TINTA};font-weight:bold;">{corpo[:1]}</span>')
    return f"""
<tr><td class="p" style="padding:22px 32px 6px;">
  {_pequeno("Manchete" + (" — " + _chapeu(p) if _chapeu(p) else ""), VERMELHO)}
  <h1 class="manchete" style="margin:0 0 10px;font-family:{SERIF};font-size:30px;line-height:1.15;font-weight:bold;color:{TINTA};">
    <a href="{escape(p['link'])}" style="color:{TINTA};text-decoration:none;">{escape(p['titulo'])}</a></h1>
  <p style="margin:0 0 14px;font-family:{SERIF};font-size:13px;font-style:italic;color:{APAGADO};">{escape(_assinatura(p, 4))}</p>
  {_em_uma_frase(p, 18)}
  <p style="margin:0;font-family:{SERIF};font-size:15px;line-height:1.65;color:{TINTA};">{capitular}{corpo[1:]}</p>
  {_links(p)}
</td></tr>"""


def _artigo(p, ultimo=False):
    borda = "" if ultimo else f"border-bottom:1px solid {FIO};"
    chapeu = _pequeno(_chapeu(p)) if _chapeu(p) else ""
    return f"""
<tr><td class="p" style="padding:16px 32px;{borda}">
  {chapeu}
  <h3 style="margin:0 0 6px;font-family:{SERIF};font-size:20px;line-height:1.25;font-weight:bold;color:{TINTA};">
    <a href="{escape(p['link'])}" style="color:{TINTA};text-decoration:none;">{escape(p['titulo'])}</a></h3>
  <p style="margin:0 0 10px;font-family:{SERIF};font-size:13px;font-style:italic;color:{APAGADO};">{escape(_assinatura(p))}</p>
  {_em_uma_frase(p)}
  <p style="margin:0;font-family:{SERIF};font-size:15px;line-height:1.6;color:{TINTA};">{escape(resumo.resumo(p['resumo']))}</p>
  {_links(p)}
</td></tr>"""


def _titulo_secao(titulo):
    return f"""
<tr><td class="p" style="padding:26px 32px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    <td style="border-top:3px solid {TINTA};border-bottom:1px solid {TINTA};padding:7px 0 6px;font-family:{SANS};
      font-size:12px;font-weight:bold;letter-spacing:2.5px;text-transform:uppercase;color:{TINTA};">{escape(titulo)}</td>
  </tr></table>
</td></tr>"""


def _lista(papers, mostra_votos=False):
    itens = []
    for p in papers:
        extra = f' <span style="font-family:{SANS};font-size:11px;color:{VERMELHO};">{p["votos"]} votos</span>' if mostra_votos and p.get("votos") else ""
        itens.append(f"""
  <p style="margin:0 0 12px;font-family:{SERIF};font-size:15px;line-height:1.45;color:{TINTA};">
    <span style="color:{VERMELHO};">■</span>&nbsp; <a href="{escape(p['link'])}" style="color:{TINTA};font-weight:bold;text-decoration:none;">{escape(p['titulo'])}</a>{extra}<br>
    <span style="font-size:14px;color:{APAGADO};">{escape(p.get('tldr') or resumo.linha(p['resumo']))}</span></p>""")
    return f'<tr><td class="p" style="padding:14px 32px 4px;">{"".join(itens)}</td></tr>'


def renderiza(edicao, numero, data, hora, avisos=()):
    m = edicao["manchete"]
    total = len(edicao["alta"]) + sum(len(ps) for _, ps in edicao["secoes"]) + len(edicao["tambem"]) + bool(m)
    titulo_curto = (m["titulo"][:70] + "…") if m and len(m["titulo"]) > 70 else (m["titulo"] if m else "sem papers novos hoje")
    assunto = f"O Compilado nº {numero} · {data:%d/%m} — {titulo_curto}"
    previa = (m.get("tldr") or resumo.linha(m["resumo"])) if m else ""

    blocos = []
    if m:
        blocos.append(_manchete(m))
    if edicao["alta"]:
        blocos.append(_titulo_secao("Em alta na comunidade"))
        blocos += [_artigo(p, i == len(edicao["alta"]) - 1) for i, p in enumerate(edicao["alta"])]
    for titulo, ps in edicao["secoes"]:
        blocos.append(_titulo_secao(titulo))
        blocos += [_artigo(p, i == len(ps) - 1) for i, p in enumerate(ps)]
    if edicao["tambem"]:
        blocos.append(_titulo_secao("Também nesta edição"))
        blocos.append(_lista(edicao["tambem"]))
    if edicao["semana"]:
        blocos.append(_titulo_secao("Os mais votados da semana"))
        blocos.append(f'<tr><td class="p" style="padding:10px 32px 0;font-family:{SERIF};font-size:14px;font-style:italic;color:{APAGADO};">'
                      "Dia fraco de anúncios no arXiv, então vai uma retrospectiva do que mais circulou nos últimos 7 dias.</td></tr>")
        blocos.append(_lista(edicao["semana"], mostra_votos=True))
    if not m and not edicao["semana"]:
        blocos.append(f'<tr><td class="p" style="padding:30px 32px;font-family:{SERIF};font-size:16px;font-style:italic;color:{APAGADO};">'
                      "Nenhum paper novo de programação apareceu desde a última edição. Até amanhã!</td></tr>")

    aviso_html = "".join(f"<br>⚠ {escape(a)}" for a in avisos)
    html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{escape(assunto)}</title>
<style>@media (max-width:520px){{.p{{padding-left:18px!important;padding-right:18px!important}}.nome{{font-size:40px!important}}.manchete{{font-size:25px!important}}}}</style></head>
<body style="margin:0;padding:0;background:{FUNDO};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(previa)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{FUNDO};"><tr><td align="center" style="padding:24px 10px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:660px;background:{PAPEL};border:1px solid {FIO};">
<tr><td class="p" style="padding:18px 32px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    <td style="font-family:{SANS};font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:{APAGADO};">{escape(data_extenso(data))}</td>
    <td align="right" style="white-space:nowrap;padding-left:12px;font-family:{SANS};font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:{APAGADO};">Edição nº {numero}</td>
  </tr></table>
</td></tr>
<tr><td class="p" align="center" style="padding:10px 32px 0;">
  <div style="border-top:4px solid {TINTA};"></div>
  <h1 class="nome" style="margin:14px 0 2px;font-family:{SERIF};font-size:52px;line-height:1;font-weight:bold;letter-spacing:-1px;color:{TINTA};">O Compilado</h1>
  <p style="margin:0 0 12px;font-family:{SERIF};font-size:15px;font-style:italic;color:{APAGADO};">Os papers de programação do dia, resumidos às 8h</p>
  <div style="border-top:1px solid {TINTA};padding-top:3px;"><div style="border-top:1px solid {TINTA};"></div></div>
  <p style="margin:8px 0 0;font-family:{SANS};font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:{APAGADO};">
    {total} papers nesta edição &nbsp;·&nbsp; {edicao['analisados']} analisados &nbsp;·&nbsp; arXiv + Hugging Face</p>
</td></tr>
{"".join(blocos)}
<tr><td class="p" style="padding:26px 32px 24px;">
  <div style="border-top:3px double {TINTA};padding-top:12px;font-family:{SANS};font-size:11px;line-height:1.6;color:{APAGADO};">
    Varredura às {hora} (horário de Brasília) no feed de anúncios do arXiv (cs.SE e cs.PL) e no Hugging Face Daily Papers.
    Os resumos são trechos dos abstracts escritos pelos próprios autores; a frase em itálico, quando aparece,
    é o resumo automático do Hugging Face.{aviso_html}
  </div>
</td></tr>
</table></td></tr></table>
</body></html>"""
    return assunto, html, _texto(edicao, numero, data, hora, avisos)


def _texto(edicao, numero, data, hora, avisos):
    linhas = [f"O COMPILADO · Edição nº {numero} · {data_extenso(data)}", "=" * 60, ""]

    def artigo(p, completo=False):
        linhas.extend([p["titulo"].upper(), _assinatura(p)])
        if p.get("tldr"):
            linhas.append(f"Em uma frase: {p['tldr']}")
        linhas.extend([p["resumo"] if completo else resumo.resumo(p["resumo"]), f"→ {p['link']}", ""])

    if edicao["manchete"]:
        linhas.extend(["MANCHETE", "-" * 60])
        artigo(edicao["manchete"], completo=True)
    for titulo, ps in [("EM ALTA NA COMUNIDADE", edicao["alta"])] + [(t.upper(), ps) for t, ps in edicao["secoes"]]:
        if ps:
            linhas.extend([titulo, "-" * 60])
            for p in ps:
                artigo(p)
    for titulo, ps in (("TAMBÉM NESTA EDIÇÃO", edicao["tambem"]), ("OS MAIS VOTADOS DA SEMANA", edicao["semana"])):
        if ps:
            linhas.extend([titulo, "-" * 60])
            linhas.extend(f"* {p['titulo']}\n  {p['link']}" for p in ps)
            linhas.append("")
    linhas.append(f"Varredura às {hora} (Brasília) · arXiv cs.SE/cs.PL + Hugging Face Daily Papers")
    linhas.extend(f"⚠ {a}" for a in avisos)
    return "\n".join(linhas)
