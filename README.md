# aiXplain SDK

<div align="center">
  <img src="docs/assets/aixplain-brandmark-line.png" alt="aiXplain logo" title="aiXplain" height="132" width="85"/>
  <br>
  <br>
  
  [![Python 3.5+](https://img.shields.io/badge/python-3.5+-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
  [![PyPI version](https://badge.fury.io/py/aiXplain.svg)](https://badge.fury.io/py/aiXplain)
  
  **The professional AI SDK for developers and enterprises**
</div>

## 📖 API Reference

- **Complete documentation:**
  - [Python](https://docs.aixplain.com/api-reference/python/)
  - [Swift](https://docs.aixplain.com/api-reference/swift/)

## 🚀 Overview

The aiXplain SDK is a comprehensive Python library that empowers developers to integrate cutting-edge AI capabilities into their applications with ease. Access thousands of AI models, build custom pipelines, and deploy intelligent solutions at scale.

### ✨ Key Features

- **🔍 Discover**: Access 35,000+ ready-to-use AI models across multiple domains
- **⚡ Benchmark**: Compare AI systems using comprehensive datasets and metrics
- **🛠️ Design**: Create and deploy custom AI pipelines with our visual designer
- **🎯 FineTune**: Enhance pre-trained models with your data for optimal performance

## 📦 Installation

### Basic Installation
```bash
pip install aixplain
```

### With Model Building Support
```bash
pip install aixplain[model-builder]
```

## 🔑 Authentication

Get your API key from the aiXplain platform:

1. Visit [platform.aixplain.com](https://platform.aixplain.com)
2. Navigate to your API Keys section
3. Generate a new Team API key

### Set Your API Key

**Linux/macOS:**
```bash
export TEAM_API_KEY=your_api_key_here
```

**Windows:**
```cmd
set TEAM_API_KEY=your_api_key_here
```

**Jupyter Notebook:**
```python
%env TEAM_API_KEY=your_api_key_here
```

For detailed setup instructions, visit [docs.aixplain.com/setup](https://docs.aixplain.com/setup).

## 🏃‍♂️ Quick Start

### Running Your First Model

```python
from aixplain.factories import ModelFactory

# Get an English to French translation model
model = ModelFactory.get("61dc52976eb5634cf06e97cc")

# Run translation
result = model.run("Hello, how are you today?")
print(result.data)  # "Bonjour, comment allez-vous aujourd'hui?"
```

### Building a Pipeline

```python
from aixplain.factories.pipeline_factory import PipelineFactory
from aixplain.modules.pipeline.designer import Input

pipeline = PipelineFactory.init("Multi Input-Output Pipeline")
text_input_node = Input(data="text_input", data_types=["TEXT"], pipeline=pipeline)

TRANSLATION_ASSET_ID = '60ddefbe8d38c51c5885f98a'
translation_node = pipeline.translation(asset_id=TRANSLATION_ASSET_ID)

SENTIMENT_ASSET_ID = '61728750720b09325cbcdc36'
sentiment_node = pipeline.sentiment_analysis(asset_id=SENTIMENT_ASSET_ID)

text_input_node.link(translation_node, 'input', 'text')
translation_node.link(sentiment_node, 'data', 'text')

translated_output_node = translation_node.use_output('data')
sentiment_output_node = sentiment_node.use_output('data')

pipeline.save()
outputs = pipeline.run({
    'text_input': 'This is example text to translate.'
})

print(outputs)
```

### Working with Agents

```python
from aixplain.factories import AgentFactory

agent = AgentFactory.create(
    name="Google Search Agent",
    description="A search agent",
    instructions="Use Google Search to answer queries.",
    tools=[
        AgentFactory.create_model_tool("65c51c556eb563350f6e1bb1")
    ],
    llm_id="669a63646eb56306647e1091"
)
response = agent.run("How can I help you today?")
```

## 📊 Core Modules

| Module | Description | Documentation |
|--------|-------------|---------------|
| **Models** | Access 35,000+ AI models | [docs.aixplain.com/concepts/assets/models](https://docs.aixplain.com/concepts/assets/models/) |
| **Pipelines** | Build custom AI workflows | [docs.aixplain.com/concepts/assets/pipelines](https://docs.aixplain.com/concepts/assets/pipelines) |
| **Agents** | Deploy intelligent AI assistants | [docs.aixplain.com/concepts/assets/agents](https://docs.aixplain.com/concepts/assets/agents) |
| **Datasets** | Manage and process data | [docs.aixplain.com/concepts/assets/data/overview](https://docs.aixplain.com/concepts/assets/data/overview) |
| **Benchmarks** | Evaluate AI performance | [docs.aixplain.com/concepts/services/benchmark/benchmark-models](https://docs.aixplain.com/concepts/services/benchmark/benchmark-models) |
| **FineTuning** | Customize models with your data | [docs.aixplain.com/concepts/services/finetune/finetune-llm](https://docs.aixplain.com/concepts/services/finetune/finetune-llm) |

## 📚 Documentation

Comprehensive documentation and guides are available at **[docs.aixplain.com](https://docs.aixplain.com)**:

### 🎯 Getting Started
- [**Quick Start Guide**](https://docs.aixplain.com/getting-started/) - Get up and running in minutes
- [**API Key Setup**](https://docs.aixplain.com/getting-started/python) - Authentication and configuration
- [**Tutorials**](https://docs.aixplain.com/tutorials/) - Build your first AI application

### 📖 Core Guides
- [**Discover**](https://docs.aixplain.com/concepts/assets/models) aiXplain’s ever-expanding catalog of 35,000+ ready-to-use AI models and utilize them.
- [**Benchmark**](https://docs.aixplain.com/concepts/services/benchmark/benchmark-models) AI systems by choosing models, datasets and metrics.
- [**Design**](https://docs.aixplain.com/concepts/assets/pipelines) their own custom pipelines and run them.
- [**FineTune**](https://docs.aixplain.com/concepts/services/finetune/finetune-llm) pre-trained models by tuning them using your data, enhancing their performance.


## 🛠️ Advanced Examples

### Batch Processing
```python
# Process multiple inputs efficiently
inputs = ["text1", "text2", "text3"]
results = model.run_batch(inputs)
```

## 🤝 Community & Support

- **📖 Documentation**: [docs.aixplain.com](https://docs.aixplain.com)
- **💬 Discord Community**: [discord.gg/aixplain](https://discord.gg/aixplain)
- **🐛 Issues**: [GitHub Issues](https://github.com/aixplain/aiXplain/issues)
- **📧 Support**: support@aixplain.com
- **🔄 Release Notes**: [GitHub Releases](https://github.com/aixplain/aiXplain/releases)

## 🔗 Platform Links

- **🏠 Platform Home**: [platform.aixplain.com](https://platform.aixplain.com)
- **🔍 Model Discovery**: [platform.aixplain.com/discovery/models](https://platform.aixplain.com/discovery/models)
- **📊 Datasets**: [platform.aixplain.com/discovery/datasets](https://platform.aixplain.com/discovery/datasets)
- **📏 Metrics**: [platform.aixplain.com/discovery/metrics](https://platform.aixplain.com/discovery/metrics)

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## 🏢 About aiXplain

aiXplain is the leading AI platform for building, deploying, and managing AI solutions at scale. We democratize AI by making cutting-edge models accessible to developers and enterprises worldwide.

---

<div align="center">
  
**Ready to build the future with AI?**

[**Get Started →**](https://docs.aixplain.com/getting-started/) | [**Explore Models →**](https://platform.aixplain.com/discovery/models) | [**Join Community →**](https://www.linkedin.com/company/aixplain/)

</div>