"""
Multi-Modal AI Vision Engine
Handles image input processing (.png, .jpg, .jpeg, .pdf scans),
base64 encoding, table extraction from screenshots, and visual chart analysis.
"""

import base64
import io
import json
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
        cls, image_bytes: bytes, filename: str = "chart.png", prompt: str = "Extract key metrics and data tables", model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze an uploaded screenshot or chart image using Groq Cloud or local Ollama."""
        meta = ImageProcessor.inspect_image(image_bytes)
        if "error" in meta:
            return {"status": "error", "message": meta["error"]}

        b64_data = ImageProcessor.encode_image(image_bytes)
        mime_fmt = meta.get('format', 'png').lower()
        if mime_fmt == "jpg":
            mime_fmt = "jpeg"
        data_url = f"data:image/{mime_fmt};base64,{b64_data}"

        # 1. Try Groq Cloud Vision first (zero local RAM usage)
        groq_res = GroqVisionProvider.analyze_image_with_groq(data_url, prompt=prompt)
        if groq_res.get("status") == "success":
            return {
                "status": "success",
                "filename": filename,
                "metadata": meta,
                "data_url_preview": data_url[:50] + "...",
                "extracted_insight": groq_res.get("analysis", ""),
                "provider_info": groq_res,
            }

        # 2. Fallback to local Ollama (llava)
        ollama_model = model or OllamaVisionProvider.DEFAULT_MODEL
        ollama_res = OllamaVisionProvider.analyze_image_with_ollama(b64_data, prompt=prompt, model=ollama_model)

        if ollama_res.get("status") == "success":
            insight = ollama_res.get("analysis", "")
        else:
            insight = (
                f"Multi-modal vision processed `{filename}` ({meta['width']}x{meta['height']}px, {meta['size_kb']} KB). "
                f"Groq Vision note: {groq_res.get('error', 'N/A')}. "
                f"Ollama status: {ollama_res.get('error', 'Ollama offline')}."
            )

        return {
            "status": "success",
            "filename": filename,
            "metadata": meta,
            "data_url_preview": data_url[:50] + "...",
            "extracted_insight": insight,
            "provider_info": ollama_res,
        }


class GroqVisionProvider:
    """Groq Cloud Vision provider (llama-3.2-11b-vision-preview / llama-3.2-90b-vision-preview)."""

    DEFAULT_MODEL = "llama-3.2-11b-vision-preview"

    @classmethod
    def analyze_image_with_groq(
        cls, data_url: str, prompt: str = "Extract tabular data and key metrics from this image", model: str = DEFAULT_MODEL
    ) -> Dict[str, Any]:
        """Calls Groq Cloud vision endpoint with base64 image data URL."""
        try:
            from ..core.config import GROQ_API_KEY
            if not GROQ_API_KEY:
                return {"status": "error", "provider": "Groq", "error": "GROQ_API_KEY not configured in environment."}

            from langchain_groq import ChatGroq
            from langchain_core.messages import HumanMessage

            groq_llm = ChatGroq(
                model=model,
                api_key=GROQ_API_KEY,
                temperature=0,
                max_tokens=512,
            )
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]
            )
            response = groq_llm.invoke([message])
            return {
                "status": "success",
                "provider": "Groq Cloud",
                "model": model,
                "analysis": str(response.content),
            }
        except Exception as err:
            return {
                "status": "error",
                "provider": "Groq Cloud",
                "model": model,
                "error": f"Groq Vision error: {err}",
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

