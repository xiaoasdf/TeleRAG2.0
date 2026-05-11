from __future__ import annotations

import argparse

from telerag.pipeline import RAGPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the local TeleRAG index.")
    parser.add_argument("question", help="Question to answer from the indexed documents.")
    parser.add_argument("--config", default="config.yaml", help="Path to TeleRAG config YAML.")
    args = parser.parse_args()

    pipeline = RAGPipeline(args.config)
    result = pipeline.query(args.question)

    print("Answer:")
    print(result.answer)

    if result.thinking:
        print("\nThinking:")
        print(result.thinking)

    print("\nSources:")
    if not result.sources:
        print("- No sources")
        return

    for source in result.sources:
        location = f"{source.source} (page {source.page})" if source.page else source.source
        print(f"- {location} | {source.chunk_id} | score={source.score:.4f}")
        print(f"  {source.snippet}")


if __name__ == "__main__":
    main()
