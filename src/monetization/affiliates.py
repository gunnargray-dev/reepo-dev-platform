"""Reepo affiliate links — map repos to hosted/cloud versions with click tracking."""
from __future__ import annotations

from src.db import _connect, DEFAULT_DB_PATH


KNOWN_AFFILIATES = [
    {"owner": "supabase", "name": "supabase", "provider": "Supabase", "url": "https://supabase.com", "description": "Try Supabase Cloud"},
    {"owner": "vercel", "name": "next.js", "provider": "Vercel", "url": "https://vercel.com", "description": "Deploy on Vercel"},
    {"owner": "replicate", "name": "replicate", "provider": "Replicate", "url": "https://replicate.com", "description": "Run on Replicate"},
    {"owner": "chroma-core", "name": "chroma", "provider": "Chroma Cloud", "url": "https://trychroma.com", "description": "Try Chroma Cloud"},
    {"owner": "qdrant", "name": "qdrant", "provider": "Qdrant Cloud", "url": "https://cloud.qdrant.io", "description": "Try Qdrant Cloud"},
    {"owner": "milvus-io", "name": "milvus", "provider": "Zilliz Cloud", "url": "https://cloud.zilliz.com", "description": "Try Zilliz Cloud"},
    {"owner": "streamlit", "name": "streamlit", "provider": "Streamlit Cloud", "url": "https://streamlit.io/cloud", "description": "Deploy on Streamlit Cloud"},
    {"owner": "gradio-app", "name": "gradio", "provider": "Hugging Face Spaces", "url": "https://huggingface.co/spaces", "description": "Deploy on HF Spaces"},
    {"owner": "mlflow", "name": "mlflow", "provider": "Databricks", "url": "https://databricks.com/product/managed-mlflow", "description": "Try Managed MLflow"},
    {"owner": "wandb", "name": "wandb", "provider": "Weights & Biases", "url": "https://wandb.ai", "description": "Try W&B Cloud"},
    {"owner": "langgenius", "name": "dify", "provider": "Dify Cloud", "url": "https://dify.ai", "description": "Try Dify Cloud"},
    {"owner": "ollama", "name": "ollama", "provider": "Ollama", "url": "https://ollama.com", "description": "Download Ollama"},
]


def seed_affiliate_links(path: str = DEFAULT_DB_PATH) -> int:
    """Seed affiliate links for known repos. Returns count created."""
    conn = _connect(path)
    count = 0
    for aff in KNOWN_AFFILIATES:
        repo = conn.execute(
            "SELECT id FROM repos WHERE owner = ? AND name = ?",
            (aff["owner"], aff["name"]),
        ).fetchone()
        if not repo:
            continue
        existing = conn.execute(
            "SELECT id FROM affiliate_links WHERE repo_id = ? AND provider = ?",
            (repo["id"], aff["provider"]),
        ).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO affiliate_links (repo_id, provider, url) VALUES (?, ?, ?)",
            (repo["id"], aff["provider"], aff["url"]),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def get_affiliate_link(repo_id: int, path: str = DEFAULT_DB_PATH) -> dict | None:
    """Get the affiliate link for a repo, if one exists."""
    conn = _connect(path)
    try:
        row = conn.execute(
            "SELECT * FROM affiliate_links WHERE repo_id = ? LIMIT 1",
            (repo_id,),
        ).fetchone()
    except Exception:
        conn.close()
        return None
    conn.close()
    if not row:
        return None
    return dict(row)


def get_affiliate_link_by_repo(
    owner: str, name: str, path: str = DEFAULT_DB_PATH
) -> dict | None:
    """Get the affiliate link for a repo by owner/name."""
    conn = _connect(path)
    row = conn.execute(
        "SELECT al.* FROM affiliate_links al "
        "JOIN repos r ON al.repo_id = r.id "
        "WHERE r.owner = ? AND r.name = ?",
        (owner, name),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def record_affiliate_click(link_id: int, path: str = DEFAULT_DB_PATH) -> None:
    """Increment click count for an affiliate link."""
    conn = _connect(path)
    conn.execute(
        "UPDATE affiliate_links SET click_count = click_count + 1 WHERE id = ?",
        (link_id,),
    )
    conn.commit()
    conn.close()
