import logging
logging.basicConfig(level=logging.WARN)
import os
from aixplain.factories import ModelFactory
os.environ["TEAM_API_KEY"] = "f8dcf228a8a0d2b85a800eabe8f73b9af89f571c668b7524ffe82fca83a95096"
model = ModelFactory.get("66b2708c6eb5635d1c71f611")