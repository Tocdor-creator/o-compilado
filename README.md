# O Compilado

Um jornal diário de papers sobre programação que chega no meu e-mail. Todo dia às 08:00 (horário de Brasília) ele varre o que saiu de novo, escolhe os principais, resume cada um e manda tudo com cara de jornal, com manchete, seções e link pra cada paper. O e-mail chega por volta das 08:01.

## De onde vêm os papers

- **arXiv**: o feed de anúncios do dia de **cs.SE** (Engenharia de Software) e **cs.PL** (Linguagens de Programação), incluindo os papers de outras áreas listados nessas categorias.
- **Hugging Face Daily Papers**: a lista que a comunidade vota todo dia. Daqui só entra o que é claramente sobre programação: o assunto tem que estar no título, ou dominar o abstract. Paper de LLM que cita "code reasoning" de passagem fica de fora.

## Como escolhe os principais

Paper recém-saído ainda não tem citação, então a nota usa o que dá pra saber no dia:

- **o quanto é sobre programação**: termos como *code generation*, *program repair*, *compiler*, *fuzzing*, *SWE-bench*... Os que aparecem no título valem o dobro;
- **votos no Hugging Face**: é o melhor sinal de "todo mundo está falando disso";
- **código publicado** (link de GitHub/GitLab) e **já aceito** em conferência ou revista.

Com isso o jornal sai assim:

| Seção | O que entra |
|---|---|
| **Manchete** | O mais votado do dia (se tiver 10+ votos); senão, a maior nota do arXiv. Vem com o abstract inteiro. |
| **Em alta na comunidade** | Os mais votados no Hugging Face. |
| **IA aplicada ao código**, **Engenharia de Software**, **Linguagens & Compiladores** | Os melhores do arXiv em cada área. |
| **Também nesta edição** | Mais 8, só com título, uma linha e link. |
| **Os mais votados da semana** | Só em dia fraco (fim de semana, feriado), quando não há 5 destaques novos. |

Nenhum paper aparece duas vezes: o que já saiu numa edição fica registrado em `dados/estado.json`.

## Como resume (sem IA)

O resumo sai do próprio abstract. Abstract de paper é bem previsível, então dá pra achar com expressões regulares as frases que dizem **o que o paper faz** ("We propose...", "In this paper...") e **o que ele encontrou** ("Results show...", números, "outperforms..."), e juntar com a frase de contexto. Quando o Hugging Face tem o resumo automático de uma frase do paper, ele aparece em itálico logo abaixo do título.

Os textos ficam em inglês, como os autores escreveram. Não é preciso nenhuma chave de API paga.

## Onde roda

No **GitHub Actions**, de graça, sem depender do PC ou do celular estarem ligados. O cron do GitHub pode atrasar, então o workflow dispara às 07:45, o script espera até 08:00 em ponto e só então faz a varredura. Às 08:05 e 08:20 rodam agendamentos reserva, que só fazem alguma coisa se a edição do dia ainda não saiu. Depois de enviar, o workflow faz commit do estado e de uma cópia da edição em `edicoes/AAAA-MM-DD.html`, que acaba virando o arquivo do jornal.

Se as duas fontes estiverem fora do ar, o workflow falha e o GitHub avisa por e-mail. Se só uma cair, a edição sai com a outra e um aviso no rodapé.

### Configuração (uma vez só)

1. **Senha de app do Gmail**: com a verificação em duas etapas ligada, crie uma em <https://myaccount.google.com/apppasswords>. Ela é diferente da senha normal da conta.
2. **Repositório privado no GitHub** com este código.
3. Em *Settings → Secrets and variables → Actions*, crie três secrets:

   | Secret | Valor |
   |---|---|
   | `SMTP_USER` | o Gmail que envia, ex.: `voce@gmail.com` |
   | `SMTP_PASSWORD` | a senha de app de 16 letras |
   | `EMAIL_TO` | quem recebe (pode ser o mesmo Gmail) |

4. Pra testar, vá em *Actions → Edição diária → Run workflow*. O e-mail chega em um ou dois minutos.

Pra receber de novo uma edição que já saiu (trocou de e-mail, apagou sem querer), use o mesmo *Run workflow* e preencha **reenviar** com a data (`2026-10-16`). Ela sai idêntica à arquivada em `edicoes/`, sem contar como edição nova.

Pra mandar por outro provedor, crie também `SMTP_HOST` e `SMTP_PORT` e passe os dois no `env` do workflow.

## Rodando no PC

```bash
python edicao.py --previa previa.html
```

Gera a edição de hoje num HTML local sem enviar nada e sem mexer no estado. Só usa a biblioteca padrão do Python, sem `pip install`.

```bash
python -m unittest discover -s tests -t .
```

## Organização

```
o-compilado/
├── edicao.py               # ponto de entrada: coleta → escolhe → monta → envia
├── compilado/
│   ├── config.py           # categorias, limites por seção, horários
│   ├── fontes.py           # arXiv (feed Atom) e Hugging Face (API Daily Papers)
│   ├── ranking.py          # relevância, nota e montagem das seções
│   ├── resumo.py           # resumo extraído do abstract
│   ├── jornal.py           # HTML do e-mail (estilo jornal) + versão texto
│   ├── envio.py            # SMTP
│   └── estado.py           # o que já foi enviado
├── dados/estado.json       # criado pelo workflow
├── edicoes/                # uma cópia de cada edição enviada
└── .github/workflows/edicao.yml
```
