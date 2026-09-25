import smtplib

from email.message import EmailMessage
from email.utils import (
    formataddr,
    parseaddr,
)

from app.core.config import settings


class EmailDeliveryError(
    RuntimeError
):
    """
    Safe, user-displayable email delivery error.

    Do not put passwords, raw SMTP responses containing
    secrets, or other sensitive configuration in messages.
    """


def _clean_header_value(
    value: object,
    field_name: str,
) -> str:

    cleaned = str(
        value or ""
    ).strip()

    if not cleaned:

        raise EmailDeliveryError(
            f"{field_name} is required."
        )

    if (
        "\r" in cleaned
        or "\n" in cleaned
    ):

        raise EmailDeliveryError(
            f"{field_name} contains invalid characters."
        )

    return cleaned


def _clean_recipient(
    value: object,
) -> str:

    recipient = _clean_header_value(
        value,
        "Email recipient",
    )

    _, parsed_address = parseaddr(
        recipient
    )

    if (
        not parsed_address
        or "@" not in parsed_address
    ):

        raise EmailDeliveryError(
            "Email recipient is invalid."
        )

    return parsed_address


def _get_from_email() -> str:

    candidate = (
        settings.SMTP_FROM_EMAIL
        or settings.SMTP_USERNAME
        or ""
    )

    sender = _clean_header_value(
        candidate,
        "SMTP sender email",
    )

    _, parsed_address = parseaddr(
        sender
    )

    if (
        not parsed_address
        or "@" not in parsed_address
    ):

        raise EmailDeliveryError(
            "SMTP sender email is invalid."
        )

    return parsed_address


def _validate_smtp_settings():

    if not settings.SMTP_HOST:

        raise EmailDeliveryError(
            "SMTP is not configured. "
            "Set SMTP_HOST in the backend .env file."
        )

    if settings.SMTP_PORT <= 0:

        raise EmailDeliveryError(
            "SMTP_PORT must be greater than zero."
        )

    if (
        settings.SMTP_USE_SSL
        and settings.SMTP_USE_TLS
    ):

        raise EmailDeliveryError(
            "Choose either SMTP_USE_SSL or "
            "SMTP_USE_TLS, not both."
        )

    if (
        settings.SMTP_USERNAME
        and not settings.SMTP_PASSWORD
    ):

        raise EmailDeliveryError(
            "SMTP_PASSWORD is required when "
            "SMTP_USERNAME is configured."
        )


def send_email_action(
    payload: dict,
) -> None:
    """
    Send one approved ContextForge email action.

    This function never decides whether an email is allowed
    to be sent. Approval/status authorization is enforced
    by the Actions API before this function is called.
    """

    _validate_smtp_settings()

    recipient = _clean_recipient(
        payload.get(
            "to"
        )
    )

    subject = _clean_header_value(
        payload.get(
            "subject"
        ),
        "Email subject",
    )

    body = str(
        payload.get(
            "body"
        )
        or ""
    ).strip()

    if not body:

        raise EmailDeliveryError(
            "Email body is required."
        )

    sender_email = (
        _get_from_email()
    )

    sender_name = str(
        settings.SMTP_FROM_NAME
        or "ContextForge"
    ).strip()

    if (
        "\r" in sender_name
        or "\n" in sender_name
    ):

        raise EmailDeliveryError(
            "SMTP_FROM_NAME contains "
            "invalid characters."
        )

    message = EmailMessage()

    message["From"] = formataddr(
        (
            sender_name,
            sender_email,
        )
    )

    message["To"] = recipient

    message["Subject"] = subject

    message.set_content(
        body
    )

    smtp_client = None

    try:

        if settings.SMTP_USE_SSL:

            smtp_client = (
                smtplib.SMTP_SSL(
                    host=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    timeout=(
                        settings
                        .SMTP_TIMEOUT_SECONDS
                    ),
                )
            )

        else:

            smtp_client = smtplib.SMTP(
                host=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                timeout=(
                    settings
                    .SMTP_TIMEOUT_SECONDS
                ),
            )

            smtp_client.ehlo()

            if settings.SMTP_USE_TLS:

                smtp_client.starttls()

                smtp_client.ehlo()

        if settings.SMTP_USERNAME:

            smtp_client.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD
                or "",
            )

        smtp_client.send_message(
            message
        )

    except smtplib.SMTPAuthenticationError as exc:

        raise EmailDeliveryError(
            "SMTP authentication failed. "
            "Check the configured email credentials."
        ) from exc

    except smtplib.SMTPRecipientsRefused as exc:

        raise EmailDeliveryError(
            "The SMTP server rejected the recipient."
        ) from exc

    except smtplib.SMTPSenderRefused as exc:

        raise EmailDeliveryError(
            "The SMTP server rejected the sender address."
        ) from exc

    except (
        smtplib.SMTPException,
        OSError,
        TimeoutError,
    ) as exc:

        raise EmailDeliveryError(
            "Email delivery failed. "
            "Check the SMTP configuration and provider."
        ) from exc

    finally:

        if smtp_client is not None:

            try:

                smtp_client.quit()

            except Exception:

                try:

                    smtp_client.close()

                except Exception:

                    pass
