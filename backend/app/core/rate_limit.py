"""
Rate limiting via slowapi (in-memory by default).

In-memory storage is fine for local development and a single backend
process. If you deploy multiple backend workers/instances, point slowapi
at a shared store (e.g. Redis) instead -- see slowapi's docs for the
`storage_uri` option; no route code needs to change.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)