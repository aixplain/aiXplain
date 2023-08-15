from enum import Enum
from aixplain.env import client as env_client
from aixplain.client import AixplainClient


def populate_language_enum(client: AixplainClient = env_client,
                           path: str = 'sdk/languages') -> Enum:
    'Generate an Enum representing available languages and dialects.'
    response = client.get(path)
    payload = response.json()
    languages = {}
    for entry in payload:
        language = entry['value']
        language_label = '_'.join(entry['label'].split())
        languages[language_label] = {'language': language, 'dialect': None}
        for dialect in entry['dialects']:
            dialect_label = '_'.join(dialect['label'].split()).upper()
            dialect_value = dialect['value']
            dialect_key = f'{language_label}_{dialect_label}'
            languages[dialect_key] = {
                'language': language,
                'dialect': dialect_value
            }
    return Enum('Language', languages, type=dict)


def populate_license_enum(client: AixplainClient = env_client,
                          path: str = 'sdk/licenses') -> Enum:
    'Generate an Enum representing available licenses.'
    response = client.get(path)
    payload = response.json()
    licences = {}
    for entry in payload:
        license_key = '_'.join(entry['name'].split())
        license_value = entry['id']
        licences[license_key] = license_value
    return Enum('License', licences, type=str)


def populate_function_enum(client: AixplainClient = env_client,
                           path: str = 'sdk/functions') -> Enum:
    'Generate an Enum representing available functions.'
    response = client.get(path)
    payload = response.json()
    licences = {}
    for entry in payload['items']:
        function_key = entry['id'].upper().replace('-', '_')
        function_value = entry['id']
        licences[function_key] = function_value
    return Enum('Function', licences, type=str)


# Dynamic population of certain enum types
Function = populate_function_enum()
License = populate_license_enum()
Language = populate_language_enum()


class DataSplit(Enum):
    TRAIN = 'train'
    VALIDATION = 'validation'
    TEST = 'test'


class DataSubtype(Enum):
    AGE = 'age'
    GENDER = 'gender'
    INTERVAL = 'interval'
    OTHER = 'other'
    RACE = 'race'
    SPLIT = 'split'
    TOPIC = 'topic'


class DataType(Enum):
    AUDIO = 'audio'
    FLOAT = 'float'
    IMAGE = 'image'
    INTEGER = 'integer'
    LABEL = 'label'
    TENSOR = 'tensor'
    TEXT = 'text'
    VIDEO = 'video'


class ErrorHandler(Enum):
    SKIP = 'skip'
    FAIL = 'fail'


class FileType(Enum):
    CSV = '.csv'
    JSON = '.json'
    TXT = '.txt'
    XML = '.xml'
    FLAC = '.flac'
    MP3 = '.mp3'
    WAV = '.wav'
    JPEG = '.jpeg'
    PNG = '.png'
    JPG = '.jpg'
    GIF = '.gif'
    WEBP = '.webp'
    AVI = '.avi'
    MP4 = '.mp4'
    MOV = '.mov'
    MPEG4 = '.mpeg4'


class OnboardStatus(Enum):
    ONBOARDING = 'onboarding'
    ONBOARDED = 'onboarded'
    FAILED = 'failed'
    DELETED = 'deleted'


class Privacy (Enum):
    PUBLIC = 'Public'
    PRIVATE = 'Private'
    RESTRICTED = 'Restricted'


class StorageType(Enum):
    TEXT = 'text'
    URL = 'url'
    FILE = 'file'
