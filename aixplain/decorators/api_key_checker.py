from aixplain.utils import config


def check_api_key(method):
    def wrapper(*args, **kwargs):
        if config.TEAM_API_KEY == "":
            raise Exception(
                "A 'TEAM_API_KEY' is required to run an asset. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)"
            )
        return method(*args, **kwargs)

    return wrapper
