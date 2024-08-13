from aixplain.factories import ModelFactory
# model = ModelFactory.get("61dc52976eb5634cf06e97cc") # Get the ID of a model from our platform. 
# translation = model.run("Hello, how is the weather today?") # Alternatively, you can input a public URL or provide a file path on your local machine.




model = ModelFactory.get("64aee5824d34b1221e70ac07")
# Run the model. Inputs can be URLs, file paths, or direct text/labels (if applicable). 
result = model.run("a girl whos gonna pass her medicine internal exam tmrw and get a good grade")
