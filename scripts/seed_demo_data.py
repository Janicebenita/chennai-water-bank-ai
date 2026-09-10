"""Seed demo nodes into the selected repository backend."""

from src.persistence.repository import get_repository
from src.persistence.memory_repository import MemoryRepository


def main() -> None:
    source = MemoryRepository.from_demo_data()
    target = get_repository()
    target.save_nodes(source.list_nodes())
    print(f"Seeded {len(source.list_nodes())} demonstration nodes into {target.backend_name}.")


if __name__ == "__main__":
    main()

