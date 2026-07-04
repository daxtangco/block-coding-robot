"""Camera proxy route.

The browser cannot fetch directly from the ESP32-CAM due to cross-origin
restrictions. This route proxies a single JPEG frame from any camera URL
(ESP32-CAM /capture endpoint) so the frontend can use it like a webcam frame.
"""

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter()

_client = httpx.AsyncClient(timeout=3.0)


@router.get("/camera/frame")
async def proxy_frame(url: str = Query(..., description="Full URL to the ESP32-CAM /capture endpoint")):
    """Fetch one JPEG from the ESP32-CAM and return it to the browser.

    The frontend calls this instead of the camera directly, sidestepping
    the browser's cross-origin block on local-network addresses.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(400, "URL must start with http:// or https://")

    try:
        resp = await _client.get(url)
    except httpx.TimeoutException:
        raise HTTPException(504, "ESP32-CAM did not respond in time — check IP and power")
    except httpx.RequestError as e:
        raise HTTPException(502, f"Could not reach ESP32-CAM: {e}")

    if resp.status_code != 200:
        raise HTTPException(502, f"ESP32-CAM returned {resp.status_code}")

    content_type = resp.headers.get("content-type", "image/jpeg")
    if "image" not in content_type:
        raise HTTPException(502, "ESP32-CAM did not return an image")

    return Response(content=resp.content, media_type="image/jpeg")


@router.get("/camera/ping")
async def ping_camera(url: str = Query(..., description="Base URL of the ESP32-CAM, e.g. http://192.168.4.2")):
    """Check whether an ESP32-CAM is reachable at the given base URL."""
    capture_url = url.rstrip("/") + "/capture"
    try:
        resp = await _client.get(capture_url)
        ok = resp.status_code == 200 and "image" in resp.headers.get("content-type", "")
        return {"reachable": ok, "url": capture_url}
    except Exception:
        return {"reachable": False, "url": capture_url}
