# aiXplain SDK

<div align="center">
  <img src="assets/aixplain-brandmark-line.png" alt="aiXplain logo" title="aiXplain" height="132" width="85"/>
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
```bash
pip install aixplain
```

## 🔑 Authentication
```bash
export TEAM_API_KEY=your_api_key_here
```

## 🏃‍♂️ Quick Start
```python
agent = AgentFactory.create(
    name="Google Search Agent",
    description="A search agent",
    instructions="Use Google Search to answer queries.",
    tools=[
        # Google Search (Serp)
        AgentFactory.create_model_tool("65c51c556eb563350f6e1bb1")])

response = agent.run("What's the latest AI news?").data.output
print(response)

agent.deploy()
```

## 🔗 Platform Links
- **Platform**: [platform.aixplain.com](https://platform.aixplain.com)
- **Discover**: [platform.aixplain.com/discover](https://platform.aixplain.com/discover)
- **Docs**: [docs.aixplain.com/](https://docs.aixplain.com/)
- **Support**: [GitHub Issues](https://github.com/aixplain/aiXplain/issues)
