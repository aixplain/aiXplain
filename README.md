<img src="docs/assets/aixplain-brandmark-common.png" alt="aiXplain logo" title="aiXplain" align="right" height="132" width="85"/>

# aiXtend

aiXtend is a software development kit (SDK) for the [aiXplain platform](https://aixplain.com/). With aiXtend, developers can quickly and easily:

- [Browse](https://aixplain.com/platform/discovery/) and use aiXplain’s ever-expanding catalog of 35,000+ ready-to-use AI models.
- [Benchmark](https://aixplain.com/platform/benchmark/) AI systems by choosing models, datasets and metrics.
- Run your own custom designed [pipelines](https://aixplain.com/platform/studio/).

[🎓 **Documentation**](https://huggingface.co/docs/evaluate/)

🔎 **Find a [model](https://platform.aixplain.com/discovery/models), [dataset](https://platform.aixplain.com/discovery/datasets), [metric](https://platform.aixplain.com/discovery/metrics) on the platform.**

## Getting Started

### Installation
To install simply,
```bash
pip install aixtend
```

###  API Key Setup
Before you can use the aiXtend SDK, you'll need to obtain an API key from our platform. <Here's how to do it>

Once you get the API key, you'll  need to add this API key as an environment variable on your system.
#### Linux and macOS
```bash
export TEAM_API_KEY=YOUR_API_KEY
```
#### Windows
```bash
set TEAM_API_KEY=YOUR_API_KEY
```
## Usage

Let’s see how we can use aiXtend to run a machine translation model.


```python
from aixtend.factories.model_factory  import ModelFactory
model = ModelFactory.create_asset_from_id("61b27086c45ecd3c10d0608c") # Got the ID of an MT model from on our platform
translation = model.run("This is a sample text")
```


## Developer Guide

Follow the developer guide [documentation](docs/development/developer_guide.md).

## Support

Raise issues for support in this repository.  
Pull requests are welcome!
