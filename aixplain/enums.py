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

class Function(Enum):
    ASR_QUALITY_ESTIMATION = 'asr-quality-estimation'
    AUDIO_FORCED_ALIGNMENT = 'audio-forced-alignment'
    AUDIO_GENERATION_METRIC = 'audio-generation-metric'
    AUDIO_RECONSTRUCTION = 'audio-reconstruction'
    AUDIO_TRANSCRIPT_ANALYSIS = 'audio-transcript-analysis'
    AUDIO_TRANSCRIPT_IMPROVEMENT = 'audio-transcript-improvement'
    DIACRITIZATION = 'diacritization'
    DIALECT_DETECTION = 'dialect-detection'
    EMOTION_DETECTION = 'emotion-detection'
    ENTITY_LINKING = 'entity-linking'
    EXTRACT_AUDIO_FROM_VIDEO = 'extract-audio-from-video'
    FILL_TEXT_MASK = 'fill-text-mask'
    IMAGE_COMPRESSION = 'image-compression'
    IMAGE_CONTENT_MODERATION = 'image-content-moderation'
    IMAGE_LABEL_DETECTION = 'image-label-detection'
    LANGUAGE_IDENTIFICATION = 'language-identification'
    METRIC_AGGREGATION = 'metric-aggregation'
    NAMED_ENTITY_RECOGNITION = 'named-entity-recognition'
    OCR = 'ocr'
    OFFENSIVE_LANGUAGE_IDENTIFICATION = 'offensive-language-identification'
    REFERENCELESS_AUDIO_GENERATION_METRIC = 'referenceless-audio-generation-metric'
    REFERENCELESS_TEXT_GENERATION_METRIC = 'referenceless-text-generation-metric'
    REFERENCELESS_TEXT_GENERATION_METRIC_DEFAULT = 'referenceless-text-generation-metric-default'
    SEARCH = 'search'
    SENTIMENT_ANALYSIS = 'sentiment-analysis'
    SPEAKER_DIARIZATION_AUDIO = 'speaker-diarization-audio'
    SPEAKER_DIARIZATION_VIDEO = 'speaker-diarization-video'
    SPEECH_CLASSIFICATION = 'speech-classification'
    SPEECH_EMBEDDING = 'speech-embedding'
    SPEECH_NON_SPEECH_CLASSIFICATION = 'speech-non-speech-classification'
    SPEECH_RECOGNITION = 'speech-recognition'
    SPEECH_SYNTHESIS = 'speech-synthesis'
    SPLIT_ON_LINEBREAK = 'split-on-linebreak'
    SPLIT_ON_SILENCE = 'split-on-silence'
    SUBTITLING = 'subtitling'
    SUBTITLING_TRANSLATION = 'subtitling-translation'
    TEXT_CLASSIFICATION = 'text-classification'
    TEXT_CONTENT_MODERATION = 'text-content-moderation'
    TEXT_DENORMALIZATION = 'text-denormalization'
    TEXT_GENERATION = 'text-generation'
    TEXT_GENERATION_METRIC = 'text-generation-metric'
    TEXT_GENERATION_METRIC_DEFAULT = 'text-generation-metric-default'
    TEXT_NORMALIZATION = 'text-normalization'
    TEXT_RECONSTRUCTION = 'text-reconstruction'
    TEXT_SPAM_DETECTION = 'text-spam-detection'
    TEXT_SUMMARIZATION = 'text-summarization'
    TEXT_TO_IMAGE_GENERATION = 'text-to-image-generation'
    TOPIC_CLASSIFICATION = 'topic-classification'
    TRANSLATION = 'translation'
    VIDEO_CONTENT_MODERATION = 'video-content-moderation'
    VIDEO_FORCED_ALIGNMENT = 'video-forced-alignment'
    VIDEO_GENERATION = 'video-generation'
    VIDEO_LABEL_DETECTION = 'video-label-detection'
    VOICE_ACTIVITY_DETECTION = 'voice-activity-detection'
    VOICE_CLONING = 'voice-cloning'

class License(Enum):
    Apache_License__Version_2_0 = '620ba3ae3e2fa95c500b429f'
    BSD_3_Clause = '620ba3b13e2fa95c500b42a0'
    CC_BY = '620ba3983e2fa95c500b4297'
    CC_BY_NC = '620ba39e3e2fa95c500b4299'
    CC_BY_NC_ND = '620ba3a63e2fa95c500b429c'
    CC_BY_NC_SA = '620ba3a03e2fa95c500b429a'
    CC_BY_ND = '620ba3a33e2fa95c500b429b'
    CC_BY_SA = '620ba39b3e2fa95c500b4298'
    Custom = '620ba3b43e2fa95c500b42a1'
    GPL = '620ba3ab3e2fa95c500b429e'
    MIT = '620ba3a83e2fa95c500b429d'
    Public_domain_CC0 = '620ba3943e2fa95c500b4296'
    Unknown = '620ba3b73e2fa95c500b42a2'

class Language(Enum):
    Afrikaans = {'language': 'af', 'dialect': None}
    Afrikaans_SOUTH_AFRICA = {'language': 'af', 'dialect': 'South Africa'}
    Albanian = {'language': 'sq', 'dialect': None}
    Albanian_ALBANIA = {'language': 'sq', 'dialect': 'Albania'}
    Amharic = {'language': 'am', 'dialect': None}
    Amharic_ETHIOPIA = {'language': 'am', 'dialect': 'Ethiopia'}
    Arabic = {'language': 'ar', 'dialect': None}
    Arabic_ALGERIA = {'language': 'ar', 'dialect': 'Algeria'}
    Arabic_AUTO_DETECT = {'language': 'ar', 'dialect': 'Auto-Detect'}
    Arabic_BAHRAIN = {'language': 'ar', 'dialect': 'Bahrain'}
    Arabic_CLASSICAL_ARABIC = {'language': 'ar', 'dialect': 'Classical Arabic'}
    Arabic_EGYPT = {'language': 'ar', 'dialect': 'Egypt'}
    Arabic_GULF = {'language': 'ar', 'dialect': 'Gulf'}
    Arabic_IRAQ = {'language': 'ar', 'dialect': 'Iraq'}
    Arabic_ISRAEL = {'language': 'ar', 'dialect': 'Israel'}
    Arabic_JORDAN = {'language': 'ar', 'dialect': 'Jordan'}
    Arabic_KUWAIT = {'language': 'ar', 'dialect': 'Kuwait'}
    Arabic_LEBANON = {'language': 'ar', 'dialect': 'Lebanon'}
    Arabic_LIBYA = {'language': 'ar', 'dialect': 'Libya'}
    Arabic_MODERN_STANDARD_ARABIC = {'language': 'ar', 'dialect': 'Modern Standard Arabic'}
    Arabic_MOROCCO = {'language': 'ar', 'dialect': 'Morocco'}
    Arabic_OMAN = {'language': 'ar', 'dialect': 'Oman'}
    Arabic_PALESTINE = {'language': 'ar', 'dialect': 'Palestine'}
    Arabic_QATAR = {'language': 'ar', 'dialect': 'Qatar'}
    Arabic_SAUDI_ARABIA = {'language': 'ar', 'dialect': 'Saudi Arabia'}
    Arabic_SYRIA = {'language': 'ar', 'dialect': 'Syria'}
    Arabic_TUNISIA = {'language': 'ar', 'dialect': 'Tunisia'}
    Arabic_UNITED_ARAB_EMIRATES = {'language': 'ar', 'dialect': 'United Arab Emirates'}
    Arabic_YEMEN = {'language': 'ar', 'dialect': 'Yemen'}
    Armenian = {'language': 'hy', 'dialect': None}
    Armenian_ARMENIA = {'language': 'hy', 'dialect': 'Armenia'}
    Assamese = {'language': 'asm', 'dialect': None}
    Azerbaijani = {'language': 'az', 'dialect': None}
    Azerbaijani_AZERBAIJAN = {'language': 'az', 'dialect': 'Azerbaijan'}
    Bangla = {'language': 'bn', 'dialect': None}
    Bangla_BANGLADESH = {'language': 'bn', 'dialect': 'Bangladesh'}
    Bangla_INDIA = {'language': 'bn', 'dialect': 'India'}
    Bashkir = {'language': 'ba', 'dialect': None}
    Basque = {'language': 'eu', 'dialect': None}
    Basque_SPAIN = {'language': 'eu', 'dialect': 'Spain'}
    Belarusian = {'language': 'be', 'dialect': None}
    Bosnian = {'language': 'bs', 'dialect': None}
    Bosnian_BOSNIA = {'language': 'bs', 'dialect': 'Bosnia'}
    Bulgarian = {'language': 'bg', 'dialect': None}
    Bulgarian_BULGARIA = {'language': 'bg', 'dialect': 'Bulgaria'}
    Bulgarian_BULGARY = {'language': 'bg', 'dialect': 'Bulgary'}
    Burmese = {'language': 'my', 'dialect': None}
    Burmese_MYANMAR = {'language': 'my', 'dialect': 'Myanmar'}
    Catalan = {'language': 'ca', 'dialect': None}
    Catalan_SPAIN = {'language': 'ca', 'dialect': 'Spain'}
    Cebuano = {'language': 'ceb', 'dialect': None}
    Chinese = {'language': 'zh', 'dialect': None}
    Chinese_HONG_KONG = {'language': 'zh', 'dialect': 'Hong Kong'}
    Chinese_MANDARIN = {'language': 'zh', 'dialect': 'Mandarin'}
    Chinese_TAIWANESE,_MANDARIN = {'language': 'zh', 'dialect': 'Taiwanese, Mandarin'}
    Chinese_TRADITIONAL = {'language': 'zh', 'dialect': 'Traditional'}
    Corsican = {'language': 'co', 'dialect': None}
    Croatian = {'language': 'hr', 'dialect': None}
    Croatian_CROATIA = {'language': 'hr', 'dialect': 'Croatia'}
    Czech = {'language': 'cs', 'dialect': None}
    Czech_CZECH = {'language': 'cs', 'dialect': 'Czech'}
    Czech_CZECH_REPUBLIC = {'language': 'cs', 'dialect': 'Czech Republic'}
    Danish = {'language': 'da', 'dialect': None}
    Danish_DENMARK = {'language': 'da', 'dialect': 'Denmark'}
    Dari = {'language': 'prs', 'dialect': None}
    Divehi = {'language': 'dv', 'dialect': None}
    Dutch = {'language': 'nl', 'dialect': None}
    Dutch_BELGIUM = {'language': 'nl', 'dialect': 'Belgium'}
    Dutch_NETHERLANDS = {'language': 'nl', 'dialect': 'Netherlands'}
    English = {'language': 'en', 'dialect': None}
    English_AUSTRALIA = {'language': 'en', 'dialect': 'Australia'}
    English_AUSTRALIAN = {'language': 'en', 'dialect': 'Australian'}
    English_CANADA = {'language': 'en', 'dialect': 'Canada'}
    English_GHANA = {'language': 'en', 'dialect': 'Ghana'}
    English_HONG_KONG = {'language': 'en', 'dialect': 'Hong Kong'}
    English_INDIA = {'language': 'en', 'dialect': 'India'}
    English_INDIAN = {'language': 'en', 'dialect': 'Indian'}
    English_IRELAND = {'language': 'en', 'dialect': 'Ireland'}
    English_KENYA = {'language': 'en', 'dialect': 'Kenya'}
    English_NEW_ZEALAND = {'language': 'en', 'dialect': 'New Zealand'}
    English_NIGERIA = {'language': 'en', 'dialect': 'Nigeria'}
    English_PAKISTAN = {'language': 'en', 'dialect': 'Pakistan'}
    English_PHILIPPINES = {'language': 'en', 'dialect': 'Philippines'}
    English_SCOTTISH = {'language': 'en', 'dialect': 'Scottish'}
    English_SINGAPORE = {'language': 'en', 'dialect': 'Singapore'}
    English_SOUTH_AFRICA = {'language': 'en', 'dialect': 'South Africa'}
    English_TANZANIA = {'language': 'en', 'dialect': 'Tanzania'}
    English_UNITED_KINGDOM = {'language': 'en', 'dialect': 'United Kingdom'}
    English_UNITED_STATES = {'language': 'en', 'dialect': 'United States'}
    English_WELSH = {'language': 'en', 'dialect': 'Welsh'}
    Esperanto = {'language': 'eo', 'dialect': None}
    Estonian = {'language': 'et', 'dialect': None}
    Estonian_ESTONIA = {'language': 'et', 'dialect': 'Estonia'}
    Fijian = {'language': 'fj', 'dialect': None}
    Filipino = {'language': 'fil', 'dialect': None}
    Filipino_PHILIPPINES = {'language': 'fil', 'dialect': 'Philippines'}
    Filipino_TAGALOG = {'language': 'fil', 'dialect': 'Tagalog'}
    Finnish = {'language': 'fi', 'dialect': None}
    Finnish_FINLAND = {'language': 'fi', 'dialect': 'Finland'}
    French = {'language': 'fr', 'dialect': None}
    French_BELGIUM = {'language': 'fr', 'dialect': 'Belgium'}
    French_CANADA = {'language': 'fr', 'dialect': 'Canada'}
    French_CANADIAN = {'language': 'fr', 'dialect': 'Canadian'}
    French_FRANCE = {'language': 'fr', 'dialect': 'France'}
    French_SWITZERLAND = {'language': 'fr', 'dialect': 'Switzerland'}
    Frisian = {'language': 'fy', 'dialect': None}
    Galician = {'language': 'gl', 'dialect': None}
    Galician_SPAIN = {'language': 'gl', 'dialect': 'Spain'}
    Georgian = {'language': 'ka', 'dialect': None}
    Georgian_GEORGIA = {'language': 'ka', 'dialect': 'Georgia'}
    German = {'language': 'de', 'dialect': None}
    German_AUSTRIA = {'language': 'de', 'dialect': 'Austria'}
    German_GERMANY = {'language': 'de', 'dialect': 'Germany'}
    German_SWITZERLAND = {'language': 'de', 'dialect': 'Switzerland'}
    Greek = {'language': 'el', 'dialect': None}
    Greek_GREECE = {'language': 'el', 'dialect': 'Greece'}
    Gujarati = {'language': 'gu', 'dialect': None}
    Gujarati_INDIA = {'language': 'gu', 'dialect': 'India'}
    Gujarati_INDIAN = {'language': 'gu', 'dialect': 'Indian'}
    Haitian = {'language': 'ht', 'dialect': None}
    Hausa = {'language': 'ha', 'dialect': None}
    Hawaiian = {'language': 'haw', 'dialect': None}
    Hebrew = {'language': 'he', 'dialect': None}
    Hebrew_ISRAEL = {'language': 'he', 'dialect': 'Israel'}
    Hindi = {'language': 'hi', 'dialect': None}
    Hindi_INDIA = {'language': 'hi', 'dialect': 'India'}
    Hmong = {'language': 'hmn', 'dialect': None}
    Hungarian = {'language': 'hu', 'dialect': None}
    Hungarian_HUNGARY = {'language': 'hu', 'dialect': 'Hungary'}
    Icelandic = {'language': 'isl', 'dialect': None}
    Igbo = {'language': 'ig', 'dialect': None}
    Indonesian = {'language': 'id', 'dialect': None}
    Indonesian_INDONESIA = {'language': 'id', 'dialect': 'Indonesia'}
    Inuktitut = {'language': 'iu', 'dialect': None}
    Irish = {'language': 'ga', 'dialect': None}
    Irish_IRELAND = {'language': 'ga', 'dialect': 'Ireland'}
    Italian = {'language': 'it', 'dialect': None}
    Italian_ITALY = {'language': 'it', 'dialect': 'Italy'}
    Italian_SWITZERLAND = {'language': 'it', 'dialect': 'Switzerland'}
    Japanese = {'language': 'ja', 'dialect': None}
    Japanese_JAPAN = {'language': 'ja', 'dialect': 'Japan'}
    Javanese = {'language': 'jv', 'dialect': None}
    Javanese_INDONESIA = {'language': 'jv', 'dialect': 'Indonesia'}
    Kannada = {'language': 'kn', 'dialect': None}
    Kannada_INDIA = {'language': 'kn', 'dialect': 'India'}
    Kazakh = {'language': 'kk', 'dialect': None}
    Kazakh_KAZAKHSTAN = {'language': 'kk', 'dialect': 'Kazakhstan'}
    Khmer = {'language': 'km', 'dialect': None}
    Khmer_CAMBODIA = {'language': 'km', 'dialect': 'Cambodia'}
    Kinyarwanda = {'language': 'rw', 'dialect': None}
    Klingon = {'language': 'tlh', 'dialect': None}
    Korean = {'language': 'ko', 'dialect': None}
    Korean_KOREA = {'language': 'ko', 'dialect': 'Korea'}
    Kurdish = {'language': 'ku', 'dialect': None}
    Kyrgyz = {'language': 'ky', 'dialect': None}
    Lao = {'language': 'lo', 'dialect': None}
    Lao_LAOS = {'language': 'lo', 'dialect': 'Laos'}
    Latvian = {'language': 'lv', 'dialect': None}
    Latvian_LATVIA = {'language': 'lv', 'dialect': 'Latvia'}
    Lithuanian = {'language': 'lt', 'dialect': None}
    Lithuanian_LITHUANIA = {'language': 'lt', 'dialect': 'Lithuania'}
    Luxembourgish = {'language': 'lb', 'dialect': None}
    Luxembourgish_SOUTH_AFRICA = {'language': 'lb', 'dialect': 'South Africa'}
    Macedonian = {'language': 'mk', 'dialect': None}
    Macedonian_NORTH_MACEDONIA = {'language': 'mk', 'dialect': 'North Macedonia'}
    Malagasy = {'language': 'mg', 'dialect': None}
    Malay = {'language': 'ms', 'dialect': None}
    Malay_MALAYSIA = {'language': 'ms', 'dialect': 'Malaysia'}
    Malayalam = {'language': 'ml', 'dialect': None}
    Malayalam_INDIA = {'language': 'ml', 'dialect': 'India'}
    Maltese = {'language': 'mt', 'dialect': None}
    Maltese_MALTA = {'language': 'mt', 'dialect': 'Malta'}
    Maori = {'language': 'mi', 'dialect': None}
    Marathi = {'language': 'mr', 'dialect': None}
    Marathi_INDIA = {'language': 'mr', 'dialect': 'India'}
    Mongolian = {'language': 'mn', 'dialect': None}
    Mongolian_MONGOLIA = {'language': 'mn', 'dialect': 'Mongolia'}
    Nepali = {'language': 'ne', 'dialect': None}
    Nepali_NEPAL = {'language': 'ne', 'dialect': 'Nepal'}
    Norwegian = {'language': 'no', 'dialect': None}
    Norwegian_NORWAY = {'language': 'no', 'dialect': 'Norway'}
    Nyanja = {'language': 'ny', 'dialect': None}
    Odia = {'language': 'or', 'dialect': None}
    Pashto = {'language': 'ps', 'dialect': None}
    Persian = {'language': 'fa', 'dialect': None}
    Persian_IRAN = {'language': 'fa', 'dialect': 'Iran'}
    Persian_PERSIAN = {'language': 'fa', 'dialect': 'Persian'}
    Polish = {'language': 'pl', 'dialect': None}
    Polish_POLAND = {'language': 'pl', 'dialect': 'Poland'}
    Portuguese = {'language': 'pt', 'dialect': None}
    Portuguese_BRAZIL = {'language': 'pt', 'dialect': 'Brazil'}
    Portuguese_BRAZILIAN = {'language': 'pt', 'dialect': 'Brazilian'}
    Portuguese_EUROPEAN = {'language': 'pt', 'dialect': 'European'}
    Portuguese_PORTUGAL = {'language': 'pt', 'dialect': 'Portugal'}
    Punjabi = {'language': 'pa', 'dialect': None}
    Punjabi_GURMUKHI_INDIA = {'language': 'pa', 'dialect': 'Gurmukhi India'}
    Punjabi_INDIA = {'language': 'pa', 'dialect': 'India'}
    Queretaro = {'language': 'oto', 'dialect': None}
    Romanian = {'language': 'ro', 'dialect': None}
    Romanian_ROMANIA = {'language': 'ro', 'dialect': 'Romania'}
    Russian = {'language': 'ru', 'dialect': None}
    Russian_RUSSIA = {'language': 'ru', 'dialect': 'Russia'}
    Samoan = {'language': 'sm', 'dialect': None}
    Scots_Gaelic = {'language': 'gd', 'dialect': None}
    Serbian = {'language': 'sr', 'dialect': None}
    Serbian_SERBIA = {'language': 'sr', 'dialect': 'Serbia'}
    Sesotho = {'language': 'st', 'dialect': None}
    Shona = {'language': 'sn', 'dialect': None}
    Sindhi = {'language': 'sd', 'dialect': None}
    Sinhala = {'language': 'si', 'dialect': None}
    Sinhala_SRI_LANKA = {'language': 'si', 'dialect': 'Sri Lanka'}
    Slovak = {'language': 'sk', 'dialect': None}
    Slovak_SLOVAKIA = {'language': 'sk', 'dialect': 'Slovakia'}
    Slovenian = {'language': 'sl', 'dialect': None}
    Slovenian_SLOVENIA = {'language': 'sl', 'dialect': 'Slovenia'}
    Somali = {'language': 'so', 'dialect': None}
    Somali_SOMALIA = {'language': 'so', 'dialect': 'Somalia'}
    Spanish = {'language': 'es', 'dialect': None}
    Spanish_ARGENTINA = {'language': 'es', 'dialect': 'Argentina'}
    Spanish_BOLIVIA = {'language': 'es', 'dialect': 'Bolivia'}
    Spanish_CHILE = {'language': 'es', 'dialect': 'Chile'}
    Spanish_COLOMBIA = {'language': 'es', 'dialect': 'Colombia'}
    Spanish_COSTA_RICA = {'language': 'es', 'dialect': 'Costa Rica'}
    Spanish_CUBA = {'language': 'es', 'dialect': 'Cuba'}
    Spanish_DOMINICAN_REPUBLIC = {'language': 'es', 'dialect': 'Dominican Republic'}
    Spanish_ECUADOR = {'language': 'es', 'dialect': 'Ecuador'}
    Spanish_EL_SALVADOR = {'language': 'es', 'dialect': 'El Salvador'}
    Spanish_EQUATORIAL_GUINEA = {'language': 'es', 'dialect': 'Equatorial Guinea'}
    Spanish_EUROPEAN = {'language': 'es', 'dialect': 'European'}
    Spanish_GUATEMALA = {'language': 'es', 'dialect': 'Guatemala'}
    Spanish_HONDURAS = {'language': 'es', 'dialect': 'Honduras'}
    Spanish_MEXICAN = {'language': 'es', 'dialect': 'Mexican'}
    Spanish_MEXICO = {'language': 'es', 'dialect': 'Mexico'}
    Spanish_NICARAGUA = {'language': 'es', 'dialect': 'Nicaragua'}
    Spanish_PANAMA = {'language': 'es', 'dialect': 'Panama'}
    Spanish_PARAGUAY = {'language': 'es', 'dialect': 'Paraguay'}
    Spanish_PERU = {'language': 'es', 'dialect': 'Peru'}
    Spanish_PUERTO_RICO = {'language': 'es', 'dialect': 'Puerto Rico'}
    Spanish_SPAIN = {'language': 'es', 'dialect': 'Spain'}
    Spanish_UNITED_STATES = {'language': 'es', 'dialect': 'United States'}
    Spanish_URUGUAY = {'language': 'es', 'dialect': 'Uruguay'}
    Spanish_VENEZUELA = {'language': 'es', 'dialect': 'Venezuela'}
    Sundanese = {'language': 'su', 'dialect': None}
    Sundanese_INDONESIA = {'language': 'su', 'dialect': 'Indonesia'}
    Swahili = {'language': 'sw', 'dialect': None}
    Swahili_KENYA = {'language': 'sw', 'dialect': 'Kenya'}
    Swahili_TANZANIA = {'language': 'sw', 'dialect': 'Tanzania'}
    Swedish = {'language': 'sv', 'dialect': None}
    Swedish_SWEDEN = {'language': 'sv', 'dialect': 'Sweden'}
    Tagalog = {'language': 'tl', 'dialect': None}
    Tahitian = {'language': 'ty', 'dialect': None}
    Tajik = {'language': 'tg', 'dialect': None}
    Tamil = {'language': 'ta', 'dialect': None}
    Tamil_INDIA = {'language': 'ta', 'dialect': 'India'}
    Tamil_MALAYSIA = {'language': 'ta', 'dialect': 'Malaysia'}
    Tamil_SINGAPORE = {'language': 'ta', 'dialect': 'Singapore'}
    Tamil_SRI_LANKA = {'language': 'ta', 'dialect': 'Sri Lanka'}
    Tatar = {'language': 'tt', 'dialect': None}
    Telugu = {'language': 'te', 'dialect': None}
    Telugu_INDIA = {'language': 'te', 'dialect': 'India'}
    Thai = {'language': 'th', 'dialect': None}
    Thai_THAILAND = {'language': 'th', 'dialect': 'Thailand'}
    Tibetan = {'language': 'bo', 'dialect': None}
    Tigrinya = {'language': 'tir', 'dialect': None}
    Tongan = {'language': 'to', 'dialect': None}
    Turkish = {'language': 'tr', 'dialect': None}
    Turkish_TURKEY = {'language': 'tr', 'dialect': 'Turkey'}
    Turkmen = {'language': 'tk', 'dialect': None}
    Ukrainian = {'language': 'ukr', 'dialect': None}
    Ukrainian_UKRAINE = {'language': 'ukr', 'dialect': 'Ukraine'}
    Urdu = {'language': 'ur', 'dialect': None}
    Urdu_INDIA = {'language': 'ur', 'dialect': 'India'}
    Urdu_PAKISTAN = {'language': 'ur', 'dialect': 'Pakistan'}
    Uyghur = {'language': 'ug', 'dialect': None}
    Uzbek = {'language': 'uz', 'dialect': None}
    Uzbek_UZBEKISTAN = {'language': 'uz', 'dialect': 'Uzbekistan'}
    Vietnamese = {'language': 'vi', 'dialect': None}
    Vietnamese_VIETNAM = {'language': 'vi', 'dialect': 'Vietnam'}
    Welsh = {'language': 'cy', 'dialect': None}
    Xhosa = {'language': 'xh', 'dialect': None}
    Yiddish = {'language': 'yi', 'dialect': None}
    Yoruba = {'language': 'yo', 'dialect': None}
    Yucatec = {'language': 'yua', 'dialect': None}
    Zulu = {'language': 'zu', 'dialect': None}

#Function = populate_function_enum()
#License = populate_license_enum()
#Language = populate_language_enum()


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
