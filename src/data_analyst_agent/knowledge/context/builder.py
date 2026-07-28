def render_knowledge_context(hits) -> str:
    if not hits: return ""
    return "Relevant knowledge (cite these sources in the final answer):\n" + "\n".join(
        f"- [{hit.citation}; confidence={hit.score:.2f}] {hit.chunk.text}" for hit in hits
    )
