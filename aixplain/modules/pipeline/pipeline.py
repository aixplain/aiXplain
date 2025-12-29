"""Auto-generated pipeline module containing node classes and Pipeline factory methods."""

# This is an auto generated module. PLEASE DO NOT EDIT

from typing import Union, Type
from aixplain.enums import DataType

from .designer import (
    InputParam,
    OutputParam,
    Inputs,
    Outputs,
    TI,
    TO,
    AssetNode,
    BaseReconstructor,
    BaseSegmentor,
    BaseMetric,
)
from .default import DefaultPipeline
from aixplain.modules import asset


class TextNormalizationInputs(Inputs):
    """Input parameters for TextNormalization."""

    text: InputParam = None
    language: InputParam = None
    settings: InputParam = None

    def __init__(self, node=None):
        """Initialize TextNormalizationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)
        self.settings = self.create_param(code="settings", data_type=DataType.TEXT, is_required=False)


class TextNormalizationOutputs(Outputs):
    """Output parameters for TextNormalization."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextNormalizationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextNormalization(AssetNode[TextNormalizationInputs, TextNormalizationOutputs]):
    """TextNormalization node.

    Converts unstructured or non-standard textual data into a more readable and
    uniform format, dealing with abbreviations, numerals, and other non-standard
    words.

    InputType: text
    OutputType: label
    """

    function: str = "text-normalization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextNormalizationInputs
    outputs_class: Type[TO] = TextNormalizationOutputs


class ParaphrasingInputs(Inputs):
    """Input parameters for Paraphrasing."""

    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize ParaphrasingInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)


class ParaphrasingOutputs(Outputs):
    """Output parameters for Paraphrasing."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ParaphrasingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Paraphrasing(AssetNode[ParaphrasingInputs, ParaphrasingOutputs]):
    """Paraphrasing node.

    Express the meaning of the writer or speaker or something written or spoken
    using different words.

    InputType: text
    OutputType: text
    """

    function: str = "paraphrasing"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ParaphrasingInputs
    outputs_class: Type[TO] = ParaphrasingOutputs


class LanguageIdentificationInputs(Inputs):
    """Input parameters for LanguageIdentification."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize LanguageIdentificationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class LanguageIdentificationOutputs(Outputs):
    """Output parameters for LanguageIdentification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize LanguageIdentificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class LanguageIdentification(AssetNode[LanguageIdentificationInputs, LanguageIdentificationOutputs]):
    """LanguageIdentification node.

    Detects the language in which a given text is written, aiding in multilingual
    platforms or content localization.

    InputType: text
    OutputType: text
    """

    function: str = "language-identification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = LanguageIdentificationInputs
    outputs_class: Type[TO] = LanguageIdentificationOutputs


class BenchmarkScoringAsrInputs(Inputs):
    """Input parameters for BenchmarkScoringAsr."""

    input: InputParam = None
    text: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize BenchmarkScoringAsrInputs."""
        super().__init__(node=node)
        self.input = self.create_param(code="input", data_type=DataType.AUDIO, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class BenchmarkScoringAsrOutputs(Outputs):
    """Output parameters for BenchmarkScoringAsr."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize BenchmarkScoringAsrOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class BenchmarkScoringAsr(AssetNode[BenchmarkScoringAsrInputs, BenchmarkScoringAsrOutputs]):
    """BenchmarkScoringAsr node.

    Benchmark Scoring ASR is a function that evaluates and compares the performance
    of automatic speech recognition systems by analyzing their accuracy, speed, and
    other relevant metrics against a standardized set of benchmarks.

    InputType: audio
    OutputType: label
    """

    function: str = "benchmark-scoring-asr"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = BenchmarkScoringAsrInputs
    outputs_class: Type[TO] = BenchmarkScoringAsrOutputs


class MultiClassTextClassificationInputs(Inputs):
    """Input parameters for MultiClassTextClassification."""

    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize MultiClassTextClassificationInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class MultiClassTextClassificationOutputs(Outputs):
    """Output parameters for MultiClassTextClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize MultiClassTextClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class MultiClassTextClassification(AssetNode[MultiClassTextClassificationInputs, MultiClassTextClassificationOutputs]):
    """MultiClassTextClassification node.

    Multi Class Text Classification is a natural language processing task that
    involves categorizing a given text into one of several predefined classes or
    categories based on its content.

    InputType: text
    OutputType: label
    """

    function: str = "multi-class-text-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = MultiClassTextClassificationInputs
    outputs_class: Type[TO] = MultiClassTextClassificationOutputs


class SpeechEmbeddingInputs(Inputs):
    """Input parameters for SpeechEmbedding."""

    audio: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeechEmbeddingInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class SpeechEmbeddingOutputs(Outputs):
    """Output parameters for SpeechEmbedding."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeechEmbeddingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SpeechEmbedding(AssetNode[SpeechEmbeddingInputs, SpeechEmbeddingOutputs]):
    """SpeechEmbedding node.

    Transforms spoken content into a fixed-size vector in a high-dimensional space
    that captures the content's essence. Facilitates tasks like speech recognition
    and speaker verification.

    InputType: audio
    OutputType: text
    """

    function: str = "speech-embedding"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SpeechEmbeddingInputs
    outputs_class: Type[TO] = SpeechEmbeddingOutputs


class DocumentImageParsingInputs(Inputs):
    """Input parameters for DocumentImageParsing."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize DocumentImageParsingInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class DocumentImageParsingOutputs(Outputs):
    """Output parameters for DocumentImageParsing."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize DocumentImageParsingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class DocumentImageParsing(AssetNode[DocumentImageParsingInputs, DocumentImageParsingOutputs]):
    """DocumentImageParsing node.

    Document Image Parsing is the process of analyzing and converting scanned or
    photographed images of documents into structured, machine-readable formats by
    identifying and extracting text, layout, and other relevant information.

    InputType: image
    OutputType: text
    """

    function: str = "document-image-parsing"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = DocumentImageParsingInputs
    outputs_class: Type[TO] = DocumentImageParsingOutputs


class TranslationInputs(Inputs):
    """Input parameters for Translation."""

    text: InputParam = None
    sourcelanguage: InputParam = None
    targetlanguage: InputParam = None
    script_in: InputParam = None
    script_out: InputParam = None
    dialect_in: InputParam = None
    dialect_out: InputParam = None
    context: InputParam = None

    def __init__(self, node=None):
        """Initialize TranslationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.sourcelanguage = self.create_param(code="sourcelanguage", data_type=DataType.LABEL, is_required=True)
        self.targetlanguage = self.create_param(code="targetlanguage", data_type=DataType.LABEL, is_required=True)
        self.script_in = self.create_param(code="script_in", data_type=DataType.LABEL, is_required=False)
        self.script_out = self.create_param(code="script_out", data_type=DataType.LABEL, is_required=False)
        self.dialect_in = self.create_param(code="dialect_in", data_type=DataType.LABEL, is_required=False)
        self.dialect_out = self.create_param(code="dialect_out", data_type=DataType.LABEL, is_required=False)
        self.context = self.create_param(code="context", data_type=DataType.LABEL, is_required=False)


class TranslationOutputs(Outputs):
    """Output parameters for Translation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TranslationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Translation(AssetNode[TranslationInputs, TranslationOutputs]):
    """Translation node.

    Converts text from one language to another while maintaining the original
    message's essence and context. Crucial for global communication.

    InputType: text
    OutputType: text
    """

    function: str = "translation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TranslationInputs
    outputs_class: Type[TO] = TranslationOutputs


class AudioSourceSeparationInputs(Inputs):
    """Input parameters for AudioSourceSeparation."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioSourceSeparationInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class AudioSourceSeparationOutputs(Outputs):
    """Output parameters for AudioSourceSeparation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioSourceSeparationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class AudioSourceSeparation(AssetNode[AudioSourceSeparationInputs, AudioSourceSeparationOutputs]):
    """AudioSourceSeparation node.

    Audio Source Separation is the process of separating a mixture (e.g. a pop band
    recording) into isolated sounds from individual sources (e.g. just the lead
    vocals).

    InputType: audio
    OutputType: audio
    """

    function: str = "audio-source-separation"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = AudioSourceSeparationInputs
    outputs_class: Type[TO] = AudioSourceSeparationOutputs


class SpeechRecognitionInputs(Inputs):
    """Input parameters for SpeechRecognition."""

    language: InputParam = None
    dialect: InputParam = None
    voice: InputParam = None
    source_audio: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeechRecognitionInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.voice = self.create_param(code="voice", data_type=DataType.LABEL, is_required=False)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class SpeechRecognitionOutputs(Outputs):
    """Output parameters for SpeechRecognition."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeechRecognitionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SpeechRecognition(AssetNode[SpeechRecognitionInputs, SpeechRecognitionOutputs]):
    """SpeechRecognition node.

    Converts spoken language into written text. Useful for transcription services,
    voice assistants, and applications requiring voice-to-text capabilities.

    InputType: audio
    OutputType: text
    """

    function: str = "speech-recognition"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SpeechRecognitionInputs
    outputs_class: Type[TO] = SpeechRecognitionOutputs


class KeywordSpottingInputs(Inputs):
    """Input parameters for KeywordSpotting."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize KeywordSpottingInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)


class KeywordSpottingOutputs(Outputs):
    """Output parameters for KeywordSpotting."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize KeywordSpottingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class KeywordSpotting(AssetNode[KeywordSpottingInputs, KeywordSpottingOutputs]):
    """KeywordSpotting node.

    Keyword Spotting is a function that enables the detection and identification of
    specific words or phrases within a stream of audio, often used in voice-
    activated systems to trigger actions or commands based on recognized keywords.

    InputType: audio
    OutputType: label
    """

    function: str = "keyword-spotting"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = KeywordSpottingInputs
    outputs_class: Type[TO] = KeywordSpottingOutputs


class PartOfSpeechTaggingInputs(Inputs):
    """Input parameters for PartOfSpeechTagging."""

    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize PartOfSpeechTaggingInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class PartOfSpeechTaggingOutputs(Outputs):
    """Output parameters for PartOfSpeechTagging."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize PartOfSpeechTaggingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class PartOfSpeechTagging(AssetNode[PartOfSpeechTaggingInputs, PartOfSpeechTaggingOutputs]):
    """PartOfSpeechTagging node.

    Part of Speech Tagging is a natural language processing task that involves
    assigning each word in a sentence its corresponding part of speech, such as
    noun, verb, adjective, or adverb, based on its role and context within the
    sentence.

    InputType: text
    OutputType: label
    """

    function: str = "part-of-speech-tagging"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = PartOfSpeechTaggingInputs
    outputs_class: Type[TO] = PartOfSpeechTaggingOutputs


class ReferencelessAudioGenerationMetricInputs(Inputs):
    """Input parameters for ReferencelessAudioGenerationMetric."""

    hypotheses: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        """Initialize ReferencelessAudioGenerationMetricInputs."""
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.AUDIO, is_required=True)
        self.sources = self.create_param(code="sources", data_type=DataType.AUDIO, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class ReferencelessAudioGenerationMetricOutputs(Outputs):
    """Output parameters for ReferencelessAudioGenerationMetric."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ReferencelessAudioGenerationMetricOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ReferencelessAudioGenerationMetric(
    BaseMetric[ReferencelessAudioGenerationMetricInputs, ReferencelessAudioGenerationMetricOutputs]
):
    """ReferencelessAudioGenerationMetric node.

    The Referenceless Audio Generation Metric is a tool designed to evaluate the
    quality of generated audio content without the need for a reference or original
    audio sample for comparison.

    InputType: text
    OutputType: text
    """

    function: str = "referenceless-audio-generation-metric"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ReferencelessAudioGenerationMetricInputs
    outputs_class: Type[TO] = ReferencelessAudioGenerationMetricOutputs


class VoiceActivityDetectionInputs(Inputs):
    """Input parameters for VoiceActivityDetection."""

    audio: InputParam = None
    onset: InputParam = None
    offset: InputParam = None
    min_duration_on: InputParam = None
    min_duration_off: InputParam = None

    def __init__(self, node=None):
        """Initialize VoiceActivityDetectionInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.onset = self.create_param(code="onset", data_type=DataType.TEXT, is_required=False)
        self.offset = self.create_param(code="offset", data_type=DataType.TEXT, is_required=False)
        self.min_duration_on = self.create_param(code="min_duration_on", data_type=DataType.TEXT, is_required=False)
        self.min_duration_off = self.create_param(code="min_duration_off", data_type=DataType.TEXT, is_required=False)


class VoiceActivityDetectionOutputs(Outputs):
    """Output parameters for VoiceActivityDetection."""

    data: OutputParam = None
    audio: OutputParam = None

    def __init__(self, node=None):
        """Initialize VoiceActivityDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)


class VoiceActivityDetection(BaseSegmentor[VoiceActivityDetectionInputs, VoiceActivityDetectionOutputs]):
    """VoiceActivityDetection node.

    Determines when a person is speaking in an audio clip. It's an essential
    preprocessing step for other audio-related tasks.

    InputType: audio
    OutputType: audio
    """

    function: str = "voice-activity-detection"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = VoiceActivityDetectionInputs
    outputs_class: Type[TO] = VoiceActivityDetectionOutputs


class SentimentAnalysisInputs(Inputs):
    """Input parameters for SentimentAnalysis."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize SentimentAnalysisInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class SentimentAnalysisOutputs(Outputs):
    """Output parameters for SentimentAnalysis."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SentimentAnalysisOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SentimentAnalysis(AssetNode[SentimentAnalysisInputs, SentimentAnalysisOutputs]):
    """SentimentAnalysis node.

    Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
    piece of text, aiding in understanding user feedback or market sentiment.

    InputType: text
    OutputType: label
    """

    function: str = "sentiment-analysis"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SentimentAnalysisInputs
    outputs_class: Type[TO] = SentimentAnalysisOutputs


class SubtitlingInputs(Inputs):
    """Input parameters for Subtitling."""

    source_audio: InputParam = None
    sourcelanguage: InputParam = None
    dialect_in: InputParam = None
    source_supplier: InputParam = None
    target_supplier: InputParam = None
    targetlanguages: InputParam = None

    def __init__(self, node=None):
        """Initialize SubtitlingInputs."""
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.sourcelanguage = self.create_param(code="sourcelanguage", data_type=DataType.LABEL, is_required=True)
        self.dialect_in = self.create_param(code="dialect_in", data_type=DataType.LABEL, is_required=False)
        self.source_supplier = self.create_param(code="source_supplier", data_type=DataType.LABEL, is_required=False)
        self.target_supplier = self.create_param(code="target_supplier", data_type=DataType.LABEL, is_required=False)
        self.targetlanguages = self.create_param(code="targetlanguages", data_type=DataType.LABEL, is_required=False)


class SubtitlingOutputs(Outputs):
    """Output parameters for Subtitling."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SubtitlingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Subtitling(AssetNode[SubtitlingInputs, SubtitlingOutputs]):
    """Subtitling node.

    Generates accurate subtitles for videos, enhancing accessibility for diverse
    audiences.

    InputType: audio
    OutputType: text
    """

    function: str = "subtitling"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SubtitlingInputs
    outputs_class: Type[TO] = SubtitlingOutputs


class MultiLabelTextClassificationInputs(Inputs):
    """Input parameters for MultiLabelTextClassification."""

    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize MultiLabelTextClassificationInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class MultiLabelTextClassificationOutputs(Outputs):
    """Output parameters for MultiLabelTextClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize MultiLabelTextClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class MultiLabelTextClassification(AssetNode[MultiLabelTextClassificationInputs, MultiLabelTextClassificationOutputs]):
    """MultiLabelTextClassification node.

    Multi Label Text Classification is a natural language processing task where a
    given text is analyzed and assigned multiple relevant labels or categories from
    a predefined set, allowing for the text to belong to more than one category
    simultaneously.

    InputType: text
    OutputType: label
    """

    function: str = "multi-label-text-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = MultiLabelTextClassificationInputs
    outputs_class: Type[TO] = MultiLabelTextClassificationOutputs


class VisemeGenerationInputs(Inputs):
    """Input parameters for VisemeGeneration."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize VisemeGenerationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class VisemeGenerationOutputs(Outputs):
    """Output parameters for VisemeGeneration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize VisemeGenerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class VisemeGeneration(AssetNode[VisemeGenerationInputs, VisemeGenerationOutputs]):
    """VisemeGeneration node.

    Viseme Generation is the process of creating visual representations of
    phonemes, which are the distinct units of sound in speech, to synchronize lip
    movements with spoken words in animations or virtual avatars.

    InputType: text
    OutputType: label
    """

    function: str = "viseme-generation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = VisemeGenerationInputs
    outputs_class: Type[TO] = VisemeGenerationOutputs


class TextSegmenationInputs(Inputs):
    """Input parameters for TextSegmenation."""

    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize TextSegmenationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)


class TextSegmenationOutputs(Outputs):
    """Output parameters for TextSegmenation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextSegmenationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextSegmenation(AssetNode[TextSegmenationInputs, TextSegmenationOutputs]):
    """TextSegmenation node.

    Text Segmentation is the process of dividing a continuous text into meaningful
    units, such as words, sentences, or topics, to facilitate easier analysis and
    understanding.

    InputType: text
    OutputType: text
    """

    function: str = "text-segmenation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextSegmenationInputs
    outputs_class: Type[TO] = TextSegmenationOutputs


class ZeroShotClassificationInputs(Inputs):
    """Input parameters for ZeroShotClassification."""

    text: InputParam = None
    language: InputParam = None
    script_in: InputParam = None

    def __init__(self, node=None):
        """Initialize ZeroShotClassificationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script_in = self.create_param(code="script_in", data_type=DataType.LABEL, is_required=False)


class ZeroShotClassificationOutputs(Outputs):
    """Output parameters for ZeroShotClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ZeroShotClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ZeroShotClassification(AssetNode[ZeroShotClassificationInputs, ZeroShotClassificationOutputs]):
    """ZeroShotClassification node.

    InputType: text
    OutputType: text
    """

    function: str = "zero-shot-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ZeroShotClassificationInputs
    outputs_class: Type[TO] = ZeroShotClassificationOutputs


class TextGenerationInputs(Inputs):
    """Input parameters for TextGeneration."""

    text: InputParam = None
    temperature: InputParam = None
    prompt: InputParam = None
    context: InputParam = None
    language: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize TextGenerationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.temperature = self.create_param(code="temperature", data_type=DataType.NUMBER, is_required=False)
        self.prompt = self.create_param(code="prompt", data_type=DataType.TEXT, is_required=False)
        self.context = self.create_param(code="context", data_type=DataType.TEXT, is_required=False)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextGenerationOutputs(Outputs):
    """Output parameters for TextGeneration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextGenerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextGeneration(AssetNode[TextGenerationInputs, TextGenerationOutputs]):
    """TextGeneration node.

    Creates coherent and contextually relevant textual content based on prompts or
    certain parameters. Useful for chatbots, content creation, and data
    augmentation.

    InputType: text
    OutputType: text
    """

    function: str = "text-generation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextGenerationInputs
    outputs_class: Type[TO] = TextGenerationOutputs


class AudioIntentDetectionInputs(Inputs):
    """Input parameters for AudioIntentDetection."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioIntentDetectionInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)


class AudioIntentDetectionOutputs(Outputs):
    """Output parameters for AudioIntentDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioIntentDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AudioIntentDetection(AssetNode[AudioIntentDetectionInputs, AudioIntentDetectionOutputs]):
    """AudioIntentDetection node.

    Audio Intent Detection is a process that involves analyzing audio signals to
    identify and interpret the underlying intentions or purposes behind spoken
    words, enabling systems to understand and respond appropriately to human
    speech.

    InputType: audio
    OutputType: label
    """

    function: str = "audio-intent-detection"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = AudioIntentDetectionInputs
    outputs_class: Type[TO] = AudioIntentDetectionOutputs


class EntityLinkingInputs(Inputs):
    """Input parameters for EntityLinking."""

    text: InputParam = None
    language: InputParam = None
    domain: InputParam = None

    def __init__(self, node=None):
        """Initialize EntityLinkingInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.domain = self.create_param(code="domain", data_type=DataType.LABEL, is_required=False)


class EntityLinkingOutputs(Outputs):
    """Output parameters for EntityLinking."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize EntityLinkingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class EntityLinking(AssetNode[EntityLinkingInputs, EntityLinkingOutputs]):
    """EntityLinking node.

    Associates identified entities in the text with specific entries in a knowledge
    base or database.

    InputType: text
    OutputType: label
    """

    function: str = "entity-linking"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = EntityLinkingInputs
    outputs_class: Type[TO] = EntityLinkingOutputs


class ConnectionInputs(Inputs):
    """Input parameters for Connection."""

    name: InputParam = None

    def __init__(self, node=None):
        """Initialize ConnectionInputs."""
        super().__init__(node=node)
        self.name = self.create_param(code="name", data_type=DataType.TEXT, is_required=True)


class ConnectionOutputs(Outputs):
    """Output parameters for Connection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ConnectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Connection(AssetNode[ConnectionInputs, ConnectionOutputs]):
    """Connection node.

    Connections are integration that allow you to connect your AI agents to
    external tools

    InputType: text
    OutputType: text
    """

    function: str = "connection"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ConnectionInputs
    outputs_class: Type[TO] = ConnectionOutputs


class VisualQuestionAnsweringInputs(Inputs):
    """Input parameters for VisualQuestionAnswering."""

    text: InputParam = None
    language: InputParam = None
    image: InputParam = None

    def __init__(self, node=None):
        """Initialize VisualQuestionAnsweringInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class VisualQuestionAnsweringOutputs(Outputs):
    """Output parameters for VisualQuestionAnswering."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize VisualQuestionAnsweringOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class VisualQuestionAnswering(AssetNode[VisualQuestionAnsweringInputs, VisualQuestionAnsweringOutputs]):
    """VisualQuestionAnswering node.

    Visual Question Answering (VQA) is a task in artificial intelligence that
    involves analyzing an image and providing accurate, contextually relevant
    answers to questions posed about the visual content of that image.

    InputType: image
    OutputType: video
    """

    function: str = "visual-question-answering"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.VIDEO

    inputs_class: Type[TI] = VisualQuestionAnsweringInputs
    outputs_class: Type[TO] = VisualQuestionAnsweringOutputs


class LoglikelihoodInputs(Inputs):
    """Input parameters for Loglikelihood."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize LoglikelihoodInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class LoglikelihoodOutputs(Outputs):
    """Output parameters for Loglikelihood."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize LoglikelihoodOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.NUMBER)


class Loglikelihood(AssetNode[LoglikelihoodInputs, LoglikelihoodOutputs]):
    """Loglikelihood node.

    The Log Likelihood function measures the probability of observing the given
    data under a specific statistical model by taking the natural logarithm of the
    likelihood function, thereby transforming the product of probabilities into a
    sum, which simplifies the process of optimization and parameter estimation.

    InputType: text
    OutputType: number
    """

    function: str = "loglikelihood"
    input_type: str = DataType.TEXT
    output_type: str = DataType.NUMBER

    inputs_class: Type[TI] = LoglikelihoodInputs
    outputs_class: Type[TO] = LoglikelihoodOutputs


class LanguageIdentificationAudioInputs(Inputs):
    """Input parameters for LanguageIdentificationAudio."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize LanguageIdentificationAudioInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class LanguageIdentificationAudioOutputs(Outputs):
    """Output parameters for LanguageIdentificationAudio."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize LanguageIdentificationAudioOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class LanguageIdentificationAudio(AssetNode[LanguageIdentificationAudioInputs, LanguageIdentificationAudioOutputs]):
    """LanguageIdentificationAudio node.

    The Language Identification Audio function analyzes audio input to determine
    and identify the language being spoken.

    InputType: audio
    OutputType: label
    """

    function: str = "language-identification-audio"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = LanguageIdentificationAudioInputs
    outputs_class: Type[TO] = LanguageIdentificationAudioOutputs


class FactCheckingInputs(Inputs):
    """Input parameters for FactChecking."""

    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize FactCheckingInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class FactCheckingOutputs(Outputs):
    """Output parameters for FactChecking."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize FactCheckingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class FactChecking(AssetNode[FactCheckingInputs, FactCheckingOutputs]):
    """FactChecking node.

    Fact Checking is the process of verifying the accuracy and truthfulness of
    information, statements, or claims by cross-referencing with reliable sources
    and evidence.

    InputType: text
    OutputType: label
    """

    function: str = "fact-checking"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = FactCheckingInputs
    outputs_class: Type[TO] = FactCheckingOutputs


class TableQuestionAnsweringInputs(Inputs):
    """Input parameters for TableQuestionAnswering."""

    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize TableQuestionAnsweringInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)


class TableQuestionAnsweringOutputs(Outputs):
    """Output parameters for TableQuestionAnswering."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TableQuestionAnsweringOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TableQuestionAnswering(AssetNode[TableQuestionAnsweringInputs, TableQuestionAnsweringOutputs]):
    """TableQuestionAnswering node.

    The task of question answering over tables is given an input table (or a set of
    tables) T and a natural language question Q (a user query), output the correct
    answer A

    InputType: text
    OutputType: text
    """

    function: str = "table-question-answering"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TableQuestionAnsweringInputs
    outputs_class: Type[TO] = TableQuestionAnsweringOutputs


class SpeechClassificationInputs(Inputs):
    """Input parameters for SpeechClassification."""

    audio: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeechClassificationInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeechClassificationOutputs(Outputs):
    """Output parameters for SpeechClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeechClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SpeechClassification(AssetNode[SpeechClassificationInputs, SpeechClassificationOutputs]):
    """SpeechClassification node.

    Categorizes audio clips based on their content, aiding in content organization
    and targeted actions.

    InputType: audio
    OutputType: label
    """

    function: str = "speech-classification"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeechClassificationInputs
    outputs_class: Type[TO] = SpeechClassificationOutputs


class InverseTextNormalizationInputs(Inputs):
    """Input parameters for InverseTextNormalization."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize InverseTextNormalizationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class InverseTextNormalizationOutputs(Outputs):
    """Output parameters for InverseTextNormalization."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize InverseTextNormalizationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class InverseTextNormalization(AssetNode[InverseTextNormalizationInputs, InverseTextNormalizationOutputs]):
    """InverseTextNormalization node.

    Inverse Text Normalization is the process of converting spoken or written
    language in its normalized form, such as numbers, dates, and abbreviations,
    back into their original, more complex or detailed textual representations.

    InputType: text
    OutputType: label
    """

    function: str = "inverse-text-normalization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = InverseTextNormalizationInputs
    outputs_class: Type[TO] = InverseTextNormalizationOutputs


class MultiClassImageClassificationInputs(Inputs):
    """Input parameters for MultiClassImageClassification."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize MultiClassImageClassificationInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class MultiClassImageClassificationOutputs(Outputs):
    """Output parameters for MultiClassImageClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize MultiClassImageClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class MultiClassImageClassification(
    AssetNode[MultiClassImageClassificationInputs, MultiClassImageClassificationOutputs]
):
    """MultiClassImageClassification node.

    Multi Class Image Classification is a machine learning task where an algorithm
    is trained to categorize images into one of several predefined classes or
    categories based on their visual content.

    InputType: image
    OutputType: label
    """

    function: str = "multi-class-image-classification"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = MultiClassImageClassificationInputs
    outputs_class: Type[TO] = MultiClassImageClassificationOutputs


class AsrGenderClassificationInputs(Inputs):
    """Input parameters for AsrGenderClassification."""

    source_audio: InputParam = None

    def __init__(self, node=None):
        """Initialize AsrGenderClassificationInputs."""
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)


class AsrGenderClassificationOutputs(Outputs):
    """Output parameters for AsrGenderClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AsrGenderClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AsrGenderClassification(AssetNode[AsrGenderClassificationInputs, AsrGenderClassificationOutputs]):
    """AsrGenderClassification node.

    The ASR Gender Classification function analyzes audio recordings to determine
    and classify the speaker's gender based on their voice characteristics.

    InputType: audio
    OutputType: label
    """

    function: str = "asr-gender-classification"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = AsrGenderClassificationInputs
    outputs_class: Type[TO] = AsrGenderClassificationOutputs


class SummarizationInputs(Inputs):
    """Input parameters for Summarization."""

    text: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize SummarizationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SummarizationOutputs(Outputs):
    """Output parameters for Summarization."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SummarizationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Summarization(AssetNode[SummarizationInputs, SummarizationOutputs]):
    """Summarization node.

    Text summarization is the process of distilling the most important information
    from a source (or sources) to produce an abridged version for a particular user
    (or users) and task (or tasks)

    InputType: text
    OutputType: text
    """

    function: str = "summarization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SummarizationInputs
    outputs_class: Type[TO] = SummarizationOutputs


class TopicModelingInputs(Inputs):
    """Input parameters for TopicModeling."""

    text: InputParam = None
    language: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize TopicModelingInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TopicModelingOutputs(Outputs):
    """Output parameters for TopicModeling."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TopicModelingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TopicModeling(AssetNode[TopicModelingInputs, TopicModelingOutputs]):
    """TopicModeling node.

    Topic modeling is a type of statistical modeling for discovering the abstract
    “topics” that occur in a collection of documents.

    InputType: text
    OutputType: label
    """

    function: str = "topic-modeling"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TopicModelingInputs
    outputs_class: Type[TO] = TopicModelingOutputs


class AudioReconstructionInputs(Inputs):
    """Input parameters for AudioReconstruction."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioReconstructionInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class AudioReconstructionOutputs(Outputs):
    """Output parameters for AudioReconstruction."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioReconstructionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class AudioReconstruction(BaseReconstructor[AudioReconstructionInputs, AudioReconstructionOutputs]):
    """AudioReconstruction node.

    Audio Reconstruction is the process of restoring or recreating audio signals
    from incomplete, damaged, or degraded recordings to achieve a high-quality,
    accurate representation of the original sound.

    InputType: audio
    OutputType: audio
    """

    function: str = "audio-reconstruction"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = AudioReconstructionInputs
    outputs_class: Type[TO] = AudioReconstructionOutputs


class TextEmbeddingInputs(Inputs):
    """Input parameters for TextEmbedding."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize TextEmbeddingInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextEmbeddingOutputs(Outputs):
    """Output parameters for TextEmbedding."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextEmbeddingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextEmbedding(AssetNode[TextEmbeddingInputs, TextEmbeddingOutputs]):
    """TextEmbedding node.

    Text embedding is a process that converts text into numerical vectors,
    capturing the semantic meaning and contextual relationships of words or
    phrases, enabling machines to understand and analyze natural language more
    effectively.

    InputType: text
    OutputType: text
    """

    function: str = "text-embedding"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextEmbeddingInputs
    outputs_class: Type[TO] = TextEmbeddingOutputs


class DetectLanguageFromTextInputs(Inputs):
    """Input parameters for DetectLanguageFromText."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize DetectLanguageFromTextInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class DetectLanguageFromTextOutputs(Outputs):
    """Output parameters for DetectLanguageFromText."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize DetectLanguageFromTextOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class DetectLanguageFromText(AssetNode[DetectLanguageFromTextInputs, DetectLanguageFromTextOutputs]):
    """DetectLanguageFromText node.

    Detect Language From Text

    InputType: text
    OutputType: label
    """

    function: str = "detect-language-from-text"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = DetectLanguageFromTextInputs
    outputs_class: Type[TO] = DetectLanguageFromTextOutputs


class ExtractAudioFromVideoInputs(Inputs):
    """Input parameters for ExtractAudioFromVideo."""

    video: InputParam = None

    def __init__(self, node=None):
        """Initialize ExtractAudioFromVideoInputs."""
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)


class ExtractAudioFromVideoOutputs(Outputs):
    """Output parameters for ExtractAudioFromVideo."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ExtractAudioFromVideoOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class ExtractAudioFromVideo(AssetNode[ExtractAudioFromVideoInputs, ExtractAudioFromVideoOutputs]):
    """ExtractAudioFromVideo node.

    Isolates and extracts audio tracks from video files, aiding in audio analysis
    or transcription tasks.

    InputType: video
    OutputType: audio
    """

    function: str = "extract-audio-from-video"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = ExtractAudioFromVideoInputs
    outputs_class: Type[TO] = ExtractAudioFromVideoOutputs


class SceneDetectionInputs(Inputs):
    """Input parameters for SceneDetection."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize SceneDetectionInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class SceneDetectionOutputs(Outputs):
    """Output parameters for SceneDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SceneDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SceneDetection(AssetNode[SceneDetectionInputs, SceneDetectionOutputs]):
    """SceneDetection node.

    Scene detection is used for detecting transitions between shots in a video to
    split it into basic temporal segments.

    InputType: image
    OutputType: text
    """

    function: str = "scene-detection"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SceneDetectionInputs
    outputs_class: Type[TO] = SceneDetectionOutputs


class TextToImageGenerationInputs(Inputs):
    """Input parameters for TextToImageGeneration."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize TextToImageGenerationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class TextToImageGenerationOutputs(Outputs):
    """Output parameters for TextToImageGeneration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextToImageGenerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.IMAGE)


class TextToImageGeneration(AssetNode[TextToImageGenerationInputs, TextToImageGenerationOutputs]):
    """TextToImageGeneration node.

    Creates a visual representation based on textual input, turning descriptions
    into pictorial forms. Used in creative processes and content generation.

    InputType: text
    OutputType: image
    """

    function: str = "text-to-image-generation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.IMAGE

    inputs_class: Type[TI] = TextToImageGenerationInputs
    outputs_class: Type[TO] = TextToImageGenerationOutputs


class AutoMaskGenerationInputs(Inputs):
    """Input parameters for AutoMaskGeneration."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize AutoMaskGenerationInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class AutoMaskGenerationOutputs(Outputs):
    """Output parameters for AutoMaskGeneration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AutoMaskGenerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AutoMaskGeneration(AssetNode[AutoMaskGenerationInputs, AutoMaskGenerationOutputs]):
    """AutoMaskGeneration node.

    Auto-mask generation refers to the automated process of creating masks in image
    processing or computer vision, typically for segmentation tasks. A mask is a
    binary or multi-class image that labels different parts of an image, usually
    separating the foreground (objects of interest) from the background, or
    identifying specific object classes in an image.

    InputType: image
    OutputType: label
    """

    function: str = "auto-mask-generation"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = AutoMaskGenerationInputs
    outputs_class: Type[TO] = AutoMaskGenerationOutputs


class AudioLanguageIdentificationInputs(Inputs):
    """Input parameters for AudioLanguageIdentification."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioLanguageIdentificationInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class AudioLanguageIdentificationOutputs(Outputs):
    """Output parameters for AudioLanguageIdentification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioLanguageIdentificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AudioLanguageIdentification(AssetNode[AudioLanguageIdentificationInputs, AudioLanguageIdentificationOutputs]):
    """AudioLanguageIdentification node.

    Audio Language Identification is a process that involves analyzing an audio
    recording to determine the language being spoken.

    InputType: audio
    OutputType: label
    """

    function: str = "audio-language-identification"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = AudioLanguageIdentificationInputs
    outputs_class: Type[TO] = AudioLanguageIdentificationOutputs


class FacialRecognitionInputs(Inputs):
    """Input parameters for FacialRecognition."""

    video: InputParam = None

    def __init__(self, node=None):
        """Initialize FacialRecognitionInputs."""
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)


class FacialRecognitionOutputs(Outputs):
    """Output parameters for FacialRecognition."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize FacialRecognitionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class FacialRecognition(AssetNode[FacialRecognitionInputs, FacialRecognitionOutputs]):
    """FacialRecognition node.

    A facial recognition system is a technology capable of matching a human face
    from a digital image or a video frame against a database of faces

    InputType: image
    OutputType: label
    """

    function: str = "facial-recognition"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = FacialRecognitionInputs
    outputs_class: Type[TO] = FacialRecognitionOutputs


class QuestionAnsweringInputs(Inputs):
    """Input parameters for QuestionAnswering."""

    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize QuestionAnsweringInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)


class QuestionAnsweringOutputs(Outputs):
    """Output parameters for QuestionAnswering."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize QuestionAnsweringOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class QuestionAnswering(AssetNode[QuestionAnsweringInputs, QuestionAnsweringOutputs]):
    """QuestionAnswering node.

    building systems that automatically answer questions posed by humans in a
    natural language usually from a given text

    InputType: text
    OutputType: text
    """

    function: str = "question-answering"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = QuestionAnsweringInputs
    outputs_class: Type[TO] = QuestionAnsweringOutputs


class ImageImpaintingInputs(Inputs):
    """Input parameters for ImageImpainting."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageImpaintingInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class ImageImpaintingOutputs(Outputs):
    """Output parameters for ImageImpainting."""

    image: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageImpaintingOutputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class ImageImpainting(AssetNode[ImageImpaintingInputs, ImageImpaintingOutputs]):
    """ImageImpainting node.

    Image inpainting is a process that involves filling in missing or damaged parts
    of an image in a way that is visually coherent and seamlessly blends with the
    surrounding areas, often using advanced algorithms and techniques to restore
    the image to its original or intended appearance.

    InputType: image
    OutputType: image
    """

    function: str = "image-impainting"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.IMAGE

    inputs_class: Type[TI] = ImageImpaintingInputs
    outputs_class: Type[TO] = ImageImpaintingOutputs


class TextReconstructionInputs(Inputs):
    """Input parameters for TextReconstruction."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize TextReconstructionInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class TextReconstructionOutputs(Outputs):
    """Output parameters for TextReconstruction."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextReconstructionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextReconstruction(BaseReconstructor[TextReconstructionInputs, TextReconstructionOutputs]):
    """TextReconstruction node.

    Text Reconstruction is a process that involves piecing together fragmented or
    incomplete text data to restore it to its original, coherent form.

    InputType: text
    OutputType: text
    """

    function: str = "text-reconstruction"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextReconstructionInputs
    outputs_class: Type[TO] = TextReconstructionOutputs


class ScriptExecutionInputs(Inputs):
    """Input parameters for ScriptExecution."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize ScriptExecutionInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class ScriptExecutionOutputs(Outputs):
    """Output parameters for ScriptExecution."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ScriptExecutionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ScriptExecution(AssetNode[ScriptExecutionInputs, ScriptExecutionOutputs]):
    """ScriptExecution node.

    Script Execution refers to the process of running a set of programmed
    instructions or code within a computing environment, enabling the automated
    performance of tasks, calculations, or operations as defined by the script.

    InputType: text
    OutputType: text
    """

    function: str = "script-execution"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ScriptExecutionInputs
    outputs_class: Type[TO] = ScriptExecutionOutputs


class SemanticSegmentationInputs(Inputs):
    """Input parameters for SemanticSegmentation."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize SemanticSegmentationInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class SemanticSegmentationOutputs(Outputs):
    """Output parameters for SemanticSegmentation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SemanticSegmentationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SemanticSegmentation(AssetNode[SemanticSegmentationInputs, SemanticSegmentationOutputs]):
    """SemanticSegmentation node.

    Semantic segmentation is a computer vision process that involves classifying
    each pixel in an image into a predefined category, effectively partitioning the
    image into meaningful segments based on the objects or regions they represent.

    InputType: image
    OutputType: label
    """

    function: str = "semantic-segmentation"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SemanticSegmentationInputs
    outputs_class: Type[TO] = SemanticSegmentationOutputs


class AudioEmotionDetectionInputs(Inputs):
    """Input parameters for AudioEmotionDetection."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioEmotionDetectionInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)


class AudioEmotionDetectionOutputs(Outputs):
    """Output parameters for AudioEmotionDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioEmotionDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AudioEmotionDetection(AssetNode[AudioEmotionDetectionInputs, AudioEmotionDetectionOutputs]):
    """AudioEmotionDetection node.

    Audio Emotion Detection is a technology that analyzes vocal characteristics and
    patterns in audio recordings to identify and classify the emotional state of
    the speaker.

    InputType: audio
    OutputType: label
    """

    function: str = "audio-emotion-detection"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = AudioEmotionDetectionInputs
    outputs_class: Type[TO] = AudioEmotionDetectionOutputs


class ImageCaptioningInputs(Inputs):
    """Input parameters for ImageCaptioning."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageCaptioningInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class ImageCaptioningOutputs(Outputs):
    """Output parameters for ImageCaptioning."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageCaptioningOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ImageCaptioning(AssetNode[ImageCaptioningInputs, ImageCaptioningOutputs]):
    """ImageCaptioning node.

    Image Captioning is a process that involves generating a textual description of
    an image, typically using machine learning models to analyze the visual content
    and produce coherent and contextually relevant sentences that describe the
    objects, actions, and scenes depicted in the image.

    InputType: image
    OutputType: text
    """

    function: str = "image-captioning"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ImageCaptioningInputs
    outputs_class: Type[TO] = ImageCaptioningOutputs


class SplitOnLinebreakInputs(Inputs):
    """Input parameters for SplitOnLinebreak."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize SplitOnLinebreakInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class SplitOnLinebreakOutputs(Outputs):
    """Output parameters for SplitOnLinebreak."""

    data: OutputParam = None
    audio: OutputParam = None

    def __init__(self, node=None):
        """Initialize SplitOnLinebreakOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)


class SplitOnLinebreak(BaseSegmentor[SplitOnLinebreakInputs, SplitOnLinebreakOutputs]):
    """SplitOnLinebreak node.

    The "Split On Linebreak" function divides a given string into a list of
    substrings, using linebreaks (newline characters) as the points of separation.

    InputType: text
    OutputType: text
    """

    function: str = "split-on-linebreak"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SplitOnLinebreakInputs
    outputs_class: Type[TO] = SplitOnLinebreakOutputs


class StyleTransferInputs(Inputs):
    """Input parameters for StyleTransfer."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize StyleTransferInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class StyleTransferOutputs(Outputs):
    """Output parameters for StyleTransfer."""

    image: OutputParam = None

    def __init__(self, node=None):
        """Initialize StyleTransferOutputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class StyleTransfer(AssetNode[StyleTransferInputs, StyleTransferOutputs]):
    """StyleTransfer node.

    Style Transfer is a technique in artificial intelligence that applies the
    visual style of one image (such as the brushstrokes of a famous painting) to
    the content of another image, effectively blending the artistic elements of the
    first image with the subject matter of the second.

    InputType: image
    OutputType: image
    """

    function: str = "style-transfer"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.IMAGE

    inputs_class: Type[TI] = StyleTransferInputs
    outputs_class: Type[TO] = StyleTransferOutputs


class BaseModelInputs(Inputs):
    """Input parameters for BaseModel."""

    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize BaseModelInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class BaseModelOutputs(Outputs):
    """Output parameters for BaseModel."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize BaseModelOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class BaseModel(AssetNode[BaseModelInputs, BaseModelOutputs]):
    """BaseModel node.

    The Base-Model function serves as a foundational framework designed to provide
    essential features and capabilities upon which more specialized or advanced
    models can be built and customized.

    InputType: text
    OutputType: text
    """

    function: str = "base-model"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = BaseModelInputs
    outputs_class: Type[TO] = BaseModelOutputs


class ImageManipulationInputs(Inputs):
    """Input parameters for ImageManipulation."""

    image: InputParam = None
    targetimage: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageManipulationInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.targetimage = self.create_param(code="targetimage", data_type=DataType.IMAGE, is_required=True)


class ImageManipulationOutputs(Outputs):
    """Output parameters for ImageManipulation."""

    image: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageManipulationOutputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class ImageManipulation(AssetNode[ImageManipulationInputs, ImageManipulationOutputs]):
    """ImageManipulation node.

    Image Manipulation refers to the process of altering or enhancing digital
    images using various techniques and tools to achieve desired visual effects,
    correct imperfections, or transform the image's appearance.

    InputType: image
    OutputType: image
    """

    function: str = "image-manipulation"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.IMAGE

    inputs_class: Type[TI] = ImageManipulationInputs
    outputs_class: Type[TO] = ImageManipulationOutputs


class VideoEmbeddingInputs(Inputs):
    """Input parameters for VideoEmbedding."""

    language: InputParam = None
    video: InputParam = None

    def __init__(self, node=None):
        """Initialize VideoEmbeddingInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=False)


class VideoEmbeddingOutputs(Outputs):
    """Output parameters for VideoEmbedding."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize VideoEmbeddingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.EMBEDDING)


class VideoEmbedding(AssetNode[VideoEmbeddingInputs, VideoEmbeddingOutputs]):
    """VideoEmbedding node.

    Video Embedding is a process that transforms video content into a fixed-
    dimensional vector representation, capturing essential features and patterns to
    facilitate tasks such as retrieval, classification, and recommendation.

    InputType: video
    OutputType: embedding
    """

    function: str = "video-embedding"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.EMBEDDING

    inputs_class: Type[TI] = VideoEmbeddingInputs
    outputs_class: Type[TO] = VideoEmbeddingOutputs


class DialectDetectionInputs(Inputs):
    """Input parameters for DialectDetection."""

    audio: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize DialectDetectionInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)


class DialectDetectionOutputs(Outputs):
    """Output parameters for DialectDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize DialectDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class DialectDetection(AssetNode[DialectDetectionInputs, DialectDetectionOutputs]):
    """DialectDetection node.

    Identifies specific dialects within a language, aiding in localized content
    creation or user experience personalization.

    InputType: audio
    OutputType: text
    """

    function: str = "dialect-detection"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = DialectDetectionInputs
    outputs_class: Type[TO] = DialectDetectionOutputs


class FillTextMaskInputs(Inputs):
    """Input parameters for FillTextMask."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize FillTextMaskInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class FillTextMaskOutputs(Outputs):
    """Output parameters for FillTextMask."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize FillTextMaskOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class FillTextMask(AssetNode[FillTextMaskInputs, FillTextMaskOutputs]):
    """FillTextMask node.

    Completes missing parts of a text based on the context, ideal for content
    generation or data augmentation tasks.

    InputType: text
    OutputType: text
    """

    function: str = "fill-text-mask"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = FillTextMaskInputs
    outputs_class: Type[TO] = FillTextMaskOutputs


class ActivityDetectionInputs(Inputs):
    """Input parameters for ActivityDetection."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ActivityDetectionInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class ActivityDetectionOutputs(Outputs):
    """Output parameters for ActivityDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ActivityDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ActivityDetection(AssetNode[ActivityDetectionInputs, ActivityDetectionOutputs]):
    """ActivityDetection node.

    detection of the presence or absence of human speech, used in speech
    processing.

    InputType: audio
    OutputType: label
    """

    function: str = "activity-detection"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = ActivityDetectionInputs
    outputs_class: Type[TO] = ActivityDetectionOutputs


class SelectSupplierForTranslationInputs(Inputs):
    """Input parameters for SelectSupplierForTranslation."""

    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize SelectSupplierForTranslationInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class SelectSupplierForTranslationOutputs(Outputs):
    """Output parameters for SelectSupplierForTranslation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SelectSupplierForTranslationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SelectSupplierForTranslation(AssetNode[SelectSupplierForTranslationInputs, SelectSupplierForTranslationOutputs]):
    """SelectSupplierForTranslation node.

    Supplier For Translation

    InputType: text
    OutputType: label
    """

    function: str = "select-supplier-for-translation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SelectSupplierForTranslationInputs
    outputs_class: Type[TO] = SelectSupplierForTranslationOutputs


class ExpressionDetectionInputs(Inputs):
    """Input parameters for ExpressionDetection."""

    media: InputParam = None

    def __init__(self, node=None):
        """Initialize ExpressionDetectionInputs."""
        super().__init__(node=node)
        self.media = self.create_param(code="media", data_type=DataType.IMAGE, is_required=True)


class ExpressionDetectionOutputs(Outputs):
    """Output parameters for ExpressionDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ExpressionDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ExpressionDetection(AssetNode[ExpressionDetectionInputs, ExpressionDetectionOutputs]):
    """ExpressionDetection node.

    Expression Detection is the process of identifying and analyzing facial
    expressions to interpret emotions or intentions using AI and computer vision
    techniques.

    InputType: text
    OutputType: label
    """

    function: str = "expression-detection"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = ExpressionDetectionInputs
    outputs_class: Type[TO] = ExpressionDetectionOutputs


class VideoGenerationInputs(Inputs):
    """Input parameters for VideoGeneration."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize VideoGenerationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class VideoGenerationOutputs(Outputs):
    """Output parameters for VideoGeneration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize VideoGenerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.VIDEO)


class VideoGeneration(AssetNode[VideoGenerationInputs, VideoGenerationOutputs]):
    """VideoGeneration node.

    Produces video content based on specific inputs or datasets. Can be used for
    simulations, animations, or even deepfake detection.

    InputType: text
    OutputType: video
    """

    function: str = "video-generation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.VIDEO

    inputs_class: Type[TI] = VideoGenerationInputs
    outputs_class: Type[TO] = VideoGenerationOutputs


class ImageAnalysisInputs(Inputs):
    """Input parameters for ImageAnalysis."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageAnalysisInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class ImageAnalysisOutputs(Outputs):
    """Output parameters for ImageAnalysis."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageAnalysisOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ImageAnalysis(AssetNode[ImageAnalysisInputs, ImageAnalysisOutputs]):
    """ImageAnalysis node.

    Image analysis is the extraction of meaningful information from images

    InputType: image
    OutputType: label
    """

    function: str = "image-analysis"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = ImageAnalysisInputs
    outputs_class: Type[TO] = ImageAnalysisOutputs


class NoiseRemovalInputs(Inputs):
    """Input parameters for NoiseRemoval."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize NoiseRemovalInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)


class NoiseRemovalOutputs(Outputs):
    """Output parameters for NoiseRemoval."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize NoiseRemovalOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class NoiseRemoval(AssetNode[NoiseRemovalInputs, NoiseRemovalOutputs]):
    """NoiseRemoval node.

    Noise Removal is a process that involves identifying and eliminating unwanted
    random variations or disturbances from an audio signal to enhance the clarity
    and quality of the underlying information.

    InputType: audio
    OutputType: audio
    """

    function: str = "noise-removal"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = NoiseRemovalInputs
    outputs_class: Type[TO] = NoiseRemovalOutputs


class ImageAndVideoAnalysisInputs(Inputs):
    """Input parameters for ImageAndVideoAnalysis."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageAndVideoAnalysisInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class ImageAndVideoAnalysisOutputs(Outputs):
    """Output parameters for ImageAndVideoAnalysis."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageAndVideoAnalysisOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ImageAndVideoAnalysis(AssetNode[ImageAndVideoAnalysisInputs, ImageAndVideoAnalysisOutputs]):
    """ImageAndVideoAnalysis node.

    InputType: image
    OutputType: text
    """

    function: str = "image-and-video-analysis"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ImageAndVideoAnalysisInputs
    outputs_class: Type[TO] = ImageAndVideoAnalysisOutputs


class KeywordExtractionInputs(Inputs):
    """Input parameters for KeywordExtraction."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize KeywordExtractionInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class KeywordExtractionOutputs(Outputs):
    """Output parameters for KeywordExtraction."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize KeywordExtractionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class KeywordExtraction(AssetNode[KeywordExtractionInputs, KeywordExtractionOutputs]):
    """KeywordExtraction node.

    It helps concise the text and obtain relevant keywords Example use-cases are
    finding topics of interest from a news article and identifying the problems
    based on customer reviews and so.

    InputType: text
    OutputType: label
    """

    function: str = "keyword-extraction"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = KeywordExtractionInputs
    outputs_class: Type[TO] = KeywordExtractionOutputs


class SplitOnSilenceInputs(Inputs):
    """Input parameters for SplitOnSilence."""

    audio: InputParam = None

    def __init__(self, node=None):
        """Initialize SplitOnSilenceInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class SplitOnSilenceOutputs(Outputs):
    """Output parameters for SplitOnSilence."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SplitOnSilenceOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class SplitOnSilence(AssetNode[SplitOnSilenceInputs, SplitOnSilenceOutputs]):
    """SplitOnSilence node.

    The "Split On Silence" function divides an audio recording into separate
    segments based on periods of silence, allowing for easier editing and analysis
    of individual sections.

    InputType: audio
    OutputType: audio
    """

    function: str = "split-on-silence"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = SplitOnSilenceInputs
    outputs_class: Type[TO] = SplitOnSilenceOutputs


class IntentRecognitionInputs(Inputs):
    """Input parameters for IntentRecognition."""

    audio: InputParam = None
    language: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize IntentRecognitionInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class IntentRecognitionOutputs(Outputs):
    """Output parameters for IntentRecognition."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize IntentRecognitionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class IntentRecognition(AssetNode[IntentRecognitionInputs, IntentRecognitionOutputs]):
    """IntentRecognition node.

    classify the user's utterance (provided in varied natural language)  or text
    into one of several predefined classes, that is, intents.

    InputType: audio
    OutputType: text
    """

    function: str = "intent-recognition"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = IntentRecognitionInputs
    outputs_class: Type[TO] = IntentRecognitionOutputs


class DepthEstimationInputs(Inputs):
    """Input parameters for DepthEstimation."""

    language: InputParam = None
    image: InputParam = None

    def __init__(self, node=None):
        """Initialize DepthEstimationInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class DepthEstimationOutputs(Outputs):
    """Output parameters for DepthEstimation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize DepthEstimationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class DepthEstimation(AssetNode[DepthEstimationInputs, DepthEstimationOutputs]):
    """DepthEstimation node.

    Depth estimation is a computational process that determines the distance of
    objects from a viewpoint, typically using visual data from cameras or sensors
    to create a three-dimensional understanding of a scene.

    InputType: image
    OutputType: text
    """

    function: str = "depth-estimation"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = DepthEstimationInputs
    outputs_class: Type[TO] = DepthEstimationOutputs


class ConnectorInputs(Inputs):
    """Input parameters for Connector."""

    name: InputParam = None

    def __init__(self, node=None):
        """Initialize ConnectorInputs."""
        super().__init__(node=node)
        self.name = self.create_param(code="name", data_type=DataType.TEXT, is_required=True)


class ConnectorOutputs(Outputs):
    """Output parameters for Connector."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ConnectorOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Connector(AssetNode[ConnectorInputs, ConnectorOutputs]):
    """Connector node.

    Connectors are integration that allow you to connect your AI agents to external
    tools

    InputType: text
    OutputType: text
    """

    function: str = "connector"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ConnectorInputs
    outputs_class: Type[TO] = ConnectorOutputs


class SpeakerRecognitionInputs(Inputs):
    """Input parameters for SpeakerRecognition."""

    audio: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeakerRecognitionInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeakerRecognitionOutputs(Outputs):
    """Output parameters for SpeakerRecognition."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeakerRecognitionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SpeakerRecognition(AssetNode[SpeakerRecognitionInputs, SpeakerRecognitionOutputs]):
    """SpeakerRecognition node.

    In speaker identification, an utterance from an unknown speaker is analyzed and
    compared with speech models of known speakers.

    InputType: audio
    OutputType: label
    """

    function: str = "speaker-recognition"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeakerRecognitionInputs
    outputs_class: Type[TO] = SpeakerRecognitionOutputs


class SyntaxAnalysisInputs(Inputs):
    """Input parameters for SyntaxAnalysis."""

    text: InputParam = None
    language: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize SyntaxAnalysisInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.TEXT, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.TEXT, is_required=False)


class SyntaxAnalysisOutputs(Outputs):
    """Output parameters for SyntaxAnalysis."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SyntaxAnalysisOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SyntaxAnalysis(AssetNode[SyntaxAnalysisInputs, SyntaxAnalysisOutputs]):
    """SyntaxAnalysis node.

    Is the process of analyzing natural language with the rules of a formal
    grammar. Grammatical rules are applied to categories and groups of words, not
    individual words. Syntactic analysis basically assigns a semantic structure to
    text.

    InputType: text
    OutputType: text
    """

    function: str = "syntax-analysis"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SyntaxAnalysisInputs
    outputs_class: Type[TO] = SyntaxAnalysisOutputs


class EntitySentimentAnalysisInputs(Inputs):
    """Input parameters for EntitySentimentAnalysis."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize EntitySentimentAnalysisInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class EntitySentimentAnalysisOutputs(Outputs):
    """Output parameters for EntitySentimentAnalysis."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize EntitySentimentAnalysisOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class EntitySentimentAnalysis(AssetNode[EntitySentimentAnalysisInputs, EntitySentimentAnalysisOutputs]):
    """EntitySentimentAnalysis node.

    Entity Sentiment Analysis combines both entity analysis and sentiment analysis
    and attempts to determine the sentiment (positive or negative) expressed about
    entities within the text.

    InputType: text
    OutputType: label
    """

    function: str = "entity-sentiment-analysis"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = EntitySentimentAnalysisInputs
    outputs_class: Type[TO] = EntitySentimentAnalysisOutputs


class ClassificationMetricInputs(Inputs):
    """Input parameters for ClassificationMetric."""

    hypotheses: InputParam = None
    references: InputParam = None
    lowerIsBetter: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        """Initialize ClassificationMetricInputs."""
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.LABEL, is_required=True)
        self.references = self.create_param(code="references", data_type=DataType.LABEL, is_required=True)
        self.lowerIsBetter = self.create_param(code="lowerIsBetter", data_type=DataType.TEXT, is_required=False)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class ClassificationMetricOutputs(Outputs):
    """Output parameters for ClassificationMetric."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ClassificationMetricOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.NUMBER)


class ClassificationMetric(BaseMetric[ClassificationMetricInputs, ClassificationMetricOutputs]):
    """ClassificationMetric node.

    A Classification Metric is a quantitative measure used to evaluate the quality
    and effectiveness of classification models.

    InputType: text
    OutputType: text
    """

    function: str = "classification-metric"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ClassificationMetricInputs
    outputs_class: Type[TO] = ClassificationMetricOutputs


class TextDetectionInputs(Inputs):
    """Input parameters for TextDetection."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize TextDetectionInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class TextDetectionOutputs(Outputs):
    """Output parameters for TextDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextDetection(AssetNode[TextDetectionInputs, TextDetectionOutputs]):
    """TextDetection node.

    detect text regions in the complex background and label them with bounding
    boxes.

    InputType: image
    OutputType: text
    """

    function: str = "text-detection"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextDetectionInputs
    outputs_class: Type[TO] = TextDetectionOutputs


class GuardrailsInputs(Inputs):
    """Input parameters for Guardrails."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize GuardrailsInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class GuardrailsOutputs(Outputs):
    """Output parameters for Guardrails."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize GuardrailsOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class Guardrails(AssetNode[GuardrailsInputs, GuardrailsOutputs]):
    """Guardrails node.

     Guardrails are governance rules that enforce security, compliance, and
    operational best practices, helping prevent mistakes and detect suspicious
    activity

    InputType: text
    OutputType: text
    """

    function: str = "guardrails"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = GuardrailsInputs
    outputs_class: Type[TO] = GuardrailsOutputs


class EmotionDetectionInputs(Inputs):
    """Input parameters for EmotionDetection."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize EmotionDetectionInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class EmotionDetectionOutputs(Outputs):
    """Output parameters for EmotionDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize EmotionDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class EmotionDetection(AssetNode[EmotionDetectionInputs, EmotionDetectionOutputs]):
    """EmotionDetection node.

    Identifies human emotions from text or audio, enhancing user experience in
    chatbots or customer feedback analysis.

    InputType: text
    OutputType: label
    """

    function: str = "emotion-detection"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = EmotionDetectionInputs
    outputs_class: Type[TO] = EmotionDetectionOutputs


class VideoForcedAlignmentInputs(Inputs):
    """Input parameters for VideoForcedAlignment."""

    video: InputParam = None
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize VideoForcedAlignmentInputs."""
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class VideoForcedAlignmentOutputs(Outputs):
    """Output parameters for VideoForcedAlignment."""

    text: OutputParam = None
    video: OutputParam = None

    def __init__(self, node=None):
        """Initialize VideoForcedAlignmentOutputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO)


class VideoForcedAlignment(AssetNode[VideoForcedAlignmentInputs, VideoForcedAlignmentOutputs]):
    """VideoForcedAlignment node.

    Aligns the transcription of spoken content in a video with its corresponding
    timecodes, facilitating subtitle creation.

    InputType: video
    OutputType: video
    """

    function: str = "video-forced-alignment"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.VIDEO

    inputs_class: Type[TI] = VideoForcedAlignmentInputs
    outputs_class: Type[TO] = VideoForcedAlignmentOutputs


class ImageContentModerationInputs(Inputs):
    """Input parameters for ImageContentModeration."""

    image: InputParam = None
    min_confidence: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageContentModerationInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.min_confidence = self.create_param(code="min_confidence", data_type=DataType.TEXT, is_required=False)


class ImageContentModerationOutputs(Outputs):
    """Output parameters for ImageContentModeration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageContentModerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ImageContentModeration(AssetNode[ImageContentModerationInputs, ImageContentModerationOutputs]):
    """ImageContentModeration node.

    Detects and filters out inappropriate or harmful images, essential for
    platforms with user-generated visual content.

    InputType: image
    OutputType: label
    """

    function: str = "image-content-moderation"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = ImageContentModerationInputs
    outputs_class: Type[TO] = ImageContentModerationOutputs


class TextSummarizationInputs(Inputs):
    """Input parameters for TextSummarization."""

    text: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize TextSummarizationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class TextSummarizationOutputs(Outputs):
    """Output parameters for TextSummarization."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextSummarizationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextSummarization(AssetNode[TextSummarizationInputs, TextSummarizationOutputs]):
    """TextSummarization node.

    Extracts the main points from a larger body of text, producing a concise
    summary without losing the primary message.

    InputType: text
    OutputType: text
    """

    function: str = "text-summarization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextSummarizationInputs
    outputs_class: Type[TO] = TextSummarizationOutputs


class ImageToVideoGenerationInputs(Inputs):
    """Input parameters for ImageToVideoGeneration."""

    language: InputParam = None
    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageToVideoGenerationInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class ImageToVideoGenerationOutputs(Outputs):
    """Output parameters for ImageToVideoGeneration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageToVideoGenerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.VIDEO)


class ImageToVideoGeneration(AssetNode[ImageToVideoGenerationInputs, ImageToVideoGenerationOutputs]):
    """ImageToVideoGeneration node.

    The Image To Video Generation function transforms a series of static images
    into a cohesive, dynamic video sequence, often incorporating transitions,
    effects, and synchronization with audio to create a visually engaging
    narrative.

    InputType: image
    OutputType: video
    """

    function: str = "image-to-video-generation"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.VIDEO

    inputs_class: Type[TI] = ImageToVideoGenerationInputs
    outputs_class: Type[TO] = ImageToVideoGenerationOutputs


class VideoUnderstandingInputs(Inputs):
    """Input parameters for VideoUnderstanding."""

    video: InputParam = None
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize VideoUnderstandingInputs."""
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class VideoUnderstandingOutputs(Outputs):
    """Output parameters for VideoUnderstanding."""

    text: OutputParam = None

    def __init__(self, node=None):
        """Initialize VideoUnderstandingOutputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT)


class VideoUnderstanding(AssetNode[VideoUnderstandingInputs, VideoUnderstandingOutputs]):
    """VideoUnderstanding node.

    Video Understanding is the process of analyzing and interpreting video content
    to extract meaningful information, such as identifying objects, actions,
    events, and contextual relationships within the footage.

    InputType: video
    OutputType: text
    """

    function: str = "video-understanding"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = VideoUnderstandingInputs
    outputs_class: Type[TO] = VideoUnderstandingOutputs


class TextGenerationMetricDefaultInputs(Inputs):
    """Input parameters for TextGenerationMetricDefault."""

    hypotheses: InputParam = None
    references: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        """Initialize TextGenerationMetricDefaultInputs."""
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.TEXT, is_required=True)
        self.references = self.create_param(code="references", data_type=DataType.TEXT, is_required=False)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class TextGenerationMetricDefaultOutputs(Outputs):
    """Output parameters for TextGenerationMetricDefault."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextGenerationMetricDefaultOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextGenerationMetricDefault(BaseMetric[TextGenerationMetricDefaultInputs, TextGenerationMetricDefaultOutputs]):
    """TextGenerationMetricDefault node.

    The "Text Generation Metric Default" function provides a standard set of
    evaluation metrics for assessing the quality and performance of text generation
    models.

    InputType: text
    OutputType: text
    """

    function: str = "text-generation-metric-default"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextGenerationMetricDefaultInputs
    outputs_class: Type[TO] = TextGenerationMetricDefaultOutputs


class TextToVideoGenerationInputs(Inputs):
    """Input parameters for TextToVideoGeneration."""

    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize TextToVideoGenerationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)


class TextToVideoGenerationOutputs(Outputs):
    """Output parameters for TextToVideoGeneration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextToVideoGenerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.VIDEO)


class TextToVideoGeneration(AssetNode[TextToVideoGenerationInputs, TextToVideoGenerationOutputs]):
    """TextToVideoGeneration node.

    Text To Video Generation is a process that converts written descriptions or
    scripts into dynamic, visual video content using advanced algorithms and
    artificial intelligence.

    InputType: text
    OutputType: video
    """

    function: str = "text-to-video-generation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.VIDEO

    inputs_class: Type[TI] = TextToVideoGenerationInputs
    outputs_class: Type[TO] = TextToVideoGenerationOutputs


class VideoLabelDetectionInputs(Inputs):
    """Input parameters for VideoLabelDetection."""

    video: InputParam = None
    min_confidence: InputParam = None

    def __init__(self, node=None):
        """Initialize VideoLabelDetectionInputs."""
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.min_confidence = self.create_param(code="min_confidence", data_type=DataType.TEXT, is_required=False)


class VideoLabelDetectionOutputs(Outputs):
    """Output parameters for VideoLabelDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize VideoLabelDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class VideoLabelDetection(AssetNode[VideoLabelDetectionInputs, VideoLabelDetectionOutputs]):
    """VideoLabelDetection node.

    Identifies and tags objects, scenes, or activities within a video. Useful for
    content indexing and recommendation systems.

    InputType: video
    OutputType: label
    """

    function: str = "video-label-detection"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = VideoLabelDetectionInputs
    outputs_class: Type[TO] = VideoLabelDetectionOutputs


class TextSpamDetectionInputs(Inputs):
    """Input parameters for TextSpamDetection."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize TextSpamDetectionInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextSpamDetectionOutputs(Outputs):
    """Output parameters for TextSpamDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextSpamDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextSpamDetection(AssetNode[TextSpamDetectionInputs, TextSpamDetectionOutputs]):
    """TextSpamDetection node.

    Identifies and filters out unwanted or irrelevant text content, ideal for
    moderating user-generated content or ensuring quality in communication
    platforms.

    InputType: text
    OutputType: label
    """

    function: str = "text-spam-detection"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextSpamDetectionInputs
    outputs_class: Type[TO] = TextSpamDetectionOutputs


class TextContentModerationInputs(Inputs):
    """Input parameters for TextContentModeration."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize TextContentModerationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextContentModerationOutputs(Outputs):
    """Output parameters for TextContentModeration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextContentModerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextContentModeration(AssetNode[TextContentModerationInputs, TextContentModerationOutputs]):
    """TextContentModeration node.

    Scans and identifies potentially harmful, offensive, or inappropriate textual
    content, ensuring safer user environments.

    InputType: text
    OutputType: label
    """

    function: str = "text-content-moderation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextContentModerationInputs
    outputs_class: Type[TO] = TextContentModerationOutputs


class AudioTranscriptImprovementInputs(Inputs):
    """Input parameters for AudioTranscriptImprovement."""

    language: InputParam = None
    dialect: InputParam = None
    source_supplier: InputParam = None
    is_medical: InputParam = None
    source_audio: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioTranscriptImprovementInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.source_supplier = self.create_param(code="source_supplier", data_type=DataType.LABEL, is_required=False)
        self.is_medical = self.create_param(code="is_medical", data_type=DataType.TEXT, is_required=True)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class AudioTranscriptImprovementOutputs(Outputs):
    """Output parameters for AudioTranscriptImprovement."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioTranscriptImprovementOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class AudioTranscriptImprovement(AssetNode[AudioTranscriptImprovementInputs, AudioTranscriptImprovementOutputs]):
    """AudioTranscriptImprovement node.

    Refines and corrects transcriptions generated from audio data, improving
    readability and accuracy.

    InputType: audio
    OutputType: text
    """

    function: str = "audio-transcript-improvement"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = AudioTranscriptImprovementInputs
    outputs_class: Type[TO] = AudioTranscriptImprovementOutputs


class AudioTranscriptAnalysisInputs(Inputs):
    """Input parameters for AudioTranscriptAnalysis."""

    language: InputParam = None
    dialect: InputParam = None
    source_supplier: InputParam = None
    source_audio: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioTranscriptAnalysisInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.source_supplier = self.create_param(code="source_supplier", data_type=DataType.LABEL, is_required=False)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class AudioTranscriptAnalysisOutputs(Outputs):
    """Output parameters for AudioTranscriptAnalysis."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioTranscriptAnalysisOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class AudioTranscriptAnalysis(AssetNode[AudioTranscriptAnalysisInputs, AudioTranscriptAnalysisOutputs]):
    """AudioTranscriptAnalysis node.

    Analyzes transcribed audio data for insights, patterns, or specific information
    extraction.

    InputType: audio
    OutputType: text
    """

    function: str = "audio-transcript-analysis"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = AudioTranscriptAnalysisInputs
    outputs_class: Type[TO] = AudioTranscriptAnalysisOutputs


class SpeechNonSpeechClassificationInputs(Inputs):
    """Input parameters for SpeechNonSpeechClassification."""

    audio: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeechNonSpeechClassificationInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeechNonSpeechClassificationOutputs(Outputs):
    """Output parameters for SpeechNonSpeechClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeechNonSpeechClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SpeechNonSpeechClassification(
    AssetNode[SpeechNonSpeechClassificationInputs, SpeechNonSpeechClassificationOutputs]
):
    """SpeechNonSpeechClassification node.

    Differentiates between speech and non-speech audio segments. Great for editing
    software and transcription services to exclude irrelevant audio.

    InputType: audio
    OutputType: label
    """

    function: str = "speech-non-speech-classification"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeechNonSpeechClassificationInputs
    outputs_class: Type[TO] = SpeechNonSpeechClassificationOutputs


class AudioGenerationMetricInputs(Inputs):
    """Input parameters for AudioGenerationMetric."""

    hypotheses: InputParam = None
    references: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioGenerationMetricInputs."""
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.AUDIO, is_required=True)
        self.references = self.create_param(code="references", data_type=DataType.AUDIO, is_required=False)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class AudioGenerationMetricOutputs(Outputs):
    """Output parameters for AudioGenerationMetric."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioGenerationMetricOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class AudioGenerationMetric(BaseMetric[AudioGenerationMetricInputs, AudioGenerationMetricOutputs]):
    """AudioGenerationMetric node.

    The Audio Generation Metric is a quantitative measure used to evaluate the
    quality, accuracy, and overall performance of audio generated by artificial
    intelligence systems, often considering factors such as fidelity,
    intelligibility, and similarity to human-produced audio.

    InputType: text
    OutputType: text
    """

    function: str = "audio-generation-metric"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = AudioGenerationMetricInputs
    outputs_class: Type[TO] = AudioGenerationMetricOutputs


class NamedEntityRecognitionInputs(Inputs):
    """Input parameters for NamedEntityRecognition."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None
    domain: InputParam = None

    def __init__(self, node=None):
        """Initialize NamedEntityRecognitionInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.domain = self.create_param(code="domain", data_type=DataType.LABEL, is_required=False)


class NamedEntityRecognitionOutputs(Outputs):
    """Output parameters for NamedEntityRecognition."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize NamedEntityRecognitionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class NamedEntityRecognition(AssetNode[NamedEntityRecognitionInputs, NamedEntityRecognitionOutputs]):
    """NamedEntityRecognition node.

    Identifies and classifies named entities (e.g., persons, organizations,
    locations) within text. Useful for information extraction, content tagging, and
    search enhancements.

    InputType: text
    OutputType: label
    """

    function: str = "named-entity-recognition"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = NamedEntityRecognitionInputs
    outputs_class: Type[TO] = NamedEntityRecognitionOutputs


class SpeechSynthesisInputs(Inputs):
    """Input parameters for SpeechSynthesis."""

    audio: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    voice: InputParam = None
    script: InputParam = None
    text: InputParam = None
    type: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeechSynthesisInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.voice = self.create_param(code="voice", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.type = self.create_param(code="type", data_type=DataType.LABEL, is_required=False)


class SpeechSynthesisOutputs(Outputs):
    """Output parameters for SpeechSynthesis."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeechSynthesisOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class SpeechSynthesis(AssetNode[SpeechSynthesisInputs, SpeechSynthesisOutputs]):
    """SpeechSynthesis node.

    Generates human-like speech from written text. Ideal for text-to-speech
    applications, audiobooks, and voice assistants.

    InputType: text
    OutputType: audio
    """

    function: str = "speech-synthesis"
    input_type: str = DataType.TEXT
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = SpeechSynthesisInputs
    outputs_class: Type[TO] = SpeechSynthesisOutputs


class DocumentInformationExtractionInputs(Inputs):
    """Input parameters for DocumentInformationExtraction."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize DocumentInformationExtractionInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class DocumentInformationExtractionOutputs(Outputs):
    """Output parameters for DocumentInformationExtraction."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize DocumentInformationExtractionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class DocumentInformationExtraction(
    AssetNode[DocumentInformationExtractionInputs, DocumentInformationExtractionOutputs]
):
    """DocumentInformationExtraction node.

    Document Information Extraction is the process of automatically identifying,
    extracting, and structuring relevant data from unstructured or semi-structured
    documents, such as invoices, receipts, contracts, and forms, to facilitate
    easier data management and analysis.

    InputType: image
    OutputType: text
    """

    function: str = "document-information-extraction"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = DocumentInformationExtractionInputs
    outputs_class: Type[TO] = DocumentInformationExtractionOutputs


class OcrInputs(Inputs):
    """Input parameters for Ocr."""

    image: InputParam = None
    featuretypes: InputParam = None

    def __init__(self, node=None):
        """Initialize OcrInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.featuretypes = self.create_param(code="featuretypes", data_type=DataType.TEXT, is_required=True)


class OcrOutputs(Outputs):
    """Output parameters for Ocr."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize OcrOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Ocr(AssetNode[OcrInputs, OcrOutputs]):
    """Ocr node.

    Converts images of typed, handwritten, or printed text into machine-encoded
    text. Used in digitizing printed texts for data retrieval.

    InputType: image
    OutputType: text
    """

    function: str = "ocr"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = OcrInputs
    outputs_class: Type[TO] = OcrOutputs


class SubtitlingTranslationInputs(Inputs):
    """Input parameters for SubtitlingTranslation."""

    text: InputParam = None
    sourcelanguage: InputParam = None
    dialect_in: InputParam = None
    target_supplier: InputParam = None
    targetlanguages: InputParam = None

    def __init__(self, node=None):
        """Initialize SubtitlingTranslationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.sourcelanguage = self.create_param(code="sourcelanguage", data_type=DataType.LABEL, is_required=True)
        self.dialect_in = self.create_param(code="dialect_in", data_type=DataType.LABEL, is_required=False)
        self.target_supplier = self.create_param(code="target_supplier", data_type=DataType.LABEL, is_required=False)
        self.targetlanguages = self.create_param(code="targetlanguages", data_type=DataType.LABEL, is_required=False)


class SubtitlingTranslationOutputs(Outputs):
    """Output parameters for SubtitlingTranslation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SubtitlingTranslationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SubtitlingTranslation(AssetNode[SubtitlingTranslationInputs, SubtitlingTranslationOutputs]):
    """SubtitlingTranslation node.

    Converts the text of subtitles from one language to another, ensuring context
    and cultural nuances are maintained. Essential for global content distribution.

    InputType: text
    OutputType: text
    """

    function: str = "subtitling-translation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SubtitlingTranslationInputs
    outputs_class: Type[TO] = SubtitlingTranslationOutputs


class TextToAudioInputs(Inputs):
    """Input parameters for TextToAudio."""

    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize TextToAudioInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)


class TextToAudioOutputs(Outputs):
    """Output parameters for TextToAudio."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextToAudioOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class TextToAudio(AssetNode[TextToAudioInputs, TextToAudioOutputs]):
    """TextToAudio node.

    The Text to Audio function converts written text into spoken words, allowing
    users to listen to the content instead of reading it.

    InputType: text
    OutputType: audio
    """

    function: str = "text-to-audio"
    input_type: str = DataType.TEXT
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = TextToAudioInputs
    outputs_class: Type[TO] = TextToAudioOutputs


class MultilingualSpeechRecognitionInputs(Inputs):
    """Input parameters for MultilingualSpeechRecognition."""

    source_audio: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize MultilingualSpeechRecognitionInputs."""
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)


class MultilingualSpeechRecognitionOutputs(Outputs):
    """Output parameters for MultilingualSpeechRecognition."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize MultilingualSpeechRecognitionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class MultilingualSpeechRecognition(
    AssetNode[MultilingualSpeechRecognitionInputs, MultilingualSpeechRecognitionOutputs]
):
    """MultilingualSpeechRecognition node.

    Multilingual Speech Recognition is a technology that enables the automatic
    transcription of spoken language into text across multiple languages, allowing
    for seamless communication and understanding in diverse linguistic contexts.

    InputType: audio
    OutputType: text
    """

    function: str = "multilingual-speech-recognition"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = MultilingualSpeechRecognitionInputs
    outputs_class: Type[TO] = MultilingualSpeechRecognitionOutputs


class OffensiveLanguageIdentificationInputs(Inputs):
    """Input parameters for OffensiveLanguageIdentification."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize OffensiveLanguageIdentificationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class OffensiveLanguageIdentificationOutputs(Outputs):
    """Output parameters for OffensiveLanguageIdentification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize OffensiveLanguageIdentificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class OffensiveLanguageIdentification(
    AssetNode[OffensiveLanguageIdentificationInputs, OffensiveLanguageIdentificationOutputs]
):
    """OffensiveLanguageIdentification node.

    Detects language or phrases that might be considered offensive, aiding in
    content moderation and creating respectful user interactions.

    InputType: text
    OutputType: label
    """

    function: str = "offensive-language-identification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = OffensiveLanguageIdentificationInputs
    outputs_class: Type[TO] = OffensiveLanguageIdentificationOutputs


class BenchmarkScoringMtInputs(Inputs):
    """Input parameters for BenchmarkScoringMt."""

    input: InputParam = None
    text: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize BenchmarkScoringMtInputs."""
        super().__init__(node=node)
        self.input = self.create_param(code="input", data_type=DataType.TEXT, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class BenchmarkScoringMtOutputs(Outputs):
    """Output parameters for BenchmarkScoringMt."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize BenchmarkScoringMtOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class BenchmarkScoringMt(AssetNode[BenchmarkScoringMtInputs, BenchmarkScoringMtOutputs]):
    """BenchmarkScoringMt node.

    Benchmark Scoring MT is a function designed to evaluate and score machine
    translation systems by comparing their output against a set of predefined
    benchmarks, thereby assessing their accuracy and performance.

    InputType: text
    OutputType: label
    """

    function: str = "benchmark-scoring-mt"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = BenchmarkScoringMtInputs
    outputs_class: Type[TO] = BenchmarkScoringMtOutputs


class SpeakerDiarizationAudioInputs(Inputs):
    """Input parameters for SpeakerDiarizationAudio."""

    audio: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeakerDiarizationAudioInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeakerDiarizationAudioOutputs(Outputs):
    """Output parameters for SpeakerDiarizationAudio."""

    data: OutputParam = None
    audio: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeakerDiarizationAudioOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)


class SpeakerDiarizationAudio(BaseSegmentor[SpeakerDiarizationAudioInputs, SpeakerDiarizationAudioOutputs]):
    """SpeakerDiarizationAudio node.

    Identifies individual speakers and their respective speech segments within an
    audio clip. Ideal for multi-speaker recordings or conference calls.

    InputType: audio
    OutputType: label
    """

    function: str = "speaker-diarization-audio"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeakerDiarizationAudioInputs
    outputs_class: Type[TO] = SpeakerDiarizationAudioOutputs


class VoiceCloningInputs(Inputs):
    """Input parameters for VoiceCloning."""

    text: InputParam = None
    audio: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    voice: InputParam = None
    script: InputParam = None
    type: InputParam = None

    def __init__(self, node=None):
        """Initialize VoiceCloningInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.voice = self.create_param(code="voice", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.type = self.create_param(code="type", data_type=DataType.LABEL, is_required=False)


class VoiceCloningOutputs(Outputs):
    """Output parameters for VoiceCloning."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize VoiceCloningOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class VoiceCloning(AssetNode[VoiceCloningInputs, VoiceCloningOutputs]):
    """VoiceCloning node.

    Replicates a person's voice based on a sample, allowing for the generation of
    speech in that person's tone and style. Used cautiously due to ethical
    considerations.

    InputType: text
    OutputType: audio
    """

    function: str = "voice-cloning"
    input_type: str = DataType.TEXT
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = VoiceCloningInputs
    outputs_class: Type[TO] = VoiceCloningOutputs


class SearchInputs(Inputs):
    """Input parameters for Search."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize SearchInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class SearchOutputs(Outputs):
    """Output parameters for Search."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SearchOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Search(AssetNode[SearchInputs, SearchOutputs]):
    """Search node.

    An algorithm that identifies and returns data or items that match particular
    keywords or conditions from a dataset. A fundamental tool for databases and
    websites.

    InputType: text
    OutputType: text
    """

    function: str = "search"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SearchInputs
    outputs_class: Type[TO] = SearchOutputs


class ObjectDetectionInputs(Inputs):
    """Input parameters for ObjectDetection."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ObjectDetectionInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class ObjectDetectionOutputs(Outputs):
    """Output parameters for ObjectDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ObjectDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ObjectDetection(AssetNode[ObjectDetectionInputs, ObjectDetectionOutputs]):
    """ObjectDetection node.

    Object Detection is a computer vision technology that identifies and locates
    objects within an image, typically by drawing bounding boxes around the
    detected objects and classifying them into predefined categories.

    InputType: video
    OutputType: text
    """

    function: str = "object-detection"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ObjectDetectionInputs
    outputs_class: Type[TO] = ObjectDetectionOutputs


class DiacritizationInputs(Inputs):
    """Input parameters for Diacritization."""

    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize DiacritizationInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class DiacritizationOutputs(Outputs):
    """Output parameters for Diacritization."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize DiacritizationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Diacritization(AssetNode[DiacritizationInputs, DiacritizationOutputs]):
    """Diacritization node.

    Adds diacritical marks to text, essential for languages where meaning can
    change based on diacritics.

    InputType: text
    OutputType: text
    """

    function: str = "diacritization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = DiacritizationInputs
    outputs_class: Type[TO] = DiacritizationOutputs


class SpeakerDiarizationVideoInputs(Inputs):
    """Input parameters for SpeakerDiarizationVideo."""

    video: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeakerDiarizationVideoInputs."""
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeakerDiarizationVideoOutputs(Outputs):
    """Output parameters for SpeakerDiarizationVideo."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeakerDiarizationVideoOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.VIDEO)


class SpeakerDiarizationVideo(AssetNode[SpeakerDiarizationVideoInputs, SpeakerDiarizationVideoOutputs]):
    """SpeakerDiarizationVideo node.

    Segments a video based on different speakers, identifying when each individual
    speaks. Useful for transcriptions and understanding multi-person conversations.

    InputType: video
    OutputType: label
    """

    function: str = "speaker-diarization-video"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeakerDiarizationVideoInputs
    outputs_class: Type[TO] = SpeakerDiarizationVideoOutputs


class AudioForcedAlignmentInputs(Inputs):
    """Input parameters for AudioForcedAlignment."""

    audio: InputParam = None
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize AudioForcedAlignmentInputs."""
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class AudioForcedAlignmentOutputs(Outputs):
    """Output parameters for AudioForcedAlignment."""

    text: OutputParam = None
    audio: OutputParam = None

    def __init__(self, node=None):
        """Initialize AudioForcedAlignmentOutputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)


class AudioForcedAlignment(AssetNode[AudioForcedAlignmentInputs, AudioForcedAlignmentOutputs]):
    """AudioForcedAlignment node.

    Synchronizes phonetic and phonological text with the corresponding segments in
    an audio file. Useful in linguistic research and detailed transcription tasks.

    InputType: audio
    OutputType: audio
    """

    function: str = "audio-forced-alignment"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = AudioForcedAlignmentInputs
    outputs_class: Type[TO] = AudioForcedAlignmentOutputs


class TokenClassificationInputs(Inputs):
    """Input parameters for TokenClassification."""

    text: InputParam = None
    language: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize TokenClassificationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TokenClassificationOutputs(Outputs):
    """Output parameters for TokenClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TokenClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TokenClassification(AssetNode[TokenClassificationInputs, TokenClassificationOutputs]):
    """TokenClassification node.

    Token-level classification means that each token will be given a label, for
    example a part-of-speech tagger will classify each word as one particular part
    of speech.

    InputType: text
    OutputType: label
    """

    function: str = "token-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TokenClassificationInputs
    outputs_class: Type[TO] = TokenClassificationOutputs


class TopicClassificationInputs(Inputs):
    """Input parameters for TopicClassification."""

    text: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        """Initialize TopicClassificationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class TopicClassificationOutputs(Outputs):
    """Output parameters for TopicClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TopicClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TopicClassification(AssetNode[TopicClassificationInputs, TopicClassificationOutputs]):
    """TopicClassification node.

    Assigns categories or topics to a piece of text based on its content,
    facilitating content organization and retrieval.

    InputType: text
    OutputType: label
    """

    function: str = "topic-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TopicClassificationInputs
    outputs_class: Type[TO] = TopicClassificationOutputs


class IntentClassificationInputs(Inputs):
    """Input parameters for IntentClassification."""

    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        """Initialize IntentClassificationInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class IntentClassificationOutputs(Outputs):
    """Output parameters for IntentClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize IntentClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class IntentClassification(AssetNode[IntentClassificationInputs, IntentClassificationOutputs]):
    """IntentClassification node.

    Intent Classification is a natural language processing task that involves
    analyzing and categorizing user text input to determine the underlying purpose
    or goal behind the communication, such as booking a flight, asking for weather
    information, or setting a reminder.

    InputType: text
    OutputType: label
    """

    function: str = "intent-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = IntentClassificationInputs
    outputs_class: Type[TO] = IntentClassificationOutputs


class VideoContentModerationInputs(Inputs):
    """Input parameters for VideoContentModeration."""

    video: InputParam = None
    min_confidence: InputParam = None

    def __init__(self, node=None):
        """Initialize VideoContentModerationInputs."""
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.min_confidence = self.create_param(code="min_confidence", data_type=DataType.TEXT, is_required=False)


class VideoContentModerationOutputs(Outputs):
    """Output parameters for VideoContentModeration."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize VideoContentModerationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class VideoContentModeration(AssetNode[VideoContentModerationInputs, VideoContentModerationOutputs]):
    """VideoContentModeration node.

    Automatically reviews video content to detect and possibly remove inappropriate
    or harmful material. Essential for user-generated content platforms.

    InputType: video
    OutputType: label
    """

    function: str = "video-content-moderation"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = VideoContentModerationInputs
    outputs_class: Type[TO] = VideoContentModerationOutputs


class TextGenerationMetricInputs(Inputs):
    """Input parameters for TextGenerationMetric."""

    hypotheses: InputParam = None
    references: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        """Initialize TextGenerationMetricInputs."""
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.TEXT, is_required=True)
        self.references = self.create_param(code="references", data_type=DataType.TEXT, is_required=False)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class TextGenerationMetricOutputs(Outputs):
    """Output parameters for TextGenerationMetric."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextGenerationMetricOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextGenerationMetric(BaseMetric[TextGenerationMetricInputs, TextGenerationMetricOutputs]):
    """TextGenerationMetric node.

    A Text Generation Metric is a quantitative measure used to evaluate the quality
    and effectiveness of text produced by natural language processing models, often
    assessing aspects such as coherence, relevance, fluency, and adherence to given
    prompts or instructions.

    InputType: text
    OutputType: text
    """

    function: str = "text-generation-metric"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextGenerationMetricInputs
    outputs_class: Type[TO] = TextGenerationMetricOutputs


class ImageEmbeddingInputs(Inputs):
    """Input parameters for ImageEmbedding."""

    language: InputParam = None
    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageEmbeddingInputs."""
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class ImageEmbeddingOutputs(Outputs):
    """Output parameters for ImageEmbedding."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageEmbeddingOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ImageEmbedding(AssetNode[ImageEmbeddingInputs, ImageEmbeddingOutputs]):
    """ImageEmbedding node.

    Image Embedding is a process that transforms an image into a fixed-dimensional
    vector representation, capturing its essential features and enabling efficient
    comparison, retrieval, and analysis in various machine learning and computer
    vision tasks.

    InputType: image
    OutputType: text
    """

    function: str = "image-embedding"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ImageEmbeddingInputs
    outputs_class: Type[TO] = ImageEmbeddingOutputs


class ImageLabelDetectionInputs(Inputs):
    """Input parameters for ImageLabelDetection."""

    image: InputParam = None
    min_confidence: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageLabelDetectionInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.min_confidence = self.create_param(code="min_confidence", data_type=DataType.TEXT, is_required=False)


class ImageLabelDetectionOutputs(Outputs):
    """Output parameters for ImageLabelDetection."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageLabelDetectionOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ImageLabelDetection(AssetNode[ImageLabelDetectionInputs, ImageLabelDetectionOutputs]):
    """ImageLabelDetection node.

    Identifies objects, themes, or topics within images, useful for image
    categorization, search, and recommendation systems.

    InputType: image
    OutputType: label
    """

    function: str = "image-label-detection"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = ImageLabelDetectionInputs
    outputs_class: Type[TO] = ImageLabelDetectionOutputs


class ImageColorizationInputs(Inputs):
    """Input parameters for ImageColorization."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageColorizationInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class ImageColorizationOutputs(Outputs):
    """Output parameters for ImageColorization."""

    image: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageColorizationOutputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class ImageColorization(AssetNode[ImageColorizationInputs, ImageColorizationOutputs]):
    """ImageColorization node.

    Image colorization is a process that involves adding color to grayscale images,
    transforming them from black-and-white to full-color representations, often
    using advanced algorithms and machine learning techniques to predict and apply
    the appropriate hues and shades.

    InputType: image
    OutputType: image
    """

    function: str = "image-colorization"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.IMAGE

    inputs_class: Type[TI] = ImageColorizationInputs
    outputs_class: Type[TO] = ImageColorizationOutputs


class MetricAggregationInputs(Inputs):
    """Input parameters for MetricAggregation."""

    text: InputParam = None

    def __init__(self, node=None):
        """Initialize MetricAggregationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class MetricAggregationOutputs(Outputs):
    """Output parameters for MetricAggregation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize MetricAggregationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class MetricAggregation(BaseMetric[MetricAggregationInputs, MetricAggregationOutputs]):
    """MetricAggregation node.

    Metric Aggregation is a function that computes and summarizes numerical data by
    applying statistical operations, such as averaging, summing, or finding the
    minimum and maximum values, to provide insights and facilitate analysis of
    large datasets.

    InputType: text
    OutputType: text
    """

    function: str = "metric-aggregation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = MetricAggregationInputs
    outputs_class: Type[TO] = MetricAggregationOutputs


class InstanceSegmentationInputs(Inputs):
    """Input parameters for InstanceSegmentation."""

    image: InputParam = None

    def __init__(self, node=None):
        """Initialize InstanceSegmentationInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class InstanceSegmentationOutputs(Outputs):
    """Output parameters for InstanceSegmentation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize InstanceSegmentationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class InstanceSegmentation(AssetNode[InstanceSegmentationInputs, InstanceSegmentationOutputs]):
    """InstanceSegmentation node.

    Instance segmentation is a computer vision task that involves detecting and
    delineating each distinct object within an image, assigning a unique label and
    precise boundary to every individual instance of objects, even if they belong
    to the same category.

    InputType: image
    OutputType: label
    """

    function: str = "instance-segmentation"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = InstanceSegmentationInputs
    outputs_class: Type[TO] = InstanceSegmentationOutputs


class OtherMultipurposeInputs(Inputs):
    """Input parameters for OtherMultipurpose."""

    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        """Initialize OtherMultipurposeInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)


class OtherMultipurposeOutputs(Outputs):
    """Output parameters for OtherMultipurpose."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize OtherMultipurposeOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class OtherMultipurpose(AssetNode[OtherMultipurposeInputs, OtherMultipurposeOutputs]):
    """OtherMultipurpose node.

    The "Other (Multipurpose)" function serves as a versatile category designed to
    accommodate a wide range of tasks and activities that do not fit neatly into
    predefined classifications, offering flexibility and adaptability for various
    needs.

    InputType: text
    OutputType: text
    """

    function: str = "other-(multipurpose)"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = OtherMultipurposeInputs
    outputs_class: Type[TO] = OtherMultipurposeOutputs


class SpeechTranslationInputs(Inputs):
    """Input parameters for SpeechTranslation."""

    source_audio: InputParam = None
    sourcelanguage: InputParam = None
    targetlanguage: InputParam = None
    dialect: InputParam = None
    voice: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize SpeechTranslationInputs."""
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.sourcelanguage = self.create_param(code="sourcelanguage", data_type=DataType.LABEL, is_required=True)
        self.targetlanguage = self.create_param(code="targetlanguage", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.voice = self.create_param(code="voice", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class SpeechTranslationOutputs(Outputs):
    """Output parameters for SpeechTranslation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize SpeechTranslationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SpeechTranslation(AssetNode[SpeechTranslationInputs, SpeechTranslationOutputs]):
    """SpeechTranslation node.

    Speech Translation is a technology that converts spoken language in real-time
    from one language to another, enabling seamless communication between speakers
    of different languages.

    InputType: audio
    OutputType: text
    """

    function: str = "speech-translation"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SpeechTranslationInputs
    outputs_class: Type[TO] = SpeechTranslationOutputs


class ReferencelessTextGenerationMetricDefaultInputs(Inputs):
    """Input parameters for ReferencelessTextGenerationMetricDefault."""

    hypotheses: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        """Initialize ReferencelessTextGenerationMetricDefaultInputs."""
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.TEXT, is_required=True)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class ReferencelessTextGenerationMetricDefaultOutputs(Outputs):
    """Output parameters for ReferencelessTextGenerationMetricDefault."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ReferencelessTextGenerationMetricDefaultOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ReferencelessTextGenerationMetricDefault(
    BaseMetric[ReferencelessTextGenerationMetricDefaultInputs, ReferencelessTextGenerationMetricDefaultOutputs]
):
    """ReferencelessTextGenerationMetricDefault node.

    The Referenceless Text Generation Metric Default is a function designed to
    evaluate the quality of generated text without relying on reference texts for
    comparison.

    InputType: text
    OutputType: text
    """

    function: str = "referenceless-text-generation-metric-default"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ReferencelessTextGenerationMetricDefaultInputs
    outputs_class: Type[TO] = ReferencelessTextGenerationMetricDefaultOutputs


class ReferencelessTextGenerationMetricInputs(Inputs):
    """Input parameters for ReferencelessTextGenerationMetric."""

    hypotheses: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        """Initialize ReferencelessTextGenerationMetricInputs."""
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.TEXT, is_required=True)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class ReferencelessTextGenerationMetricOutputs(Outputs):
    """Output parameters for ReferencelessTextGenerationMetric."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize ReferencelessTextGenerationMetricOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ReferencelessTextGenerationMetric(
    BaseMetric[ReferencelessTextGenerationMetricInputs, ReferencelessTextGenerationMetricOutputs]
):
    """ReferencelessTextGenerationMetric node.

    The Referenceless Text Generation Metric is a method for evaluating the quality
    of generated text without requiring a reference text for comparison, often
    leveraging models or algorithms to assess coherence, relevance, and fluency
    based on intrinsic properties of the text itself.

    InputType: text
    OutputType: text
    """

    function: str = "referenceless-text-generation-metric"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = ReferencelessTextGenerationMetricInputs
    outputs_class: Type[TO] = ReferencelessTextGenerationMetricOutputs


class TextDenormalizationInputs(Inputs):
    """Input parameters for TextDenormalization."""

    text: InputParam = None
    language: InputParam = None
    lowercase_latin: InputParam = None
    remove_accents: InputParam = None
    remove_punctuation: InputParam = None

    def __init__(self, node=None):
        """Initialize TextDenormalizationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.lowercase_latin = self.create_param(code="lowercase_latin", data_type=DataType.TEXT, is_required=False)
        self.remove_accents = self.create_param(code="remove_accents", data_type=DataType.TEXT, is_required=False)
        self.remove_punctuation = self.create_param(
            code="remove_punctuation", data_type=DataType.TEXT, is_required=False
        )


class TextDenormalizationOutputs(Outputs):
    """Output parameters for TextDenormalization."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextDenormalizationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextDenormalization(AssetNode[TextDenormalizationInputs, TextDenormalizationOutputs]):
    """TextDenormalization node.

    Converts standardized or normalized text into its original, often more
    readable, form. Useful in natural language generation tasks.

    InputType: text
    OutputType: label
    """

    function: str = "text-denormalization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextDenormalizationInputs
    outputs_class: Type[TO] = TextDenormalizationOutputs


class ImageCompressionInputs(Inputs):
    """Input parameters for ImageCompression."""

    image: InputParam = None
    apl_qfactor: InputParam = None

    def __init__(self, node=None):
        """Initialize ImageCompressionInputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.apl_qfactor = self.create_param(code="apl_qfactor", data_type=DataType.TEXT, is_required=False)


class ImageCompressionOutputs(Outputs):
    """Output parameters for ImageCompression."""

    image: OutputParam = None

    def __init__(self, node=None):
        """Initialize ImageCompressionOutputs."""
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class ImageCompression(AssetNode[ImageCompressionInputs, ImageCompressionOutputs]):
    """ImageCompression node.

    Reduces the size of image files without significantly compromising their visual
    quality. Useful for optimizing storage and improving webpage load times.

    InputType: image
    OutputType: image
    """

    function: str = "image-compression"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.IMAGE

    inputs_class: Type[TI] = ImageCompressionInputs
    outputs_class: Type[TO] = ImageCompressionOutputs


class TextClassificationInputs(Inputs):
    """Input parameters for TextClassification."""

    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize TextClassificationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextClassificationOutputs(Outputs):
    """Output parameters for TextClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize TextClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextClassification(AssetNode[TextClassificationInputs, TextClassificationOutputs]):
    """TextClassification node.

    Categorizes text into predefined groups or topics, facilitating content
    organization and targeted actions.

    InputType: text
    OutputType: label
    """

    function: str = "text-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextClassificationInputs
    outputs_class: Type[TO] = TextClassificationOutputs


class AsrAgeClassificationInputs(Inputs):
    """Input parameters for AsrAgeClassification."""

    source_audio: InputParam = None

    def __init__(self, node=None):
        """Initialize AsrAgeClassificationInputs."""
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)


class AsrAgeClassificationOutputs(Outputs):
    """Output parameters for AsrAgeClassification."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AsrAgeClassificationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AsrAgeClassification(AssetNode[AsrAgeClassificationInputs, AsrAgeClassificationOutputs]):
    """AsrAgeClassification node.

    The ASR Age Classification function is designed to analyze audio recordings of
    speech to determine the speaker's age group by leveraging automatic speech
    recognition (ASR) technology and machine learning algorithms.

    InputType: audio
    OutputType: label
    """

    function: str = "asr-age-classification"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = AsrAgeClassificationInputs
    outputs_class: Type[TO] = AsrAgeClassificationOutputs


class AsrQualityEstimationInputs(Inputs):
    """Input parameters for AsrQualityEstimation."""

    text: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        """Initialize AsrQualityEstimationInputs."""
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class AsrQualityEstimationOutputs(Outputs):
    """Output parameters for AsrQualityEstimation."""

    data: OutputParam = None

    def __init__(self, node=None):
        """Initialize AsrQualityEstimationOutputs."""
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AsrQualityEstimation(AssetNode[AsrQualityEstimationInputs, AsrQualityEstimationOutputs]):
    """AsrQualityEstimation node.

    ASR Quality Estimation is a process that evaluates the accuracy and reliability
    of automatic speech recognition systems by analyzing their performance in
    transcribing spoken language into text.

    InputType: text
    OutputType: label
    """

    function: str = "asr-quality-estimation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = AsrQualityEstimationInputs
    outputs_class: Type[TO] = AsrQualityEstimationOutputs


class Pipeline(DefaultPipeline):
    """Pipeline class for creating and managing AI processing pipelines."""

    def text_normalization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextNormalization:
        """Create a TextNormalization node.

        Converts unstructured or non-standard textual data into a more readable and
        uniform format, dealing with abbreviations, numerals, and other non-standard
        words.
        """
        return TextNormalization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def paraphrasing(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Paraphrasing:
        """Create a Paraphrasing node.

        Express the meaning of the writer or speaker or something written or spoken
        using different words.
        """
        return Paraphrasing(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def language_identification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> LanguageIdentification:
        """Create a LanguageIdentification node.

        Detects the language in which a given text is written, aiding in multilingual
        platforms or content localization.
        """
        return LanguageIdentification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def benchmark_scoring_asr(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> BenchmarkScoringAsr:
        """Create a BenchmarkScoringAsr node.

        Benchmark Scoring ASR is a function that evaluates and compares the performance
        of automatic speech recognition systems by analyzing their accuracy, speed, and
        other relevant metrics against a standardized set of benchmarks.
        """
        return BenchmarkScoringAsr(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_class_text_classification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> MultiClassTextClassification:
        """Create a MultiClassTextClassification node.

        Multi Class Text Classification is a natural language processing task that
        involves categorizing a given text into one of several predefined classes or
        categories based on its content.
        """
        return MultiClassTextClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechEmbedding:
        """Create a SpeechEmbedding node.

        Transforms spoken content into a fixed-size vector in a high-dimensional space
        that captures the content's essence. Facilitates tasks like speech recognition
        and speaker verification.
        """
        return SpeechEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def document_image_parsing(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DocumentImageParsing:
        """Create a DocumentImageParsing node.

        Document Image Parsing is the process of analyzing and converting scanned or
        photographed images of documents into structured, machine-readable formats by
        identifying and extracting text, layout, and other relevant information.
        """
        return DocumentImageParsing(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Translation:
        """Create a Translation node.

        Converts text from one language to another while maintaining the original
        message's essence and context. Crucial for global communication.
        """
        return Translation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_source_separation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioSourceSeparation:
        """Create a AudioSourceSeparation node.

        Audio Source Separation is the process of separating a mixture (e.g. a pop band
        recording) into isolated sounds from individual sources (e.g. just the lead
        vocals).
        """
        return AudioSourceSeparation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechRecognition:
        """Create a SpeechRecognition node.

        Converts spoken language into written text. Useful for transcription services,
        voice assistants, and applications requiring voice-to-text capabilities.
        """
        return SpeechRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def keyword_spotting(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> KeywordSpotting:
        """Create a KeywordSpotting node.

        Keyword Spotting is a function that enables the detection and identification of
        specific words or phrases within a stream of audio, often used in voice-
        activated systems to trigger actions or commands based on recognized keywords.
        """
        return KeywordSpotting(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def part_of_speech_tagging(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> PartOfSpeechTagging:
        """Create a PartOfSpeechTagging node.

        Part of Speech Tagging is a natural language processing task that involves
        assigning each word in a sentence its corresponding part of speech, such as
        noun, verb, adjective, or adverb, based on its role and context within the
        sentence.
        """
        return PartOfSpeechTagging(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_audio_generation_metric(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> ReferencelessAudioGenerationMetric:
        """Create a ReferencelessAudioGenerationMetric node.

        The Referenceless Audio Generation Metric is a tool designed to evaluate the
        quality of generated audio content without the need for a reference or original
        audio sample for comparison.
        """
        return ReferencelessAudioGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def voice_activity_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VoiceActivityDetection:
        """Create a VoiceActivityDetection node.

        Determines when a person is speaking in an audio clip. It's an essential
        preprocessing step for other audio-related tasks.
        """
        return VoiceActivityDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def sentiment_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SentimentAnalysis:
        """Create a SentimentAnalysis node.

        Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
        piece of text, aiding in understanding user feedback or market sentiment.
        """
        return SentimentAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def subtitling(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Subtitling:
        """Create a Subtitling node.

        Generates accurate subtitles for videos, enhancing accessibility for diverse
        audiences.
        """
        return Subtitling(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_label_text_classification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> MultiLabelTextClassification:
        """Create a MultiLabelTextClassification node.

        Multi Label Text Classification is a natural language processing task where a
        given text is analyzed and assigned multiple relevant labels or categories from
        a predefined set, allowing for the text to belong to more than one category
        simultaneously.
        """
        return MultiLabelTextClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def viseme_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VisemeGeneration:
        """Create a VisemeGeneration node.

        Viseme Generation is the process of creating visual representations of
        phonemes, which are the distinct units of sound in speech, to synchronize lip
        movements with spoken words in animations or virtual avatars.
        """
        return VisemeGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_segmenation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSegmenation:
        """Create a TextSegmenation node.

        Text Segmentation is the process of dividing a continuous text into meaningful
        units, such as words, sentences, or topics, to facilitate easier analysis and
        understanding.
        """
        return TextSegmenation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def zero_shot_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ZeroShotClassification:
        """Create a ZeroShotClassification node."""
        return ZeroShotClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextGeneration:
        """Create a TextGeneration node.

        Creates coherent and contextually relevant textual content based on prompts or
        certain parameters. Useful for chatbots, content creation, and data
        augmentation.
        """
        return TextGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_intent_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioIntentDetection:
        """Create a AudioIntentDetection node.

        Audio Intent Detection is a process that involves analyzing audio signals to
        identify and interpret the underlying intentions or purposes behind spoken
        words, enabling systems to understand and respond appropriately to human
        speech.
        """
        return AudioIntentDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def entity_linking(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> EntityLinking:
        """Create a EntityLinking node.

        Associates identified entities in the text with specific entries in a knowledge
        base or database.
        """
        return EntityLinking(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def connection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Connection:
        """Create a Connection node.

        Connections are integration that allow you to connect your AI agents to
        external tools
        """
        return Connection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def visual_question_answering(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VisualQuestionAnswering:
        """Create a VisualQuestionAnswering node.

        Visual Question Answering (VQA) is a task in artificial intelligence that
        involves analyzing an image and providing accurate, contextually relevant
        answers to questions posed about the visual content of that image.
        """
        return VisualQuestionAnswering(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def loglikelihood(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Loglikelihood:
        """Create a Loglikelihood node.

        The Log Likelihood function measures the probability of observing the given
        data under a specific statistical model by taking the natural logarithm of the
        likelihood function, thereby transforming the product of probabilities into a
        sum, which simplifies the process of optimization and parameter estimation.
        """
        return Loglikelihood(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def language_identification_audio(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> LanguageIdentificationAudio:
        """Create a LanguageIdentificationAudio node.

        The Language Identification Audio function analyzes audio input to determine
        and identify the language being spoken.
        """
        return LanguageIdentificationAudio(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def fact_checking(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> FactChecking:
        """Create a FactChecking node.

        Fact Checking is the process of verifying the accuracy and truthfulness of
        information, statements, or claims by cross-referencing with reliable sources
        and evidence.
        """
        return FactChecking(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def table_question_answering(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TableQuestionAnswering:
        """Create a TableQuestionAnswering node.

        The task of question answering over tables is given an input table (or a set of
        tables) T and a natural language question Q (a user query), output the correct
        answer A
        """
        return TableQuestionAnswering(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechClassification:
        """Create a SpeechClassification node.

        Categorizes audio clips based on their content, aiding in content organization
        and targeted actions.
        """
        return SpeechClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def inverse_text_normalization(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> InverseTextNormalization:
        """Create a InverseTextNormalization node.

        Inverse Text Normalization is the process of converting spoken or written
        language in its normalized form, such as numbers, dates, and abbreviations,
        back into their original, more complex or detailed textual representations.
        """
        return InverseTextNormalization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_class_image_classification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> MultiClassImageClassification:
        """Create a MultiClassImageClassification node.

        Multi Class Image Classification is a machine learning task where an algorithm
        is trained to categorize images into one of several predefined classes or
        categories based on their visual content.
        """
        return MultiClassImageClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def asr_gender_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrGenderClassification:
        """Create a AsrGenderClassification node.

        The ASR Gender Classification function analyzes audio recordings to determine
        and classify the speaker's gender based on their voice characteristics.
        """
        return AsrGenderClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def summarization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Summarization:
        """Create a Summarization node.

        Text summarization is the process of distilling the most important information
        from a source (or sources) to produce an abridged version for a particular user
        (or users) and task (or tasks)
        """
        return Summarization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def topic_modeling(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TopicModeling:
        """Create a TopicModeling node.

        Topic modeling is a type of statistical modeling for discovering the abstract
        “topics” that occur in a collection of documents.
        """
        return TopicModeling(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_reconstruction(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioReconstruction:
        """Create a AudioReconstruction node.

        Audio Reconstruction is the process of restoring or recreating audio signals
        from incomplete, damaged, or degraded recordings to achieve a high-quality,
        accurate representation of the original sound.
        """
        return AudioReconstruction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextEmbedding:
        """Create a TextEmbedding node.

        Text embedding is a process that converts text into numerical vectors,
        capturing the semantic meaning and contextual relationships of words or
        phrases, enabling machines to understand and analyze natural language more
        effectively.
        """
        return TextEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def detect_language_from_text(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DetectLanguageFromText:
        """Create a DetectLanguageFromText node.

        Detect Language From Text
        """
        return DetectLanguageFromText(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def extract_audio_from_video(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ExtractAudioFromVideo:
        """Create a ExtractAudioFromVideo node.

        Isolates and extracts audio tracks from video files, aiding in audio analysis
        or transcription tasks.
        """
        return ExtractAudioFromVideo(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def scene_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SceneDetection:
        """Create a SceneDetection node.

        Scene detection is used for detecting transitions between shots in a video to
        split it into basic temporal segments.
        """
        return SceneDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_to_image_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextToImageGeneration:
        """Create a TextToImageGeneration node.

        Creates a visual representation based on textual input, turning descriptions
        into pictorial forms. Used in creative processes and content generation.
        """
        return TextToImageGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def auto_mask_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AutoMaskGeneration:
        """Create a AutoMaskGeneration node.

        Auto-mask generation refers to the automated process of creating masks in image
        processing or computer vision, typically for segmentation tasks. A mask is a
        binary or multi-class image that labels different parts of an image, usually
        separating the foreground (objects of interest) from the background, or
        identifying specific object classes in an image.
        """
        return AutoMaskGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_language_identification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> AudioLanguageIdentification:
        """Create a AudioLanguageIdentification node.

        Audio Language Identification is a process that involves analyzing an audio
        recording to determine the language being spoken.
        """
        return AudioLanguageIdentification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def facial_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> FacialRecognition:
        """Create a FacialRecognition node.

        A facial recognition system is a technology capable of matching a human face
        from a digital image or a video frame against a database of faces
        """
        return FacialRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def question_answering(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> QuestionAnswering:
        """Create a QuestionAnswering node.

        building systems that automatically answer questions posed by humans in a
        natural language usually from a given text
        """
        return QuestionAnswering(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_impainting(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageImpainting:
        """Create a ImageImpainting node.

        Image inpainting is a process that involves filling in missing or damaged parts
        of an image in a way that is visually coherent and seamlessly blends with the
        surrounding areas, often using advanced algorithms and techniques to restore
        the image to its original or intended appearance.
        """
        return ImageImpainting(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_reconstruction(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextReconstruction:
        """Create a TextReconstruction node.

        Text Reconstruction is a process that involves piecing together fragmented or
        incomplete text data to restore it to its original, coherent form.
        """
        return TextReconstruction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def script_execution(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ScriptExecution:
        """Create a ScriptExecution node.

        Script Execution refers to the process of running a set of programmed
        instructions or code within a computing environment, enabling the automated
        performance of tasks, calculations, or operations as defined by the script.
        """
        return ScriptExecution(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def semantic_segmentation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SemanticSegmentation:
        """Create a SemanticSegmentation node.

        Semantic segmentation is a computer vision process that involves classifying
        each pixel in an image into a predefined category, effectively partitioning the
        image into meaningful segments based on the objects or regions they represent.
        """
        return SemanticSegmentation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_emotion_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioEmotionDetection:
        """Create a AudioEmotionDetection node.

        Audio Emotion Detection is a technology that analyzes vocal characteristics and
        patterns in audio recordings to identify and classify the emotional state of
        the speaker.
        """
        return AudioEmotionDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_captioning(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageCaptioning:
        """Create a ImageCaptioning node.

        Image Captioning is a process that involves generating a textual description of
        an image, typically using machine learning models to analyze the visual content
        and produce coherent and contextually relevant sentences that describe the
        objects, actions, and scenes depicted in the image.
        """
        return ImageCaptioning(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def split_on_linebreak(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SplitOnLinebreak:
        """Create a SplitOnLinebreak node.

        The "Split On Linebreak" function divides a given string into a list of
        substrings, using linebreaks (newline characters) as the points of separation.
        """
        return SplitOnLinebreak(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def style_transfer(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> StyleTransfer:
        """Create a StyleTransfer node.

        Style Transfer is a technique in artificial intelligence that applies the
        visual style of one image (such as the brushstrokes of a famous painting) to
        the content of another image, effectively blending the artistic elements of the
        first image with the subject matter of the second.
        """
        return StyleTransfer(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def base_model(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> BaseModel:
        """Create a BaseModel node.

        The Base-Model function serves as a foundational framework designed to provide
        essential features and capabilities upon which more specialized or advanced
        models can be built and customized.
        """
        return BaseModel(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_manipulation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageManipulation:
        """Create a ImageManipulation node.

        Image Manipulation refers to the process of altering or enhancing digital
        images using various techniques and tools to achieve desired visual effects,
        correct imperfections, or transform the image's appearance.
        """
        return ImageManipulation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoEmbedding:
        """Create a VideoEmbedding node.

        Video Embedding is a process that transforms video content into a fixed-
        dimensional vector representation, capturing essential features and patterns to
        facilitate tasks such as retrieval, classification, and recommendation.
        """
        return VideoEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def dialect_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DialectDetection:
        """Create a DialectDetection node.

        Identifies specific dialects within a language, aiding in localized content
        creation or user experience personalization.
        """
        return DialectDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def fill_text_mask(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> FillTextMask:
        """Create a FillTextMask node.

        Completes missing parts of a text based on the context, ideal for content
        generation or data augmentation tasks.
        """
        return FillTextMask(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def activity_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ActivityDetection:
        """Create a ActivityDetection node.

        detection of the presence or absence of human speech, used in speech
        processing.
        """
        return ActivityDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def select_supplier_for_translation(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> SelectSupplierForTranslation:
        """Create a SelectSupplierForTranslation node.

        Supplier For Translation
        """
        return SelectSupplierForTranslation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def expression_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ExpressionDetection:
        """Create a ExpressionDetection node.

        Expression Detection is the process of identifying and analyzing facial
        expressions to interpret emotions or intentions using AI and computer vision
        techniques.
        """
        return ExpressionDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoGeneration:
        """Create a VideoGeneration node.

        Produces video content based on specific inputs or datasets. Can be used for
        simulations, animations, or even deepfake detection.
        """
        return VideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageAnalysis:
        """Create a ImageAnalysis node.

        Image analysis is the extraction of meaningful information from images
        """
        return ImageAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def noise_removal(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> NoiseRemoval:
        """Create a NoiseRemoval node.

        Noise Removal is a process that involves identifying and eliminating unwanted
        random variations or disturbances from an audio signal to enhance the clarity
        and quality of the underlying information.
        """
        return NoiseRemoval(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_and_video_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageAndVideoAnalysis:
        """Create a ImageAndVideoAnalysis node."""
        return ImageAndVideoAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def keyword_extraction(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> KeywordExtraction:
        """Create a KeywordExtraction node.

        It helps concise the text and obtain relevant keywords Example use-cases are
        finding topics of interest from a news article and identifying the problems
        based on customer reviews and so.
        """
        return KeywordExtraction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def split_on_silence(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SplitOnSilence:
        """Create a SplitOnSilence node.

        The "Split On Silence" function divides an audio recording into separate
        segments based on periods of silence, allowing for easier editing and analysis
        of individual sections.
        """
        return SplitOnSilence(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def intent_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> IntentRecognition:
        """Create a IntentRecognition node.

        classify the user's utterance (provided in varied natural language)  or text
        into one of several predefined classes, that is, intents.
        """
        return IntentRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def depth_estimation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DepthEstimation:
        """Create a DepthEstimation node.

        Depth estimation is a computational process that determines the distance of
        objects from a viewpoint, typically using visual data from cameras or sensors
        to create a three-dimensional understanding of a scene.
        """
        return DepthEstimation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def connector(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Connector:
        """Create a Connector node.

        Connectors are integration that allow you to connect your AI agents to external
        tools
        """
        return Connector(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speaker_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeakerRecognition:
        """Create a SpeakerRecognition node.

        In speaker identification, an utterance from an unknown speaker is analyzed and
        compared with speech models of known speakers.
        """
        return SpeakerRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def syntax_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SyntaxAnalysis:
        """Create a SyntaxAnalysis node.

        Is the process of analyzing natural language with the rules of a formal
        grammar. Grammatical rules are applied to categories and groups of words, not
        individual words. Syntactic analysis basically assigns a semantic structure to
        text.
        """
        return SyntaxAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def entity_sentiment_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> EntitySentimentAnalysis:
        """Create a EntitySentimentAnalysis node.

        Entity Sentiment Analysis combines both entity analysis and sentiment analysis
        and attempts to determine the sentiment (positive or negative) expressed about
        entities within the text.
        """
        return EntitySentimentAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def classification_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ClassificationMetric:
        """Create a ClassificationMetric node.

        A Classification Metric is a quantitative measure used to evaluate the quality
        and effectiveness of classification models.
        """
        return ClassificationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextDetection:
        """Create a TextDetection node.

        detect text regions in the complex background and label them with bounding
        boxes.
        """
        return TextDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def guardrails(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Guardrails:
        """Create a Guardrails node.

         Guardrails are governance rules that enforce security, compliance, and
        operational best practices, helping prevent mistakes and detect suspicious
        activity
        """
        return Guardrails(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def emotion_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> EmotionDetection:
        """Create a EmotionDetection node.

        Identifies human emotions from text or audio, enhancing user experience in
        chatbots or customer feedback analysis.
        """
        return EmotionDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_forced_alignment(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoForcedAlignment:
        """Create a VideoForcedAlignment node.

        Aligns the transcription of spoken content in a video with its corresponding
        timecodes, facilitating subtitle creation.
        """
        return VideoForcedAlignment(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageContentModeration:
        """Create a ImageContentModeration node.

        Detects and filters out inappropriate or harmful images, essential for
        platforms with user-generated visual content.
        """
        return ImageContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_summarization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSummarization:
        """Create a TextSummarization node.

        Extracts the main points from a larger body of text, producing a concise
        summary without losing the primary message.
        """
        return TextSummarization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_to_video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageToVideoGeneration:
        """Create a ImageToVideoGeneration node.

        The Image To Video Generation function transforms a series of static images
        into a cohesive, dynamic video sequence, often incorporating transitions,
        effects, and synchronization with audio to create a visually engaging
        narrative.
        """
        return ImageToVideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_understanding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoUnderstanding:
        """Create a VideoUnderstanding node.

        Video Understanding is the process of analyzing and interpreting video content
        to extract meaningful information, such as identifying objects, actions,
        events, and contextual relationships within the footage.
        """
        return VideoUnderstanding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation_metric_default(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> TextGenerationMetricDefault:
        """Create a TextGenerationMetricDefault node.

        The "Text Generation Metric Default" function provides a standard set of
        evaluation metrics for assessing the quality and performance of text generation
        models.
        """
        return TextGenerationMetricDefault(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_to_video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextToVideoGeneration:
        """Create a TextToVideoGeneration node.

        Text To Video Generation is a process that converts written descriptions or
        scripts into dynamic, visual video content using advanced algorithms and
        artificial intelligence.
        """
        return TextToVideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_label_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoLabelDetection:
        """Create a VideoLabelDetection node.

        Identifies and tags objects, scenes, or activities within a video. Useful for
        content indexing and recommendation systems.
        """
        return VideoLabelDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_spam_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSpamDetection:
        """Create a TextSpamDetection node.

        Identifies and filters out unwanted or irrelevant text content, ideal for
        moderating user-generated content or ensuring quality in communication
        platforms.
        """
        return TextSpamDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextContentModeration:
        """Create a TextContentModeration node.

        Scans and identifies potentially harmful, offensive, or inappropriate textual
        content, ensuring safer user environments.
        """
        return TextContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_transcript_improvement(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> AudioTranscriptImprovement:
        """Create a AudioTranscriptImprovement node.

        Refines and corrects transcriptions generated from audio data, improving
        readability and accuracy.
        """
        return AudioTranscriptImprovement(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_transcript_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioTranscriptAnalysis:
        """Create a AudioTranscriptAnalysis node.

        Analyzes transcribed audio data for insights, patterns, or specific information
        extraction.
        """
        return AudioTranscriptAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_non_speech_classification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> SpeechNonSpeechClassification:
        """Create a SpeechNonSpeechClassification node.

        Differentiates between speech and non-speech audio segments. Great for editing
        software and transcription services to exclude irrelevant audio.
        """
        return SpeechNonSpeechClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_generation_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioGenerationMetric:
        """Create a AudioGenerationMetric node.

        The Audio Generation Metric is a quantitative measure used to evaluate the
        quality, accuracy, and overall performance of audio generated by artificial
        intelligence systems, often considering factors such as fidelity,
        intelligibility, and similarity to human-produced audio.
        """
        return AudioGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def named_entity_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> NamedEntityRecognition:
        """Create a NamedEntityRecognition node.

        Identifies and classifies named entities (e.g., persons, organizations,
        locations) within text. Useful for information extraction, content tagging, and
        search enhancements.
        """
        return NamedEntityRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_synthesis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechSynthesis:
        """Create a SpeechSynthesis node.

        Generates human-like speech from written text. Ideal for text-to-speech
        applications, audiobooks, and voice assistants.
        """
        return SpeechSynthesis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def document_information_extraction(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> DocumentInformationExtraction:
        """Create a DocumentInformationExtraction node.

        Document Information Extraction is the process of automatically identifying,
        extracting, and structuring relevant data from unstructured or semi-structured
        documents, such as invoices, receipts, contracts, and forms, to facilitate
        easier data management and analysis.
        """
        return DocumentInformationExtraction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def ocr(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Ocr:
        """Create a Ocr node.

        Converts images of typed, handwritten, or printed text into machine-encoded
        text. Used in digitizing printed texts for data retrieval.
        """
        return Ocr(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def subtitling_translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SubtitlingTranslation:
        """Create a SubtitlingTranslation node.

        Converts the text of subtitles from one language to another, ensuring context
        and cultural nuances are maintained. Essential for global content distribution.
        """
        return SubtitlingTranslation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_to_audio(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextToAudio:
        """Create a TextToAudio node.

        The Text to Audio function converts written text into spoken words, allowing
        users to listen to the content instead of reading it.
        """
        return TextToAudio(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multilingual_speech_recognition(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> MultilingualSpeechRecognition:
        """Create a MultilingualSpeechRecognition node.

        Multilingual Speech Recognition is a technology that enables the automatic
        transcription of spoken language into text across multiple languages, allowing
        for seamless communication and understanding in diverse linguistic contexts.
        """
        return MultilingualSpeechRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def offensive_language_identification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> OffensiveLanguageIdentification:
        """Create a OffensiveLanguageIdentification node.

        Detects language or phrases that might be considered offensive, aiding in
        content moderation and creating respectful user interactions.
        """
        return OffensiveLanguageIdentification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def benchmark_scoring_mt(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> BenchmarkScoringMt:
        """Create a BenchmarkScoringMt node.

        Benchmark Scoring MT is a function designed to evaluate and score machine
        translation systems by comparing their output against a set of predefined
        benchmarks, thereby assessing their accuracy and performance.
        """
        return BenchmarkScoringMt(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speaker_diarization_audio(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeakerDiarizationAudio:
        """Create a SpeakerDiarizationAudio node.

        Identifies individual speakers and their respective speech segments within an
        audio clip. Ideal for multi-speaker recordings or conference calls.
        """
        return SpeakerDiarizationAudio(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def voice_cloning(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VoiceCloning:
        """Create a VoiceCloning node.

        Replicates a person's voice based on a sample, allowing for the generation of
        speech in that person's tone and style. Used cautiously due to ethical
        considerations.
        """
        return VoiceCloning(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def search(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Search:
        """Create a Search node.

        An algorithm that identifies and returns data or items that match particular
        keywords or conditions from a dataset. A fundamental tool for databases and
        websites.
        """
        return Search(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def object_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ObjectDetection:
        """Create a ObjectDetection node.

        Object Detection is a computer vision technology that identifies and locates
        objects within an image, typically by drawing bounding boxes around the
        detected objects and classifying them into predefined categories.
        """
        return ObjectDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def diacritization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Diacritization:
        """Create a Diacritization node.

        Adds diacritical marks to text, essential for languages where meaning can
        change based on diacritics.
        """
        return Diacritization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speaker_diarization_video(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeakerDiarizationVideo:
        """Create a SpeakerDiarizationVideo node.

        Segments a video based on different speakers, identifying when each individual
        speaks. Useful for transcriptions and understanding multi-person conversations.
        """
        return SpeakerDiarizationVideo(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_forced_alignment(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioForcedAlignment:
        """Create a AudioForcedAlignment node.

        Synchronizes phonetic and phonological text with the corresponding segments in
        an audio file. Useful in linguistic research and detailed transcription tasks.
        """
        return AudioForcedAlignment(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def token_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TokenClassification:
        """Create a TokenClassification node.

        Token-level classification means that each token will be given a label, for
        example a part-of-speech tagger will classify each word as one particular part
        of speech.
        """
        return TokenClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def topic_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TopicClassification:
        """Create a TopicClassification node.

        Assigns categories or topics to a piece of text based on its content,
        facilitating content organization and retrieval.
        """
        return TopicClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def intent_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> IntentClassification:
        """Create a IntentClassification node.

        Intent Classification is a natural language processing task that involves
        analyzing and categorizing user text input to determine the underlying purpose
        or goal behind the communication, such as booking a flight, asking for weather
        information, or setting a reminder.
        """
        return IntentClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoContentModeration:
        """Create a VideoContentModeration node.

        Automatically reviews video content to detect and possibly remove inappropriate
        or harmful material. Essential for user-generated content platforms.
        """
        return VideoContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextGenerationMetric:
        """Create a TextGenerationMetric node.

        A Text Generation Metric is a quantitative measure used to evaluate the quality
        and effectiveness of text produced by natural language processing models, often
        assessing aspects such as coherence, relevance, fluency, and adherence to given
        prompts or instructions.
        """
        return TextGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageEmbedding:
        """Create a ImageEmbedding node.

        Image Embedding is a process that transforms an image into a fixed-dimensional
        vector representation, capturing its essential features and enabling efficient
        comparison, retrieval, and analysis in various machine learning and computer
        vision tasks.
        """
        return ImageEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_label_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageLabelDetection:
        """Create a ImageLabelDetection node.

        Identifies objects, themes, or topics within images, useful for image
        categorization, search, and recommendation systems.
        """
        return ImageLabelDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_colorization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageColorization:
        """Create a ImageColorization node.

        Image colorization is a process that involves adding color to grayscale images,
        transforming them from black-and-white to full-color representations, often
        using advanced algorithms and machine learning techniques to predict and apply
        the appropriate hues and shades.
        """
        return ImageColorization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def metric_aggregation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> MetricAggregation:
        """Create a MetricAggregation node.

        Metric Aggregation is a function that computes and summarizes numerical data by
        applying statistical operations, such as averaging, summing, or finding the
        minimum and maximum values, to provide insights and facilitate analysis of
        large datasets.
        """
        return MetricAggregation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def instance_segmentation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> InstanceSegmentation:
        """Create a InstanceSegmentation node.

        Instance segmentation is a computer vision task that involves detecting and
        delineating each distinct object within an image, assigning a unique label and
        precise boundary to every individual instance of objects, even if they belong
        to the same category.
        """
        return InstanceSegmentation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def other__multipurpose_(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> OtherMultipurpose:
        """Create a OtherMultipurpose node.

        The "Other (Multipurpose)" function serves as a versatile category designed to
        accommodate a wide range of tasks and activities that do not fit neatly into
        predefined classifications, offering flexibility and adaptability for various
        needs.
        """
        return OtherMultipurpose(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechTranslation:
        """Create a SpeechTranslation node.

        Speech Translation is a technology that converts spoken language in real-time
        from one language to another, enabling seamless communication between speakers
        of different languages.
        """
        return SpeechTranslation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_text_generation_metric_default(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> ReferencelessTextGenerationMetricDefault:
        """Create a ReferencelessTextGenerationMetricDefault node.

        The Referenceless Text Generation Metric Default is a function designed to
        evaluate the quality of generated text without relying on reference texts for
        comparison.
        """
        return ReferencelessTextGenerationMetricDefault(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_text_generation_metric(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> ReferencelessTextGenerationMetric:
        """Create a ReferencelessTextGenerationMetric node.

        The Referenceless Text Generation Metric is a method for evaluating the quality
        of generated text without requiring a reference text for comparison, often
        leveraging models or algorithms to assess coherence, relevance, and fluency
        based on intrinsic properties of the text itself.
        """
        return ReferencelessTextGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_denormalization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextDenormalization:
        """Create a TextDenormalization node.

        Converts standardized or normalized text into its original, often more
        readable, form. Useful in natural language generation tasks.
        """
        return TextDenormalization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_compression(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageCompression:
        """Create a ImageCompression node.

        Reduces the size of image files without significantly compromising their visual
        quality. Useful for optimizing storage and improving webpage load times.
        """
        return ImageCompression(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextClassification:
        """Create a TextClassification node.

        Categorizes text into predefined groups or topics, facilitating content
        organization and targeted actions.
        """
        return TextClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def asr_age_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrAgeClassification:
        """Create a AsrAgeClassification node.

        The ASR Age Classification function is designed to analyze audio recordings of
        speech to determine the speaker's age group by leveraging automatic speech
        recognition (ASR) technology and machine learning algorithms.
        """
        return AsrAgeClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def asr_quality_estimation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrQualityEstimation:
        """Create a AsrQualityEstimation node.

        ASR Quality Estimation is a process that evaluates the accuracy and reliability
        of automatic speech recognition systems by analyzing their performance in
        transcribing spoken language into text.
        """
        return AsrQualityEstimation(*args, asset_id=asset_id, pipeline=self, **kwargs)
