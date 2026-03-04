"""Reepo taxonomy — category classification for AI repositories."""

CATEGORIES = {
    "frameworks": {
        "name": "Frameworks",
        "keywords": [
            "framework", "training", "fine-tune", "fine-tuning", "finetuning",
            "distributed training", "model training", "ml framework",
            "deep learning framework", "neural network framework",
        ],
        "topics": [
            "pytorch", "tensorflow", "jax", "keras", "mxnet", "paddle",
            "caffe", "caffe2", "theano", "deeplearning4j", "flux",
            "machine-learning-framework", "dl-framework",
        ],
        "name_patterns": [
            "torch", "flow", "keras", "jax",
        ],
    },
    "apis-sdks": {
        "name": "APIs & SDKs",
        "keywords": [
            "api client", "sdk", "api wrapper", "client library",
            "api integration", "rest api", "openai api", "anthropic api",
            "cloud api", "api sdk",
        ],
        "topics": [
            "openai", "anthropic", "sdk", "api-client", "api-wrapper",
            "google-ai", "azure-ai", "aws-ai", "cohere", "mistral",
        ],
        "name_patterns": [
            "openai-", "-sdk", "-client", "-api",
        ],
    },
    "agents": {
        "name": "Agents",
        "keywords": [
            "agent", "autonomous agent", "ai agent", "multi-agent",
            "agent framework", "agent orchestration", "tool use",
            "function calling", "agent swarm", "agentic",
        ],
        "topics": [
            "agents", "ai-agents", "autonomous-agents", "multi-agent",
            "agent-framework", "langchain", "langgraph", "crewai",
            "autogen", "autogpt",
        ],
        "name_patterns": [
            "agent", "crew", "swarm",
        ],
    },
    "apps": {
        "name": "Apps",
        "keywords": [
            "web app", "application", "chat ui", "chatbot", "web ui",
            "desktop app", "user interface", "frontend", "gradio app",
            "streamlit app", "demo app",
        ],
        "topics": [
            "chatbot", "chat-ui", "web-app", "gradio", "streamlit",
            "stable-diffusion-webui", "text-generation-webui",
            "desktop-app", "gui",
        ],
        "name_patterns": [
            "webui", "web-ui", "chat", "app", "ui",
        ],
    },
    "tools-utilities": {
        "name": "Tools & Utilities",
        "keywords": [
            "cli tool", "utility", "developer tool", "dev tool",
            "command line", "helper", "toolkit", "toolchain",
            "evaluation", "benchmarking", "monitoring",
        ],
        "topics": [
            "cli", "developer-tools", "devtools", "evaluation",
            "benchmark", "monitoring", "profiling", "debugging",
            "visualization", "notebook",
        ],
        "name_patterns": [
            "tool", "util", "bench", "eval",
        ],
    },
    "models": {
        "name": "Models",
        "keywords": [
            "pre-trained model", "model weights", "model hub",
            "model serving", "model zoo", "checkpoint", "gguf", "ggml",
            "quantized model", "model card",
        ],
        "topics": [
            "pretrained-models", "model-hub", "huggingface",
            "model-serving", "model-zoo", "gguf", "ggml",
            "stable-diffusion", "llama", "mistral-ai",
        ],
        "name_patterns": [
            "model", "llama", "mistral", "falcon", "phi-",
        ],
    },
    "datasets": {
        "name": "Datasets",
        "keywords": [
            "dataset", "data loader", "benchmark dataset", "corpus",
            "data processing", "data pipeline", "data annotation",
            "labeling", "synthetic data",
        ],
        "topics": [
            "dataset", "datasets", "data-processing", "annotation",
            "labeling", "synthetic-data", "data-augmentation",
            "benchmark-dataset", "corpus",
        ],
        "name_patterns": [
            "dataset", "data-", "corpus",
        ],
    },
    "infrastructure": {
        "name": "Infrastructure",
        "keywords": [
            "mlops", "deployment", "infrastructure", "serving",
            "orchestration", "pipeline", "kubernetes", "docker",
            "model deployment", "inference server", "gpu",
            "distributed computing", "cluster",
        ],
        "topics": [
            "mlops", "deployment", "kubernetes", "docker",
            "inference", "serving", "ray", "kubeflow",
            "ml-pipeline", "model-deployment", "gpu",
        ],
        "name_patterns": [
            "deploy", "serve", "infra", "kube", "mlops",
        ],
    },
    "skills-plugins": {
        "name": "Skills & Plugins",
        "keywords": [
            "plugin", "extension", "integration", "connector",
            "skill", "add-on", "middleware", "adapter",
            "chatgpt plugin", "langchain tool",
        ],
        "topics": [
            "plugin", "extension", "integration", "connector",
            "chatgpt-plugin", "langchain-tools", "middleware",
            "adapter", "add-on",
        ],
        "name_patterns": [
            "plugin", "extension", "connector", "adapter",
        ],
    },
    "libraries": {
        "name": "Libraries",
        "keywords": [
            "library", "embedding", "vector", "tokenizer", "nlp",
            "computer vision", "text processing", "image processing",
            "rag", "retrieval", "search", "similarity",
        ],
        "topics": [
            "nlp", "computer-vision", "embedding", "vector-database",
            "rag", "retrieval-augmented-generation", "transformers",
            "tokenizer", "text-processing", "image-processing",
            "vector-search", "similarity",
        ],
        "name_patterns": [
            "lib", "embed", "vector", "token",
        ],
    },
}


def classify_repo(
    name: str,
    description: str,
    topics: list[str],
    readme_excerpt: str = "",
) -> tuple[str, list[str]]:
    """Classify a repo into primary and secondary categories.

    Returns (primary_category_slug, [secondary_category_slugs]).
    """
    description = (description or "").lower()
    name = (name or "").lower()
    readme_excerpt = (readme_excerpt or "").lower()
    topics_lower = [t.lower() for t in (topics or [])]
    text = f"{name} {description} {readme_excerpt}"

    scores: dict[str, float] = {}

    for slug, cat in CATEGORIES.items():
        score = 0.0

        for topic in cat["topics"]:
            if topic in topics_lower:
                score += 3.0

        for kw in cat["keywords"]:
            if kw in description:
                score += 2.0
            if kw in readme_excerpt:
                score += 1.0

        for pat in cat["name_patterns"]:
            if pat in name:
                score += 2.5

        if score > 0:
            scores[slug] = score

    if not scores:
        return "libraries", []

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0][0]
    threshold = ranked[0][1] * 0.4
    secondary = [s for s, v in ranked[1:] if v >= threshold]

    return primary, secondary
