from aixplain import config
from aixplain.client import AixplainClient

client = AixplainClient(aixplain_api_key=config.AIXPLAIN_API_KEY,
                        team_api_key=config.TEAM_API_KEY,
                        base_url=config.BACKEND_URL)
