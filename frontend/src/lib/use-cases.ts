/**
 * Derive use cases from a repo's topics, category, and description.
 * Returns up to `limit` relevant use case strings.
 */

const TOPIC_USE_CASES: Record<string, string[]> = {
  // LLM & text generation
  'llm': ['Build conversational AI assistants', 'Generate and summarize text'],
  'chatbot': ['Create customer support bots', 'Build interactive chat interfaces'],
  'chatgpt': ['Integrate ChatGPT into applications', 'Build GPT-powered workflows'],
  'gpt': ['Text generation and completion', 'Content creation pipelines'],
  'prompt-engineering': ['Optimize LLM prompts for production', 'Build prompt testing frameworks'],

  // Agents
  'agents': ['Orchestrate autonomous AI workflows', 'Build multi-step task automation'],
  'ai-agents': ['Create goal-oriented AI systems', 'Automate complex decision-making'],
  'multi-agent': ['Coordinate multiple AI agents', 'Simulate agent-based systems'],
  'langchain': ['Chain LLM calls with tools and data', 'Build retrieval-augmented pipelines'],
  'langgraph': ['Design stateful agent workflows', 'Build cyclical AI reasoning graphs'],
  'autogen': ['Create multi-agent conversations', 'Automate collaborative AI tasks'],
  'mcp': ['Connect AI models to external tools', 'Build model context protocol servers'],
  'agentic-ai': ['Build self-directed AI systems', 'Create autonomous task agents'],

  // RAG & search
  'rag': ['Build knowledge-grounded Q&A systems', 'Augment LLMs with private data'],
  'retrieval-augmented-generation': ['Answer questions from document collections', 'Build enterprise search with AI'],
  'vector-database': ['Store and query embeddings at scale', 'Build semantic search engines'],
  'vector-search': ['Find similar items by meaning', 'Power recommendation systems'],
  'embedding': ['Convert text/images to vector representations', 'Build similarity matching'],
  'embeddings': ['Generate embeddings for search and clustering', 'Semantic document analysis'],
  'semantic-search': ['Search by meaning instead of keywords', 'Build intelligent document retrieval'],

  // NLP
  'nlp': ['Extract entities and sentiment from text', 'Build text classification pipelines'],
  'natural-language-processing': ['Process and analyze natural language', 'Build language understanding systems'],
  'transformers': ['Fine-tune models for custom NLP tasks', 'Run state-of-the-art language models'],
  'tokenizer': ['Tokenize text for model input', 'Build custom tokenization pipelines'],
  'bert': ['Text classification and named entity recognition', 'Semantic similarity scoring'],
  'speech-recognition': ['Transcribe audio to text', 'Build voice-controlled interfaces'],

  // Computer vision
  'computer-vision': ['Detect and classify objects in images', 'Build visual inspection systems'],
  'object-detection': ['Real-time object detection in video', 'Build surveillance or safety systems'],
  'stable-diffusion': ['Generate images from text prompts', 'Create AI art and design tools'],
  'image-processing': ['Automate image editing workflows', 'Build visual content pipelines'],

  // ML frameworks & training
  'pytorch': ['Train custom deep learning models', 'Research and prototype neural networks'],
  'tensorflow': ['Build and deploy ML models at scale', 'Run models on edge devices'],
  'keras': ['Rapid deep learning prototyping', 'Build neural networks with minimal code'],
  'jax': ['High-performance numerical computing', 'Accelerated ML research'],
  'fine-tuning': ['Adapt pre-trained models to your data', 'Build domain-specific AI'],

  // Infrastructure & MLOps
  'mlops': ['Automate ML model lifecycle', 'Monitor models in production'],
  'model-serving': ['Serve models as APIs', 'Scale inference endpoints'],
  'deployment': ['Deploy ML models to production', 'Build CI/CD for ML pipelines'],
  'kubernetes': ['Orchestrate ML workloads at scale', 'Run distributed training jobs'],
  'inference': ['Optimize model inference speed', 'Run models efficiently on hardware'],
  'gpu': ['Accelerate training and inference', 'Optimize GPU memory usage'],

  // Data
  'dataset': ['Curate training data for ML models', 'Build data processing pipelines'],
  'datasets': ['Access and load benchmark datasets', 'Preprocess data for model training'],
  'annotation': ['Label data for supervised learning', 'Build annotation workflows'],
  'data-augmentation': ['Expand training datasets synthetically', 'Improve model robustness'],

  // Apps & UI
  'gradio': ['Build ML model demos in minutes', 'Create interactive AI prototypes'],
  'streamlit': ['Build data apps and dashboards', 'Prototype ML tools with Python'],
  'web-app': ['Build AI-powered web applications', 'Create user-facing AI tools'],

  // Specific models
  'llama': ['Run Llama models locally', 'Fine-tune Llama for your domain'],
  'mistral': ['Deploy Mistral models', 'Build with efficient open LLMs'],
  'whisper': ['Transcribe and translate audio', 'Build speech-to-text pipelines'],
  'ollama': ['Run LLMs locally on your machine', 'Build offline AI applications'],
  'comfyui': ['Design complex image generation workflows', 'Build node-based AI pipelines'],

  // Dev tools
  'cli': ['Build command-line AI tools', 'Automate terminal workflows with AI'],
  'api': ['Integrate AI capabilities via APIs', 'Build AI-powered backend services'],
  'sdk': ['Build applications with AI provider SDKs', 'Integrate AI into existing apps'],
  'automation': ['Automate repetitive tasks with AI', 'Build intelligent workflow automation'],
  'monitoring': ['Track model performance in production', 'Detect model drift and anomalies'],
};

const CATEGORY_USE_CASES: Record<string, string[]> = {
  'frameworks': ['Train and fine-tune ML models', 'Build custom neural network architectures'],
  'apis-sdks': ['Integrate AI services into your app', 'Build on top of AI provider APIs'],
  'agents': ['Build autonomous AI agents', 'Automate multi-step workflows'],
  'apps': ['Deploy AI-powered applications', 'Build user-facing AI interfaces'],
  'tools-utilities': ['Streamline AI development workflows', 'Evaluate and benchmark models'],
  'models': ['Use pre-trained models for inference', 'Fine-tune models for specific tasks'],
  'datasets': ['Train models on curated datasets', 'Benchmark model performance'],
  'infrastructure': ['Deploy and scale ML systems', 'Manage the ML model lifecycle'],
  'skills-plugins': ['Extend AI platforms with custom capabilities', 'Connect AI to external services'],
  'libraries': ['Add AI capabilities to your codebase', 'Process text, images, or embeddings'],
};

export function getUseCases(
  topics: string[],
  category: string | null,
  limit: number = 4,
): string[] {
  const seen = new Set<string>();
  const results: string[] = [];

  // Collect from topics (higher priority)
  for (const topic of topics) {
    const cases = TOPIC_USE_CASES[topic.toLowerCase()];
    if (!cases) continue;
    for (const c of cases) {
      if (!seen.has(c)) {
        seen.add(c);
        results.push(c);
      }
      if (results.length >= limit) return results;
    }
  }

  // Fill from category
  if (category && results.length < limit) {
    const cases = CATEGORY_USE_CASES[category] || [];
    for (const c of cases) {
      if (!seen.has(c)) {
        seen.add(c);
        results.push(c);
      }
      if (results.length >= limit) return results;
    }
  }

  return results;
}
