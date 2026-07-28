"""
Generate LangGraph architecture diagrams.

Outputs:
1. Mermaid (.mmd)
2. PNG (.png) if supported
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from data_analyst_agent.agent.graph import graph

OUTPUT_DIR = PROJECT_ROOT / "docs" / "diagrams"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_mermaid():
    """Save Mermaid diagram."""

    mermaid = graph.get_graph().draw_mermaid()

    file = OUTPUT_DIR / "agent_graph.mmd"

    file.write_text(mermaid)

    print(f"✅ Mermaid saved -> {file}")

    print("\n")
    print("=" * 80)
    print(mermaid)
    print("=" * 80)


def save_png():
    """Save PNG diagram."""

    try:
        png = graph.get_graph().draw_mermaid_png()

        file = OUTPUT_DIR / "agent_graph.png"

        with open(file, "wb") as f:
            f.write(png)

        print(f"✅ PNG saved -> {file}")

    except Exception as e:
        print("❌ PNG generation failed")
        print(e)


if __name__ == "__main__":

    print("\nGenerating Graph...\n")

    save_mermaid()

    save_png()

    print("\nDone.\n")
