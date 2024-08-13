from aixplain.factories import ModelFactory
import os
# os.environ["TEAM_API_KEY"] = "9136c08bf02b5552885b9f2a5e0fae517d81ff2fa6fe7084a3adb655c4aa7215"
model = ModelFactory.get("62f40a92e008518c64547b97")
data = model.run("https://aixplain-platform-assets.s3.amazonaws.com/samples/en/en-00000001.csv")
data