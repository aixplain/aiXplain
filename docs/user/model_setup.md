# How to develop an aiXplain hosted model?

## Model development

The aixplain-models package organizes your model's code in a standardized format in order to deploy these models on aixplain model hosting instances. The following description covers how to organize your aiXplain hosted model.

### Model directory structure

The directory structure needs to be following:
```
src
│   model.py
│   bash.sh [Optional]
│   requirements.txt [Optional]
|   Addtional files required by your code [Optional]
```

### The model artefact directory

The hosted model might depend on files for loading parameters, configurations or other model assets. Create a model directory having the same name as the value provided in `ASSET_URI` and place all your dependant model assets in this directory.

Note:
1. The contents of this directory would be accessed or loaded by the model class' load function. 
2. The environment variable `ASSET_URI` defaults to the value `asset`.

### Implementing the model.py file

Each hosted model needs to be an instance of a function based aiXplain model. If the model that your are building is a translation model, the model class implementation should inherit the TranslationModel class interface as shown below.

```
class ExampleTranslationModel(TranslationModel):
```

To implement the model interface, define the following functions:

#### Load function

Implement the load function to load all model artefacts from the model directory specified in `ASSET_URI`. The model artefacts loaded here can be used by the model during prediction time, i.e. executing run_model().
Set the value self.ready as 'True' to indicate that loading has successfully executed.

```
    def load(self):
        model_path = AssetResolver.resolve_path()
        if not os.path.exists(model_path):
            raise ValueError('Model not found')
        self.model = pickle.load(os.path.join(model_path, 'model.pkl'))
        self.ready = True
```

#### Run model function

The run model function should contain the business logic to obtain a prediction from the loaded model.

Input:  
The input to the run model function is a dictionary. This dictionary has a key "instances" having values in a list containing AI function based subclass of APIInput values, for example TranslationInput.

Output:  
The output to the run model function is a dictionary. This dictionary has a key "predictions" having values in a list containing AI function based subclass of APIOutput values, for example TranslationOutput.  
The output is expected to return the predictions from the model in the same order as the input instances were received.

```
    def run_model(self, api_input: Dict[str, List[TranslationInput]]) -> Dict[str, List[TranslationOutput]]:
        src_text = self.parse_inputs(api_input["instances"])

        translated = self.model.generate(
            **self.tokenizer(
                src_text, return_tensors="pt", padding=True
            )
        )

        predictions = []
        for t in translated:
            data = self.tokenizer.decode(t, skip_special_tokens=True)
            details = TextSegmentDetails(text=data)
            output_dict = {
                "data": data,
                "details": details
            }
            translation_output = TranslationOutput(**output_dict)
            predictions.append(translation_output)
            predict_output = {"predictions": predictions}
        return predict_output
```


### The system and Python requirements files

The bash.sh file:  
This file implementation should include installing any system dependencies using bash commands.

The requirements.txt file:  
Include all python packages that you need to run the model by extracting the requirements using the command below

```
pip freeze >> requirements.txt
```
### Testing the model locally

Run your model with the following command:
```
ASSET_DIR=<path/to/model_artefacts_dir> ASSET_URI=<asset_uri> python -m model
```

Make an inference call:

```
ASSET_URI=<asset_uri>
curl -v -H http://localhost:8080/v1/models/$ASSET_URI:predict -d '{"instances": [{"supplier": <supplier>, "function": <function>, "data": <data>}]}'
```

The input parameter in request above needs to be modified according to the target model's function input. Refer to the [function input definition documentation.](/src/aixplain_models/schemas/function_input.py)

### Dockerfile
Create an image using the following sample Dockerfile. Add features as needed:
```Dockerfile
FROM python:3.8.10

RUN mkdir /code
WORKDIR /code
COPY . /code/

RUN pip install -r --no-cache-dir requirements.txt

RUN chmod +x /code/bash.sh
RUN ./bash.sh

CMD python -m model
```

### The environment variables

 - `ASSET_DIR`: The relative or absolute path of the model artefacts directory (ASSET_URI) on your system. This defaults to current directory.
 - `ASSET_URI`: The name of the model artefacts directory. The default name is `asset`.
