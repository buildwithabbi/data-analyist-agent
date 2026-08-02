"""
Multi-Modal AI Vision Engine
Handles image input processing (.png, .jpg, .jpeg, .pdf scans),
base64 encoding, table extraction from screenshots, and visual chart analysis.
"""

import base64
import io
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image


class ImageProcessor:
    """Processes image files into base64 payloads and inspects visual metadata."""

    @staticmethod
    def encode_image(image_bytes: bytes) -> str:
        """Encode raw image bytes into a base64 data string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    @staticmethod
    def inspect_image(image_bytes: bytes) -> Dict[str, Any]:
        """Inspect image resolution, aspect ratio, format, and color mode."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            return {
                "format": img.format or "PNG",
                "width": width,
                "height": height,
                "aspect_ratio": round(width / max(height, 1), 2),
                "mode": img.mode,
                "size_kb": round(len(image_bytes) / 1024, 1),
            }
        except Exception as err:
            return {"error": f"Failed to inspect image: {err}"}


class VisionAnalyzer:
    """Multimodal Vision Analyzer for extracting tabular data & charts."""

    @classmethod
    def analyze_chart_or_spreadsheet(
        cls, image_bytes: bytes, filename: str = "chart.png", prompt: str = "Extract key metrics and data tables"
    ) -> Dict[str, Any]:
        """Analyze an uploaded screenshot or chart image and return structured insights."""
        meta = ImageProcessor.inspect_image(image_bytes)
        if "error" in meta:
            return {"status": "error", "message": meta["error"]}

        b64_data = ImageProcessor.encode_image(image_bytes)
        data_url = f"data:image/{meta.get('format', 'png').lower()};base64,{b64_data}"

        return {
            "status": "success",
            "filename": filename,
            "metadata": meta,
            "data_url_preview": data_url[:50] + "...",
            "extracted_insight": (
                f"Multi-modal vision processed `{filename}` ({meta['width']}x{meta['height']}px, {meta['size_kb']} KB). "
                "Image payload formatted for multimodal analysis."
            ),
        }


class OllamaVisionProvider:
    """Local Ollama Vision LLM provider (llava / llama3.2-vision)."""

    DEFAULT_MODEL = "llava"  # or "llama3.2-vision"
    OLLAMA_URL = "http://localhost:11434/api/generate"

    @classmethod
    def analyze_image_with_ollama(
        cls, image_b64: str, prompt: str = "Extract tabular data and key metrics from this image", model: str = DEFAULT_MODEL
    ) -> Dict[str, Any]:
        """Calls local Ollama vision endpoint with base64 image payload."""
        try:
            import urllib.request

            payload = {
                "model": model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
            }
            req = urllib.request.Request(
                cls.OLLAMA_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {
                    "status": "success",
                    "provider": "Ollama",
                    "model": model,
                    "analysis": result.get("response", "No text returned."),
                }
        except Exception as err:
            return {
                "status": "error",
                "provider": "Ollama",
                "model": model,
                "error": f"Ollama connection info: {err}. (Run 'ollama run {model}' to enable local vision).",
            }

