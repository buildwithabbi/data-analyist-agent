"""Unit tests for Multi-Modal AI Vision Engine."""

import io
from PIL import Image
from data_analyst_agent.vision.analyzer import ImageProcessor, VisionAnalyzer


def _create_sample_image_bytes():
    img = Image.new("RGB", (200, 100), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_processor_encoding_and_inspection():
    raw = _create_sample_image_bytes()
    b64 = ImageProcessor.encode_image(raw)
    assert len(b64) > 0

    meta = ImageProcessor.inspect_image(raw)
    assert meta["width"] == 200
    assert meta["height"] == 100
    assert meta["aspect_ratio"] == 2.0
    assert meta["format"] == "PNG"


def test_vision_analyzer_chart_processing():
    raw = _create_sample_image_bytes()
    res = VisionAnalyzer.analyze_chart_or_spreadsheet(raw, filename="test_chart.png")
    assert res["status"] == "success"
    assert res["filename"] == "test_chart.png"
    assert "data_url_preview" in res
    assert res["metadata"]["width"] == 200
