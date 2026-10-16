"""Envio por SMTP. Padrão é o Gmail com senha de app; outro provedor é só mudar SMTP_HOST/SMTP_PORT."""
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid


def envia(assunto, html, texto):
    usuario = os.environ["SMTP_USER"]
    senha = os.environ["SMTP_PASSWORD"]
    destino = os.environ.get("EMAIL_TO") or usuario
    host = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
    porta = int(os.environ.get("SMTP_PORT") or 465)

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = formataddr(("O Compilado", usuario))
    msg["To"] = destino
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=usuario.split("@")[-1])
    msg.set_content(texto)
    msg.add_alternative(html, subtype="html")

    for tentativa in range(3):
        try:
            if porta == 465:
                with smtplib.SMTP_SSL(host, porta, context=ssl.create_default_context(), timeout=60) as s:
                    s.login(usuario, senha)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(host, porta, timeout=60) as s:
                    s.starttls(context=ssl.create_default_context())
                    s.login(usuario, senha)
                    s.send_message(msg)
            return destino
        except smtplib.SMTPAuthenticationError:
            raise  # senha errada não melhora tentando de novo
        except (smtplib.SMTPException, OSError):
            if tentativa == 2:
                raise
            time.sleep(20)
