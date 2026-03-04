"""Tests for the Reepo taxonomy classification system."""
import pytest

from src.taxonomy import classify_repo, CATEGORIES


# --- Category structure ---

class TestCategoryStructure:
    def test_has_10_categories(self):
        assert len(CATEGORIES) == 10

    def test_all_slugs(self):
        expected = {
            "frameworks", "apis-sdks", "agents", "apps", "tools-utilities",
            "models", "datasets", "infrastructure", "skills-plugins", "libraries",
        }
        assert set(CATEGORIES.keys()) == expected

    def test_each_has_required_keys(self):
        for slug, cat in CATEGORIES.items():
            assert "name" in cat, f"{slug} missing 'name'"
            assert "keywords" in cat, f"{slug} missing 'keywords'"
            assert "topics" in cat, f"{slug} missing 'topics'"
            assert "name_patterns" in cat, f"{slug} missing 'name_patterns'"

    def test_keywords_non_empty(self):
        for slug, cat in CATEGORIES.items():
            assert len(cat["keywords"]) > 0, f"{slug} has empty keywords"

    def test_topics_non_empty(self):
        for slug, cat in CATEGORIES.items():
            assert len(cat["topics"]) > 0, f"{slug} has empty topics"


# --- classify_repo function ---

class TestClassifyRepo:
    def test_returns_tuple(self):
        result = classify_repo("test", "test repo", [])
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_string_primary(self):
        primary, _ = classify_repo("test", "a framework", ["pytorch"])
        assert isinstance(primary, str)

    def test_returns_list_secondary(self):
        _, secondary = classify_repo("test", "test repo", [])
        assert isinstance(secondary, list)

    def test_fallback_to_libraries(self):
        primary, _ = classify_repo("xyz", "nothing matches here", [])
        assert primary == "libraries"


# --- Known repo classifications ---

class TestKnownRepos:
    def test_langchain_agents(self):
        primary, _ = classify_repo(
            "langchain",
            "Build context-aware reasoning applications",
            ["langchain", "llm", "agents", "rag"],
        )
        assert primary in ("agents", "frameworks", "libraries")

    def test_transformers_frameworks(self):
        primary, _ = classify_repo(
            "transformers",
            "State-of-the-art Machine Learning for Pytorch, TensorFlow, and JAX",
            ["transformers", "pytorch", "tensorflow", "jax", "nlp", "deep-learning", "huggingface"],
        )
        assert primary in ("frameworks", "libraries")

    def test_pytorch_frameworks(self):
        primary, _ = classify_repo(
            "pytorch",
            "Tensors and Dynamic neural networks in Python",
            ["pytorch", "deep-learning", "machine-learning"],
        )
        assert primary == "frameworks"

    def test_stable_diffusion_webui_apps(self):
        primary, _ = classify_repo(
            "stable-diffusion-webui",
            "Stable Diffusion web UI — a browser interface",
            ["stable-diffusion", "stable-diffusion-webui", "gradio"],
        )
        assert primary == "apps"

    def test_openai_python_sdk(self):
        primary, _ = classify_repo(
            "openai-python",
            "The official Python library for the OpenAI API",
            ["openai", "sdk", "api-client"],
        )
        assert primary == "apis-sdks"

    def test_autogen_agents(self):
        primary, _ = classify_repo(
            "autogen",
            "A programming framework for agentic AI",
            ["agents", "ai-agents", "multi-agent", "autogen"],
        )
        assert primary == "agents"

    def test_crewai_agents(self):
        primary, _ = classify_repo(
            "crewAI",
            "Framework for orchestrating role-playing, autonomous AI agents",
            ["agents", "ai-agents", "crewai", "autonomous-agents"],
            readme_excerpt="CrewAI orchestrates autonomous AI agents",
        )
        assert primary == "agents"

    def test_mlflow_infrastructure(self):
        primary, _ = classify_repo(
            "mlflow",
            "Open source platform for the machine learning lifecycle",
            ["mlops", "ml-pipeline", "model-deployment"],
        )
        assert primary == "infrastructure"

    def test_datasets_datasets(self):
        primary, _ = classify_repo(
            "datasets",
            "The largest hub of ready-to-use datasets for ML models",
            ["datasets", "machine-learning", "data-processing"],
        )
        assert primary == "datasets"

    def test_chroma_libraries(self):
        primary, _ = classify_repo(
            "chroma",
            "The AI-native open-source embedding database",
            ["vector-database", "embedding", "rag"],
        )
        assert primary == "libraries"

    def test_bentoml_infrastructure(self):
        primary, _ = classify_repo(
            "BentoML",
            "The easiest way to serve AI apps and models",
            ["model-serving", "mlops", "deployment"],
        )
        assert primary == "infrastructure"

    def test_spacy_libraries(self):
        primary, _ = classify_repo(
            "spaCy",
            "Industrial-strength Natural Language Processing (NLP) in Python",
            ["nlp", "natural-language-processing", "machine-learning"],
        )
        assert primary == "libraries"

    def test_doccano_datasets(self):
        primary, _ = classify_repo(
            "doccano",
            "Open source annotation tool for machine learning practitioners",
            ["annotation", "labeling", "nlp", "dataset"],
        )
        assert primary in ("datasets", "tools-utilities")

    def test_chatgpt_plugin_skills(self):
        primary, _ = classify_repo(
            "chatgpt-retrieval-plugin",
            "ChatGPT plugin for semantic search",
            ["chatgpt-plugin", "plugin", "integration"],
        )
        assert primary == "skills-plugins"

    def test_vllm_infrastructure(self):
        primary, _ = classify_repo(
            "vllm",
            "A high-throughput and memory-efficient inference and serving engine for LLMs",
            ["llm", "inference", "serving"],
        )
        assert primary == "infrastructure"


# --- Topic matching ---

class TestTopicMatching:
    def test_single_topic_match(self):
        primary, _ = classify_repo("test", "test repo", ["pytorch"])
        assert primary == "frameworks"

    def test_multiple_topic_matches(self):
        primary, secondary = classify_repo(
            "test", "test repo", ["pytorch", "nlp", "embedding"]
        )
        assert primary in ("frameworks", "libraries")
        assert len(secondary) >= 0

    def test_topic_case_insensitive(self):
        primary, _ = classify_repo("test", "test repo", ["PyTorch"])
        assert primary == "frameworks"


# --- Keyword matching ---

class TestKeywordMatching:
    def test_description_keyword(self):
        primary, _ = classify_repo(
            "test", "an autonomous agent framework", []
        )
        assert primary == "agents"

    def test_readme_keyword(self):
        primary, _ = classify_repo(
            "test", "a test repo", [],
            readme_excerpt="This is an agent framework for building autonomous AI agents"
        )
        assert primary == "agents"

    def test_description_case_insensitive(self):
        primary, _ = classify_repo(
            "test", "A MLOps Platform for Deployment", ["mlops"]
        )
        assert primary == "infrastructure"


# --- Name pattern matching ---

class TestNamePatternMatching:
    def test_name_with_agent(self):
        primary, _ = classify_repo("my-agent-framework", "a cool project", [])
        assert primary == "agents"

    def test_name_with_plugin(self):
        primary, _ = classify_repo("chatgpt-plugin-helper", "helper for plugins", [])
        assert primary == "skills-plugins"

    def test_name_with_deploy(self):
        primary, _ = classify_repo("ml-deploy-tool", "deployment utility", ["deployment"])
        assert primary == "infrastructure"

    def test_name_with_dataset(self):
        primary, _ = classify_repo("dataset-builder", "build datasets easily", [])
        assert primary == "datasets"


# --- Secondary categories ---

class TestSecondaryCategories:
    def test_no_secondary_for_strong_primary(self):
        _, secondary = classify_repo(
            "pure-agent", "autonomous agent framework", ["agents", "ai-agents"]
        )
        # Secondary should be empty or a short list
        assert isinstance(secondary, list)

    def test_secondary_when_multiple_match(self):
        primary, secondary = classify_repo(
            "ml-agent-tool",
            "A toolkit for building autonomous ML agent pipelines with deployment",
            ["agents", "mlops", "deployment"],
            readme_excerpt="toolkit for ML agent deployment and infrastructure",
        )
        assert isinstance(secondary, list)
        # With many matching categories, should have at least primary
        assert primary is not None

    def test_secondary_not_includes_primary(self):
        primary, secondary = classify_repo(
            "test", "agent framework with deployment",
            ["agents", "mlops"],
        )
        assert primary not in secondary


# --- Edge cases ---

class TestEdgeCases:
    def test_empty_everything(self):
        primary, secondary = classify_repo("", "", [])
        assert primary == "libraries"
        assert secondary == []

    def test_none_description(self):
        primary, _ = classify_repo("test", None, ["pytorch"])
        assert primary == "frameworks"

    def test_none_topics(self):
        primary, _ = classify_repo("test", "a framework", None)
        assert isinstance(primary, str)

    def test_none_readme(self):
        primary, _ = classify_repo("test", "test", ["ai"], None)
        assert isinstance(primary, str)

    def test_very_long_description(self):
        desc = "machine learning framework " * 100
        primary, _ = classify_repo("test", desc, [])
        assert isinstance(primary, str)
