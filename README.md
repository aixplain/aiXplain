<img src="docs/assets/aixplain-brandmark-line.png" alt="aiXplain logo" title="aiXplain" align="right" height="132" width="85"/>

# aiXplain

aixplain is a software development kit (SDK) for the [aiXplain](https://aixplain.com/) platform. With aixplain, developers can quickly and easily:

- [Discover](https://aixplain.com/platform/discovery/) aiXplain’s ever-expanding catalog of 35,000+ ready-to-use AI models and utilize them.
- [Benchmark](https://aixplain.com/platform/benchmark/) AI systems by choosing models, datasets and metrics.
- [Design](https://aixplain.com/platform/studio/) their own custom pipelines and run them.
- [FineTune](https://aixplain.com/platform/finetune/) pre-trained models by tuning them using your data, enhancing their performance.

🔎 **Find [models](https://platform.aixplain.com/discovery/models), [datasets](https://platform.aixplain.com/discovery/datasets), [metrics](https://platform.aixplain.com/discovery/metrics) on the platform.**

💛 Our repository is constantly evolving. With the help of the scientific community, we plan to add even more datasets, models, and metrics across domains and tasks.

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
#### Jupyter Notebook
```
%env TEAM_API_KEY=YOUR_API_KEY
```

### Usage

Let’s see how we can use aixplain to run a machine translation model. The following example shows an [English to French translation model](https://platform.aixplain.com/discovery/model/61dc52976eb5634cf06e97cc).

```python
>>> from aixplain.assets import Model
>>> model = Model.get("61dc52976eb5634cf06e97cc") # Get the ID of a model from our platform.
>>> model.name
Translate from English to French (Transformer12x2)
>>> translation = model.run("This is a sample text") # Alternatively, you can input a public URL or provide a file path on your local machine.

>>> [model.name for model in Model.list()] # List and page other available models
['Translate from Norwegian (Nynorsk) to Hebrew',
 'Translate from Catalan to Hungarian',
 'Speech Synthesis - Japanese [ja-JP.default-ja_adapt]',
 'Speech Synthesis - English (US) [en-US.default-en_male_01]',
 'Translate from Catalan to Albanian',
 'Translate from Dutch to Japanese',
 'Translate from Romanian to Japanese',
 'Translate from Catalan to Indonesian',
 'Translate from Greek to Norwegian (Bokmal)',
 'Translate from Danish to English']
```
*Check out the [explore section](docs/user/user_doc.md#explore) of our guide on Models to get the ID of your desired model*

## Quick Links

* [Team API Key Guide](docs/user/api_setup.md)
* [User Documentation](docs/user/user_doc.md)
* [Developer Guide](docs/development/developer_guide.md)
* [API Reference](https://docs.aixplain.com/main.html)
* [Release notes](https://github.com/aixplain/aiXplain/releases)

## Support
Raise issues for support in this repository.  
Pull requests are welcome!

## Note
The **aiXtend** python package was renamed to **aiXplain** from the release v0.1.1.
