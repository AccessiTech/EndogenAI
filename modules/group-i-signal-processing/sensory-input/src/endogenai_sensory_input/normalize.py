"""
Payload normalisation for the Sensory / Input Layer.

Normalisation is intentionally lightweight: the Sensory / Input Layer must NOT
assign semantic meaning (that is the job of the Perception Layer).  It only
ensures payloads are in a consistent, safe format before forwarding.
"""

from __future__ import annotations

import base64
from typing import Any

from endogenai_sensory_input.models import Modality


def normalize_payload(modality: Modality, payload: Any, encoding: str | None) -> Any:
    """
    Normalise a raw payload for a given modality.

    Rules
    -----
    * TEXT — coerce to ``str``; strip leading/trailing whitespace.
    * IMAGE — if bytes/bytearray, base64-encode and return the encoded string; if str, return
      as-is (assumed to be a URI or already-encoded value).  The caller is responsible for
      recording ``encoding="base64"`` on the emitted Signal when bytes were encoded.
    * AUDIO — same as IMAGE.
    * SENSOR — coerce dict to dict; non-dict values wrapped in ``{"value": payload}``.
    * API_EVENT — dict passed through; non-dict coerced to ``{"value": payload}``.
    * INTERNAL / CONTROL — passed through unchanged.

    Parameters
    ----------
    modality:
        The modality determines which normalisation path to apply.
    payload:
        The raw value from the external source.
    encoding:
        Optional encoding hint (e.g. ``"base64"``, ``"utf-8"``).

    Returns
    -------
    Any
        The normalised payload.
    """
    match modality:
        case Modality.TEXT:
            return str(payload).strip()

        case Modality.IMAGE | Modality.AUDIO:
            if isinstance(payload, (bytes, bytearray)):
                return base64.b64encode(payload).decode("ascii")
            return payload

        case Modality.SENSOR:
            if isinstance(payload, dict):
                return payload
            return {"value": payload}

        case Modality.API_EVENT:
            if isinstance(payload, dict):
                return payload
            return {"value": payload}

        case _:
            return payload
