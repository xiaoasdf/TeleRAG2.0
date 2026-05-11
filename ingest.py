from __future__ import annotations

import argparse

from telerag.config import load_config
from telerag.ingestion.pipeline import IngestionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local TeleRAG vector index.")
    parser.add_argument("--docs", required=True, help="Path to a file or directory of documents.")
    parser.add_argument("--config", default="config.yaml", help="Path to TeleRAG config YAML.")
    args = parser.parse_args()

    config = load_config(args.config)
    pipeline = IngestionPipeline(config)
    stats = pipeline.run(args.docs)

    print(f"Indexed {stats.documents} documents into {stats.chunks} chunks.")
    print(f"Saved index to {stats.index_dir}")
    print(f"Elapsed: {stats.elapsed_seconds:.2f}s")


if __name__ == "__main__":
    main()
