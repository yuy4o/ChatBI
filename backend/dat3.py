from config.constants import CHROMA_PERSIST_DIR
import os

print(f"ChromaDB目录: {CHROMA_PERSIST_DIR}")
print(f"目录存在: {os.path.exists(CHROMA_PERSIST_DIR)}")
print(f"目录可写: {os.access(CHROMA_PERSIST_DIR, os.W_OK)}")
