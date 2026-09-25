import json
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.request import (
    Request,
    urlopen,
)

from app.core.config import settings


class N8NExecutionError(Exception):
    """Safe exception for n8n execution failures."""



def _require_n8n_config() -> tuple[str, str, int]:
    webhook_url = str(
        settings.N8N_ACTION_WEBHOOK_URL or ""
    ).strip()

    secret = str(
        settings.N8N_WEBHOOK_SECRET or ""
    ).strip()

    timeout = int(
        settings.N8N_TIMEOUT_SECONDS
    )

    if not webhook_url:
        raise N8NExecutionError(
            "n8n is not configured. Set N8N_ACTION_WEBHOOK_URL in the backend .env file."
        )

    if not secret:
        raise N8NExecutionError(
            "n8n webhook authentication is not configured. Set N8N_WEBHOOK_SECRET in the backend .env file."
        )

    if timeout <= 0:
        timeout = 30

    return webhook_url, secret, timeout



def execute_n8n_action(
    *,
    action_id: int,
    action_type: str,
    user_id: int,
    payload: dict,
) -> dict:
    """
    Execute one already-approved ContextForge action through n8n.

    Security boundary:
    - This function does not decide whether an action is approved.
    - The API route must enforce ownership + approved status first.
    - A shared secret is sent in X-ContextForge-Secret.
    """

    webhook_url, secret, timeout = (
        _require_n8n_config()
    )

    request_body = {
        "action_id": action_id,
        "action_type": action_type,
        "user_id": user_id,
        "payload": payload,
    }

    encoded_body = json.dumps(
        request_body
    ).encode("utf-8")

    request = Request(
        webhook_url,
        data=encoded_body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-ContextForge-Secret": secret,
        },
    )

    try:
        with urlopen(
            request,
            timeout=timeout,
        ) as response:
            status_code = response.getcode()
            raw_body = response.read().decode(
                "utf-8",
                errors="replace",
            )

    except HTTPError as exc:
        # Keep provider internals/HTML out of the frontend.
        raise N8NExecutionError(
            f"n8n returned HTTP {exc.code}."
        ) from exc

    except URLError as exc:
        raise N8NExecutionError(
            "Could not connect to the n8n automation service."
        ) from exc

    except TimeoutError as exc:
        raise N8NExecutionError(
            "The n8n automation request timed out."
        ) from exc

    if status_code < 200 or status_code >= 300:
        raise N8NExecutionError(
            f"n8n returned HTTP {status_code}."
        )

    if not raw_body.strip():
        raise N8NExecutionError(
            "n8n returned an empty response."
        )

    try:
        result = json.loads(
            raw_body
        )
    except json.JSONDecodeError as exc:
        raise N8NExecutionError(
            "n8n returned an invalid response."
        ) from exc

    if not isinstance(result, dict):
        raise N8NExecutionError(
            "n8n returned an invalid response object."
        )

    return result
