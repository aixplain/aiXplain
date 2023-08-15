import os

BACKEND_URL = os.getenv('BACKEND_URL', 'https://platform-api.aixplain.com')
MODELS_RUN_URL = os.getenv('MODELS_RUN_URL',
                           'https://models.aixplain.com/api/v1/execute/')

# GET THE API KEY FROM CMD
TEAM_API_KEY = os.getenv('TEAM_API_KEY', '')
AIXPLAIN_API_KEY = os.getenv('AIXPLAIN_API_KEY', '')
PIPELINE_API_KEY = os.getenv('PIPELINE_API_KEY', '')
MODEL_API_KEY = os.getenv('MODEL_API_KEY', '')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
