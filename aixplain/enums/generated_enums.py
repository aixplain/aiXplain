# This is an auto generated module. PLEASE DO NOT EDIT
# This module contains static enums that were previously loaded dynamically

from enum import Enum
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from aixplain.base.parameters import BaseParameters, Parameter

# Function enum with static values
class Function(str, Enum):
    IMAGE_AND_VIDEO_ANALYSIS = "image-and-video-analysis"
    SELECT_SUPPLIER_FOR_TRANSLATION = "select-supplier-for-translation"
    OBJECT_DETECTION = "object-detection"
    LANGUAGE_IDENTIFICATION = "language-identification"
    VISEME_GENERATION = "viseme-generation"
    IMAGE_LABEL_DETECTION = "image-label-detection"
    OFFENSIVE_LANGUAGE_IDENTIFICATION = "offensive-language-identification"
    ACTIVITY_DETECTION = "activity-detection"
    DEPTH_ESTIMATION = "depth-estimation"
    SCRIPT_EXECUTION = "script-execution"
    TEXT_DETECTION = "text-detection"
    AUDIO_SOURCE_SEPARATION = "audio-source-separation"
    IMAGE_IMPAINTING = "image-impainting"
    MULTI_CLASS_TEXT_CLASSIFICATION = "multi-class-text-classification"
    STYLE_TRANSFER = "style-transfer"
    IMAGE_COLORIZATION = "image-colorization"
    KEYWORD_EXTRACTION = "keyword-extraction"
    INTENT_CLASSIFICATION = "intent-classification"
    SCENE_DETECTION = "scene-detection"
    TRANSLATION = "translation"
    AUDIO_INTENT_DETECTION = "audio-intent-detection"
    ZERO_SHOT_CLASSIFICATION = "zero-shot-classification"
    OCR = "ocr"
    INTENT_RECOGNITION = "intent-recognition"
    UTILITIES = "utilities"
    VIDEO_EMBEDDING = "video-embedding"
    EXPRESSION_DETECTION = "expression-detection"
    EXTRACT_AUDIO_FROM_VIDEO = "extract-audio-from-video"
    IMAGE_CAPTIONING = "image-captioning"
    IMAGE_ANALYSIS = "image-analysis"
    INSTANCE_SEGMENTATION = "instance-segmentation"
    BENCHMARK_SCORING_MT = "benchmark-scoring-mt"
    SPEAKER_DIARIZATION_AUDIO = "speaker-diarization-audio"
    SPEAKER_DIARIZATION_VIDEO = "speaker-diarization-video"
    AUDIO_TRANSCRIPT_IMPROVEMENT = "audio-transcript-improvement"
    CONNECTION = "connection"
    CONNECTOR = "connector"
    BENCHMARK_SCORING_ASR = "benchmark-scoring-asr"
    SENTIMENT_ANALYSIS = "sentiment-analysis"
    METRIC_AGGREGATION = "metric-aggregation"
    TOPIC_MODELING = "topic-modeling"
    SUBTITLING = "subtitling"
    TEXT_GENERATION_METRIC_DEFAULT = "text-generation-metric-default"
    VISUAL_QUESTION_ANSWERING = "visual-question-answering"
    TEXT_GENERATION = "text-generation"
    DOCUMENT_IMAGE_PARSING = "document-image-parsing"
    SPEECH_RECOGNITION = "speech-recognition"
    TEXT_RECONSTRUCTION = "text-reconstruction"
    MULTI_LABEL_TEXT_CLASSIFICATION = "multi-label-text-classification"
    MULTILINGUAL_SPEECH_RECOGNITION = "multilingual-speech-recognition"
    VIDEO_CONTENT_MODERATION = "video-content-moderation"
    AUDIO_EMOTION_DETECTION = "audio-emotion-detection"
    KEYWORD_SPOTTING = "keyword-spotting"
    NAMED_ENTITY_RECOGNITION = "named-entity-recognition"
    SPLIT_ON_SILENCE = "split-on-silence"
    DOCUMENT_INFORMATION_EXTRACTION = "document-information-extraction"
    TEXT_TO_VIDEO_GENERATION = "text-to-video-generation"
    VIDEO_GENERATION = "video-generation"
    TEXT_TO_IMAGE_GENERATION = "text-to-image-generation"
    DIALECT_DETECTION = "dialect-detection"
    SPEAKER_RECOGNITION = "speaker-recognition"
    SYNTAX_ANALYSIS = "syntax-analysis"
    QUESTION_ANSWERING = "question-answering"
    PARAPHRASING = "paraphrasing"
    REFERENCELESS_TEXT_GENERATION_METRIC = "referenceless-text-generation-metric"
    DETECT_LANGUAGE_FROM_TEXT = "detect-language-from-text"
    AUDIO_LANGUAGE_IDENTIFICATION = "audio-language-identification"
    BASE_MODEL = "base-model"
    LANGUAGE_IDENTIFICATION_AUDIO = "language-identification-audio"
    MULTI_CLASS_IMAGE_CLASSIFICATION = "multi-class-image-classification"
    SEMANTIC_SEGMENTATION = "semantic-segmentation"
    EMOTION_DETECTION = "emotion-detection"
    IMAGE_CONTENT_MODERATION = "image-content-moderation"
    AUDIO_GENERATION_METRIC = "audio-generation-metric"
    AUTO_MASK_GENERATION = "auto-mask-generation"
    FACT_CHECKING = "fact-checking"
    TEXT_TO_AUDIO = "text-to-audio"
    TABLE_QUESTION_ANSWERING = "table-question-answering"
    CLASSIFICATION_METRIC = "classification-metric"
    TEXT_GENERATION_METRIC = "text-generation-metric"
    ASR_GENDER_CLASSIFICATION = "asr-gender-classification"
    ENTITY_LINKING = "entity-linking"
    REFERENCELESS_TEXT_GENERATION_METRIC_DEFAULT = "referenceless-text-generation-metric-default"
    PART_OF_SPEECH_TAGGING = "part-of-speech-tagging"
    FILL_TEXT_MASK = "fill-text-mask"
    TEXT_EMBEDDING = "text-embedding"
    OTHER_MULTIPURPOSE = "other-(multipurpose)"
    VIDEO_LABEL_DETECTION = "video-label-detection"
    NOISE_REMOVAL = "noise-removal"
    IMAGE_EMBEDDING = "image-embedding"
    INVERSE_TEXT_NORMALIZATION = "inverse-text-normalization"
    VOICE_CLONING = "voice-cloning"
    IMAGE_TO_VIDEO_GENERATION = "image-to-video-generation"
    FACIAL_RECOGNITION = "facial-recognition"
    LOGLIKELIHOOD = "loglikelihood"
    SPEECH_CLASSIFICATION = "speech-classification"
    SPEECH_SYNTHESIS = "speech-synthesis"
    SUMMARIZATION = "summarization"
    AUDIO_TRANSCRIPT_ANALYSIS = "audio-transcript-analysis"
    TOPIC_CLASSIFICATION = "topic-classification"
    SPEECH_EMBEDDING = "speech-embedding"
    VIDEO_FORCED_ALIGNMENT = "video-forced-alignment"
    SUBTITLING_TRANSLATION = "subtitling-translation"
    TEXT_SPAM_DETECTION = "text-spam-detection"
    VIDEO_UNDERSTANDING = "video-understanding"
    TEXT_DENORMALIZATION = "text-denormalization"
    SPEECH_NON_SPEECH_CLASSIFICATION = "speech-non-speech-classification"
    AUDIO_RECONSTRUCTION = "audio-reconstruction"
    AUDIO_FORCED_ALIGNMENT = "audio-forced-alignment"
    DIACRITIZATION = "diacritization"
    REFERENCELESS_AUDIO_GENERATION_METRIC = "referenceless-audio-generation-metric"
    VOICE_ACTIVITY_DETECTION = "voice-activity-detection"
    TOKEN_CLASSIFICATION = "token-classification"
    SPEECH_TRANSLATION = "speech-translation"
    SPLIT_ON_LINEBREAK = "split-on-linebreak"
    TEXT_CLASSIFICATION = "text-classification"
    TEXT_SUMMARIZATION = "text-summarization"
    ASR_QUALITY_ESTIMATION = "asr-quality-estimation"
    SEARCH = "search"
    ASR_AGE_CLASSIFICATION = "asr-age-classification"
    TEXT_SEGMENATION = "text-segmenation"
    IMAGE_MANIPULATION = "image-manipulation"
    IMAGE_COMPRESSION = "image-compression"
    TEXT_CONTENT_MODERATION = "text-content-moderation"
    ENTITY_SENTIMENT_ANALYSIS = "entity-sentiment-analysis"
    TEXT_NORMALIZATION = "text-normalization"
    GUARDRAILS = "guardrails"

    def get_input_output_params(self) -> Tuple[Dict, Dict]:
        """Gets the input and output parameters for this function

        Returns:
            Tuple[Dict, Dict]: A tuple containing (input_params, output_params)
        """
        function_io = FunctionInputOutput.get(self.value, None)
        if function_io is None:
            return {}, {}
        input_params = {
            param["code"]: param for param in function_io["spec"]["params"]
        }
        output_params = {
            param["code"]: param for param in function_io["spec"]["output"]
        }
        return input_params, output_params

    def get_parameters(self) -> "FunctionParameters":
        """Gets a FunctionParameters object for this function

        Returns:
            FunctionParameters: Object containing the function's parameters
        """
        if not hasattr(self, '_parameters') or self._parameters is None:
            input_params, _ = self.get_input_output_params()
            self._parameters = FunctionParameters(input_params)
        return self._parameters

# Static FunctionInputOutput dictionary
FunctionInputOutput = {
    "image-and-video-analysis": {
        "input": { "image" },
        "output": { "label" },
        "spec": {
            "id": "image-and-video-analysis",
            "name": "Image and Video Analysis",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "select-supplier-for-translation": {
        "input": { "label", "text" },
        "output": { "label" },
        "spec": {
            "id": "select-supplier-for-translation",
            "name": "Select Supplier For Translation",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "object-detection": {
        "input": { "image" },
        "output": { "label" },
        "spec": {
            "id": "object-detection",
            "name": "Object Detection",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "language-identification": {
        "input": { "text" },
        "output": { "label" },
        "spec": {
            "id": "language-identification",
            "name": "Language Identification",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "viseme-generation": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "viseme-generation",
            "name": "Viseme Generation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "image-label-detection": {
        "input": { "image",  },
        "output": { "label" },
        "spec": {
            "id": "image-label-detection",
            "name": "Image Label Detection",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "min_confidence",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0.5', 'label': '0.5'}],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "offensive-language-identification": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "offensive-language-identification",
            "name": "Offensive Language Identification",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "activity-detection": {
        "input": { "image" },
        "output": { "label" },
        "spec": {
            "id": "activity-detection",
            "name": "Activity Detection",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "depth-estimation": {
        "input": { "label",  },
        "output": { "text" },
        "spec": {
            "id": "depth-estimation",
            "name": "Depth Estimation",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "script-execution": {
        "input": { "text" },
        "output": { "text" },
        "spec": {
            "id": "script-execution",
            "name": "Script Execution",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "text-detection": {
        "input": { "image" },
        "output": { "text" },
        "spec": {
            "id": "text-detection",
            "name": "Text Detection",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "audio-source-separation": {
        "input": { "audio" },
        "output": { "audio" },
        "spec": {
            "id": "audio-source-separation",
            "name": "Audio Source Separation",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": []
                }            ]
        }
    },    "image-impainting": {
        "input": {  },
        "output": { "image" },
        "spec": {
            "id": "image-impainting",
            "name": "Image Impainting",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "image",
                    "dataType": "image",
                    "defaultValue": None
                }            ]
        }
    },    "multi-class-text-classification": {
        "input": { "label",  },
        "output": { "label" },
        "spec": {
            "id": "multi-class-text-classification",
            "name": "Multi Class Text Classification",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "style-transfer": {
        "input": {  },
        "output": { "image" },
        "spec": {
            "id": "style-transfer",
            "name": "Style Transfer",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "image",
                    "dataType": "image",
                    "defaultValue": None
                }            ]
        }
    },    "image-colorization": {
        "input": {  },
        "output": { "image" },
        "spec": {
            "id": "image-colorization",
            "name": "Image Colorization",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "image",
                    "dataType": "image",
                    "defaultValue": None
                }            ]
        }
    },    "keyword-extraction": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "keyword-extraction",
            "name": "Keyword Extraction",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "intent-classification": {
        "input": { "label",  },
        "output": { "label" },
        "spec": {
            "id": "intent-classification",
            "name": "Intent Classification",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "scene-detection": {
        "input": { "image" },
        "output": { "label" },
        "spec": {
            "id": "scene-detection",
            "name": "Scene Detection",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "translation": {
        "input": { "text", "label", "label",  },
        "output": { "text" },
        "spec": {
            "id": "translation",
            "name": "Translation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "sourcelanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "targetlanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script_out",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect_out",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "context",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": True
                }            ]
        }
    },    "audio-intent-detection": {
        "input": {  },
        "output": { "label" },
        "spec": {
            "id": "audio-intent-detection",
            "name": "Audio Intent Detection",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "zero-shot-classification": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "zero-shot-classification",
            "name": "Zero-Shot Classification",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "ocr": {
        "input": { "image", "text" },
        "output": { "text" },
        "spec": {
            "id": "ocr",
            "name": "OCR",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "featuretypes",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "intent-recognition": {
        "input": { "audio", "label",  },
        "output": { "label" },
        "spec": {
            "id": "intent-recognition",
            "name": "Intent Recognition",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "utilities": {
        "input": { "text" },
        "output": { "text" },
        "spec": {
            "id": "utilities",
            "name": "Utilites",
            "description": "",
            "params": [
                {
                    "code": "inputs",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "outputs",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "video-embedding": {
        "input": { "label",  },
        "output": { "embedding" },
        "spec": {
            "id": "video-embedding",
            "name": "Video Embedding",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "video",
                    "dataType": "video",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "embedding",
                    "defaultValue": None
                }            ]
        }
    },    "expression-detection": {
        "input": { "image" },
        "output": { "label" },
        "spec": {
            "id": "expression-detection",
            "name": "Expression Detection",
            "description": "",
            "params": [
                {
                    "code": "media",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "extract-audio-from-video": {
        "input": { "video" },
        "output": { "audio" },
        "spec": {
            "id": "extract-audio-from-video",
            "name": "Extract Audio From Video",
            "description": "",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": None
                }            ]
        }
    },    "image-captioning": {
        "input": { "image" },
        "output": { "text" },
        "spec": {
            "id": "image-captioning",
            "name": "Image Captioning",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "image-analysis": {
        "input": { "image" },
        "output": { "label" },
        "spec": {
            "id": "image-analysis",
            "name": "Image Analysis",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "instance-segmentation": {
        "input": {  },
        "output": { "label" },
        "spec": {
            "id": "instance-segmentation",
            "name": "Instance Segmentation",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "benchmark-scoring-mt": {
        "input": { "text", "text", "text" },
        "output": { "label" },
        "spec": {
            "id": "benchmark-scoring-mt",
            "name": "Benchmark Scoring MT",
            "description": "",
            "params": [
                {
                    "code": "input",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "speaker-diarization-audio": {
        "input": { "audio",  },
        "output": { "label" },
        "spec": {
            "id": "speaker-diarization-audio",
            "name": "Speaker Diarization Audio",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "speaker-diarization-video": {
        "input": { "video",  },
        "output": { "video" },
        "spec": {
            "id": "speaker-diarization-video",
            "name": "Speaker Diarization Video",
            "description": "",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "video",
                    "defaultValue": []
                }            ]
        }
    },    "audio-transcript-improvement": {
        "input": { "label", "text", "audio",  },
        "output": { "text" },
        "spec": {
            "id": "audio-transcript-improvement",
            "name": "Audio Transcript Improvement",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "source_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                },                {
                    "code": "is_medical",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                },                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "connection": {
        "input": { "text" },
        "output": { "text" },
        "spec": {
            "id": "connection",
            "name": "Connection",
            "description": "",
            "params": [
                {
                    "code": "name",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "connector": {
        "input": { "text" },
        "output": { "text" },
        "spec": {
            "id": "connector",
            "name": "Connector",
            "description": "",
            "params": [
                {
                    "code": "name",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "benchmark-scoring-asr": {
        "input": { "audio", "text", "text" },
        "output": { "label" },
        "spec": {
            "id": "benchmark-scoring-asr",
            "name": "Benchmark Scoring ASR",
            "description": "",
            "params": [
                {
                    "code": "input",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "sentiment-analysis": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "sentiment-analysis",
            "name": "Sentiment Analysis",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "metric-aggregation": {
        "input": { "text" },
        "output": { "text" },
        "spec": {
            "id": "metric-aggregation",
            "name": "Metric Aggregation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "topic-modeling": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "topic-modeling",
            "name": "Topic Modeling",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "subtitling": {
        "input": { "audio", "label",  },
        "output": { "text" },
        "spec": {
            "id": "subtitling",
            "name": "Subtitling",
            "description": "",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "sourcelanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                },                {
                    "code": "dialect_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                },                {
                    "code": "source_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': 'aws', 'label': 'AWS'}],
                    "isFixed": False
                },                {
                    "code": "target_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "targetlanguages",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "text-generation-metric-default": {
        "input": { "text", "text" },
        "output": { "text" },
        "spec": {
            "id": "text-generation-metric-default",
            "name": "Text Generation Metric Default",
            "description": "",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "references",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "visual-question-answering": {
        "input": { "text", "label",  },
        "output": { "text" },
        "spec": {
            "id": "visual-question-answering",
            "name": "Visual Question Answering",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "text-generation": {
        "input": { "text",  },
        "output": { "text" },
        "spec": {
            "id": "text-generation",
            "name": "Text Generation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "temperature",
                    "dataType": "number",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "prompt",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "context",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "document-image-parsing": {
        "input": {  },
        "output": { "text" },
        "spec": {
            "id": "document-image-parsing",
            "name": "Document Image Parsing",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "speech-recognition": {
        "input": { "label", "audio",  },
        "output": { "text" },
        "spec": {
            "id": "speech-recognition",
            "name": "Speech Recognition",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "voice",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "text-reconstruction": {
        "input": { "text" },
        "output": { "text" },
        "spec": {
            "id": "text-reconstruction",
            "name": "Text Reconstruction",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "multi-label-text-classification": {
        "input": { "label",  },
        "output": { "label" },
        "spec": {
            "id": "multi-label-text-classification",
            "name": "Multi Label Text Classification",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "multilingual-speech-recognition": {
        "input": { "audio",  },
        "output": { "text" },
        "spec": {
            "id": "multilingual-speech-recognition",
            "name": "Multilingual Speech Recognition",
            "description": "",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "video-content-moderation": {
        "input": { "video",  },
        "output": { "label" },
        "spec": {
            "id": "video-content-moderation",
            "name": "Video Content Moderation",
            "description": "",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "min_confidence",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0.5', 'label': '0.5'}],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "audio-emotion-detection": {
        "input": {  },
        "output": { "label" },
        "spec": {
            "id": "audio-emotion-detection",
            "name": "Audio Emotion Detection",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "keyword-spotting": {
        "input": {  },
        "output": { "label" },
        "spec": {
            "id": "keyword-spotting",
            "name": "Keyword Spotting",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "named-entity-recognition": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "named-entity-recognition",
            "name": "Named Entity Recognition",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "domain",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "split-on-silence": {
        "input": { "audio" },
        "output": { "audio" },
        "spec": {
            "id": "split-on-silence",
            "name": "Split On Silence",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": []
                }            ]
        }
    },    "document-information-extraction": {
        "input": {  },
        "output": { "text" },
        "spec": {
            "id": "document-information-extraction",
            "name": "Document Information Extraction",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "text-to-video-generation": {
        "input": { "text",  },
        "output": { "video" },
        "spec": {
            "id": "text-to-video-generation",
            "name": "Text To Video Generation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "video",
                    "defaultValue": None
                }            ]
        }
    },    "video-generation": {
        "input": { "text" },
        "output": { "video" },
        "spec": {
            "id": "video-generation",
            "name": "Video Generation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "video",
                    "defaultValue": []
                }            ]
        }
    },    "text-to-image-generation": {
        "input": { "text" },
        "output": { "image" },
        "spec": {
            "id": "text-to-image-generation",
            "name": "Text To Image Generation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "image",
                    "defaultValue": []
                }            ]
        }
    },    "dialect-detection": {
        "input": { "audio",  },
        "output": { "text" },
        "spec": {
            "id": "dialect-detection",
            "name": "Dialect Detection",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "speaker-recognition": {
        "input": { "audio", "label",  },
        "output": { "label" },
        "spec": {
            "id": "speaker-recognition",
            "name": "Speaker Recognition",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "syntax-analysis": {
        "input": { "text", "text",  },
        "output": { "text" },
        "spec": {
            "id": "syntax-analysis",
            "name": "Syntax Analysis",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "question-answering": {
        "input": { "text", "label" },
        "output": { "text" },
        "spec": {
            "id": "question-answering",
            "name": "Question Answering",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "paraphrasing": {
        "input": { "text", "label" },
        "output": { "text" },
        "spec": {
            "id": "paraphrasing",
            "name": "Paraphrasing",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "referenceless-text-generation-metric": {
        "input": { "text", "text" },
        "output": { "text" },
        "spec": {
            "id": "referenceless-text-generation-metric",
            "name": "Referenceless Text Generation Metric",
            "description": "",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "detect-language-from-text": {
        "input": { "text" },
        "output": { "label" },
        "spec": {
            "id": "detect-language-from-text",
            "name": "Detect Language From Text",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "audio-language-identification": {
        "input": { "audio" },
        "output": { "label" },
        "spec": {
            "id": "audio-language-identification",
            "name": "Audio Language Identification",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "base-model": {
        "input": { "label", "text" },
        "output": { "text" },
        "spec": {
            "id": "base-model",
            "name": "Base-Model",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": True
                }            ]
        }
    },    "language-identification-audio": {
        "input": { "audio" },
        "output": { "label" },
        "spec": {
            "id": "language-identification-audio",
            "name": "Language Identification Audio",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "multi-class-image-classification": {
        "input": {  },
        "output": { "label" },
        "spec": {
            "id": "multi-class-image-classification",
            "name": "Multi Class Image Classification",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "semantic-segmentation": {
        "input": {  },
        "output": { "label" },
        "spec": {
            "id": "semantic-segmentation",
            "name": "Semantic Segmentation",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "emotion-detection": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "emotion-detection",
            "name": "Emotion Detection",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "image-content-moderation": {
        "input": { "image",  },
        "output": { "label" },
        "spec": {
            "id": "image-content-moderation",
            "name": "Image Content Moderation",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "min_confidence",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0.5', 'label': '0.5'}],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "audio-generation-metric": {
        "input": { "audio", "text" },
        "output": { "text" },
        "spec": {
            "id": "audio-generation-metric",
            "name": "Audio Generation Metric",
            "description": "",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "references",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "auto-mask-generation": {
        "input": { "image" },
        "output": { "label" },
        "spec": {
            "id": "auto-mask-generation",
            "name": "Auto Mask Generation",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "fact-checking": {
        "input": { "label",  },
        "output": { "label" },
        "spec": {
            "id": "fact-checking",
            "name": "Fact Checking",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "text-to-audio": {
        "input": { "text",  },
        "output": { "audio" },
        "spec": {
            "id": "text-to-audio",
            "name": "Text to Audio",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": None
                }            ]
        }
    },    "table-question-answering": {
        "input": { "text", "label" },
        "output": { "text" },
        "spec": {
            "id": "table-question-answering",
            "name": "Table Question Answering",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "classification-metric": {
        "input": { "label", "label", "text" },
        "output": { "number" },
        "spec": {
            "id": "classification-metric",
            "name": "Classification Metric",
            "description": "",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "references",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "lowerIsBetter",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "number",
                    "defaultValue": None
                }            ]
        }
    },    "text-generation-metric": {
        "input": { "text", "text" },
        "output": { "text" },
        "spec": {
            "id": "text-generation-metric",
            "name": "Text Generation Metric",
            "description": "",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "references",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "asr-gender-classification": {
        "input": { "audio" },
        "output": { "label" },
        "spec": {
            "id": "asr-gender-classification",
            "name": "ASR Gender Classification",
            "description": "",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "entity-linking": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "entity-linking",
            "name": "Entity Linking",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "domain",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "referenceless-text-generation-metric-default": {
        "input": { "text", "text" },
        "output": { "text" },
        "spec": {
            "id": "referenceless-text-generation-metric-default",
            "name": "Referenceless Text Generation Metric Default",
            "description": "",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "part-of-speech-tagging": {
        "input": { "label",  },
        "output": { "label" },
        "spec": {
            "id": "part-of-speech-tagging",
            "name": "Part of Speech Tagging",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "fill-text-mask": {
        "input": { "text", "label",  },
        "output": { "text" },
        "spec": {
            "id": "fill-text-mask",
            "name": "Fill Text Mask",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "text-embedding": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "text-embedding",
            "name": "Text Embedding",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "other-(multipurpose)": {
        "input": { "text", "label" },
        "output": { "text" },
        "spec": {
            "id": "other-(multipurpose)",
            "name": "Other (Multipurpose)",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "video-label-detection": {
        "input": { "video",  },
        "output": { "label" },
        "spec": {
            "id": "video-label-detection",
            "name": "Video Label Detection",
            "description": "",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "min_confidence",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0.5', 'label': '0.5'}],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "noise-removal": {
        "input": {  },
        "output": { "audio" },
        "spec": {
            "id": "noise-removal",
            "name": "Noise Removal",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": None
                }            ]
        }
    },    "image-embedding": {
        "input": { "label",  },
        "output": { "text" },
        "spec": {
            "id": "image-embedding",
            "name": "Image Embedding",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "inverse-text-normalization": {
        "input": {  },
        "output": { "label" },
        "spec": {
            "id": "inverse-text-normalization",
            "name": "Inverse Text Normalization",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": None
                }            ]
        }
    },    "voice-cloning": {
        "input": { "text", "audio", "label",  },
        "output": { "audio" },
        "spec": {
            "id": "voice-cloning",
            "name": "Voice Cloning",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "voice",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "type",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": []
                }            ]
        }
    },    "image-to-video-generation": {
        "input": { "label",  },
        "output": { "video" },
        "spec": {
            "id": "image-to-video-generation",
            "name": "Image To Video Generation",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "video",
                    "defaultValue": None
                }            ]
        }
    },    "facial-recognition": {
        "input": { "video" },
        "output": { "label" },
        "spec": {
            "id": "facial-recognition",
            "name": "Facial Recognition",
            "description": "",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "loglikelihood": {
        "input": { "text" },
        "output": { "number" },
        "spec": {
            "id": "loglikelihood",
            "name": "Log Likelihood",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "number",
                    "defaultValue": []
                }            ]
        }
    },    "speech-classification": {
        "input": { "audio", "label",  },
        "output": { "label" },
        "spec": {
            "id": "speech-classification",
            "name": "Speech Classification",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "speech-synthesis": {
        "input": { "label", "text",  },
        "output": { "audio" },
        "spec": {
            "id": "speech-synthesis",
            "name": "Speech Synthesis",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "voice",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "type",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": []
                }            ]
        }
    },    "summarization": {
        "input": { "text", "label",  },
        "output": { "text" },
        "spec": {
            "id": "summarization",
            "name": "Summarization",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "audio-transcript-analysis": {
        "input": { "label", "audio",  },
        "output": { "text" },
        "spec": {
            "id": "audio-transcript-analysis",
            "name": "Audio Transcript Analysis",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "source_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "topic-classification": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "topic-classification",
            "name": "Topic Classification",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "speech-embedding": {
        "input": { "audio", "label",  },
        "output": { "text" },
        "spec": {
            "id": "speech-embedding",
            "name": "Speech Embedding",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "video-forced-alignment": {
        "input": { "video", "text", "label",  },
        "output": { "text", "video" },
        "spec": {
            "id": "video-forced-alignment",
            "name": "Video Forced Alignment",
            "description": "",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "text",
                    "dataType": "text",
                    "defaultValue": []
                },                {
                    "code": "video",
                    "dataType": "video",
                    "defaultValue": []
                }            ]
        }
    },    "subtitling-translation": {
        "input": { "text", "label",  },
        "output": { "text" },
        "spec": {
            "id": "subtitling-translation",
            "name": "Subtitling Translation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "sourcelanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                },                {
                    "code": "dialect_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                },                {
                    "code": "target_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "targetlanguages",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "text-spam-detection": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "text-spam-detection",
            "name": "Text Spam Detection",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "video-understanding": {
        "input": { "video", "text", "label",  },
        "output": { "text" },
        "spec": {
            "id": "video-understanding",
            "name": "Video Understanding",
            "description": "",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "text",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "text-denormalization": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "text-denormalization",
            "name": "Text Denormalization",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                },                {
                    "code": "lowercase_latin",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0', 'label': 'No'}],
                    "isFixed": False
                },                {
                    "code": "remove_accents",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '1', 'label': 'Yes'}],
                    "isFixed": False
                },                {
                    "code": "remove_punctuation",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0', 'label': 'No'}],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "speech-non-speech-classification": {
        "input": { "audio", "label",  },
        "output": { "label" },
        "spec": {
            "id": "speech-non-speech-classification",
            "name": "Speech or Non-Speech Classification",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "audio-reconstruction": {
        "input": { "audio" },
        "output": { "audio" },
        "spec": {
            "id": "audio-reconstruction",
            "name": "Audio Reconstruction",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": []
                }            ]
        }
    },    "audio-forced-alignment": {
        "input": { "audio", "text", "label",  },
        "output": { "text", "audio" },
        "spec": {
            "id": "audio-forced-alignment",
            "name": "Audio Forced Alignment",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "text",
                    "dataType": "text",
                    "defaultValue": []
                },                {
                    "code": "audio",
                    "dataType": "audio",
                    "defaultValue": []
                }            ]
        }
    },    "diacritization": {
        "input": { "label", "label", "text" },
        "output": { "text" },
        "spec": {
            "id": "diacritization",
            "name": "Diacritization",
            "description": "",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "referenceless-audio-generation-metric": {
        "input": { "audio", "text" },
        "output": { "text" },
        "spec": {
            "id": "referenceless-audio-generation-metric",
            "name": "Referenceless Audio Generation Metric",
            "description": "",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "sources",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": None
                }            ]
        }
    },    "voice-activity-detection": {
        "input": { "audio",  },
        "output": { "audio" },
        "spec": {
            "id": "voice-activity-detection",
            "name": "Voice Activity Detection",
            "description": "",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "onset",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0.5', 'label': '0.5'}],
                    "isFixed": False
                },                {
                    "code": "offset",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0.5', 'label': '0.5'}],
                    "isFixed": False
                },                {
                    "code": "min_duration_on",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '1', 'label': '1'}],
                    "isFixed": False
                },                {
                    "code": "min_duration_off",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '0.5', 'label': '0.5'}],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "audio",
                    "defaultValue": []
                }            ]
        }
    },    "token-classification": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "token-classification",
            "name": "Token Classification",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "speech-translation": {
        "input": { "audio", "label", "label",  },
        "output": { "text" },
        "spec": {
            "id": "speech-translation",
            "name": "Speech Translation",
            "description": "",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "sourcelanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "targetlanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "voice",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "split-on-linebreak": {
        "input": { "text" },
        "output": { "text" },
        "spec": {
            "id": "split-on-linebreak",
            "name": "Split On Linebreak",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "text-classification": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "text-classification",
            "name": "Text Classification",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "text-summarization": {
        "input": { "text", "label",  },
        "output": { "text" },
        "spec": {
            "id": "text-summarization",
            "name": "Text summarization",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "asr-quality-estimation": {
        "input": { "text",  },
        "output": { "label" },
        "spec": {
            "id": "asr-quality-estimation",
            "name": "ASR Quality Estimation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "search": {
        "input": { "text" },
        "output": { "text" },
        "spec": {
            "id": "search",
            "name": "Search",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "asr-age-classification": {
        "input": { "audio" },
        "output": { "label" },
        "spec": {
            "id": "asr-age-classification",
            "name": "ASR Age Classification",
            "description": "",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "text-segmenation": {
        "input": { "text", "label" },
        "output": { "text" },
        "spec": {
            "id": "text-segmenation",
            "name": "Text Segmentation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "text",
                    "defaultValue": []
                }            ]
        }
    },    "image-manipulation": {
        "input": { "image", "image" },
        "output": { "image" },
        "spec": {
            "id": "image-manipulation",
            "name": "Image Manipulation",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "targetimage",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "image",
                    "dataType": "image",
                    "defaultValue": []
                }            ]
        }
    },    "image-compression": {
        "input": { "image",  },
        "output": { "image" },
        "spec": {
            "id": "image-compression",
            "name": "Image Compression",
            "description": "",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "apl_qfactor",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{'value': '80', 'label': '80'}],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "image",
                    "dataType": "image",
                    "defaultValue": []
                }            ]
        }
    },    "text-content-moderation": {
        "input": { "text", "label",  },
        "output": { "label" },
        "spec": {
            "id": "text-content-moderation",
            "name": "Text Content Moderation",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                },                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "entity-sentiment-analysis": {
        "input": { "text" },
        "output": { "label" },
        "spec": {
            "id": "entity-sentiment-analysis",
            "name": "Entity Sentiment Analysis",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "text-normalization": {
        "input": { "text",  },
        "output": { "label" },
        "spec": {
            "id": "text-normalization",
            "name": "Text Normalization",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False
                },                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True
                },                {
                    "code": "settings",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    },    "guardrails": {
        "input": { "text" },
        "output": { "label" },
        "spec": {
            "id": "guardrails",
            "name": "Guardrails",
            "description": "",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False
                }            ],
            "output": [
                {
                    "code": "data",
                    "dataType": "label",
                    "defaultValue": []
                }            ]
        }
    }}

class FunctionParameters(BaseParameters):
    """Class to store and manage function parameters"""

    def __init__(self, input_params: Dict):
        """Initialize FunctionParameters with input parameters

        Args:
            input_params (Dict): Dictionary of input parameters
        """
        super().__init__()
        for param_code, param_config in input_params.items():
            self.parameters[param_code] = Parameter(
                name=param_code,
                required=param_config.get("required", False),
                value=None,
            )

# Supplier enum with static values
class Supplier(Enum):
    AWS = {"id": "208", "name": "AWS", "code": "aws"}
    RESEMBLEAI = {"id": "274", "name": "Resemble AI", "code": "resembleai"}
    HUGGINGFACE = {"id": "214", "name": "HuggingFace", "code": "huggingface"}
    NVIDIA = {"id": "219", "name": "Nvidia", "code": "nvidia"}
    REVAI = {"id": "224", "name": "RevAI", "code": "revai"}
    SCALESERP = {"id": "259", "name": "Scale SERP", "code": "scaleserp"}
    UNIVERSITYOFHELSINKI = {"id": "229", "name": "University of Helsinki", "code": "universityofhelsinki"}
    CORE42 = {"id": "271", "name": "Core42", "code": "core42"}
    SDAIA = {"id": "272", "name": "SDAIA", "code": "sdaia"}
    PLAYHT = {"id": "273", "name": "PlayHT", "code": "playht"}
    MISTRALAI = {"id": "276", "name": "Mistral AI", "code": "mistralai"}
    GROQ = {"id": "258", "name": "Groq", "code": "groq"}
    KATEB = {"id": "215", "name": "Kateb", "code": "kateb"}
    AZURE = {"id": "209", "name": "Microsoft", "code": "azure"}
    OPENAI = {"id": "220", "name": "OpenAI", "code": "openai"}
    SACREBLEU = {"id": "225", "name": "Sacrebleu", "code": "sacrebleu"}
    VUMICHIEN = {"id": "230", "name": "Vumichien", "code": "vumichien"}
    DEEPGRAM = {"id": "235", "name": "Deepgram", "code": "deepgram"}
    EBAY = {"id": "236", "name": "eBay", "code": "ebay"}
    RAMSA = {"id": "240", "name": "Ramsa", "code": "ramsa"}
    SAMBANOVA = {"id": "283", "name": "SambaNova", "code": "sambanova"}
    FIRECRAWL = {"id": "287", "name": "Firecrawl", "code": "firecrawl"}
    CREWAI = {"id": "278", "name": "Crewai", "code": "crewai"}
    BRITISHTELECOM = {"id": "210", "name": "British Telecommunications", "code": "britishtelecom"}
    KLANGOO = {"id": "216", "name": "Klangoo", "code": "klangoo"}
    QCRI = {"id": "239", "name": "QCRI", "code": "qcri"}
    PICOVOICE = {"id": "221", "name": "Picovoice", "code": "picovoice"}
    IBM = {"id": "263", "name": "IBM", "code": "ibm"}
    SAUTECH = {"id": "226", "name": "SauTech", "code": "sautech"}
    YDSHIEH = {"id": "231", "name": "Ydshieh", "code": "ydshieh"}
    OPENWEATHER = {"id": "279", "name": "OpenWeather", "code": "openweather"}
    IDENTV = {"id": "237", "name": "IdenTV", "code": "identv"}
    PANGEANIC = {"id": "238", "name": "Pangeanic", "code": "pangeanic"}
    TAVILY = {"id": "285", "name": "Tavily", "code": "tavily"}
    HUME_AI = {"id": "284", "name": "Hume Ai", "code": "hume-ai"}
    DEEPINFRA = {"id": "288", "name": "Deepinfra", "code": "deepinfra"}
    META = {"id": "211", "name": "Meta", "code": "meta"}
    PURETALKAI = {"id": "222", "name": "Puretalk.ai", "code": "puretalkai"}
    YOURTTS = {"id": "232", "name": "YourTTS", "code": "yourtts"}
    RDI = {"id": "241", "name": "RDI", "code": "rdi"}
    SUKOON = {"id": "242", "name": "Sukoon", "code": "sukoon"}
    STABILITYAI = {"id": "227", "name": "Stability AI", "code": "stabilityai"}
    APLICATA = {"id": "201", "name": "Aplicata", "code": "aplicata"}
    XAI = {"id": "298", "name": "xAI", "code": "xai"}
    GOOGLE = {"id": "212", "name": "Google", "code": "google"}
    _171 = {"id": "171", "name": "Hadi Nasrallah", "code": "171"}
    TOGETHER_AI = {"id": "281", "name": "Together Ai", "code": "together-ai"}
    FIREWORKS_AI = {"id": "282", "name": "Fireworks AI", "code": "fireworks-ai"}
    HOUNDIFY = {"id": "213", "name": "Houndify", "code": "houndify"}
    MODERMT = {"id": "218", "name": "ModernMT", "code": "modermt"}
    PYANNOTE = {"id": "223", "name": "Pyannote", "code": "pyannote"}
    STREAMN = {"id": "228", "name": "StreamN", "code": "streamn"}
    APPTEK_SPACETOON = {"id": "233", "name": "AppTek-SpaceToon", "code": "apptek-spacetoon"}
    TREATMENT = {"id": "243", "name": "Treatment", "code": "treatment"}
    UNBABEL = {"id": "244", "name": "Unbabel", "code": "unbabel"}
    VECTARA = {"id": "255", "name": "Vectara", "code": "vectara"}
    TARJAMA = {"id": "296", "name": "Tarjama", "code": "tarjama"}
    CEREBRAS = {"id": "286", "name": "Cerebras", "code": "cerebras"}
    MARITACA_AI = {"id": "290", "name": "Maritaca AI", "code": "maritaca-ai"}
    LUMA_AI = {"id": "299", "name": "Luma AI", "code": "luma-ai"}
    JINA_AI = {"id": "307", "name": "Jina Ai", "code": "jina-ai"}
    VOYAGE_AI = {"id": "300", "name": "Voyage Ai", "code": "voyage-ai"}
    BAAI = {"id": "317", "name": "Beijing Academy of Artificial Intelligence", "code": "BAAI"}
    CANOPY_LABS = {"id": "314", "name": "Canopy Labs", "code": "canopy-labs"}
    LARA_TRANSLATE = {"id": "327", "name": "Lara Translate", "code": "lara-translate"}
    APPTEK = {"id": "168", "name": "AppTek", "code": "apptek"}
    COHERE = {"id": "301", "name": "Cohere", "code": "cohere"}
    SESAME_AI_LABS = {"id": "315", "name": "Sesame AI Labs", "code": "sesame-ai-labs"}
    GROQ_KSA = {"id": "302", "name": "Groq KSA", "code": "groq-ksa"}
    COMPOSIO = {"id": "316", "name": "Composio", "code": "composio"}
    LAMBDA_AI = {"id": "324", "name": "Lambda Ai", "code": "lambda-ai"}
    AIXPLAIN = {"id": "1", "name": "aixplain", "code": "aixplain"}
    FANAR = {"id": "326", "name": "Fanar", "code": "fanar"}
    PARADIGM_NETWORKS = {"id": "313", "name": "Paradigm Networks", "code": "paradigm-networks"}

    def __str__(self):
        return self.value["name"]

# Language enum with static values
class Language(Enum):
    AFRIKAANS = {"language": "af", "dialect": ""}
    AFRIKAANS_SOUTH_AFRICA = {"language": "af", "dialect": "South Africa"}
    ALBANIAN = {"language": "sq", "dialect": ""}
    ALBANIAN_ALBANIA = {"language": "sq", "dialect": "Albania"}
    ARMENIAN = {"language": "hy", "dialect": ""}
    ARMENIAN_ARMENIA = {"language": "hy", "dialect": "Armenia"}
    ASSAMESE = {"language": "asm", "dialect": ""}
    BANGLA = {"language": "bn", "dialect": ""}
    BANGLA_BANGLADESH = {"language": "bn", "dialect": "Bangladesh"}
    BANGLA_INDIA = {"language": "bn", "dialect": "India"}
    BASQUE = {"language": "eu", "dialect": ""}
    BASQUE_SPAIN = {"language": "eu", "dialect": "Spain"}
    BULGARIAN = {"language": "bg", "dialect": ""}
    BULGARIAN_BULGARY = {"language": "bg", "dialect": "Bulgary"}
    BULGARIAN_BULGARIA = {"language": "bg", "dialect": "Bulgaria"}
    CATALAN = {"language": "ca", "dialect": ""}
    CATALAN_SPAIN = {"language": "ca", "dialect": "Spain"}
    CEBUANO = {"language": "ceb", "dialect": ""}
    CORSICAN = {"language": "co", "dialect": ""}
    CZECH = {"language": "cs", "dialect": ""}
    CZECH_CZECH_REPUBLIC = {"language": "cs", "dialect": "Czech Republic"}
    CZECH_CZECH = {"language": "cs", "dialect": "Czech"}
    DIVEHI = {"language": "dv", "dialect": ""}
    ESPERANTO = {"language": "eo", "dialect": ""}
    ESTONIAN = {"language": "et", "dialect": ""}
    ESTONIAN_ESTONIA = {"language": "et", "dialect": "Estonia"}
    FIJIAN = {"language": "fj", "dialect": ""}
    FINNISH = {"language": "fi", "dialect": ""}
    FINNISH_FINLAND = {"language": "fi", "dialect": "Finland"}
    GERMAN = {"language": "de", "dialect": ""}
    GERMAN_GERMANY = {"language": "de", "dialect": "Germany"}
    GERMAN_AUSTRIA = {"language": "de", "dialect": "Austria"}
    GERMAN_SWITZERLAND = {"language": "de", "dialect": "Switzerland"}
    GREEK = {"language": "el", "dialect": ""}
    GREEK_GREECE = {"language": "el", "dialect": "Greece"}
    HAITIAN = {"language": "ht", "dialect": ""}
    HAUSA = {"language": "ha", "dialect": ""}
    HAWAIIAN = {"language": "haw", "dialect": ""}
    ICELANDIC = {"language": "isl", "dialect": ""}
    IGBO = {"language": "ig", "dialect": ""}
    INDONESIAN = {"language": "id", "dialect": ""}
    INDONESIAN_INDONESIA = {"language": "id", "dialect": "Indonesia"}
    INUKTITUT = {"language": "iu", "dialect": ""}
    IRISH = {"language": "ga", "dialect": ""}
    IRISH_IRELAND = {"language": "ga", "dialect": "Ireland"}
    JAPANESE = {"language": "ja", "dialect": ""}
    JAPANESE_JAPAN = {"language": "ja", "dialect": "Japan"}
    KAZAKH = {"language": "kk", "dialect": ""}
    KAZAKH_KAZAKHSTAN = {"language": "kk", "dialect": "Kazakhstan"}
    KINYARWANDA = {"language": "rw", "dialect": ""}
    KLINGON = {"language": "tlh", "dialect": ""}
    KOREAN = {"language": "ko", "dialect": ""}
    KOREAN_KOREA = {"language": "ko", "dialect": "Korea"}
    KURDISH = {"language": "ku", "dialect": ""}
    KYRGYZ = {"language": "ky", "dialect": ""}
    LUXEMBOURGISH = {"language": "lb", "dialect": ""}
    LUXEMBOURGISH_SOUTH_AFRICA = {"language": "lb", "dialect": "South Africa"}
    MACEDONIAN = {"language": "mk", "dialect": ""}
    MACEDONIAN_NORTH_MACEDONIA = {"language": "mk", "dialect": "North Macedonia"}
    MALTESE = {"language": "mt", "dialect": ""}
    MALTESE_MALTA = {"language": "mt", "dialect": "Malta"}
    MAORI = {"language": "mi", "dialect": ""}
    MONGOLIAN = {"language": "mn", "dialect": ""}
    MONGOLIAN_MONGOLIA = {"language": "mn", "dialect": "Mongolia"}
    AMHARIC = {"language": "am", "dialect": ""}
    AMHARIC_ETHIOPIA = {"language": "am", "dialect": "Ethiopia"}
    ODIA = {"language": "or", "dialect": ""}
    ROMANIAN = {"language": "ro", "dialect": ""}
    ROMANIAN_ROMANIA = {"language": "ro", "dialect": "Romania"}
    ARABIC = {"language": "ar", "dialect": ""}
    ARABIC_CLASSICAL_ARABIC = {"language": "ar", "dialect": "Classical Arabic"}
    ARABIC_UNITED_ARAB_EMIRATES = {"language": "ar", "dialect": "United Arab Emirates"}
    ARABIC_EGYPT = {"language": "ar", "dialect": "Egypt"}
    ARABIC_MOROCCO = {"language": "ar", "dialect": "Morocco"}
    ARABIC_SAUDI_ARABIA = {"language": "ar", "dialect": "Saudi Arabia"}
    ARABIC_MODERN_STANDARD_ARABIC = {"language": "ar", "dialect": "Modern Standard Arabic"}
    ARABIC_QATAR = {"language": "ar", "dialect": "Qatar"}
    ARABIC_IRAQ = {"language": "ar", "dialect": "Iraq"}
    ARABIC_OMAN = {"language": "ar", "dialect": "Oman"}
    ARABIC_TUNISIA = {"language": "ar", "dialect": "Tunisia"}
    ARABIC_YEMEN = {"language": "ar", "dialect": "Yemen"}
    ARABIC_KUWAIT = {"language": "ar", "dialect": "Kuwait"}
    ARABIC_PALESTINE = {"language": "ar", "dialect": "Palestine"}
    ARABIC_ALGERIA = {"language": "ar", "dialect": "Algeria"}
    ARABIC_GULF = {"language": "ar", "dialect": "Gulf"}
    ARABIC_BAHRAIN = {"language": "ar", "dialect": "Bahrain"}
    ARABIC_JORDAN = {"language": "ar", "dialect": "Jordan"}
    ARABIC_LIBYA = {"language": "ar", "dialect": "Libya"}
    ARABIC_ISRAEL = {"language": "ar", "dialect": "Israel"}
    ARABIC_AUTO_DETECT = {"language": "ar", "dialect": "Auto-Detect"}
    ARABIC_LEBANON = {"language": "ar", "dialect": "Lebanon"}
    ARABIC_SYRIA = {"language": "ar", "dialect": "Syria"}
    AZERBAIJANI = {"language": "az", "dialect": ""}
    AZERBAIJANI_AZERBAIJAN = {"language": "az", "dialect": "Azerbaijan"}
    BASHKIR = {"language": "ba", "dialect": ""}
    BOSNIAN = {"language": "bs", "dialect": ""}
    BOSNIAN_BOSNIA = {"language": "bs", "dialect": "Bosnia"}
    BELARUSIAN = {"language": "be", "dialect": ""}
    BURMESE = {"language": "my", "dialect": ""}
    BURMESE_MYANMAR = {"language": "my", "dialect": "Myanmar"}
    DANISH = {"language": "da", "dialect": ""}
    DANISH_DENMARK = {"language": "da", "dialect": "Denmark"}
    NYANJA = {"language": "ny", "dialect": ""}
    PASHTO = {"language": "ps", "dialect": ""}
    POLISH = {"language": "pl", "dialect": ""}
    POLISH_POLAND = {"language": "pl", "dialect": "Poland"}
    PUNJABI = {"language": "pa", "dialect": ""}
    PUNJABI_INDIA = {"language": "pa", "dialect": "India"}
    PUNJABI_GURMUKHI_INDIA = {"language": "pa", "dialect": "Gurmukhi India"}
    QUERETARO = {"language": "oto", "dialect": ""}
    RUSSIAN = {"language": "ru", "dialect": ""}
    RUSSIAN_RUSSIA = {"language": "ru", "dialect": "Russia"}
    SERBIAN = {"language": "sr", "dialect": ""}
    SERBIAN_SERBIA = {"language": "sr", "dialect": "Serbia"}
    SHONA = {"language": "sn", "dialect": ""}
    SINDHI = {"language": "sd", "dialect": ""}
    SLOVAK = {"language": "sk", "dialect": ""}
    SLOVAK_SLOVAKIA = {"language": "sk", "dialect": "Slovakia"}
    SOMALI = {"language": "so", "dialect": ""}
    SOMALI_SOMALIA = {"language": "so", "dialect": "Somalia"}
    SWAHILI = {"language": "sw", "dialect": ""}
    SWAHILI_KENYA = {"language": "sw", "dialect": "Kenya"}
    SWAHILI_TANZANIA = {"language": "sw", "dialect": "Tanzania"}
    TAGALOG = {"language": "tl", "dialect": ""}
    TAHITIAN = {"language": "ty", "dialect": ""}
    TAJIK = {"language": "tg", "dialect": ""}
    TATAR = {"language": "tt", "dialect": ""}
    TELUGU = {"language": "te", "dialect": ""}
    TELUGU_INDIA = {"language": "te", "dialect": "India"}
    TIBETAN = {"language": "bo", "dialect": ""}
    TONGAN = {"language": "to", "dialect": ""}
    TURKISH = {"language": "tr", "dialect": ""}
    TURKISH_TURKEY = {"language": "tr", "dialect": "Turkey"}
    UZBEK = {"language": "uz", "dialect": ""}
    UZBEK_UZBEKISTAN = {"language": "uz", "dialect": "Uzbekistan"}
    VIETNAMESE = {"language": "vi", "dialect": ""}
    VIETNAMESE_VIETNAM = {"language": "vi", "dialect": "Vietnam"}
    WELSH = {"language": "cy", "dialect": ""}
    XHOSA = {"language": "xh", "dialect": ""}
    YUCATEC = {"language": "yua", "dialect": ""}
    ZULU = {"language": "zu", "dialect": ""}
    PERSIAN = {"language": "fa", "dialect": ""}
    PERSIAN_IRAN = {"language": "fa", "dialect": "Iran"}
    PERSIAN_PERSIAN = {"language": "fa", "dialect": "Persian"}
    PORTUGUESE = {"language": "pt", "dialect": ""}
    PORTUGUESE_PORTUGAL = {"language": "pt", "dialect": "Portugal"}
    PORTUGUESE_BRAZIL = {"language": "pt", "dialect": "Brazil"}
    PORTUGUESE_EUROPEAN = {"language": "pt", "dialect": "European"}
    PORTUGUESE_BRAZILIAN = {"language": "pt", "dialect": "Brazilian"}
    CHINESE = {"language": "zh", "dialect": ""}
    CHINESE_MANDARIN = {"language": "zh", "dialect": "Mandarin"}
    CHINESE_HONG_KONG = {"language": "zh", "dialect": "Hong Kong"}
    CHINESE_TAIWANESE_MANDARIN = {"language": "zh", "dialect": "Taiwanese, Mandarin"}
    CHINESE_TRADITIONAL = {"language": "zh", "dialect": "Traditional"}
    CROATIAN = {"language": "hr", "dialect": ""}
    CROATIAN_CROATIA = {"language": "hr", "dialect": "Croatia"}
    FILIPINO = {"language": "fil", "dialect": ""}
    FILIPINO_PHILIPPINES = {"language": "fil", "dialect": "Philippines"}
    FILIPINO_TAGALOG = {"language": "fil", "dialect": "Tagalog"}
    GUJARATI = {"language": "gu", "dialect": ""}
    GUJARATI_INDIAN = {"language": "gu", "dialect": "Indian"}
    GUJARATI_INDIA = {"language": "gu", "dialect": "India"}
    HMONG = {"language": "hmn", "dialect": ""}
    LATVIAN = {"language": "lv", "dialect": ""}
    LATVIAN_LATVIA = {"language": "lv", "dialect": "Latvia"}
    LITHUANIAN = {"language": "lt", "dialect": ""}
    LITHUANIAN_LITHUANIA = {"language": "lt", "dialect": "Lithuania"}
    UYGHUR = {"language": "ug", "dialect": ""}
    DARI = {"language": "prs", "dialect": ""}
    DUTCH = {"language": "nl", "dialect": ""}
    DUTCH_BELGIUM = {"language": "nl", "dialect": "Belgium"}
    DUTCH_NETHERLANDS = {"language": "nl", "dialect": "Netherlands"}
    ENGLISH = {"language": "en", "dialect": ""}
    ENGLISH_UNITED_STATES = {"language": "en", "dialect": "United States"}
    ENGLISH_UNITED_KINGDOM = {"language": "en", "dialect": "United Kingdom"}
    ENGLISH_INDIA = {"language": "en", "dialect": "India"}
    ENGLISH_WELSH = {"language": "en", "dialect": "Welsh"}
    ENGLISH_AUSTRALIA = {"language": "en", "dialect": "Australia"}
    ENGLISH_NIGERIA = {"language": "en", "dialect": "Nigeria"}
    ENGLISH_NEW_ZEALAND = {"language": "en", "dialect": "New Zealand"}
    ENGLISH_KENYA = {"language": "en", "dialect": "Kenya"}
    ENGLISH_PHILIPPINES = {"language": "en", "dialect": "Philippines"}
    ENGLISH_INDIAN = {"language": "en", "dialect": "Indian"}
    ENGLISH_AUSTRALIAN = {"language": "en", "dialect": "Australian"}
    ENGLISH_HONG_KONG = {"language": "en", "dialect": "Hong Kong"}
    ENGLISH_SOUTH_AFRICA = {"language": "en", "dialect": "South Africa"}
    ENGLISH_GHANA = {"language": "en", "dialect": "Ghana"}
    ENGLISH_SINGAPORE = {"language": "en", "dialect": "Singapore"}
    ENGLISH_IRELAND = {"language": "en", "dialect": "Ireland"}
    ENGLISH_CANADA = {"language": "en", "dialect": "Canada"}
    ENGLISH_TANZANIA = {"language": "en", "dialect": "Tanzania"}
    ENGLISH_SCOTTISH = {"language": "en", "dialect": "Scottish"}
    ENGLISH_PAKISTAN = {"language": "en", "dialect": "Pakistan"}
    FRENCH = {"language": "fr", "dialect": ""}
    FRENCH_CANADA = {"language": "fr", "dialect": "Canada"}
    FRENCH_FRANCE = {"language": "fr", "dialect": "France"}
    FRENCH_SWITZERLAND = {"language": "fr", "dialect": "Switzerland"}
    FRENCH_BELGIUM = {"language": "fr", "dialect": "Belgium"}
    FRENCH_CANADIAN = {"language": "fr", "dialect": "Canadian"}
    GEORGIAN = {"language": "ka", "dialect": ""}
    GEORGIAN_GEORGIA = {"language": "ka", "dialect": "Georgia"}
    GALICIAN = {"language": "gl", "dialect": ""}
    GALICIAN_SPAIN = {"language": "gl", "dialect": "Spain"}
    FRISIAN = {"language": "fy", "dialect": ""}
    HEBREW = {"language": "he", "dialect": ""}
    HEBREW_ISRAEL = {"language": "he", "dialect": "Israel"}
    HUNGARIAN = {"language": "hu", "dialect": ""}
    HUNGARIAN_HUNGARY = {"language": "hu", "dialect": "Hungary"}
    HINDI = {"language": "hi", "dialect": ""}
    HINDI_INDIA = {"language": "hi", "dialect": "India"}
    ITALIAN = {"language": "it", "dialect": ""}
    ITALIAN_ITALY = {"language": "it", "dialect": "Italy"}
    ITALIAN_SWITZERLAND = {"language": "it", "dialect": "Switzerland"}
    KANNADA = {"language": "kn", "dialect": ""}
    KANNADA_INDIA = {"language": "kn", "dialect": "India"}
    JAVANESE = {"language": "jv", "dialect": ""}
    JAVANESE_INDONESIA = {"language": "jv", "dialect": "Indonesia"}
    KHMER = {"language": "km", "dialect": ""}
    KHMER_CAMBODIA = {"language": "km", "dialect": "Cambodia"}
    LAO = {"language": "lo", "dialect": ""}
    LAO_LAOS = {"language": "lo", "dialect": "Laos"}
    MALAGASY = {"language": "mg", "dialect": ""}
    MALAY = {"language": "ms", "dialect": ""}
    MALAY_MALAYSIA = {"language": "ms", "dialect": "Malaysia"}
    MALAYALAM = {"language": "ml", "dialect": ""}
    MALAYALAM_INDIA = {"language": "ml", "dialect": "India"}
    MARATHI = {"language": "mr", "dialect": ""}
    MARATHI_INDIA = {"language": "mr", "dialect": "India"}
    NEPALI = {"language": "ne", "dialect": ""}
    NEPALI_NEPAL = {"language": "ne", "dialect": "Nepal"}
    NORWEGIAN = {"language": "no", "dialect": ""}
    NORWEGIAN_NORWAY = {"language": "no", "dialect": "Norway"}
    SAMOAN = {"language": "sm", "dialect": ""}
    SESOTHO = {"language": "st", "dialect": ""}
    SCOTS_GAELIC = {"language": "gd", "dialect": ""}
    SINHALA = {"language": "si", "dialect": ""}
    SINHALA_SRI_LANKA = {"language": "si", "dialect": "Sri Lanka"}
    SLOVENIAN = {"language": "sl", "dialect": ""}
    SLOVENIAN_SLOVENIA = {"language": "sl", "dialect": "Slovenia"}
    SWEDISH = {"language": "sv", "dialect": ""}
    SWEDISH_SWEDEN = {"language": "sv", "dialect": "Sweden"}
    YORUBA = {"language": "yo", "dialect": ""}
    SPANISH = {"language": "es", "dialect": ""}
    SPANISH_DOMINICAN_REPUBLIC = {"language": "es", "dialect": "Dominican Republic"}
    SPANISH_MEXICO = {"language": "es", "dialect": "Mexico"}
    SPANISH_PUERTO_RICO = {"language": "es", "dialect": "Puerto Rico"}
    SPANISH_EQUATORIAL_GUINEA = {"language": "es", "dialect": "Equatorial Guinea"}
    SPANISH_MEXICAN = {"language": "es", "dialect": "Mexican"}
    SPANISH_VENEZUELA = {"language": "es", "dialect": "Venezuela"}
    SPANISH_GUATEMALA = {"language": "es", "dialect": "Guatemala"}
    SPANISH_NICARAGUA = {"language": "es", "dialect": "Nicaragua"}
    SPANISH_PARAGUAY = {"language": "es", "dialect": "Paraguay"}
    SPANISH_URUGUAY = {"language": "es", "dialect": "Uruguay"}
    SPANISH_COLOMBIA = {"language": "es", "dialect": "Colombia"}
    SPANISH_PANAMA = {"language": "es", "dialect": "Panama"}
    SPANISH_UNITED_STATES = {"language": "es", "dialect": "United States"}
    SPANISH_ECUADOR = {"language": "es", "dialect": "Ecuador"}
    SPANISH_ARGENTINA = {"language": "es", "dialect": "Argentina"}
    SPANISH_SPAIN = {"language": "es", "dialect": "Spain"}
    SPANISH_HONDURAS = {"language": "es", "dialect": "Honduras"}
    SPANISH_CHILE = {"language": "es", "dialect": "Chile"}
    SPANISH_CUBA = {"language": "es", "dialect": "Cuba"}
    SPANISH_COSTA_RICA = {"language": "es", "dialect": "Costa Rica"}
    SPANISH_PERU = {"language": "es", "dialect": "Peru"}
    SPANISH_EL_SALVADOR = {"language": "es", "dialect": "El Salvador"}
    SPANISH_BOLIVIA = {"language": "es", "dialect": "Bolivia"}
    SPANISH_EUROPEAN = {"language": "es", "dialect": "European"}
    SUNDANESE = {"language": "su", "dialect": ""}
    SUNDANESE_INDONESIA = {"language": "su", "dialect": "Indonesia"}
    TURKMEN = {"language": "tk", "dialect": ""}
    TAMIL = {"language": "ta", "dialect": ""}
    TAMIL_SRI_LANKA = {"language": "ta", "dialect": "Sri Lanka"}
    TAMIL_INDIA = {"language": "ta", "dialect": "India"}
    TAMIL_SINGAPORE = {"language": "ta", "dialect": "Singapore"}
    TAMIL_MALAYSIA = {"language": "ta", "dialect": "Malaysia"}
    THAI = {"language": "th", "dialect": ""}
    THAI_THAILAND = {"language": "th", "dialect": "Thailand"}
    TIGRINYA = {"language": "tir", "dialect": ""}
    UKRAINIAN = {"language": "ukr", "dialect": ""}
    UKRAINIAN_UKRAINE = {"language": "ukr", "dialect": "Ukraine"}
    YIDDISH = {"language": "yi", "dialect": ""}
    URDU = {"language": "ur", "dialect": ""}
    URDU_PAKISTAN = {"language": "ur", "dialect": "Pakistan"}
    URDU_INDIA = {"language": "ur", "dialect": "India"}

# License enum with static values
class License(str, Enum):
    CC_BY = "620ba3983e2fa95c500b4297"
    CC_BY_SA = "620ba39b3e2fa95c500b4298"
    CC_BY_NC = "620ba39e3e2fa95c500b4299"
    CC_BY_NC_SA = "620ba3a03e2fa95c500b429a"
    MIT = "620ba3a83e2fa95c500b429d"
    CC_BY_ND = "620ba3a33e2fa95c500b429b"
    CC_BY_NC_ND = "620ba3a63e2fa95c500b429c"
    GPL = "620ba3ab3e2fa95c500b429e"
    APACHE_LICENSE_VERSION_2_0 = "620ba3ae3e2fa95c500b429f"
    BSD_3_CLAUSE = "620ba3b13e2fa95c500b42a0"
    UNKNOWN = "620ba3b73e2fa95c500b42a2"
    PUBLIC_DOMAIN_CC0 = "620ba3943e2fa95c500b4296"
    CUSTOM = "620ba3b43e2fa95c500b42a1"
