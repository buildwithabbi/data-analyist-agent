"""Converts detailed executions into compact reusable memory content."""

from .models import EpisodeMemory


class MemoryCompressor:
    def compress_episode(self, memory: EpisodeMemory) -> str:
        tools = ", ".join(memory.metadata.tool_chain) or "no tools"
        summary = memory.summary or "Execution completed without a final narrative summary."
        return f"Query: {memory.user_query}\nTools: {tools}\nOutcome: {summary}"
