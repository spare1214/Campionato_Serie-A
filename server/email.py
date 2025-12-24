import os
import smtplib
from email.message import EmailMessage


def send_delete_team_email(team_name: str, team_id: int) -> None:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    sender = os.getenv("SMTP_SENDER")
    password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("SMTP_RECIPIENT")

    # DEBUG (you can remove later)
    print("SMTP_SENDER =", sender)
    print("SMTP_RECIPIENT =", recipient)
    print("SMTP_PASSWORD set? =", bool(password))

    # Fail-safe: if not configured, do nothing
    if not sender or not password or not recipient:
        print("EMAIL SKIPPED: SMTP variables not set")
        return

    msg = EmailMessage()
    msg["Subject"] = f"[Serie A] Squadra eliminata: {team_name} (ID {team_id})"
    msg["From"] = sender
    msg["To"] = recipient

    msg.set_content(
        f"La squadra '{team_name}' (ID {team_id}) è stata eliminata dal sistema.\n"
        f"I giocatori associati sono stati svincolati (id_squadra = NULL).\n"
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

    print("EMAIL SENT SUCCESSFULLY")
