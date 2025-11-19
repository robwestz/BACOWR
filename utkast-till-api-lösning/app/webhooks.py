
import hmac, hashlib, base64, json, httpx
from typing import Optional

async def post_with_signature(url: str, payload: dict, secret: Optional[str] = None):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if secret:
        sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
        headers["X-Signature"] = base64.b64encode(sig).decode("utf-8")
    async with httpx.AsyncClient() as client:
        r = await client.post(url, content=body, headers=headers, timeout=20.0)
        r.raise_for_status()
        return r
