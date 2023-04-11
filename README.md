<img src="docs/assets/aixplain-brandmark-common.png" alt="aiXplain logo" title="aiXplain" align="right" height="132" width="85"/>

# aiXplain

aixplain is a software development kit (SDK) for the [aiXplain](https://aixplain.com/) platform. With aixplain, developers can quickly and easily:

- [Discover](https://aixplain.com/platform/discovery/) aiXplain’s ever-expanding catalog of 35,000+ ready-to-use AI models and utilize them.
- [Benchmark](https://aixplain.com/platform/benchmark/) AI systems by choosing models, datasets and metrics.
- [Design](https://aixplain.com/platform/studio/) their own custom pipelines and run them.

[🎓 **Documentation**](docs/user/user_doc.md)

🔎 **Find [models](https://platform.aixplain.com/discovery/models), [datasets](https://platform.aixplain.com/discovery/datasets), [metrics](https://platform.aixplain.com/discovery/metrics) on the platform.**

:yellow_heart: Our repository is constantly evolving. With the help of the scientific community, we plan to add even more datasets, models, and metrics across domains and tasks.

## Getting Started

### Installation
To install simply,
```bash
pip install aixplain
```

###  API Key Setup
Before you can use the aixplain SDK, you'll need to obtain an API key from our platform. For details refer this [Team API Key Guide](docs/user/api_setup.md).

Once you get the API key, you'll  need to add this API key as an environment variable on your system.
#### Linux or macOS
```bash
export TEAM_API_KEY=YOUR_API_KEY
```
#### Windows
```bash
set TEAM_API_KEY=YOUR_API_KEY
```
## Usage

Let’s see how we can use aixplain to run a machine translation model.

```python
from aixplain.factories.model_factory  import ModelFactory
model = ModelFactory.create_asset_from_id("61b27086c45ecd3c10d0608c") # Got the ID of an MT model from on our platform
translation = model.run("This is a sample text")
```
*Check out the [explore section](docs/user/user_doc.md#explore) of our guide on Models to get the ID of your desired model*

## Developer Guide

Follow the [Developer Guide](docs/development/developer_guide.md).

## Support
Raise issues for support in this repository.  
Pull requests are welcome!

## Note
The aixtend python package was renamed to aixplain from the release v0.1.1.
