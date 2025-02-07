# This is an auto generated module. PLEASE DO NOT EDIT


from typing import Union, Type
from aixplain.enums import DataType

from .designer import InputParam, OutputParam, Inputs, Outputs, TI, TO, AssetNode, BaseReconstructor, BaseSegmentor, BaseMetric
from .default import DefaultPipeline
from aixplain.modules import asset


class ObjectDetectionInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class ObjectDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ObjectDetection(AssetNode[ObjectDetectionInputs, ObjectDetectionOutputs]):
    """
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


class TextEmbeddingInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextEmbeddingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextEmbedding(AssetNode[TextEmbeddingInputs, TextEmbeddingOutputs]):
    """
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


class SemanticSegmentationInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class SemanticSegmentationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SemanticSegmentation(AssetNode[SemanticSegmentationInputs, SemanticSegmentationOutputs]):
    """
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


class ReferencelessAudioGenerationMetricInputs(Inputs):
    hypotheses: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.AUDIO, is_required=True)
        self.sources = self.create_param(code="sources", data_type=DataType.AUDIO, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class ReferencelessAudioGenerationMetricOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ReferencelessAudioGenerationMetric(
    BaseMetric[ReferencelessAudioGenerationMetricInputs, ReferencelessAudioGenerationMetricOutputs]
):
    """
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


class ScriptExecutionInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class ScriptExecutionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ScriptExecution(AssetNode[ScriptExecutionInputs, ScriptExecutionOutputs]):
    """
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


class ImageImpaintingInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class ImageImpaintingOutputs(Outputs):
    image: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class ImageImpainting(AssetNode[ImageImpaintingInputs, ImageImpaintingOutputs]):
    """
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


class ImageEmbeddingInputs(Inputs):
    language: InputParam = None
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class ImageEmbeddingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ImageEmbedding(AssetNode[ImageEmbeddingInputs, ImageEmbeddingOutputs]):
    """
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


class MetricAggregationInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class MetricAggregationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class MetricAggregation(BaseMetric[MetricAggregationInputs, MetricAggregationOutputs]):
    """
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


class SpeechTranslationInputs(Inputs):
    source_audio: InputParam = None
    sourcelanguage: InputParam = None
    targetlanguage: InputParam = None
    dialect: InputParam = None
    voice: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.sourcelanguage = self.create_param(code="sourcelanguage", data_type=DataType.LABEL, is_required=True)
        self.targetlanguage = self.create_param(code="targetlanguage", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.voice = self.create_param(code="voice", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class SpeechTranslationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SpeechTranslation(AssetNode[SpeechTranslationInputs, SpeechTranslationOutputs]):
    """
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


class DepthEstimationInputs(Inputs):
    language: InputParam = None
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class DepthEstimationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class DepthEstimation(AssetNode[DepthEstimationInputs, DepthEstimationOutputs]):
    """
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


class NoiseRemovalInputs(Inputs):
    audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)


class NoiseRemovalOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class NoiseRemoval(AssetNode[NoiseRemovalInputs, NoiseRemovalOutputs]):
    """
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


class DiacritizationInputs(Inputs):
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class DiacritizationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Diacritization(AssetNode[DiacritizationInputs, DiacritizationOutputs]):
    """
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


class AudioTranscriptAnalysisInputs(Inputs):
    language: InputParam = None
    dialect: InputParam = None
    source_supplier: InputParam = None
    source_audio: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.source_supplier = self.create_param(code="source_supplier", data_type=DataType.LABEL, is_required=False)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class AudioTranscriptAnalysisOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class AudioTranscriptAnalysis(AssetNode[AudioTranscriptAnalysisInputs, AudioTranscriptAnalysisOutputs]):
    """
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


class ExtractAudioFromVideoInputs(Inputs):
    video: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)


class ExtractAudioFromVideoOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class ExtractAudioFromVideo(AssetNode[ExtractAudioFromVideoInputs, ExtractAudioFromVideoOutputs]):
    """
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


class AudioReconstructionInputs(Inputs):
    audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class AudioReconstructionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class AudioReconstruction(BaseReconstructor[AudioReconstructionInputs, AudioReconstructionOutputs]):
    """
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


class ClassificationMetricInputs(Inputs):
    hypotheses: InputParam = None
    references: InputParam = None
    lowerIsBetter: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.LABEL, is_required=True)
        self.references = self.create_param(code="references", data_type=DataType.LABEL, is_required=True)
        self.lowerIsBetter = self.create_param(code="lowerIsBetter", data_type=DataType.TEXT, is_required=False)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class ClassificationMetricOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.NUMBER)


class ClassificationMetric(BaseMetric[ClassificationMetricInputs, ClassificationMetricOutputs]):
    """
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


class TextGenerationMetricInputs(Inputs):
    hypotheses: InputParam = None
    references: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.TEXT, is_required=True)
        self.references = self.create_param(code="references", data_type=DataType.TEXT, is_required=False)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class TextGenerationMetricOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextGenerationMetric(BaseMetric[TextGenerationMetricInputs, TextGenerationMetricOutputs]):
    """
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


class TextSpamDetectionInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextSpamDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextSpamDetection(AssetNode[TextSpamDetectionInputs, TextSpamDetectionOutputs]):
    """
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


class TextToImageGenerationInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class TextToImageGenerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.IMAGE)


class TextToImageGeneration(AssetNode[TextToImageGenerationInputs, TextToImageGenerationOutputs]):
    """
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


class VoiceCloningInputs(Inputs):
    text: InputParam = None
    audio: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    voice: InputParam = None
    script: InputParam = None
    type: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.voice = self.create_param(code="voice", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.type = self.create_param(code="type", data_type=DataType.LABEL, is_required=False)


class VoiceCloningOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class VoiceCloning(AssetNode[VoiceCloningInputs, VoiceCloningOutputs]):
    """
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


class TextSegmenationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)


class TextSegmenationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextSegmenation(AssetNode[TextSegmenationInputs, TextSegmenationOutputs]):
    """
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


class BenchmarkScoringMtInputs(Inputs):
    input: InputParam = None
    text: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.input = self.create_param(code="input", data_type=DataType.TEXT, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class BenchmarkScoringMtOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class BenchmarkScoringMt(AssetNode[BenchmarkScoringMtInputs, BenchmarkScoringMtOutputs]):
    """
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


class ImageManipulationInputs(Inputs):
    image: InputParam = None
    targetimage: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.targetimage = self.create_param(code="targetimage", data_type=DataType.IMAGE, is_required=True)


class ImageManipulationOutputs(Outputs):
    image: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class ImageManipulation(AssetNode[ImageManipulationInputs, ImageManipulationOutputs]):
    """
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


class NamedEntityRecognitionInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None
    domain: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.domain = self.create_param(code="domain", data_type=DataType.LABEL, is_required=False)


class NamedEntityRecognitionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class NamedEntityRecognition(AssetNode[NamedEntityRecognitionInputs, NamedEntityRecognitionOutputs]):
    """
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


class OffensiveLanguageIdentificationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class OffensiveLanguageIdentificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class OffensiveLanguageIdentification(AssetNode[OffensiveLanguageIdentificationInputs, OffensiveLanguageIdentificationOutputs]):
    """
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


class SearchInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class SearchOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Search(AssetNode[SearchInputs, SearchOutputs]):
    """
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


class SentimentAnalysisInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class SentimentAnalysisOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SentimentAnalysis(AssetNode[SentimentAnalysisInputs, SentimentAnalysisOutputs]):
    """
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


class ImageColorizationInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class ImageColorizationOutputs(Outputs):
    image: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class ImageColorization(AssetNode[ImageColorizationInputs, ImageColorizationOutputs]):
    """
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


class SpeechClassificationInputs(Inputs):
    audio: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeechClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SpeechClassification(AssetNode[SpeechClassificationInputs, SpeechClassificationOutputs]):
    """
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


class DialectDetectionInputs(Inputs):
    audio: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)


class DialectDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class DialectDetection(AssetNode[DialectDetectionInputs, DialectDetectionOutputs]):
    """
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


class VideoLabelDetectionInputs(Inputs):
    video: InputParam = None
    min_confidence: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.min_confidence = self.create_param(code="min_confidence", data_type=DataType.TEXT, is_required=False)


class VideoLabelDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class VideoLabelDetection(AssetNode[VideoLabelDetectionInputs, VideoLabelDetectionOutputs]):
    """
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


class SpeechSynthesisInputs(Inputs):
    audio: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    voice: InputParam = None
    script: InputParam = None
    text: InputParam = None
    type: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.voice = self.create_param(code="voice", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.type = self.create_param(code="type", data_type=DataType.LABEL, is_required=False)


class SpeechSynthesisOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class SpeechSynthesis(AssetNode[SpeechSynthesisInputs, SpeechSynthesisOutputs]):
    """
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


class SplitOnSilenceInputs(Inputs):
    audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class SplitOnSilenceOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class SplitOnSilence(AssetNode[SplitOnSilenceInputs, SplitOnSilenceOutputs]):
    """
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


class ExpressionDetectionInputs(Inputs):
    media: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.media = self.create_param(code="media", data_type=DataType.IMAGE, is_required=True)


class ExpressionDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ExpressionDetection(AssetNode[ExpressionDetectionInputs, ExpressionDetectionOutputs]):
    """
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


class AutoMaskGenerationInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class AutoMaskGenerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AutoMaskGeneration(AssetNode[AutoMaskGenerationInputs, AutoMaskGenerationOutputs]):
    """
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


class DocumentImageParsingInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class DocumentImageParsingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class DocumentImageParsing(AssetNode[DocumentImageParsingInputs, DocumentImageParsingOutputs]):
    """
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


class EntityLinkingInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    domain: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.domain = self.create_param(code="domain", data_type=DataType.LABEL, is_required=False)


class EntityLinkingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class EntityLinking(AssetNode[EntityLinkingInputs, EntityLinkingOutputs]):
    """
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


class ReferencelessTextGenerationMetricDefaultInputs(Inputs):
    hypotheses: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.TEXT, is_required=True)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class ReferencelessTextGenerationMetricDefaultOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ReferencelessTextGenerationMetricDefault(
    BaseMetric[ReferencelessTextGenerationMetricDefaultInputs, ReferencelessTextGenerationMetricDefaultOutputs]
):
    """
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


class FillTextMaskInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class FillTextMaskOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class FillTextMask(AssetNode[FillTextMaskInputs, FillTextMaskOutputs]):
    """
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


class SubtitlingTranslationInputs(Inputs):
    text: InputParam = None
    sourcelanguage: InputParam = None
    dialect_in: InputParam = None
    target_supplier: InputParam = None
    targetlanguages: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.sourcelanguage = self.create_param(code="sourcelanguage", data_type=DataType.LABEL, is_required=True)
        self.dialect_in = self.create_param(code="dialect_in", data_type=DataType.LABEL, is_required=False)
        self.target_supplier = self.create_param(code="target_supplier", data_type=DataType.LABEL, is_required=False)
        self.targetlanguages = self.create_param(code="targetlanguages", data_type=DataType.LABEL, is_required=False)


class SubtitlingTranslationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SubtitlingTranslation(AssetNode[SubtitlingTranslationInputs, SubtitlingTranslationOutputs]):
    """
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


class InstanceSegmentationInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class InstanceSegmentationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class InstanceSegmentation(AssetNode[InstanceSegmentationInputs, InstanceSegmentationOutputs]):
    """
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


class VisemeGenerationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class VisemeGenerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class VisemeGeneration(AssetNode[VisemeGenerationInputs, VisemeGenerationOutputs]):
    """
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


class AudioGenerationMetricInputs(Inputs):
    hypotheses: InputParam = None
    references: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.AUDIO, is_required=True)
        self.references = self.create_param(code="references", data_type=DataType.AUDIO, is_required=False)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class AudioGenerationMetricOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class AudioGenerationMetric(BaseMetric[AudioGenerationMetricInputs, AudioGenerationMetricOutputs]):
    """
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


class VideoUnderstandingInputs(Inputs):
    video: InputParam = None
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class VideoUnderstandingOutputs(Outputs):
    text: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT)


class VideoUnderstanding(AssetNode[VideoUnderstandingInputs, VideoUnderstandingOutputs]):
    """
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


class TextNormalizationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    settings: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)
        self.settings = self.create_param(code="settings", data_type=DataType.TEXT, is_required=False)


class TextNormalizationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextNormalization(AssetNode[TextNormalizationInputs, TextNormalizationOutputs]):
    """
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


class AsrQualityEstimationInputs(Inputs):
    text: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class AsrQualityEstimationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AsrQualityEstimation(AssetNode[AsrQualityEstimationInputs, AsrQualityEstimationOutputs]):
    """
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


class VoiceActivityDetectionInputs(Inputs):
    audio: InputParam = None
    onset: InputParam = None
    offset: InputParam = None
    min_duration_on: InputParam = None
    min_duration_off: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.onset = self.create_param(code="onset", data_type=DataType.TEXT, is_required=False)
        self.offset = self.create_param(code="offset", data_type=DataType.TEXT, is_required=False)
        self.min_duration_on = self.create_param(code="min_duration_on", data_type=DataType.TEXT, is_required=False)
        self.min_duration_off = self.create_param(code="min_duration_off", data_type=DataType.TEXT, is_required=False)


class VoiceActivityDetectionOutputs(Outputs):
    data: OutputParam = None
    audio: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)


class VoiceActivityDetection(BaseSegmentor[VoiceActivityDetectionInputs, VoiceActivityDetectionOutputs]):
    """
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


class SpeechNonSpeechClassificationInputs(Inputs):
    audio: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeechNonSpeechClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class SpeechNonSpeechClassification(AssetNode[SpeechNonSpeechClassificationInputs, SpeechNonSpeechClassificationOutputs]):
    """
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


class AudioTranscriptImprovementInputs(Inputs):
    language: InputParam = None
    dialect: InputParam = None
    source_supplier: InputParam = None
    is_medical: InputParam = None
    source_audio: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.source_supplier = self.create_param(code="source_supplier", data_type=DataType.LABEL, is_required=False)
        self.is_medical = self.create_param(code="is_medical", data_type=DataType.TEXT, is_required=True)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class AudioTranscriptImprovementOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class AudioTranscriptImprovement(AssetNode[AudioTranscriptImprovementInputs, AudioTranscriptImprovementOutputs]):
    """
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


class TextContentModerationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextContentModerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextContentModeration(AssetNode[TextContentModerationInputs, TextContentModerationOutputs]):
    """
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


class EmotionDetectionInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class EmotionDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class EmotionDetection(AssetNode[EmotionDetectionInputs, EmotionDetectionOutputs]):
    """
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


class AudioForcedAlignmentInputs(Inputs):
    audio: InputParam = None
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class AudioForcedAlignmentOutputs(Outputs):
    text: OutputParam = None
    audio: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)


class AudioForcedAlignment(AssetNode[AudioForcedAlignmentInputs, AudioForcedAlignmentOutputs]):
    """
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


class VideoContentModerationInputs(Inputs):
    video: InputParam = None
    min_confidence: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.min_confidence = self.create_param(code="min_confidence", data_type=DataType.TEXT, is_required=False)


class VideoContentModerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class VideoContentModeration(AssetNode[VideoContentModerationInputs, VideoContentModerationOutputs]):
    """
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


class ImageLabelDetectionInputs(Inputs):
    image: InputParam = None
    min_confidence: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.min_confidence = self.create_param(code="min_confidence", data_type=DataType.TEXT, is_required=False)


class ImageLabelDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ImageLabelDetection(AssetNode[ImageLabelDetectionInputs, ImageLabelDetectionOutputs]):
    """
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


class VideoForcedAlignmentInputs(Inputs):
    video: InputParam = None
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class VideoForcedAlignmentOutputs(Outputs):
    text: OutputParam = None
    video: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO)


class VideoForcedAlignment(AssetNode[VideoForcedAlignmentInputs, VideoForcedAlignmentOutputs]):
    """
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


class TextGenerationInputs(Inputs):
    text: InputParam = None
    prompt: InputParam = None
    context: InputParam = None
    language: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.prompt = self.create_param(code="prompt", data_type=DataType.TEXT, is_required=False)
        self.context = self.create_param(code="context", data_type=DataType.TEXT, is_required=False)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextGenerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextGeneration(AssetNode[TextGenerationInputs, TextGenerationOutputs]):
    """
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


class TextClassificationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class TextClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextClassification(AssetNode[TextClassificationInputs, TextClassificationOutputs]):
    """
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


class SpeechEmbeddingInputs(Inputs):
    audio: InputParam = None
    language: InputParam = None
    dialect: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class SpeechEmbeddingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SpeechEmbedding(AssetNode[SpeechEmbeddingInputs, SpeechEmbeddingOutputs]):
    """
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


class TopicClassificationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class TopicClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TopicClassification(AssetNode[TopicClassificationInputs, TopicClassificationOutputs]):
    """
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


class TranslationInputs(Inputs):
    text: InputParam = None
    sourcelanguage: InputParam = None
    targetlanguage: InputParam = None
    script_in: InputParam = None
    script_out: InputParam = None
    dialect_in: InputParam = None
    dialect_out: InputParam = None
    context: InputParam = None

    def __init__(self, node=None):
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
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Translation(AssetNode[TranslationInputs, TranslationOutputs]):
    """
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


class SpeechRecognitionInputs(Inputs):
    language: InputParam = None
    dialect: InputParam = None
    voice: InputParam = None
    source_audio: InputParam = None
    script: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)
        self.voice = self.create_param(code="voice", data_type=DataType.LABEL, is_required=False)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)


class SpeechRecognitionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class SpeechRecognition(AssetNode[SpeechRecognitionInputs, SpeechRecognitionOutputs]):
    """
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


class SubtitlingInputs(Inputs):
    source_audio: InputParam = None
    sourcelanguage: InputParam = None
    dialect_in: InputParam = None
    source_supplier: InputParam = None
    target_supplier: InputParam = None
    targetlanguages: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.sourcelanguage = self.create_param(code="sourcelanguage", data_type=DataType.LABEL, is_required=True)
        self.dialect_in = self.create_param(code="dialect_in", data_type=DataType.LABEL, is_required=False)
        self.source_supplier = self.create_param(code="source_supplier", data_type=DataType.LABEL, is_required=False)
        self.target_supplier = self.create_param(code="target_supplier", data_type=DataType.LABEL, is_required=False)
        self.targetlanguages = self.create_param(code="targetlanguages", data_type=DataType.LABEL, is_required=False)


class SubtitlingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Subtitling(AssetNode[SubtitlingInputs, SubtitlingOutputs]):
    """
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


class ImageCaptioningInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)


class ImageCaptioningOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ImageCaptioning(AssetNode[ImageCaptioningInputs, ImageCaptioningOutputs]):
    """
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


class AudioLanguageIdentificationInputs(Inputs):
    audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class AudioLanguageIdentificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AudioLanguageIdentification(AssetNode[AudioLanguageIdentificationInputs, AudioLanguageIdentificationOutputs]):
    """
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


class VideoEmbeddingInputs(Inputs):
    language: InputParam = None
    video: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=False)


class VideoEmbeddingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.EMBEDDING)


class VideoEmbedding(AssetNode[VideoEmbeddingInputs, VideoEmbeddingOutputs]):
    """
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


class AsrAgeClassificationInputs(Inputs):
    source_audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)


class AsrAgeClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AsrAgeClassification(AssetNode[AsrAgeClassificationInputs, AsrAgeClassificationOutputs]):
    """
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


class AudioIntentDetectionInputs(Inputs):
    audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)


class AudioIntentDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AudioIntentDetection(AssetNode[AudioIntentDetectionInputs, AudioIntentDetectionOutputs]):
    """
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


class LanguageIdentificationInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class LanguageIdentificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class LanguageIdentification(AssetNode[LanguageIdentificationInputs, LanguageIdentificationOutputs]):
    """
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


class OcrInputs(Inputs):
    image: InputParam = None
    featuretypes: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.featuretypes = self.create_param(code="featuretypes", data_type=DataType.TEXT, is_required=True)


class OcrOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class Ocr(AssetNode[OcrInputs, OcrOutputs]):
    """
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


class AsrGenderClassificationInputs(Inputs):
    source_audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)


class AsrGenderClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AsrGenderClassification(AssetNode[AsrGenderClassificationInputs, AsrGenderClassificationOutputs]):
    """
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


class LanguageIdentificationAudioInputs(Inputs):
    audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)


class LanguageIdentificationAudioOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class LanguageIdentificationAudio(AssetNode[LanguageIdentificationAudioInputs, LanguageIdentificationAudioOutputs]):
    """
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


class BaseModelInputs(Inputs):
    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class BaseModelOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class BaseModel(AssetNode[BaseModelInputs, BaseModelOutputs]):
    """
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


class LoglikelihoodInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class LoglikelihoodOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.NUMBER)


class Loglikelihood(AssetNode[LoglikelihoodInputs, LoglikelihoodOutputs]):
    """
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


class ImageToVideoGenerationInputs(Inputs):
    language: InputParam = None
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class ImageToVideoGenerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.VIDEO)


class ImageToVideoGeneration(AssetNode[ImageToVideoGenerationInputs, ImageToVideoGenerationOutputs]):
    """
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


class PartOfSpeechTaggingInputs(Inputs):
    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class PartOfSpeechTaggingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class PartOfSpeechTagging(AssetNode[PartOfSpeechTaggingInputs, PartOfSpeechTaggingOutputs]):
    """
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


class BenchmarkScoringAsrInputs(Inputs):
    input: InputParam = None
    text: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.input = self.create_param(code="input", data_type=DataType.AUDIO, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class BenchmarkScoringAsrOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class BenchmarkScoringAsr(AssetNode[BenchmarkScoringAsrInputs, BenchmarkScoringAsrOutputs]):
    """
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


class VisualQuestionAnsweringInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class VisualQuestionAnsweringOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class VisualQuestionAnswering(AssetNode[VisualQuestionAnsweringInputs, VisualQuestionAnsweringOutputs]):
    """
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


class DocumentInformationExtractionInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class DocumentInformationExtractionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class DocumentInformationExtraction(AssetNode[DocumentInformationExtractionInputs, DocumentInformationExtractionOutputs]):
    """
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


class VideoGenerationInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class VideoGenerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.VIDEO)


class VideoGeneration(AssetNode[VideoGenerationInputs, VideoGenerationOutputs]):
    """
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


class MultiClassImageClassificationInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class MultiClassImageClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class MultiClassImageClassification(AssetNode[MultiClassImageClassificationInputs, MultiClassImageClassificationOutputs]):
    """
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


class StyleTransferInputs(Inputs):
    image: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=False)


class StyleTransferOutputs(Outputs):
    image: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class StyleTransfer(AssetNode[StyleTransferInputs, StyleTransferOutputs]):
    """
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


class MultiClassTextClassificationInputs(Inputs):
    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class MultiClassTextClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class MultiClassTextClassification(AssetNode[MultiClassTextClassificationInputs, MultiClassTextClassificationOutputs]):
    """
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


class IntentClassificationInputs(Inputs):
    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class IntentClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class IntentClassification(AssetNode[IntentClassificationInputs, IntentClassificationOutputs]):
    """
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


class MultiLabelTextClassificationInputs(Inputs):
    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class MultiLabelTextClassificationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class MultiLabelTextClassification(AssetNode[MultiLabelTextClassificationInputs, MultiLabelTextClassificationOutputs]):
    """
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


class TextReconstructionInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class TextReconstructionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextReconstruction(BaseReconstructor[TextReconstructionInputs, TextReconstructionOutputs]):
    """
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


class FactCheckingInputs(Inputs):
    language: InputParam = None
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class FactCheckingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class FactChecking(AssetNode[FactCheckingInputs, FactCheckingOutputs]):
    """
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


class InverseTextNormalizationInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=False)


class InverseTextNormalizationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class InverseTextNormalization(AssetNode[InverseTextNormalizationInputs, InverseTextNormalizationOutputs]):
    """
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


class TextToAudioInputs(Inputs):
    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)


class TextToAudioOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.AUDIO)


class TextToAudio(AssetNode[TextToAudioInputs, TextToAudioOutputs]):
    """
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


class ImageCompressionInputs(Inputs):
    image: InputParam = None
    apl_qfactor: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.apl_qfactor = self.create_param(code="apl_qfactor", data_type=DataType.TEXT, is_required=False)


class ImageCompressionOutputs(Outputs):
    image: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE)


class ImageCompression(AssetNode[ImageCompressionInputs, ImageCompressionOutputs]):
    """
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


class MultilingualSpeechRecognitionInputs(Inputs):
    source_audio: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.source_audio = self.create_param(code="source_audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)


class MultilingualSpeechRecognitionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class MultilingualSpeechRecognition(AssetNode[MultilingualSpeechRecognitionInputs, MultilingualSpeechRecognitionOutputs]):
    """
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


class TextGenerationMetricDefaultInputs(Inputs):
    hypotheses: InputParam = None
    references: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.TEXT, is_required=True)
        self.references = self.create_param(code="references", data_type=DataType.TEXT, is_required=False)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class TextGenerationMetricDefaultOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextGenerationMetricDefault(BaseMetric[TextGenerationMetricDefaultInputs, TextGenerationMetricDefaultOutputs]):
    """
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


class ReferencelessTextGenerationMetricInputs(Inputs):
    hypotheses: InputParam = None
    sources: InputParam = None
    score_identifier: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.hypotheses = self.create_param(code="hypotheses", data_type=DataType.TEXT, is_required=True)
        self.sources = self.create_param(code="sources", data_type=DataType.TEXT, is_required=False)
        self.score_identifier = self.create_param(code="score_identifier", data_type=DataType.TEXT, is_required=True)


class ReferencelessTextGenerationMetricOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class ReferencelessTextGenerationMetric(
    BaseMetric[ReferencelessTextGenerationMetricInputs, ReferencelessTextGenerationMetricOutputs]
):
    """
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


class AudioEmotionDetectionInputs(Inputs):
    audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)


class AudioEmotionDetectionOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class AudioEmotionDetection(AssetNode[AudioEmotionDetectionInputs, AudioEmotionDetectionOutputs]):
    """
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


class KeywordSpottingInputs(Inputs):
    audio: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=False)


class KeywordSpottingOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class KeywordSpotting(AssetNode[KeywordSpottingInputs, KeywordSpottingOutputs]):
    """
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


class TextSummarizationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class TextSummarizationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class TextSummarization(AssetNode[TextSummarizationInputs, TextSummarizationOutputs]):
    """
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


class SplitOnLinebreakInputs(Inputs):
    text: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)


class SplitOnLinebreakOutputs(Outputs):
    data: OutputParam = None
    audio: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)


class SplitOnLinebreak(BaseSegmentor[SplitOnLinebreakInputs, SplitOnLinebreakOutputs]):
    """
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


class OtherMultipurposeInputs(Inputs):
    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)


class OtherMultipurposeOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.TEXT)


class OtherMultipurpose(AssetNode[OtherMultipurposeInputs, OtherMultipurposeOutputs]):
    """
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


class SpeakerDiarizationAudioInputs(Inputs):
    audio: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeakerDiarizationAudioOutputs(Outputs):
    data: OutputParam = None
    audio: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)


class SpeakerDiarizationAudio(BaseSegmentor[SpeakerDiarizationAudioInputs, SpeakerDiarizationAudioOutputs]):
    """
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


class ImageContentModerationInputs(Inputs):
    image: InputParam = None
    min_confidence: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.image = self.create_param(code="image", data_type=DataType.IMAGE, is_required=True)
        self.min_confidence = self.create_param(code="min_confidence", data_type=DataType.TEXT, is_required=False)


class ImageContentModerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class ImageContentModeration(AssetNode[ImageContentModerationInputs, ImageContentModerationOutputs]):
    """
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


class TextDenormalizationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None
    lowercase_latin: InputParam = None
    remove_accents: InputParam = None
    remove_punctuation: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=True)
        self.lowercase_latin = self.create_param(code="lowercase_latin", data_type=DataType.TEXT, is_required=False)
        self.remove_accents = self.create_param(code="remove_accents", data_type=DataType.TEXT, is_required=False)
        self.remove_punctuation = self.create_param(code="remove_punctuation", data_type=DataType.TEXT, is_required=False)


class TextDenormalizationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.LABEL)


class TextDenormalization(AssetNode[TextDenormalizationInputs, TextDenormalizationOutputs]):
    """
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


class SpeakerDiarizationVideoInputs(Inputs):
    video: InputParam = None
    language: InputParam = None
    script: InputParam = None
    dialect: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.video = self.create_param(code="video", data_type=DataType.VIDEO, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)
        self.script = self.create_param(code="script", data_type=DataType.LABEL, is_required=False)
        self.dialect = self.create_param(code="dialect", data_type=DataType.LABEL, is_required=False)


class SpeakerDiarizationVideoOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.VIDEO)


class SpeakerDiarizationVideo(AssetNode[SpeakerDiarizationVideoInputs, SpeakerDiarizationVideoOutputs]):
    """
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


class TextToVideoGenerationInputs(Inputs):
    text: InputParam = None
    language: InputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.text = self.create_param(code="text", data_type=DataType.TEXT, is_required=True)
        self.language = self.create_param(code="language", data_type=DataType.LABEL, is_required=False)


class TextToVideoGenerationOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node=None):
        super().__init__(node=node)
        self.data = self.create_param(code="data", data_type=DataType.VIDEO)


class TextToVideoGeneration(AssetNode[TextToVideoGenerationInputs, TextToVideoGenerationOutputs]):
    """
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


class Pipeline(DefaultPipeline):
    def object_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ObjectDetection:
        """
                Object Detection is a computer vision technology that identifies and locates
        objects within an image, typically by drawing bounding boxes around the
        detected objects and classifying them into predefined categories.
        """
        return ObjectDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextEmbedding:
        """
                Text embedding is a process that converts text into numerical vectors,
        capturing the semantic meaning and contextual relationships of words or
        phrases, enabling machines to understand and analyze natural language more
        effectively.
        """
        return TextEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def semantic_segmentation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SemanticSegmentation:
        """
                Semantic segmentation is a computer vision process that involves classifying
        each pixel in an image into a predefined category, effectively partitioning the
        image into meaningful segments based on the objects or regions they represent.
        """
        return SemanticSegmentation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_audio_generation_metric(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> ReferencelessAudioGenerationMetric:
        """
                The Referenceless Audio Generation Metric is a tool designed to evaluate the
        quality of generated audio content without the need for a reference or original
        audio sample for comparison.
        """
        return ReferencelessAudioGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def script_execution(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ScriptExecution:
        """
                Script Execution refers to the process of running a set of programmed
        instructions or code within a computing environment, enabling the automated
        performance of tasks, calculations, or operations as defined by the script.
        """
        return ScriptExecution(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_impainting(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageImpainting:
        """
                Image inpainting is a process that involves filling in missing or damaged parts
        of an image in a way that is visually coherent and seamlessly blends with the
        surrounding areas, often using advanced algorithms and techniques to restore
        the image to its original or intended appearance.
        """
        return ImageImpainting(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageEmbedding:
        """
                Image Embedding is a process that transforms an image into a fixed-dimensional
        vector representation, capturing its essential features and enabling efficient
        comparison, retrieval, and analysis in various machine learning and computer
        vision tasks.
        """
        return ImageEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def metric_aggregation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> MetricAggregation:
        """
                Metric Aggregation is a function that computes and summarizes numerical data by
        applying statistical operations, such as averaging, summing, or finding the
        minimum and maximum values, to provide insights and facilitate analysis of
        large datasets.
        """
        return MetricAggregation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechTranslation:
        """
                Speech Translation is a technology that converts spoken language in real-time
        from one language to another, enabling seamless communication between speakers
        of different languages.
        """
        return SpeechTranslation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def depth_estimation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DepthEstimation:
        """
                Depth estimation is a computational process that determines the distance of
        objects from a viewpoint, typically using visual data from cameras or sensors
        to create a three-dimensional understanding of a scene.
        """
        return DepthEstimation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def noise_removal(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> NoiseRemoval:
        """
                Noise Removal is a process that involves identifying and eliminating unwanted
        random variations or disturbances from an audio signal to enhance the clarity
        and quality of the underlying information.
        """
        return NoiseRemoval(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def diacritization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Diacritization:
        """
                Adds diacritical marks to text, essential for languages where meaning can
        change based on diacritics.
        """
        return Diacritization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_transcript_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioTranscriptAnalysis:
        """
                Analyzes transcribed audio data for insights, patterns, or specific information
        extraction.
        """
        return AudioTranscriptAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def extract_audio_from_video(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ExtractAudioFromVideo:
        """
                Isolates and extracts audio tracks from video files, aiding in audio analysis
        or transcription tasks.
        """
        return ExtractAudioFromVideo(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_reconstruction(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioReconstruction:
        """
                Audio Reconstruction is the process of restoring or recreating audio signals
        from incomplete, damaged, or degraded recordings to achieve a high-quality,
        accurate representation of the original sound.
        """
        return AudioReconstruction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def classification_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ClassificationMetric:
        """
                A Classification Metric is a quantitative measure used to evaluate the quality
        and effectiveness of classification models.
        """
        return ClassificationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextGenerationMetric:
        """
                A Text Generation Metric is a quantitative measure used to evaluate the quality
        and effectiveness of text produced by natural language processing models, often
        assessing aspects such as coherence, relevance, fluency, and adherence to given
        prompts or instructions.
        """
        return TextGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_spam_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSpamDetection:
        """
                Identifies and filters out unwanted or irrelevant text content, ideal for
        moderating user-generated content or ensuring quality in communication
        platforms.
        """
        return TextSpamDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_to_image_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextToImageGeneration:
        """
                Creates a visual representation based on textual input, turning descriptions
        into pictorial forms. Used in creative processes and content generation.
        """
        return TextToImageGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def voice_cloning(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VoiceCloning:
        """
                Replicates a person's voice based on a sample, allowing for the generation of
        speech in that person's tone and style. Used cautiously due to ethical
        considerations.
        """
        return VoiceCloning(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_segmenation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSegmenation:
        """
                Text Segmentation is the process of dividing a continuous text into meaningful
        units, such as words, sentences, or topics, to facilitate easier analysis and
        understanding.
        """
        return TextSegmenation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def benchmark_scoring_mt(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> BenchmarkScoringMt:
        """
                Benchmark Scoring MT is a function designed to evaluate and score machine
        translation systems by comparing their output against a set of predefined
        benchmarks, thereby assessing their accuracy and performance.
        """
        return BenchmarkScoringMt(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_manipulation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageManipulation:
        """
                Image Manipulation refers to the process of altering or enhancing digital
        images using various techniques and tools to achieve desired visual effects,
        correct imperfections, or transform the image's appearance.
        """
        return ImageManipulation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def named_entity_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> NamedEntityRecognition:
        """
                Identifies and classifies named entities (e.g., persons, organizations,
        locations) within text. Useful for information extraction, content tagging, and
        search enhancements.
        """
        return NamedEntityRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def offensive_language_identification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> OffensiveLanguageIdentification:
        """
                Detects language or phrases that might be considered offensive, aiding in
        content moderation and creating respectful user interactions.
        """
        return OffensiveLanguageIdentification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def search(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Search:
        """
                An algorithm that identifies and returns data or items that match particular
        keywords or conditions from a dataset. A fundamental tool for databases and
        websites.
        """
        return Search(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def sentiment_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SentimentAnalysis:
        """
                Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
        piece of text, aiding in understanding user feedback or market sentiment.
        """
        return SentimentAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_colorization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageColorization:
        """
                Image colorization is a process that involves adding color to grayscale images,
        transforming them from black-and-white to full-color representations, often
        using advanced algorithms and machine learning techniques to predict and apply
        the appropriate hues and shades.
        """
        return ImageColorization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechClassification:
        """
                Categorizes audio clips based on their content, aiding in content organization
        and targeted actions.
        """
        return SpeechClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def dialect_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DialectDetection:
        """
                Identifies specific dialects within a language, aiding in localized content
        creation or user experience personalization.
        """
        return DialectDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_label_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoLabelDetection:
        """
                Identifies and tags objects, scenes, or activities within a video. Useful for
        content indexing and recommendation systems.
        """
        return VideoLabelDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_synthesis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechSynthesis:
        """
                Generates human-like speech from written text. Ideal for text-to-speech
        applications, audiobooks, and voice assistants.
        """
        return SpeechSynthesis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def split_on_silence(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SplitOnSilence:
        """
                The "Split On Silence" function divides an audio recording into separate
        segments based on periods of silence, allowing for easier editing and analysis
        of individual sections.
        """
        return SplitOnSilence(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def expression_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ExpressionDetection:
        """
                Expression Detection is the process of identifying and analyzing facial
        expressions to interpret emotions or intentions using AI and computer vision
        techniques.
        """
        return ExpressionDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def auto_mask_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AutoMaskGeneration:
        """
                Auto-mask generation refers to the automated process of creating masks in image
        processing or computer vision, typically for segmentation tasks. A mask is a
        binary or multi-class image that labels different parts of an image, usually
        separating the foreground (objects of interest) from the background, or
        identifying specific object classes in an image.
        """
        return AutoMaskGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def document_image_parsing(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DocumentImageParsing:
        """
                Document Image Parsing is the process of analyzing and converting scanned or
        photographed images of documents into structured, machine-readable formats by
        identifying and extracting text, layout, and other relevant information.
        """
        return DocumentImageParsing(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def entity_linking(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> EntityLinking:
        """
                Associates identified entities in the text with specific entries in a knowledge
        base or database.
        """
        return EntityLinking(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_text_generation_metric_default(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> ReferencelessTextGenerationMetricDefault:
        """
                The Referenceless Text Generation Metric Default is a function designed to
        evaluate the quality of generated text without relying on reference texts for
        comparison.
        """
        return ReferencelessTextGenerationMetricDefault(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def fill_text_mask(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> FillTextMask:
        """
                Completes missing parts of a text based on the context, ideal for content
        generation or data augmentation tasks.
        """
        return FillTextMask(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def subtitling_translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SubtitlingTranslation:
        """
                Converts the text of subtitles from one language to another, ensuring context
        and cultural nuances are maintained. Essential for global content distribution.
        """
        return SubtitlingTranslation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def instance_segmentation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> InstanceSegmentation:
        """
                Instance segmentation is a computer vision task that involves detecting and
        delineating each distinct object within an image, assigning a unique label and
        precise boundary to every individual instance of objects, even if they belong
        to the same category.
        """
        return InstanceSegmentation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def viseme_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VisemeGeneration:
        """
                Viseme Generation is the process of creating visual representations of
        phonemes, which are the distinct units of sound in speech, to synchronize lip
        movements with spoken words in animations or virtual avatars.
        """
        return VisemeGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_generation_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioGenerationMetric:
        """
                The Audio Generation Metric is a quantitative measure used to evaluate the
        quality, accuracy, and overall performance of audio generated by artificial
        intelligence systems, often considering factors such as fidelity,
        intelligibility, and similarity to human-produced audio.
        """
        return AudioGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_understanding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoUnderstanding:
        """
                Video Understanding is the process of analyzing and interpreting video content
        to extract meaningful information, such as identifying objects, actions,
        events, and contextual relationships within the footage.
        """
        return VideoUnderstanding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_normalization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextNormalization:
        """
                Converts unstructured or non-standard textual data into a more readable and
        uniform format, dealing with abbreviations, numerals, and other non-standard
        words.
        """
        return TextNormalization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def asr_quality_estimation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrQualityEstimation:
        """
                ASR Quality Estimation is a process that evaluates the accuracy and reliability
        of automatic speech recognition systems by analyzing their performance in
        transcribing spoken language into text.
        """
        return AsrQualityEstimation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def voice_activity_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VoiceActivityDetection:
        """
                Determines when a person is speaking in an audio clip. It's an essential
        preprocessing step for other audio-related tasks.
        """
        return VoiceActivityDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_non_speech_classification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> SpeechNonSpeechClassification:
        """
                Differentiates between speech and non-speech audio segments. Great for editing
        software and transcription services to exclude irrelevant audio.
        """
        return SpeechNonSpeechClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_transcript_improvement(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioTranscriptImprovement:
        """
                Refines and corrects transcriptions generated from audio data, improving
        readability and accuracy.
        """
        return AudioTranscriptImprovement(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextContentModeration:
        """
                Scans and identifies potentially harmful, offensive, or inappropriate textual
        content, ensuring safer user environments.
        """
        return TextContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def emotion_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> EmotionDetection:
        """
                Identifies human emotions from text or audio, enhancing user experience in
        chatbots or customer feedback analysis.
        """
        return EmotionDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_forced_alignment(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioForcedAlignment:
        """
                Synchronizes phonetic and phonological text with the corresponding segments in
        an audio file. Useful in linguistic research and detailed transcription tasks.
        """
        return AudioForcedAlignment(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoContentModeration:
        """
                Automatically reviews video content to detect and possibly remove inappropriate
        or harmful material. Essential for user-generated content platforms.
        """
        return VideoContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_label_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageLabelDetection:
        """
                Identifies objects, themes, or topics within images, useful for image
        categorization, search, and recommendation systems.
        """
        return ImageLabelDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_forced_alignment(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoForcedAlignment:
        """
                Aligns the transcription of spoken content in a video with its corresponding
        timecodes, facilitating subtitle creation.
        """
        return VideoForcedAlignment(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextGeneration:
        """
                Creates coherent and contextually relevant textual content based on prompts or
        certain parameters. Useful for chatbots, content creation, and data
        augmentation.
        """
        return TextGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextClassification:
        """
                Categorizes text into predefined groups or topics, facilitating content
        organization and targeted actions.
        """
        return TextClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechEmbedding:
        """
                Transforms spoken content into a fixed-size vector in a high-dimensional space
        that captures the content's essence. Facilitates tasks like speech recognition
        and speaker verification.
        """
        return SpeechEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def topic_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TopicClassification:
        """
                Assigns categories or topics to a piece of text based on its content,
        facilitating content organization and retrieval.
        """
        return TopicClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Translation:
        """
                Converts text from one language to another while maintaining the original
        message's essence and context. Crucial for global communication.
        """
        return Translation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechRecognition:
        """
                Converts spoken language into written text. Useful for transcription services,
        voice assistants, and applications requiring voice-to-text capabilities.
        """
        return SpeechRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def subtitling(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Subtitling:
        """
                Generates accurate subtitles for videos, enhancing accessibility for diverse
        audiences.
        """
        return Subtitling(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_captioning(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageCaptioning:
        """
                Image Captioning is a process that involves generating a textual description of
        an image, typically using machine learning models to analyze the visual content
        and produce coherent and contextually relevant sentences that describe the
        objects, actions, and scenes depicted in the image.
        """
        return ImageCaptioning(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_language_identification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioLanguageIdentification:
        """
                Audio Language Identification is a process that involves analyzing an audio
        recording to determine the language being spoken.
        """
        return AudioLanguageIdentification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoEmbedding:
        """
                Video Embedding is a process that transforms video content into a fixed-
        dimensional vector representation, capturing essential features and patterns to
        facilitate tasks such as retrieval, classification, and recommendation.
        """
        return VideoEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def asr_age_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrAgeClassification:
        """
                The ASR Age Classification function is designed to analyze audio recordings of
        speech to determine the speaker's age group by leveraging automatic speech
        recognition (ASR) technology and machine learning algorithms.
        """
        return AsrAgeClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_intent_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioIntentDetection:
        """
                Audio Intent Detection is a process that involves analyzing audio signals to
        identify and interpret the underlying intentions or purposes behind spoken
        words, enabling systems to understand and respond appropriately to human
        speech.
        """
        return AudioIntentDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def language_identification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> LanguageIdentification:
        """
                Detects the language in which a given text is written, aiding in multilingual
        platforms or content localization.
        """
        return LanguageIdentification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def ocr(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Ocr:
        """
                Converts images of typed, handwritten, or printed text into machine-encoded
        text. Used in digitizing printed texts for data retrieval.
        """
        return Ocr(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def asr_gender_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrGenderClassification:
        """
                The ASR Gender Classification function analyzes audio recordings to determine
        and classify the speaker's gender based on their voice characteristics.
        """
        return AsrGenderClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def language_identification_audio(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> LanguageIdentificationAudio:
        """
                The Language Identification Audio function analyzes audio input to determine
        and identify the language being spoken.
        """
        return LanguageIdentificationAudio(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def base_model(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> BaseModel:
        """
                The Base-Model function serves as a foundational framework designed to provide
        essential features and capabilities upon which more specialized or advanced
        models can be built and customized.
        """
        return BaseModel(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def loglikelihood(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Loglikelihood:
        """
                The Log Likelihood function measures the probability of observing the given
        data under a specific statistical model by taking the natural logarithm of the
        likelihood function, thereby transforming the product of probabilities into a
        sum, which simplifies the process of optimization and parameter estimation.
        """
        return Loglikelihood(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_to_video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageToVideoGeneration:
        """
                The Image To Video Generation function transforms a series of static images
        into a cohesive, dynamic video sequence, often incorporating transitions,
        effects, and synchronization with audio to create a visually engaging
        narrative.
        """
        return ImageToVideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def part_of_speech_tagging(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> PartOfSpeechTagging:
        """
                Part of Speech Tagging is a natural language processing task that involves
        assigning each word in a sentence its corresponding part of speech, such as
        noun, verb, adjective, or adverb, based on its role and context within the
        sentence.
        """
        return PartOfSpeechTagging(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def benchmark_scoring_asr(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> BenchmarkScoringAsr:
        """
                Benchmark Scoring ASR is a function that evaluates and compares the performance
        of automatic speech recognition systems by analyzing their accuracy, speed, and
        other relevant metrics against a standardized set of benchmarks.
        """
        return BenchmarkScoringAsr(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def visual_question_answering(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VisualQuestionAnswering:
        """
                Visual Question Answering (VQA) is a task in artificial intelligence that
        involves analyzing an image and providing accurate, contextually relevant
        answers to questions posed about the visual content of that image.
        """
        return VisualQuestionAnswering(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def document_information_extraction(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> DocumentInformationExtraction:
        """
                Document Information Extraction is the process of automatically identifying,
        extracting, and structuring relevant data from unstructured or semi-structured
        documents, such as invoices, receipts, contracts, and forms, to facilitate
        easier data management and analysis.
        """
        return DocumentInformationExtraction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoGeneration:
        """
                Produces video content based on specific inputs or datasets. Can be used for
        simulations, animations, or even deepfake detection.
        """
        return VideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_class_image_classification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> MultiClassImageClassification:
        """
                Multi Class Image Classification is a machine learning task where an algorithm
        is trained to categorize images into one of several predefined classes or
        categories based on their visual content.
        """
        return MultiClassImageClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def style_transfer(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> StyleTransfer:
        """
                Style Transfer is a technique in artificial intelligence that applies the
        visual style of one image (such as the brushstrokes of a famous painting) to
        the content of another image, effectively blending the artistic elements of the
        first image with the subject matter of the second.
        """
        return StyleTransfer(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_class_text_classification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> MultiClassTextClassification:
        """
                Multi Class Text Classification is a natural language processing task that
        involves categorizing a given text into one of several predefined classes or
        categories based on its content.
        """
        return MultiClassTextClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def intent_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> IntentClassification:
        """
                Intent Classification is a natural language processing task that involves
        analyzing and categorizing user text input to determine the underlying purpose
        or goal behind the communication, such as booking a flight, asking for weather
        information, or setting a reminder.
        """
        return IntentClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_label_text_classification(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> MultiLabelTextClassification:
        """
                Multi Label Text Classification is a natural language processing task where a
        given text is analyzed and assigned multiple relevant labels or categories from
        a predefined set, allowing for the text to belong to more than one category
        simultaneously.
        """
        return MultiLabelTextClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_reconstruction(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextReconstruction:
        """
                Text Reconstruction is a process that involves piecing together fragmented or
        incomplete text data to restore it to its original, coherent form.
        """
        return TextReconstruction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def fact_checking(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> FactChecking:
        """
                Fact Checking is the process of verifying the accuracy and truthfulness of
        information, statements, or claims by cross-referencing with reliable sources
        and evidence.
        """
        return FactChecking(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def inverse_text_normalization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> InverseTextNormalization:
        """
                Inverse Text Normalization is the process of converting spoken or written
        language in its normalized form, such as numbers, dates, and abbreviations,
        back into their original, more complex or detailed textual representations.
        """
        return InverseTextNormalization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_to_audio(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextToAudio:
        """
                The Text to Audio function converts written text into spoken words, allowing
        users to listen to the content instead of reading it.
        """
        return TextToAudio(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_compression(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageCompression:
        """
                Reduces the size of image files without significantly compromising their visual
        quality. Useful for optimizing storage and improving webpage load times.
        """
        return ImageCompression(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multilingual_speech_recognition(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> MultilingualSpeechRecognition:
        """
                Multilingual Speech Recognition is a technology that enables the automatic
        transcription of spoken language into text across multiple languages, allowing
        for seamless communication and understanding in diverse linguistic contexts.
        """
        return MultilingualSpeechRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation_metric_default(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextGenerationMetricDefault:
        """
                The "Text Generation Metric Default" function provides a standard set of
        evaluation metrics for assessing the quality and performance of text generation
        models.
        """
        return TextGenerationMetricDefault(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_text_generation_metric(
        self, asset_id: Union[str, asset.Asset], *args, **kwargs
    ) -> ReferencelessTextGenerationMetric:
        """
                The Referenceless Text Generation Metric is a method for evaluating the quality
        of generated text without requiring a reference text for comparison, often
        leveraging models or algorithms to assess coherence, relevance, and fluency
        based on intrinsic properties of the text itself.
        """
        return ReferencelessTextGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_emotion_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioEmotionDetection:
        """
                Audio Emotion Detection is a technology that analyzes vocal characteristics and
        patterns in audio recordings to identify and classify the emotional state of
        the speaker.
        """
        return AudioEmotionDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def keyword_spotting(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> KeywordSpotting:
        """
                Keyword Spotting is a function that enables the detection and identification of
        specific words or phrases within a stream of audio, often used in voice-
        activated systems to trigger actions or commands based on recognized keywords.
        """
        return KeywordSpotting(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_summarization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSummarization:
        """
                Extracts the main points from a larger body of text, producing a concise
        summary without losing the primary message.
        """
        return TextSummarization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def split_on_linebreak(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SplitOnLinebreak:
        """
                The "Split On Linebreak" function divides a given string into a list of
        substrings, using linebreaks (newline characters) as the points of separation.
        """
        return SplitOnLinebreak(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def other__multipurpose_(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> OtherMultipurpose:
        """
                The "Other (Multipurpose)" function serves as a versatile category designed to
        accommodate a wide range of tasks and activities that do not fit neatly into
        predefined classifications, offering flexibility and adaptability for various
        needs.
        """
        return OtherMultipurpose(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speaker_diarization_audio(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeakerDiarizationAudio:
        """
                Identifies individual speakers and their respective speech segments within an
        audio clip. Ideal for multi-speaker recordings or conference calls.
        """
        return SpeakerDiarizationAudio(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageContentModeration:
        """
                Detects and filters out inappropriate or harmful images, essential for
        platforms with user-generated visual content.
        """
        return ImageContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_denormalization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextDenormalization:
        """
                Converts standardized or normalized text into its original, often more
        readable, form. Useful in natural language generation tasks.
        """
        return TextDenormalization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speaker_diarization_video(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeakerDiarizationVideo:
        """
                Segments a video based on different speakers, identifying when each individual
        speaks. Useful for transcriptions and understanding multi-person conversations.
        """
        return SpeakerDiarizationVideo(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_to_video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextToVideoGeneration:
        """
                Text To Video Generation is a process that converts written descriptions or
        scripts into dynamic, visual video content using advanced algorithms and
        artificial intelligence.
        """
        return TextToVideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)
