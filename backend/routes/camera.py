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


def _rotate_jpeg(jpeg_bytes: bytes, degrees: int) -> bytes:
    """Rotate a JPEG by 90/180/270 degrees (clockwise). Returns re-encoded JPEG.

    Rotating here (not in the browser) keeps the detection input and the
    displayed image identical, so bounding boxes stay aligned.
    """
    import cv2
    import numpy as np

    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return jpeg_bytes  # not decodable — return original untouched

    rotations = {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }
    img = cv2.rotate(img, rotations[degrees])
    ok, out = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return out.tobytes() if ok else jpeg_bytes


@router.get("/camera/frame")
async def proxy_frame(
    url: str = Query(..., description="Full URL to the ESP32-CAM /capture endpoint"),
    rotate: int = Query(0, description="Rotate the frame clockwise: 0, 90, 180, or 270"),
):
    """Fetch one JPEG from the ESP32-CAM and return it to the browser.

    The frontend calls this instead of the camera directly, sidestepping
    the browser's cross-origin block on local-network addresses. Optionally
    rotates the frame so a sideways-mounted camera reads upright.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(400, "URL must start with http:// or https://")
    if rotate not in (0, 90, 180, 270):
        raise HTTPException(400, "rotate must be 0, 90, 180, or 270")

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

    content = resp.content
    if rotate:
        content = _rotate_jpeg(content, rotate)

    return Response(content=content, media_type="image/jpeg")


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
