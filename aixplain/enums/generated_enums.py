"""Auto-generated enum module containing static values from the backend API."""

# This is an auto generated module. PLEASE DO NOT EDIT
# This module contains static enums that were previously loaded dynamically

from enum import Enum
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from aixplain.base.parameters import BaseParameters, Parameter


class Function(str, Enum):
    """Enum representing available functions in the aiXplain platform."""

    TEXT_NORMALIZATION = "text-normalization"
    PARAPHRASING = "paraphrasing"
    LANGUAGE_IDENTIFICATION = "language-identification"
    BENCHMARK_SCORING_ASR = "benchmark-scoring-asr"
    MULTI_CLASS_TEXT_CLASSIFICATION = "multi-class-text-classification"
    SPEECH_EMBEDDING = "speech-embedding"
    DOCUMENT_IMAGE_PARSING = "document-image-parsing"
    TRANSLATION = "translation"
    AUDIO_SOURCE_SEPARATION = "audio-source-separation"
    SPEECH_RECOGNITION = "speech-recognition"
    KEYWORD_SPOTTING = "keyword-spotting"
    PART_OF_SPEECH_TAGGING = "part-of-speech-tagging"
    REFERENCELESS_AUDIO_GENERATION_METRIC = "referenceless-audio-generation-metric"
    VOICE_ACTIVITY_DETECTION = "voice-activity-detection"
    SENTIMENT_ANALYSIS = "sentiment-analysis"
    SUBTITLING = "subtitling"
    MULTI_LABEL_TEXT_CLASSIFICATION = "multi-label-text-classification"
    VISEME_GENERATION = "viseme-generation"
    TEXT_SEGMENATION = "text-segmenation"
    ZERO_SHOT_CLASSIFICATION = "zero-shot-classification"
    TEXT_GENERATION = "text-generation"
    AUDIO_INTENT_DETECTION = "audio-intent-detection"
    ENTITY_LINKING = "entity-linking"
    CONNECTION = "connection"
    VISUAL_QUESTION_ANSWERING = "visual-question-answering"
    LOGLIKELIHOOD = "loglikelihood"
    LANGUAGE_IDENTIFICATION_AUDIO = "language-identification-audio"
    FACT_CHECKING = "fact-checking"
    TABLE_QUESTION_ANSWERING = "table-question-answering"
    SPEECH_CLASSIFICATION = "speech-classification"
    INVERSE_TEXT_NORMALIZATION = "inverse-text-normalization"
    MULTI_CLASS_IMAGE_CLASSIFICATION = "multi-class-image-classification"
    ASR_GENDER_CLASSIFICATION = "asr-gender-classification"
    SUMMARIZATION = "summarization"
    TOPIC_MODELING = "topic-modeling"
    AUDIO_RECONSTRUCTION = "audio-reconstruction"
    TEXT_EMBEDDING = "text-embedding"
    DETECT_LANGUAGE_FROM_TEXT = "detect-language-from-text"
    EXTRACT_AUDIO_FROM_VIDEO = "extract-audio-from-video"
    SCENE_DETECTION = "scene-detection"
    TEXT_TO_IMAGE_GENERATION = "text-to-image-generation"
    AUTO_MASK_GENERATION = "auto-mask-generation"
    AUDIO_LANGUAGE_IDENTIFICATION = "audio-language-identification"
    FACIAL_RECOGNITION = "facial-recognition"
    QUESTION_ANSWERING = "question-answering"
    IMAGE_IMPAINTING = "image-impainting"
    TEXT_RECONSTRUCTION = "text-reconstruction"
    SCRIPT_EXECUTION = "script-execution"
    SEMANTIC_SEGMENTATION = "semantic-segmentation"
    AUDIO_EMOTION_DETECTION = "audio-emotion-detection"
    IMAGE_CAPTIONING = "image-captioning"
    SPLIT_ON_LINEBREAK = "split-on-linebreak"
    STYLE_TRANSFER = "style-transfer"
    BASE_MODEL = "base-model"
    IMAGE_MANIPULATION = "image-manipulation"
    VIDEO_EMBEDDING = "video-embedding"
    DIALECT_DETECTION = "dialect-detection"
    FILL_TEXT_MASK = "fill-text-mask"
    ACTIVITY_DETECTION = "activity-detection"
    SELECT_SUPPLIER_FOR_TRANSLATION = "select-supplier-for-translation"
    EXPRESSION_DETECTION = "expression-detection"
    VIDEO_GENERATION = "video-generation"
    IMAGE_ANALYSIS = "image-analysis"
    UTILITIES = "utilities"
    NOISE_REMOVAL = "noise-removal"
    IMAGE_AND_VIDEO_ANALYSIS = "image-and-video-analysis"
    KEYWORD_EXTRACTION = "keyword-extraction"
    SPLIT_ON_SILENCE = "split-on-silence"
    INTENT_RECOGNITION = "intent-recognition"
    DEPTH_ESTIMATION = "depth-estimation"
    CONNECTOR = "connector"
    SPEAKER_RECOGNITION = "speaker-recognition"
    SYNTAX_ANALYSIS = "syntax-analysis"
    ENTITY_SENTIMENT_ANALYSIS = "entity-sentiment-analysis"
    CLASSIFICATION_METRIC = "classification-metric"
    TEXT_DETECTION = "text-detection"
    GUARDRAILS = "guardrails"
    EMOTION_DETECTION = "emotion-detection"
    VIDEO_FORCED_ALIGNMENT = "video-forced-alignment"
    IMAGE_CONTENT_MODERATION = "image-content-moderation"
    TEXT_SUMMARIZATION = "text-summarization"
    IMAGE_TO_VIDEO_GENERATION = "image-to-video-generation"
    VIDEO_UNDERSTANDING = "video-understanding"
    TEXT_GENERATION_METRIC_DEFAULT = "text-generation-metric-default"
    TEXT_TO_VIDEO_GENERATION = "text-to-video-generation"
    VIDEO_LABEL_DETECTION = "video-label-detection"
    TEXT_SPAM_DETECTION = "text-spam-detection"
    TEXT_CONTENT_MODERATION = "text-content-moderation"
    AUDIO_TRANSCRIPT_IMPROVEMENT = "audio-transcript-improvement"
    AUDIO_TRANSCRIPT_ANALYSIS = "audio-transcript-analysis"
    SPEECH_NON_SPEECH_CLASSIFICATION = "speech-non-speech-classification"
    AUDIO_GENERATION_METRIC = "audio-generation-metric"
    NAMED_ENTITY_RECOGNITION = "named-entity-recognition"
    SPEECH_SYNTHESIS = "speech-synthesis"
    DOCUMENT_INFORMATION_EXTRACTION = "document-information-extraction"
    OCR = "ocr"
    SUBTITLING_TRANSLATION = "subtitling-translation"
    TEXT_TO_AUDIO = "text-to-audio"
    MULTILINGUAL_SPEECH_RECOGNITION = "multilingual-speech-recognition"
    OFFENSIVE_LANGUAGE_IDENTIFICATION = "offensive-language-identification"
    BENCHMARK_SCORING_MT = "benchmark-scoring-mt"
    SPEAKER_DIARIZATION_AUDIO = "speaker-diarization-audio"
    VOICE_CLONING = "voice-cloning"
    SEARCH = "search"
    OBJECT_DETECTION = "object-detection"
    DIACRITIZATION = "diacritization"
    SPEAKER_DIARIZATION_VIDEO = "speaker-diarization-video"
    AUDIO_FORCED_ALIGNMENT = "audio-forced-alignment"
    TOKEN_CLASSIFICATION = "token-classification"
    TOPIC_CLASSIFICATION = "topic-classification"
    INTENT_CLASSIFICATION = "intent-classification"
    VIDEO_CONTENT_MODERATION = "video-content-moderation"
    TEXT_GENERATION_METRIC = "text-generation-metric"
    IMAGE_EMBEDDING = "image-embedding"
    IMAGE_LABEL_DETECTION = "image-label-detection"
    IMAGE_COLORIZATION = "image-colorization"
    METRIC_AGGREGATION = "metric-aggregation"
    INSTANCE_SEGMENTATION = "instance-segmentation"
    OTHER_MULTIPURPOSE = "other-(multipurpose)"
    SPEECH_TRANSLATION = "speech-translation"
    REFERENCELESS_TEXT_GENERATION_METRIC_DEFAULT = "referenceless-text-generation-metric-default"
    REFERENCELESS_TEXT_GENERATION_METRIC = "referenceless-text-generation-metric"
    TEXT_DENORMALIZATION = "text-denormalization"
    IMAGE_COMPRESSION = "image-compression"
    TEXT_CLASSIFICATION = "text-classification"
    ASR_AGE_CLASSIFICATION = "asr-age-classification"
    ASR_QUALITY_ESTIMATION = "asr-quality-estimation"

    def get_input_output_params(self) -> Tuple[Dict, Dict]:
        """Get the input and output parameters for this function.

        Returns:
            Tuple[Dict, Dict]: A tuple containing (input_params, output_params).
        """
        function_io = FunctionInputOutput.get(self.value, None)
        if function_io is None:
            return {}, {}
        input_params = {param["code"]: param for param in function_io["spec"]["params"]}
        output_params = {param["code"]: param for param in function_io["spec"]["output"]}
        return input_params, output_params

    def get_parameters(self) -> "FunctionParameters":
        """Get a FunctionParameters object for this function.

        Returns:
            FunctionParameters: Object containing the function's parameters.
        """
        if not hasattr(self, "_parameters") or self._parameters is None:
            input_params, _ = self.get_input_output_params()
            self._parameters = FunctionParameters(input_params)
        return self._parameters


# Static FunctionInputOutput dictionary
FunctionInputOutput = {
    "text-normalization": {
        "input": {
            "text",
        },
        "output": {"label"},
        "spec": {
            "id": "text-normalization",
            "name": "Text Normalization",
            "description": "Converts unstructured or non-standard textual data into a more readable and uniform format, dealing with abbreviations, numerals, and other non-standard words.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
                {
                    "code": "settings",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "paraphrasing": {
        "input": {"text", "label"},
        "output": {"text"},
        "spec": {
            "id": "paraphrasing",
            "name": "Paraphrasing",
            "description": "Express the meaning of the writer or speaker or something written or spoken using different words.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "language-identification": {
        "input": {"text"},
        "output": {"label"},
        "spec": {
            "id": "language-identification",
            "name": "Language Identification",
            "description": "Detects the language in which a given text is written, aiding in multilingual platforms or content localization.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "benchmark-scoring-asr": {
        "input": {"audio", "text", "text"},
        "output": {"label"},
        "spec": {
            "id": "benchmark-scoring-asr",
            "name": "Benchmark Scoring ASR",
            "description": "Benchmark Scoring ASR is a function that evaluates and compares the performance of automatic speech recognition systems by analyzing their accuracy, speed, and other relevant metrics against a standardized set of benchmarks.",
            "params": [
                {
                    "code": "input",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "multi-class-text-classification": {
        "input": {
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "multi-class-text-classification",
            "name": "Multi Class Text Classification",
            "description": "Multi Class Text Classification is a natural language processing task that involves categorizing a given text into one of several predefined classes or categories based on its content.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "speech-embedding": {
        "input": {
            "audio",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "speech-embedding",
            "name": "Speech Embedding",
            "description": "Transforms spoken content into a fixed-size vector in a high-dimensional space that captures the content's essence. Facilitates tasks like speech recognition and speaker verification.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "document-image-parsing": {
        "input": {},
        "output": {"text"},
        "spec": {
            "id": "document-image-parsing",
            "name": "Document Image Parsing",
            "description": "Document Image Parsing is the process of analyzing and converting scanned or photographed images of documents into structured, machine-readable formats by identifying and extracting text, layout, and other relevant information.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "translation": {
        "input": {
            "text",
            "label",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "translation",
            "name": "Translation",
            "description": "Converts text from one language to another while maintaining the original message's essence and context. Crucial for global communication.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "sourcelanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "targetlanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script_out",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect_out",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "context",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": True}],
        },
    },
    "audio-source-separation": {
        "input": {"audio"},
        "output": {"audio"},
        "spec": {
            "id": "audio-source-separation",
            "name": "Audio Source Separation",
            "description": "Audio Source Separation is the process of separating a mixture (e.g. a pop band recording) into isolated sounds from individual sources (e.g. just the lead vocals).",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": []}],
        },
    },
    "speech-recognition": {
        "input": {
            "label",
            "audio",
        },
        "output": {"text"},
        "spec": {
            "id": "speech-recognition",
            "name": "Speech Recognition",
            "description": "Converts spoken language into written text. Useful for transcription services, voice assistants, and applications requiring voice-to-text capabilities.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "voice",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "keyword-spotting": {
        "input": {},
        "output": {"label"},
        "spec": {
            "id": "keyword-spotting",
            "name": "Keyword Spotting",
            "description": "Keyword Spotting is a function that enables the detection and identification of specific words or phrases within a stream of audio, often used in voice-activated systems to trigger actions or commands based on recognized keywords.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "part-of-speech-tagging": {
        "input": {
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "part-of-speech-tagging",
            "name": "Part of Speech Tagging",
            "description": "Part of Speech Tagging is a natural language processing task that involves assigning each word in a sentence its corresponding part of speech, such as noun, verb, adjective, or adverb, based on its role and context within the sentence.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "referenceless-audio-generation-metric": {
        "input": {"audio", "text"},
        "output": {"text"},
        "spec": {
            "id": "referenceless-audio-generation-metric",
            "name": "Referenceless Audio Generation Metric",
            "description": "The Referenceless Audio Generation Metric is a tool designed to evaluate the quality of generated audio content without the need for a reference or original audio sample for comparison.",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "sources",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "voice-activity-detection": {
        "input": {
            "audio",
        },
        "output": {"audio"},
        "spec": {
            "id": "voice-activity-detection",
            "name": "Voice Activity Detection",
            "description": "Determines when a person is speaking in an audio clip. It's an essential preprocessing step for other audio-related tasks.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "onset",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0.5", "label": "0.5"}],
                    "isFixed": False,
                },
                {
                    "code": "offset",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0.5", "label": "0.5"}],
                    "isFixed": False,
                },
                {
                    "code": "min_duration_on",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "1", "label": "1"}],
                    "isFixed": False,
                },
                {
                    "code": "min_duration_off",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0.5", "label": "0.5"}],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": []}],
        },
    },
    "sentiment-analysis": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "sentiment-analysis",
            "name": "Sentiment Analysis",
            "description": "Determines the sentiment or emotion (e.g., positive, negative, neutral) of a piece of text, aiding in understanding user feedback or market sentiment.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "subtitling": {
        "input": {
            "audio",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "subtitling",
            "name": "Subtitling",
            "description": "Generates accurate subtitles for videos, enhancing accessibility for diverse audiences.",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "sourcelanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
                {
                    "code": "dialect_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
                {
                    "code": "source_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "aws", "label": "AWS"}],
                    "isFixed": False,
                },
                {
                    "code": "target_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "targetlanguages",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "multi-label-text-classification": {
        "input": {
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "multi-label-text-classification",
            "name": "Multi Label Text Classification",
            "description": "Multi Label Text Classification is a natural language processing task where a given text is analyzed and assigned multiple relevant labels or categories from a predefined set, allowing for the text to belong to more than one category simultaneously.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "viseme-generation": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "viseme-generation",
            "name": "Viseme Generation",
            "description": "Viseme Generation is the process of creating visual representations of phonemes, which are the distinct units of sound in speech, to synchronize lip movements with spoken words in animations or virtual avatars.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "text-segmenation": {
        "input": {"text", "label"},
        "output": {"text"},
        "spec": {
            "id": "text-segmenation",
            "name": "Text Segmentation",
            "description": "Text Segmentation is the process of dividing a continuous text into meaningful units, such as words, sentences, or topics, to facilitate easier analysis and understanding.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "zero-shot-classification": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
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
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "text-generation": {
        "input": {
            "text",
        },
        "output": {"text"},
        "spec": {
            "id": "text-generation",
            "name": "Text Generation",
            "description": "Creates coherent and contextually relevant textual content based on prompts or certain parameters. Useful for chatbots, content creation, and data augmentation.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "temperature",
                    "dataType": "number",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "prompt",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "context",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "audio-intent-detection": {
        "input": {},
        "output": {"label"},
        "spec": {
            "id": "audio-intent-detection",
            "name": "Audio Intent Detection",
            "description": "Audio Intent Detection is a process that involves analyzing audio signals to identify and interpret the underlying intentions or purposes behind spoken words, enabling systems to understand and respond appropriately to human speech.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "entity-linking": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "entity-linking",
            "name": "Entity Linking",
            "description": "Associates identified entities in the text with specific entries in a knowledge base or database.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "domain",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "connection": {
        "input": {"text"},
        "output": {"text"},
        "spec": {
            "id": "connection",
            "name": "Connection",
            "description": "Connections are integration that allow you to connect your AI agents to external tools",
            "params": [
                {
                    "code": "name",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "visual-question-answering": {
        "input": {
            "text",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "visual-question-answering",
            "name": "Visual Question Answering",
            "description": "Visual Question Answering (VQA) is a task in artificial intelligence that involves analyzing an image and providing accurate, contextually relevant answers to questions posed about the visual content of that image.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "loglikelihood": {
        "input": {"text"},
        "output": {"number"},
        "spec": {
            "id": "loglikelihood",
            "name": "Log Likelihood",
            "description": "The Log Likelihood function measures the probability of observing the given data under a specific statistical model by taking the natural logarithm of the likelihood function, thereby transforming the product of probabilities into a sum, which simplifies the process of optimization and parameter estimation.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "number", "defaultValue": []}],
        },
    },
    "language-identification-audio": {
        "input": {"audio"},
        "output": {"label"},
        "spec": {
            "id": "language-identification-audio",
            "name": "Language Identification Audio",
            "description": "The Language Identification Audio function analyzes audio input to determine and identify the language being spoken.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "fact-checking": {
        "input": {
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "fact-checking",
            "name": "Fact Checking",
            "description": "Fact Checking is the process of verifying the accuracy and truthfulness of information, statements, or claims by cross-referencing with reliable sources and evidence.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "table-question-answering": {
        "input": {"text", "label"},
        "output": {"text"},
        "spec": {
            "id": "table-question-answering",
            "name": "Table Question Answering",
            "description": "The task of question answering over tables is given an input table (or a set of tables) T and a natural language question Q (a user query), output the correct answer A",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "speech-classification": {
        "input": {
            "audio",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "speech-classification",
            "name": "Speech Classification",
            "description": "Categorizes audio clips based on their content, aiding in content organization and targeted actions.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "inverse-text-normalization": {
        "input": {},
        "output": {"label"},
        "spec": {
            "id": "inverse-text-normalization",
            "name": "Inverse Text Normalization",
            "description": "Inverse Text Normalization is the process of converting spoken or written language in its normalized form, such as numbers, dates, and abbreviations, back into their original, more complex or detailed textual representations.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "multi-class-image-classification": {
        "input": {},
        "output": {"label"},
        "spec": {
            "id": "multi-class-image-classification",
            "name": "Multi Class Image Classification",
            "description": "Multi Class Image Classification is a machine learning task where an algorithm is trained to categorize images into one of several predefined classes or categories based on their visual content.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "asr-gender-classification": {
        "input": {"audio"},
        "output": {"label"},
        "spec": {
            "id": "asr-gender-classification",
            "name": "ASR Gender Classification",
            "description": "The ASR Gender Classification function analyzes audio recordings to determine and classify the speaker's gender based on their voice characteristics.",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "summarization": {
        "input": {
            "text",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "summarization",
            "name": "Summarization",
            "description": "Text summarization is the process of distilling the most important information from a source (or sources) to produce an abridged version for a particular user (or users) and task (or tasks)",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "topic-modeling": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "topic-modeling",
            "name": "Topic Modeling",
            "description": "Topic modeling is a type of statistical modeling for discovering the abstract “topics” that occur in a collection of documents.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "audio-reconstruction": {
        "input": {"audio"},
        "output": {"audio"},
        "spec": {
            "id": "audio-reconstruction",
            "name": "Audio Reconstruction",
            "description": "Audio Reconstruction is the process of restoring or recreating audio signals from incomplete, damaged, or degraded recordings to achieve a high-quality, accurate representation of the original sound.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": []}],
        },
    },
    "text-embedding": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "text-embedding",
            "name": "Text Embedding",
            "description": "Text embedding is a process that converts text into numerical vectors, capturing the semantic meaning and contextual relationships of words or phrases, enabling machines to understand and analyze natural language more effectively.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "detect-language-from-text": {
        "input": {"text"},
        "output": {"label"},
        "spec": {
            "id": "detect-language-from-text",
            "name": "Detect Language From Text",
            "description": "Detect Language From Text",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "extract-audio-from-video": {
        "input": {"video"},
        "output": {"audio"},
        "spec": {
            "id": "extract-audio-from-video",
            "name": "Extract Audio From Video",
            "description": "Isolates and extracts audio tracks from video files, aiding in audio analysis or transcription tasks.",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": None}],
        },
    },
    "scene-detection": {
        "input": {"image"},
        "output": {"label"},
        "spec": {
            "id": "scene-detection",
            "name": "Scene Detection",
            "description": "Scene detection is used for detecting transitions between shots in a video to split it into basic temporal segments.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "text-to-image-generation": {
        "input": {"text"},
        "output": {"image"},
        "spec": {
            "id": "text-to-image-generation",
            "name": "Text To Image Generation",
            "description": "Creates a visual representation based on textual input, turning descriptions into pictorial forms. Used in creative processes and content generation.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "image", "defaultValue": []}],
        },
    },
    "auto-mask-generation": {
        "input": {"image"},
        "output": {"label"},
        "spec": {
            "id": "auto-mask-generation",
            "name": "Auto Mask Generation",
            "description": "Auto-mask generation refers to the automated process of creating masks in image processing or computer vision, typically for segmentation tasks. A mask is a binary or multi-class image that labels different parts of an image, usually separating the foreground (objects of interest) from the background, or identifying specific object classes in an image.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "audio-language-identification": {
        "input": {"audio"},
        "output": {"label"},
        "spec": {
            "id": "audio-language-identification",
            "name": "Audio Language Identification",
            "description": "Audio Language Identification is a process that involves analyzing an audio recording to determine the language being spoken.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "facial-recognition": {
        "input": {"video"},
        "output": {"label"},
        "spec": {
            "id": "facial-recognition",
            "name": "Facial Recognition",
            "description": "A facial recognition system is a technology capable of matching a human face from a digital image or a video frame against a database of faces",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "question-answering": {
        "input": {"text", "label"},
        "output": {"text"},
        "spec": {
            "id": "question-answering",
            "name": "Question Answering",
            "description": "building systems that automatically answer questions posed by humans in a natural language usually from a given text",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "image-impainting": {
        "input": {},
        "output": {"image"},
        "spec": {
            "id": "image-impainting",
            "name": "Image Impainting",
            "description": "Image inpainting is a process that involves filling in missing or damaged parts of an image in a way that is visually coherent and seamlessly blends with the surrounding areas, often using advanced algorithms and techniques to restore the image to its original or intended appearance.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "image", "dataType": "image", "defaultValue": None}],
        },
    },
    "text-reconstruction": {
        "input": {"text"},
        "output": {"text"},
        "spec": {
            "id": "text-reconstruction",
            "name": "Text Reconstruction",
            "description": "Text Reconstruction is a process that involves piecing together fragmented or incomplete text data to restore it to its original, coherent form.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "script-execution": {
        "input": {"text"},
        "output": {"text"},
        "spec": {
            "id": "script-execution",
            "name": "Script Execution",
            "description": "Script Execution refers to the process of running a set of programmed instructions or code within a computing environment, enabling the automated performance of tasks, calculations, or operations as defined by the script.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "semantic-segmentation": {
        "input": {},
        "output": {"label"},
        "spec": {
            "id": "semantic-segmentation",
            "name": "Semantic Segmentation",
            "description": "Semantic segmentation is a computer vision process that involves classifying each pixel in an image into a predefined category, effectively partitioning the image into meaningful segments based on the objects or regions they represent.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "audio-emotion-detection": {
        "input": {},
        "output": {"label"},
        "spec": {
            "id": "audio-emotion-detection",
            "name": "Audio Emotion Detection",
            "description": "Audio Emotion Detection is a technology that analyzes vocal characteristics and patterns in audio recordings to identify and classify the emotional state of the speaker.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "image-captioning": {
        "input": {"image"},
        "output": {"text"},
        "spec": {
            "id": "image-captioning",
            "name": "Image Captioning",
            "description": "Image Captioning is a process that involves generating a textual description of an image, typically using machine learning models to analyze the visual content and produce coherent and contextually relevant sentences that describe the objects, actions, and scenes depicted in the image.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "split-on-linebreak": {
        "input": {"text"},
        "output": {"text"},
        "spec": {
            "id": "split-on-linebreak",
            "name": "Split On Linebreak",
            "description": 'The "Split On Linebreak" function divides a given string into a list of substrings, using linebreaks (newline characters) as the points of separation.',
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "style-transfer": {
        "input": {},
        "output": {"image"},
        "spec": {
            "id": "style-transfer",
            "name": "Style Transfer",
            "description": "Style Transfer is a technique in artificial intelligence that applies the visual style of one image (such as the brushstrokes of a famous painting) to the content of another image, effectively blending the artistic elements of the first image with the subject matter of the second.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "image", "dataType": "image", "defaultValue": None}],
        },
    },
    "base-model": {
        "input": {"label", "text"},
        "output": {"text"},
        "spec": {
            "id": "base-model",
            "name": "Base-Model",
            "description": "The Base-Model function serves as a foundational framework designed to provide essential features and capabilities upon which more specialized or advanced models can be built and customized.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": True}],
        },
    },
    "image-manipulation": {
        "input": {"image", "image"},
        "output": {"image"},
        "spec": {
            "id": "image-manipulation",
            "name": "Image Manipulation",
            "description": "Image Manipulation refers to the process of altering or enhancing digital images using various techniques and tools to achieve desired visual effects, correct imperfections, or transform the image's appearance.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "targetimage",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "image", "dataType": "image", "defaultValue": []}],
        },
    },
    "video-embedding": {
        "input": {
            "label",
        },
        "output": {"embedding"},
        "spec": {
            "id": "video-embedding",
            "name": "Video Embedding",
            "description": "Video Embedding is a process that transforms video content into a fixed-dimensional vector representation, capturing essential features and patterns to facilitate tasks such as retrieval, classification, and recommendation.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "video",
                    "dataType": "video",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "embedding", "defaultValue": None}],
        },
    },
    "dialect-detection": {
        "input": {
            "audio",
        },
        "output": {"text"},
        "spec": {
            "id": "dialect-detection",
            "name": "Dialect Detection",
            "description": "Identifies specific dialects within a language, aiding in localized content creation or user experience personalization.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "fill-text-mask": {
        "input": {
            "text",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "fill-text-mask",
            "name": "Fill Text Mask",
            "description": "Completes missing parts of a text based on the context, ideal for content generation or data augmentation tasks.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "activity-detection": {
        "input": {"image"},
        "output": {"label"},
        "spec": {
            "id": "activity-detection",
            "name": "Activity Detection",
            "description": "detection of the presence or absence of human speech, used in speech processing.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "select-supplier-for-translation": {
        "input": {"label", "text"},
        "output": {"label"},
        "spec": {
            "id": "select-supplier-for-translation",
            "name": "Select Supplier For Translation",
            "description": "Supplier For Translation",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "expression-detection": {
        "input": {"image"},
        "output": {"label"},
        "spec": {
            "id": "expression-detection",
            "name": "Expression Detection",
            "description": "Expression Detection is the process of identifying and analyzing facial expressions to interpret emotions or intentions using AI and computer vision techniques.",
            "params": [
                {
                    "code": "media",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "video-generation": {
        "input": {"text"},
        "output": {"video"},
        "spec": {
            "id": "video-generation",
            "name": "Video Generation",
            "description": "Produces video content based on specific inputs or datasets. Can be used for simulations, animations, or even deepfake detection.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "video", "defaultValue": []}],
        },
    },
    "image-analysis": {
        "input": {"image"},
        "output": {"label"},
        "spec": {
            "id": "image-analysis",
            "name": "Image Analysis",
            "description": "Image analysis is the extraction of meaningful information from images",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "utilities": {
        "input": {"text"},
        "output": {"text"},
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
                    "isFixed": False,
                }
            ],
            "output": [{"code": "outputs", "dataType": "text", "defaultValue": []}],
        },
    },
    "noise-removal": {
        "input": {},
        "output": {"audio"},
        "spec": {
            "id": "noise-removal",
            "name": "Noise Removal",
            "description": "Noise Removal is a process that involves identifying and eliminating unwanted random variations or disturbances from an audio signal to enhance the clarity and quality of the underlying information.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": None}],
        },
    },
    "image-and-video-analysis": {
        "input": {"image"},
        "output": {"label"},
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
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "keyword-extraction": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "keyword-extraction",
            "name": "Keyword Extraction",
            "description": "It helps concise the text and obtain relevant keywords Example use-cases are finding topics of interest from a news article and identifying the problems based on customer reviews and so.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "split-on-silence": {
        "input": {"audio"},
        "output": {"audio"},
        "spec": {
            "id": "split-on-silence",
            "name": "Split On Silence",
            "description": 'The "Split On Silence" function divides an audio recording into separate segments based on periods of silence, allowing for easier editing and analysis of individual sections.',
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": []}],
        },
    },
    "intent-recognition": {
        "input": {
            "audio",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "intent-recognition",
            "name": "Intent Recognition",
            "description": "classify the user's utterance (provided in varied natural language)  or text into one of several predefined classes, that is, intents.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "depth-estimation": {
        "input": {
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "depth-estimation",
            "name": "Depth Estimation",
            "description": "Depth estimation is a computational process that determines the distance of objects from a viewpoint, typically using visual data from cameras or sensors to create a three-dimensional understanding of a scene.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "connector": {
        "input": {"text"},
        "output": {"text"},
        "spec": {
            "id": "connector",
            "name": "Connector",
            "description": "Connectors are integration that allow you to connect your AI agents to external tools",
            "params": [
                {
                    "code": "name",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "speaker-recognition": {
        "input": {
            "audio",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "speaker-recognition",
            "name": "Speaker Recognition",
            "description": "In speaker identification, an utterance from an unknown speaker is analyzed and compared with speech models of known speakers.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "syntax-analysis": {
        "input": {
            "text",
            "text",
        },
        "output": {"text"},
        "spec": {
            "id": "syntax-analysis",
            "name": "Syntax Analysis",
            "description": "Is the process of analyzing natural language with the rules of a formal grammar. Grammatical rules are applied to categories and groups of words, not individual words. Syntactic analysis basically assigns a semantic structure to text.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "entity-sentiment-analysis": {
        "input": {"text"},
        "output": {"label"},
        "spec": {
            "id": "entity-sentiment-analysis",
            "name": "Entity Sentiment Analysis",
            "description": "Entity Sentiment Analysis combines both entity analysis and sentiment analysis and attempts to determine the sentiment (positive or negative) expressed about entities within the text.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "classification-metric": {
        "input": {"label", "label", "text"},
        "output": {"number"},
        "spec": {
            "id": "classification-metric",
            "name": "Classification Metric",
            "description": "A Classification Metric is a quantitative measure used to evaluate the quality and effectiveness of classification models.",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "references",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "lowerIsBetter",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "number", "defaultValue": None}],
        },
    },
    "text-detection": {
        "input": {"image"},
        "output": {"text"},
        "spec": {
            "id": "text-detection",
            "name": "Text Detection",
            "description": "detect text regions in the complex background and label them with bounding boxes.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "guardrails": {
        "input": {"text"},
        "output": {"label"},
        "spec": {
            "id": "guardrails",
            "name": "Guardrails",
            "description": " Guardrails are governance rules that enforce security, compliance, and operational best practices, helping prevent mistakes and detect suspicious activity",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "emotion-detection": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "emotion-detection",
            "name": "Emotion Detection",
            "description": "Identifies human emotions from text or audio, enhancing user experience in chatbots or customer feedback analysis.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "video-forced-alignment": {
        "input": {
            "video",
            "text",
            "label",
        },
        "output": {"text", "video"},
        "spec": {
            "id": "video-forced-alignment",
            "name": "Video Forced Alignment",
            "description": "Aligns the transcription of spoken content in a video with its corresponding timecodes, facilitating subtitle creation.",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [
                {"code": "text", "dataType": "text", "defaultValue": []},
                {"code": "video", "dataType": "video", "defaultValue": []},
            ],
        },
    },
    "image-content-moderation": {
        "input": {
            "image",
        },
        "output": {"label"},
        "spec": {
            "id": "image-content-moderation",
            "name": "Image Content Moderation",
            "description": "Detects and filters out inappropriate or harmful images, essential for platforms with user-generated visual content.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "min_confidence",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0.5", "label": "0.5"}],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "text-summarization": {
        "input": {
            "text",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "text-summarization",
            "name": "Text summarization",
            "description": "Extracts the main points from a larger body of text, producing a concise summary without losing the primary message.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "image-to-video-generation": {
        "input": {
            "label",
        },
        "output": {"video"},
        "spec": {
            "id": "image-to-video-generation",
            "name": "Image To Video Generation",
            "description": "The Image To Video Generation function transforms a series of static images into a cohesive, dynamic video sequence, often incorporating transitions, effects, and synchronization with audio to create a visually engaging narrative.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "video", "defaultValue": None}],
        },
    },
    "video-understanding": {
        "input": {
            "video",
            "text",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "video-understanding",
            "name": "Video Understanding",
            "description": "Video Understanding is the process of analyzing and interpreting video content to extract meaningful information, such as identifying objects, actions, events, and contextual relationships within the footage.",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "text", "dataType": "text", "defaultValue": []}],
        },
    },
    "text-generation-metric-default": {
        "input": {"text", "text"},
        "output": {"text"},
        "spec": {
            "id": "text-generation-metric-default",
            "name": "Text Generation Metric Default",
            "description": 'The "Text Generation Metric Default" function provides a standard set of evaluation metrics for assessing the quality and performance of text generation models.',
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "references",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "text-to-video-generation": {
        "input": {
            "text",
        },
        "output": {"video"},
        "spec": {
            "id": "text-to-video-generation",
            "name": "Text To Video Generation",
            "description": "Text To Video Generation is a process that converts written descriptions or scripts into dynamic, visual video content using advanced algorithms and artificial intelligence.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "video", "defaultValue": None}],
        },
    },
    "video-label-detection": {
        "input": {
            "video",
        },
        "output": {"label"},
        "spec": {
            "id": "video-label-detection",
            "name": "Video Label Detection",
            "description": "Identifies and tags objects, scenes, or activities within a video. Useful for content indexing and recommendation systems.",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "min_confidence",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0.5", "label": "0.5"}],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "text-spam-detection": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "text-spam-detection",
            "name": "Text Spam Detection",
            "description": "Identifies and filters out unwanted or irrelevant text content, ideal for moderating user-generated content or ensuring quality in communication platforms.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "text-content-moderation": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "text-content-moderation",
            "name": "Text Content Moderation",
            "description": "Scans and identifies potentially harmful, offensive, or inappropriate textual content, ensuring safer user environments.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "audio-transcript-improvement": {
        "input": {
            "label",
            "text",
            "audio",
        },
        "output": {"text"},
        "spec": {
            "id": "audio-transcript-improvement",
            "name": "Audio Transcript Improvement",
            "description": "Refines and corrects transcriptions generated from audio data, improving readability and accuracy.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "source_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
                {
                    "code": "is_medical",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "audio-transcript-analysis": {
        "input": {
            "label",
            "audio",
        },
        "output": {"text"},
        "spec": {
            "id": "audio-transcript-analysis",
            "name": "Audio Transcript Analysis",
            "description": "Analyzes transcribed audio data for insights, patterns, or specific information extraction.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "source_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "speech-non-speech-classification": {
        "input": {
            "audio",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "speech-non-speech-classification",
            "name": "Speech or Non-Speech Classification",
            "description": "Differentiates between speech and non-speech audio segments. Great for editing software and transcription services to exclude irrelevant audio.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "audio-generation-metric": {
        "input": {"audio", "text"},
        "output": {"text"},
        "spec": {
            "id": "audio-generation-metric",
            "name": "Audio Generation Metric",
            "description": "The Audio Generation Metric is a quantitative measure used to evaluate the quality, accuracy, and overall performance of audio generated by artificial intelligence systems, often considering factors such as fidelity, intelligibility, and similarity to human-produced audio.",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "references",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "named-entity-recognition": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "named-entity-recognition",
            "name": "Named Entity Recognition",
            "description": "Identifies and classifies named entities (e.g., persons, organizations, locations) within text. Useful for information extraction, content tagging, and search enhancements.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "domain",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "speech-synthesis": {
        "input": {
            "label",
            "text",
        },
        "output": {"audio"},
        "spec": {
            "id": "speech-synthesis",
            "name": "Speech Synthesis",
            "description": "Generates human-like speech from written text. Ideal for text-to-speech applications, audiobooks, and voice assistants.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "voice",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "type",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": []}],
        },
    },
    "document-information-extraction": {
        "input": {},
        "output": {"text"},
        "spec": {
            "id": "document-information-extraction",
            "name": "Document Information Extraction",
            "description": "Document Information Extraction is the process of automatically identifying, extracting, and structuring relevant data from unstructured or semi-structured documents, such as invoices, receipts, contracts, and forms, to facilitate easier data management and analysis.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "ocr": {
        "input": {"image", "text"},
        "output": {"text"},
        "spec": {
            "id": "ocr",
            "name": "OCR",
            "description": "Converts images of typed, handwritten, or printed text into machine-encoded text. Used in digitizing printed texts for data retrieval.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "featuretypes",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "subtitling-translation": {
        "input": {
            "text",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "subtitling-translation",
            "name": "Subtitling Translation",
            "description": "Converts the text of subtitles from one language to another, ensuring context and cultural nuances are maintained. Essential for global content distribution.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "sourcelanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
                {
                    "code": "dialect_in",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
                {
                    "code": "target_supplier",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "targetlanguages",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "text-to-audio": {
        "input": {
            "text",
        },
        "output": {"audio"},
        "spec": {
            "id": "text-to-audio",
            "name": "Text to Audio",
            "description": "The Text to Audio function converts written text into spoken words, allowing users to listen to the content instead of reading it.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": None}],
        },
    },
    "multilingual-speech-recognition": {
        "input": {
            "audio",
        },
        "output": {"text"},
        "spec": {
            "id": "multilingual-speech-recognition",
            "name": "Multilingual Speech Recognition",
            "description": "Multilingual Speech Recognition is a technology that enables the automatic transcription of spoken language into text across multiple languages, allowing for seamless communication and understanding in diverse linguistic contexts.",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "offensive-language-identification": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "offensive-language-identification",
            "name": "Offensive Language Identification",
            "description": "Detects language or phrases that might be considered offensive, aiding in content moderation and creating respectful user interactions.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "benchmark-scoring-mt": {
        "input": {"text", "text", "text"},
        "output": {"label"},
        "spec": {
            "id": "benchmark-scoring-mt",
            "name": "Benchmark Scoring MT",
            "description": "Benchmark Scoring MT is a function designed to evaluate and score machine translation systems by comparing their output against a set of predefined benchmarks, thereby assessing their accuracy and performance.",
            "params": [
                {
                    "code": "input",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "speaker-diarization-audio": {
        "input": {
            "audio",
        },
        "output": {"label"},
        "spec": {
            "id": "speaker-diarization-audio",
            "name": "Speaker Diarization Audio",
            "description": "Identifies individual speakers and their respective speech segments within an audio clip. Ideal for multi-speaker recordings or conference calls.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "voice-cloning": {
        "input": {
            "text",
            "audio",
            "label",
        },
        "output": {"audio"},
        "spec": {
            "id": "voice-cloning",
            "name": "Voice Cloning",
            "description": "Replicates a person's voice based on a sample, allowing for the generation of speech in that person's tone and style. Used cautiously due to ethical considerations.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "voice",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "type",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "audio", "defaultValue": []}],
        },
    },
    "search": {
        "input": {"text"},
        "output": {"text"},
        "spec": {
            "id": "search",
            "name": "Search",
            "description": "An algorithm that identifies and returns data or items that match particular keywords or conditions from a dataset. A fundamental tool for databases and websites.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "object-detection": {
        "input": {"image"},
        "output": {"label"},
        "spec": {
            "id": "object-detection",
            "name": "Object Detection",
            "description": "Object Detection is a computer vision technology that identifies and locates objects within an image, typically by drawing bounding boxes around the detected objects and classifying them into predefined categories.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "diacritization": {
        "input": {"label", "label", "text"},
        "output": {"text"},
        "spec": {
            "id": "diacritization",
            "name": "Diacritization",
            "description": "Adds diacritical marks to text, essential for languages where meaning can change based on diacritics.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "speaker-diarization-video": {
        "input": {
            "video",
        },
        "output": {"video"},
        "spec": {
            "id": "speaker-diarization-video",
            "name": "Speaker Diarization Video",
            "description": "Segments a video based on different speakers, identifying when each individual speaks. Useful for transcriptions and understanding multi-person conversations.",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "video", "defaultValue": []}],
        },
    },
    "audio-forced-alignment": {
        "input": {
            "audio",
            "text",
            "label",
        },
        "output": {"text", "audio"},
        "spec": {
            "id": "audio-forced-alignment",
            "name": "Audio Forced Alignment",
            "description": "Synchronizes phonetic and phonological text with the corresponding segments in an audio file. Useful in linguistic research and detailed transcription tasks.",
            "params": [
                {
                    "code": "audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [
                {"code": "text", "dataType": "text", "defaultValue": []},
                {"code": "audio", "dataType": "audio", "defaultValue": []},
            ],
        },
    },
    "token-classification": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "token-classification",
            "name": "Token Classification",
            "description": "Token-level classification means that each token will be given a label, for example a part-of-speech tagger will classify each word as one particular part of speech.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "topic-classification": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "topic-classification",
            "name": "Topic Classification",
            "description": "Assigns categories or topics to a piece of text based on its content, facilitating content organization and retrieval.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "intent-classification": {
        "input": {
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "intent-classification",
            "name": "Intent Classification",
            "description": "Intent Classification is a natural language processing task that involves analyzing and categorizing user text input to determine the underlying purpose or goal behind the communication, such as booking a flight, asking for weather information, or setting a reminder.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "text",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "video-content-moderation": {
        "input": {
            "video",
        },
        "output": {"label"},
        "spec": {
            "id": "video-content-moderation",
            "name": "Video Content Moderation",
            "description": "Automatically reviews video content to detect and possibly remove inappropriate or harmful material. Essential for user-generated content platforms.",
            "params": [
                {
                    "code": "video",
                    "dataType": "video",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "min_confidence",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0.5", "label": "0.5"}],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "text-generation-metric": {
        "input": {"text", "text"},
        "output": {"text"},
        "spec": {
            "id": "text-generation-metric",
            "name": "Text Generation Metric",
            "description": "A Text Generation Metric is a quantitative measure used to evaluate the quality and effectiveness of text produced by natural language processing models, often assessing aspects such as coherence, relevance, fluency, and adherence to given prompts or instructions.",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "references",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "image-embedding": {
        "input": {
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "image-embedding",
            "name": "Image Embedding",
            "description": "Image Embedding is a process that transforms an image into a fixed-dimensional vector representation, capturing its essential features and enabling efficient comparison, retrieval, and analysis in various machine learning and computer vision tasks.",
            "params": [
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "image-label-detection": {
        "input": {
            "image",
        },
        "output": {"label"},
        "spec": {
            "id": "image-label-detection",
            "name": "Image Label Detection",
            "description": "Identifies objects, themes, or topics within images, useful for image categorization, search, and recommendation systems.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "min_confidence",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0.5", "label": "0.5"}],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "image-colorization": {
        "input": {},
        "output": {"image"},
        "spec": {
            "id": "image-colorization",
            "name": "Image Colorization",
            "description": "Image colorization is a process that involves adding color to grayscale images, transforming them from black-and-white to full-color representations, often using advanced algorithms and machine learning techniques to predict and apply the appropriate hues and shades.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "image", "dataType": "image", "defaultValue": None}],
        },
    },
    "metric-aggregation": {
        "input": {"text"},
        "output": {"text"},
        "spec": {
            "id": "metric-aggregation",
            "name": "Metric Aggregation",
            "description": "Metric Aggregation is a function that computes and summarizes numerical data by applying statistical operations, such as averaging, summing, or finding the minimum and maximum values, to provide insights and facilitate analysis of large datasets.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "instance-segmentation": {
        "input": {},
        "output": {"label"},
        "spec": {
            "id": "instance-segmentation",
            "name": "Instance Segmentation",
            "description": "Instance segmentation is a computer vision task that involves detecting and delineating each distinct object within an image, assigning a unique label and precise boundary to every individual instance of objects, even if they belong to the same category.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
    },
    "other-(multipurpose)": {
        "input": {"text", "label"},
        "output": {"text"},
        "spec": {
            "id": "other-(multipurpose)",
            "name": "Other (Multipurpose)",
            "description": 'The "Other (Multipurpose)" function serves as a versatile category designed to accommodate a wide range of tasks and activities that do not fit neatly into predefined classifications, offering flexibility and adaptability for various needs.',
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "speech-translation": {
        "input": {
            "audio",
            "label",
            "label",
        },
        "output": {"text"},
        "spec": {
            "id": "speech-translation",
            "name": "Speech Translation",
            "description": "Speech Translation is a technology that converts spoken language in real-time from one language to another, enabling seamless communication between speakers of different languages.",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "sourcelanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "targetlanguage",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "voice",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
    },
    "referenceless-text-generation-metric-default": {
        "input": {"text", "text"},
        "output": {"text"},
        "spec": {
            "id": "referenceless-text-generation-metric-default",
            "name": "Referenceless Text Generation Metric Default",
            "description": "The Referenceless Text Generation Metric Default is a function designed to evaluate the quality of generated text without relying on reference texts for comparison.",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "referenceless-text-generation-metric": {
        "input": {"text", "text"},
        "output": {"text"},
        "spec": {
            "id": "referenceless-text-generation-metric",
            "name": "Referenceless Text Generation Metric",
            "description": "The Referenceless Text Generation Metric is a method for evaluating the quality of generated text without requiring a reference text for comparison, often leveraging models or algorithms to assess coherence, relevance, and fluency based on intrinsic properties of the text itself.",
            "params": [
                {
                    "code": "hypotheses",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "sources",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "score_identifier",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
    },
    "text-denormalization": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "text-denormalization",
            "name": "Text Denormalization",
            "description": "Converts standardized or normalized text into its original, often more readable, form. Useful in natural language generation tasks.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": None,
                    "isFixed": True,
                },
                {
                    "code": "lowercase_latin",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0", "label": "No"}],
                    "isFixed": False,
                },
                {
                    "code": "remove_accents",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "1", "label": "Yes"}],
                    "isFixed": False,
                },
                {
                    "code": "remove_punctuation",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "0", "label": "No"}],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "image-compression": {
        "input": {
            "image",
        },
        "output": {"image"},
        "spec": {
            "id": "image-compression",
            "name": "Image Compression",
            "description": "Reduces the size of image files without significantly compromising their visual quality. Useful for optimizing storage and improving webpage load times.",
            "params": [
                {
                    "code": "image",
                    "dataType": "image",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "apl_qfactor",
                    "dataType": "text",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [{"value": "80", "label": "80"}],
                    "isFixed": False,
                },
            ],
            "output": [{"code": "image", "dataType": "image", "defaultValue": []}],
        },
    },
    "text-classification": {
        "input": {
            "text",
            "label",
        },
        "output": {"label"},
        "spec": {
            "id": "text-classification",
            "name": "Text Classification",
            "description": "Categorizes text into predefined groups or topics, facilitating content organization and targeted actions.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "language",
                    "dataType": "label",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "dialect",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "asr-age-classification": {
        "input": {"audio"},
        "output": {"label"},
        "spec": {
            "id": "asr-age-classification",
            "name": "ASR Age Classification",
            "description": "The ASR Age Classification function is designed to analyze audio recordings of speech to determine the speaker's age group by leveraging automatic speech recognition (ASR) technology and machine learning algorithms.",
            "params": [
                {
                    "code": "source_audio",
                    "dataType": "audio",
                    "required": True,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": False,
                }
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
    "asr-quality-estimation": {
        "input": {
            "text",
        },
        "output": {"label"},
        "spec": {
            "id": "asr-quality-estimation",
            "name": "ASR Quality Estimation",
            "description": "ASR Quality Estimation is a process that evaluates the accuracy and reliability of automatic speech recognition systems by analyzing their performance in transcribing spoken language into text.",
            "params": [
                {
                    "code": "text",
                    "dataType": "text",
                    "required": True,
                    "multipleValues": True,
                    "defaultValues": [],
                    "isFixed": False,
                },
                {
                    "code": "script",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": False,
                    "defaultValues": [],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": []}],
        },
    },
}


class FunctionParameters(BaseParameters):
    """Class to store and manage function parameters."""

    def __init__(self, input_params: Dict):
        """Initialize FunctionParameters with input parameters.

        Args:
            input_params (Dict): Dictionary of input parameters.
        """
        super().__init__()
        for param_code, param_config in input_params.items():
            self.parameters[param_code] = Parameter(
                name=param_code,
                required=param_config.get("required", False),
                value=None,
            )


class Supplier(Enum):
    """Enum representing available suppliers in the aiXplain platform."""

    AIXPLAIN = {"id": 1, "name": "aixplain", "code": "aixplain"}
    GOOGLE = {"id": 1769, "name": "google", "code": "google"}
    TIMECHAT = {"id": 11688, "name": "TimeChat", "code": "timechat"}
    CANOPY_LABS = {"id": 29334, "name": "Canopy Labs", "code": "canopy-labs"}
    COMPOSIO = {"id": 29342, "name": "Composio", "code": "composio"}
    MISTRALAI = {"id": 14770, "name": "Mistral AI", "code": "mistralai"}
    REVAI = {"id": 1781, "name": "revai", "code": "revai"}
    SAUTECH = {"id": 1783, "name": "sautech", "code": "sautech"}
    AZURE = {"id": 1766, "name": "Microsoft", "code": "azure"}
    NVIDIA = {"id": 1776, "name": "NVIDIA", "code": "nvidia"}
    OPENWEATHER = {"id": 16249, "name": "OpenWeather", "code": "openweather"}
    SERPAPI = {"id": 65776, "name": "SerpApi", "code": "serpapi"}
    FANAR = {"id": 32961, "name": "Fanar", "code": "fanar"}
    PURETALKAI = {"id": 1779, "name": "puretalkai", "code": "puretalkai"}
    SUKOON = {"id": 1806, "name": "Sukoon", "code": "sukoon"}
    MODERMT = {"id": 1775, "name": "modermt", "code": "modermt"}
    PYANNOTE = {"id": 1780, "name": "pyannoteAI", "code": "pyannote"}
    FIRECRAWL = {"id": 20131, "name": "Firecrawl", "code": "firecrawl"}
    RESEMBLEAI = {"id": 14588, "name": "Resemble AI", "code": "resembleai"}
    MYSHELL = {"id": 11238, "name": "MyShell AI", "code": "myshell"}
    BAAI = {"id": 29643, "name": "Beijing Academy of Artificial Intelligence", "code": "BAAI"}
    ELEVENLABS = {"id": 10482, "name": "ElevenLabs", "code": "elevenlabs"}
    LARA_TRANSLATE = {"id": 34640, "name": "Lara Translate", "code": "lara-translate"}
    LAMBDA_AI = {"id": 32839, "name": "Lambda Ai", "code": "lambda-ai"}
    FIREWORKS_AI = {"id": 17852, "name": "Fireworks AI", "code": "fireworks-ai"}
    XAI = {"id": 24097, "name": "xAI", "code": "xai"}
    OPENAI = {"id": 1777, "name": "OpenAI", "code": "openai"}
    TAVILY = {"id": 19379, "name": "Tavily", "code": "tavily"}
    APLICATA = {"id": 1409, "name": "aplicata", "code": "aplicata"}
    BRITISHTELECOM = {"id": 1767, "name": "British Telecom", "code": "britishtelecom"}
    META = {"id": 1768, "name": "meta", "code": "meta"}
    APPTEK_SPACETOON = {"id": 1796, "name": "AppTek-SpaceToon", "code": "apptek-spacetoon"}
    APPTEK = {"id": 1797, "name": "AppTek2", "code": "apptek"}
    HOUNDIFY = {"id": 1770, "name": "houndify", "code": "houndify"}
    RAMSA = {"id": 1804, "name": "Ramsa", "code": "ramsa"}
    RDI = {"id": 1805, "name": "RDI", "code": "rdi"}
    KATEB = {"id": 1772, "name": "kateb", "code": "kateb"}
    KLANGOO = {"id": 1773, "name": "klangoo", "code": "klangoo"}
    VECTARA = {"id": 2927, "name": "Vectara", "code": "vectara"}
    PICOVOICE = {"id": 1778, "name": "picovoice", "code": "picovoice"}
    SACREBLEU = {"id": 1782, "name": "sacrebleu", "code": "sacrebleu"}
    UNIVERSITYOFHELSINKI = {"id": 1786, "name": "universityofhelsinki", "code": "universityofhelsinki"}
    VUMICHIEN = {"id": 1787, "name": "vumichien", "code": "vumichien"}
    YOURTTS = {"id": 1789, "name": "yourtts", "code": "yourtts"}
    CORE42 = {"id": 12371, "name": "Core42", "code": "core42"}
    SCALESERP = {"id": 10473, "name": "Scale SERP", "code": "scaleserp"}
    SPEECHMATICS = {"id": 10930, "name": "Speechmatics", "code": "speechmatics"}
    IBM = {"id": 10931, "name": "IBM", "code": "ibm"}
    PLAYHT = {"id": 14573, "name": "PlayHT", "code": "playht"}
    VOYAGE_AI = {"id": 25056, "name": "Voyage AI", "code": "voyage-ai"}
    WIKIPEDIA = {"id": 11150, "name": "Wikipedia", "code": "wikipedia"}
    JINA_AI = {"id": 26964, "name": "Jina Ai", "code": "jina-ai"}
    SAMBANOVA = {"id": 17861, "name": "SambaNova", "code": "sambanova"}
    HUME_AI = {"id": 17905, "name": "Hume AI", "code": "hume-ai"}
    QCRI = {"id": 1803, "name": "QCRI", "code": "qcri"}
    STABILITYAI = {"id": 1784, "name": "Stability AI", "code": "stabilityai"}
    TARJAMA = {"id": 22755, "name": "Tarjama", "code": "tarjama"}
    LUMA_AI = {"id": 24593, "name": "Luma AI", "code": "luma-ai"}
    COHERE = {"id": 25059, "name": "Cohere", "code": "cohere"}
    GROQ_KSA = {"id": 25579, "name": "Groq KSA", "code": "groq-ksa"}
    PARADIGM_NETWORKS = {"id": 29093, "name": "Paradigm Networks", "code": "paradigm-networks"}
    SESAME_AI_LABS = {"id": 29337, "name": "Sesame AI Labs", "code": "sesame-ai-labs"}
    MOONSHOT_AI = {"id": 37644, "name": "Moonshot AI", "code": "moonshot-ai"}
    CREWAI = {"id": 16094, "name": "CrewAI", "code": "crewai"}
    SDAIA = {"id": 210, "name": "sdaia", "code": "sdaia"}
    UNBABEL = {"id": 1808, "name": "Unbabel", "code": "unbabel"}
    DEEPGRAM = {"id": 1799, "name": "Deepgram", "code": "deepgram"}
    EBAY = {"id": 1800, "name": "eBay", "code": "ebay"}
    IDENTV = {"id": 1801, "name": "IdenTV", "code": "identv"}
    PANGEANIC = {"id": 1802, "name": "Pangeanic", "code": "pangeanic"}
    TREATMENT = {"id": 1807, "name": "Treatment", "code": "treatment"}
    HUGGINGFACE = {"id": 1771, "name": "huggingface", "code": "huggingface"}
    STREAMN = {"id": 1785, "name": "streamn", "code": "streamn"}
    YDSHIEH = {"id": 1788, "name": "ydshieh", "code": "ydshieh"}
    AWS = {"id": 1763, "name": "AWS", "code": "aws"}
    DEEPINFRA = {"id": 20164, "name": "Deep Infra", "code": "deepinfra"}
    MARITACA_AI = {"id": 17296, "name": "Maritaca AI", "code": "maritaca-ai"}
    GROQ = {"id": 6839, "name": "Groq", "code": "groq"}
    CEREBRAS = {"id": 19790, "name": "Cerebras", "code": "cerebras"}
    TOGETHER_AI = {"id": 17845, "name": "Together AI", "code": "together-ai"}

    def __str__(self):
        """Return the supplier name."""
        return self.value["name"]


class Language(Enum):
    """Enum representing available languages in the aiXplain platform."""

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


class License(str, Enum):
    """Enum representing available licenses in the aiXplain platform."""

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
