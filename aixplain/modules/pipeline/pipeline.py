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
    BaseMetric
)
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
    Language Identification is the process of automatically determining the
language in which a given piece of text is written.

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
    OCR, or Optical Character Recognition, is a technology that converts different
types of documents, such as scanned paper documents, PDFs, or images captured
by a digital camera, into editable and searchable data by recognizing and
extracting text from the images.

    InputType: image
    OutputType: text
    """
    function: str = "ocr"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = OcrInputs
    outputs_class: Type[TO] = OcrOutputs


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
    Image Label Detection is a function that automatically identifies and assigns
descriptive tags or labels to objects, scenes, or elements within an image,
enabling easier categorization, search, and analysis of visual content.

    InputType: image
    OutputType: label
    """
    function: str = "image-label-detection"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = ImageLabelDetectionInputs
    outputs_class: Type[TO] = ImageLabelDetectionOutputs


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
    Audio Forced Alignment is a process that synchronizes a given audio recording
with its corresponding transcript by precisely aligning each spoken word or
phoneme to its exact timing within the audio.

    InputType: audio
    OutputType: audio
    """
    function: str = "audio-forced-alignment"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = AudioForcedAlignmentInputs
    outputs_class: Type[TO] = AudioForcedAlignmentOutputs


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
    Video Generation is the process of creating video content through automated or
semi-automated means, often utilizing algorithms, artificial intelligence, or
software tools to produce visual and audio elements that can range from simple
animations to complex, realistic scenes.

    InputType: text
    OutputType: video
    """
    function: str = "video-generation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.VIDEO

    inputs_class: Type[TI] = VideoGenerationInputs
    outputs_class: Type[TO] = VideoGenerationOutputs


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


class ReferencelessAudioGenerationMetric(BaseMetric[ReferencelessAudioGenerationMetricInputs, ReferencelessAudioGenerationMetricOutputs]):
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
    Speech Classification is a process that involves analyzing and categorizing
spoken language into predefined categories or classes based on various features
such as tone, pitch, and linguistic content.

    InputType: audio
    OutputType: label
    """
    function: str = "speech-classification"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeechClassificationInputs
    outputs_class: Type[TO] = SpeechClassificationOutputs


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
    Dialect Detection is a function that identifies and classifies the specific
regional or social variations of a language spoken or written by an individual,
enabling the recognition of distinct linguistic patterns and nuances associated
with different dialects.

    InputType: audio
    OutputType: text
    """
    function: str = "dialect-detection"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = DialectDetectionInputs
    outputs_class: Type[TO] = DialectDetectionOutputs


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
    The "Fill Text Mask" function takes a text input with masked or placeholder
characters and replaces those placeholders with specified or contextually
appropriate characters to generate a complete and coherent text output.

    InputType: text
    OutputType: text
    """
    function: str = "fill-text-mask"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = FillTextMaskInputs
    outputs_class: Type[TO] = FillTextMaskOutputs


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
    Video Content Moderation is the process of reviewing, analyzing, and filtering
video content to ensure it adheres to community guidelines, legal standards,
and platform policies, thereby preventing the dissemination of inappropriate,
harmful, or illegal material.

    InputType: video
    OutputType: label
    """
    function: str = "video-content-moderation"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = VideoContentModerationInputs
    outputs_class: Type[TO] = VideoContentModerationOutputs


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
    The "Extract Audio From Video" function allows users to separate and save the
audio track from a video file, enabling them to obtain just the sound without
the accompanying visual content.

    InputType: video
    OutputType: audio
    """
    function: str = "extract-audio-from-video"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = ExtractAudioFromVideoInputs
    outputs_class: Type[TO] = ExtractAudioFromVideoOutputs


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
    Image compression is a process that reduces the file size of an image by
removing redundant or non-essential data, while maintaining an acceptable level
of visual quality.

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


class ReferencelessTextGenerationMetric(BaseMetric[ReferencelessTextGenerationMetricInputs, ReferencelessTextGenerationMetricOutputs]):
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
    Voice cloning is a technology that uses artificial intelligence to create a
digital replica of a person's voice, allowing for the generation of speech that
mimics the tone, pitch, and speaking style of the original speaker.

    InputType: text
    OutputType: audio
    """
    function: str = "voice-cloning"
    input_type: str = DataType.TEXT
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = VoiceCloningInputs
    outputs_class: Type[TO] = VoiceCloningOutputs


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
    Diacritization is the process of adding diacritical marks to letters in a text
to indicate pronunciation, stress, tone, or meaning, often used in languages
such as Arabic, Hebrew, and Vietnamese to provide clarity and accuracy in
written communication.

    InputType: text
    OutputType: text
    """
    function: str = "diacritization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = DiacritizationInputs
    outputs_class: Type[TO] = DiacritizationOutputs


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
    Text summarization is the process of condensing a large body of text into a
shorter version, capturing the main points and essential information while
maintaining coherence and meaning.

    InputType: text
    OutputType: text
    """
    function: str = "text-summarization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextSummarizationInputs
    outputs_class: Type[TO] = TextSummarizationOutputs


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
    Entity Linking is the process of identifying and connecting mentions of
entities within a text to their corresponding entries in a structured knowledge
base, thereby enabling the disambiguation of terms and enhancing the
understanding of the text's context.

    InputType: text
    OutputType: label
    """
    function: str = "entity-linking"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = EntityLinkingInputs
    outputs_class: Type[TO] = EntityLinkingOutputs


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
    Sentiment Analysis is a natural language processing technique used to determine
and classify the emotional tone or subjective information expressed in a piece
of text, such as identifying whether the sentiment is positive, negative, or
neutral.

    InputType: text
    OutputType: label
    """
    function: str = "sentiment-analysis"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SentimentAnalysisInputs
    outputs_class: Type[TO] = SentimentAnalysisOutputs


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
    Text Classification is a natural language processing task that involves
categorizing text into predefined labels or classes based on its content,
enabling automated organization, filtering, and analysis of large volumes of
textual data.

    InputType: text
    OutputType: label
    """
    function: str = "text-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextClassificationInputs
    outputs_class: Type[TO] = TextClassificationOutputs


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
    Speech synthesis is the artificial production of human speech, typically
achieved through software or hardware systems that convert text into spoken
words, enabling machines to communicate verbally with users.

    InputType: text
    OutputType: audio
    """
    function: str = "speech-synthesis"
    input_type: str = DataType.TEXT
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = SpeechSynthesisInputs
    outputs_class: Type[TO] = SpeechSynthesisOutputs


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
    Video Label Detection is a function that automatically identifies and tags
various objects, scenes, activities, and other relevant elements within a
video, providing descriptive labels that enhance searchability and content
organization.

    InputType: video
    OutputType: label
    """
    function: str = "video-label-detection"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = VideoLabelDetectionInputs
    outputs_class: Type[TO] = VideoLabelDetectionOutputs


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
    Audio Transcript Analysis is a process that involves converting spoken language
from audio recordings into written text, followed by examining and interpreting
the transcribed content to extract meaningful insights, identify patterns, and
derive actionable information.

    InputType: audio
    OutputType: text
    """
    function: str = "audio-transcript-analysis"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = AudioTranscriptAnalysisInputs
    outputs_class: Type[TO] = AudioTranscriptAnalysisOutputs


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
    The "Search" function allows users to input keywords or phrases to quickly
locate specific information, files, or content within a database, website, or
application.

    InputType: text
    OutputType: text
    """
    function: str = "search"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SearchInputs
    outputs_class: Type[TO] = SearchOutputs


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
    Video Forced Alignment is a process that synchronizes video footage with
corresponding audio tracks by precisely aligning the visual and auditory
elements, ensuring that the movements of speakers' lips match the spoken words.

    InputType: video
    OutputType: video
    """
    function: str = "video-forced-alignment"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.VIDEO

    inputs_class: Type[TI] = VideoForcedAlignmentInputs
    outputs_class: Type[TO] = VideoForcedAlignmentOutputs


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
    Topic Classification is a natural language processing function that categorizes
text into predefined topics or subjects based on its content, enabling
efficient organization and retrieval of information.

    InputType: text
    OutputType: label
    """
    function: str = "topic-classification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TopicClassificationInputs
    outputs_class: Type[TO] = TopicClassificationOutputs


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
    Offensive Language Identification is a function that analyzes text to detect
and flag language that is abusive, harmful, or inappropriate, helping to
maintain a respectful and safe communication environment.

    InputType: text
    OutputType: label
    """
    function: str = "offensive-language-identification"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = OffensiveLanguageIdentificationInputs
    outputs_class: Type[TO] = OffensiveLanguageIdentificationOutputs


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
    Speaker Diarization Audio is a process that involves segmenting an audio
recording into distinct sections, each corresponding to a different speaker, in
order to identify and differentiate between multiple speakers within the same
audio stream.

    InputType: audio
    OutputType: label
    """
    function: str = "speaker-diarization-audio"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeakerDiarizationAudioInputs
    outputs_class: Type[TO] = SpeakerDiarizationAudioOutputs


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
    Audio Transcript Improvement is a function that enhances the accuracy and
clarity of transcribed audio recordings by correcting errors, refining
language, and ensuring the text faithfully represents the original spoken
content.

    InputType: audio
    OutputType: text
    """
    function: str = "audio-transcript-improvement"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = AudioTranscriptImprovementInputs
    outputs_class: Type[TO] = AudioTranscriptImprovementOutputs


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
    The function "Speech or Non-Speech Classification" is designed to analyze audio
input and determine whether the sound is human speech or non-speech noise,
enabling applications such as voice recognition systems to filter out
irrelevant background sounds.

    InputType: audio
    OutputType: label
    """
    function: str = "speech-non-speech-classification"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeechNonSpeechClassificationInputs
    outputs_class: Type[TO] = SpeechNonSpeechClassificationOutputs


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
    Text Denormalization is the process of converting abbreviated, contracted, or
otherwise simplified text into its full, standard form, often to improve
readability and ensure consistency in natural language processing tasks.

    InputType: text
    OutputType: label
    """
    function: str = "text-denormalization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextDenormalizationInputs
    outputs_class: Type[TO] = TextDenormalizationOutputs


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
    Image Content Moderation is a process that involves analyzing and filtering
images to detect and manage inappropriate, harmful, or sensitive content,
ensuring compliance with community guidelines and legal standards.

    InputType: image
    OutputType: label
    """
    function: str = "image-content-moderation"
    input_type: str = DataType.IMAGE
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = ImageContentModerationInputs
    outputs_class: Type[TO] = ImageContentModerationOutputs


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


class ReferencelessTextGenerationMetricDefault(BaseMetric[ReferencelessTextGenerationMetricDefaultInputs, ReferencelessTextGenerationMetricDefaultOutputs]):
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
    Named Entity Recognition (NER) is a natural language processing task that
involves identifying and classifying proper nouns in text into predefined
categories such as names of people, organizations, locations, dates, and other
entities.

    InputType: text
    OutputType: label
    """
    function: str = "named-entity-recognition"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = NamedEntityRecognitionInputs
    outputs_class: Type[TO] = NamedEntityRecognitionOutputs


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
    Text Content Moderation is the process of reviewing, filtering, and managing
user-generated content to ensure it adheres to community guidelines, legal
standards, and platform policies, thereby maintaining a safe and respectful
online environment.

    InputType: text
    OutputType: label
    """
    function: str = "text-content-moderation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextContentModerationInputs
    outputs_class: Type[TO] = TextContentModerationOutputs


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
    The Speaker Diarization Video function identifies and segments different
speakers in a video, attributing portions of the audio to individual speakers
to facilitate analysis and understanding of multi-speaker conversations.

    InputType: video
    OutputType: label
    """
    function: str = "speaker-diarization-video"
    input_type: str = DataType.VIDEO
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = SpeakerDiarizationVideoInputs
    outputs_class: Type[TO] = SpeakerDiarizationVideoOutputs


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
    Emotion Detection is a process that involves analyzing text to identify and
categorize the emotional states or sentiments expressed by individuals, such as
happiness, sadness, anger, or fear.

    InputType: text
    OutputType: label
    """
    function: str = "emotion-detection"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = EmotionDetectionInputs
    outputs_class: Type[TO] = EmotionDetectionOutputs


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
    Text Spam Detection is a process that involves analyzing and identifying
unsolicited or irrelevant messages within text communications, typically using
algorithms and machine learning techniques to filter out spam and ensure the
integrity of the communication platform.

    InputType: text
    OutputType: label
    """
    function: str = "text-spam-detection"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextSpamDetectionInputs
    outputs_class: Type[TO] = TextSpamDetectionOutputs


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
    Translation is the process of converting text from one language into an
equivalent text in another language, preserving the original meaning and
context.

    InputType: text
    OutputType: text
    """
    function: str = "translation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TranslationInputs
    outputs_class: Type[TO] = TranslationOutputs


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
    Voice Activity Detection (VAD) is a technology that identifies the presence or
absence of human speech within an audio signal, enabling systems to distinguish
between spoken words and background noise.

    InputType: audio
    OutputType: audio
    """
    function: str = "voice-activity-detection"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.AUDIO

    inputs_class: Type[TI] = VoiceActivityDetectionInputs
    outputs_class: Type[TO] = VoiceActivityDetectionOutputs


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
    Speech Embedding is a process that transforms spoken language into a fixed-
dimensional vector representation, capturing essential features and
characteristics of the speech for tasks such as recognition, classification,
and analysis.

    InputType: audio
    OutputType: text
    """
    function: str = "speech-embedding"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SpeechEmbeddingInputs
    outputs_class: Type[TO] = SpeechEmbeddingOutputs


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
    Subtitling Translation is the process of converting spoken dialogue from one
language into written text in another language, which is then displayed on-
screen to aid viewers in understanding the content.

    InputType: text
    OutputType: text
    """
    function: str = "subtitling-translation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SubtitlingTranslationInputs
    outputs_class: Type[TO] = SubtitlingTranslationOutputs


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
    Text Generation is a process in which artificial intelligence models, such as
neural networks, produce coherent and contextually relevant text based on a
given input or prompt, often mimicking human writing styles and patterns.

    InputType: text
    OutputType: text
    """
    function: str = "text-generation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = TextGenerationInputs
    outputs_class: Type[TO] = TextGenerationOutputs


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
    Text normalization is the process of transforming text into a standard,
consistent format by correcting spelling errors, converting all characters to a
uniform case, removing punctuation, and expanding abbreviations to improve the
text's readability and usability for further processing or analysis.

    InputType: text
    OutputType: label
    """
    function: str = "text-normalization"
    input_type: str = DataType.TEXT
    output_type: str = DataType.LABEL

    inputs_class: Type[TI] = TextNormalizationInputs
    outputs_class: Type[TO] = TextNormalizationOutputs


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
    Speech recognition is a technology that enables a computer or device to
identify and process spoken language, converting it into text.

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
    Subtitling is the process of displaying written text on a screen to represent
the spoken dialogue, narration, or other audio elements in a video, typically
to aid viewers who are deaf or hard of hearing, or to provide translations for
audiences who speak different languages.

    InputType: audio
    OutputType: text
    """
    function: str = "subtitling"
    input_type: str = DataType.AUDIO
    output_type: str = DataType.TEXT

    inputs_class: Type[TI] = SubtitlingInputs
    outputs_class: Type[TO] = SubtitlingOutputs


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
    Text To Image Generation is a process where a system creates visual images
based on descriptive text input, translating written language into
corresponding graphical representations.

    InputType: text
    OutputType: image
    """
    function: str = "text-to-image-generation"
    input_type: str = DataType.TEXT
    output_type: str = DataType.IMAGE

    inputs_class: Type[TI] = TextToImageGenerationInputs
    outputs_class: Type[TO] = TextToImageGenerationOutputs



class Pipeline(DefaultPipeline):

    def object_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ObjectDetection:
        """
        Object Detection is a computer vision technology that identifies and locates
objects within an image, typically by drawing bounding boxes around the
detected objects and classifying them into predefined categories.
        """
        return ObjectDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def language_identification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> LanguageIdentification:
        """
        Language Identification is the process of automatically determining the
language in which a given piece of text is written.
        """
        return LanguageIdentification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def ocr(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Ocr:
        """
        OCR, or Optical Character Recognition, is a technology that converts different
types of documents, such as scanned paper documents, PDFs, or images captured
by a digital camera, into editable and searchable data by recognizing and
extracting text from the images.
        """
        return Ocr(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def script_execution(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ScriptExecution:
        """
        Script Execution refers to the process of running a set of programmed
instructions or code within a computing environment, enabling the automated
performance of tasks, calculations, or operations as defined by the script.
        """
        return ScriptExecution(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_label_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageLabelDetection:
        """
        Image Label Detection is a function that automatically identifies and assigns
descriptive tags or labels to objects, scenes, or elements within an image,
enabling easier categorization, search, and analysis of visual content.
        """
        return ImageLabelDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

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

    def asr_age_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrAgeClassification:
        """
        The ASR Age Classification function is designed to analyze audio recordings of
speech to determine the speaker's age group by leveraging automatic speech
recognition (ASR) technology and machine learning algorithms.
        """
        return AsrAgeClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def benchmark_scoring_mt(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> BenchmarkScoringMt:
        """
        Benchmark Scoring MT is a function designed to evaluate and score machine
translation systems by comparing their output against a set of predefined
benchmarks, thereby assessing their accuracy and performance.
        """
        return BenchmarkScoringMt(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def asr_gender_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrGenderClassification:
        """
        The ASR Gender Classification function analyzes audio recordings to determine
and classify the speaker's gender based on their voice characteristics.
        """
        return AsrGenderClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def base_model(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> BaseModel:
        """
        The Base-Model function serves as a foundational framework designed to provide
essential features and capabilities upon which more specialized or advanced
models can be built and customized.
        """
        return BaseModel(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def language_identification_audio(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> LanguageIdentificationAudio:
        """
        The Language Identification Audio function analyzes audio input to determine
and identify the language being spoken.
        """
        return LanguageIdentificationAudio(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def loglikelihood(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Loglikelihood:
        """
        The Log Likelihood function measures the probability of observing the given
data under a specific statistical model by taking the natural logarithm of the
likelihood function, thereby transforming the product of probabilities into a
sum, which simplifies the process of optimization and parameter estimation.
        """
        return Loglikelihood(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoEmbedding:
        """
        Video Embedding is a process that transforms video content into a fixed-
dimensional vector representation, capturing essential features and patterns to
facilitate tasks such as retrieval, classification, and recommendation.
        """
        return VideoEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_segmenation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSegmenation:
        """
        Text Segmentation is the process of dividing a continuous text into meaningful
units, such as words, sentences, or topics, to facilitate easier analysis and
understanding.
        """
        return TextSegmenation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageEmbedding:
        """
        Image Embedding is a process that transforms an image into a fixed-dimensional
vector representation, capturing its essential features and enabling efficient
comparison, retrieval, and analysis in various machine learning and computer
vision tasks.
        """
        return ImageEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_manipulation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageManipulation:
        """
        Image Manipulation refers to the process of altering or enhancing digital
images using various techniques and tools to achieve desired visual effects,
correct imperfections, or transform the image's appearance.
        """
        return ImageManipulation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_to_video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageToVideoGeneration:
        """
        The Image To Video Generation function transforms a series of static images
into a cohesive, dynamic video sequence, often incorporating transitions,
effects, and synchronization with audio to create a visually engaging
narrative.
        """
        return ImageToVideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_forced_alignment(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioForcedAlignment:
        """
        Audio Forced Alignment is a process that synchronizes a given audio recording
with its corresponding transcript by precisely aligning each spoken word or
phoneme to its exact timing within the audio.
        """
        return AudioForcedAlignment(*args, asset_id=asset_id, pipeline=self, **kwargs)

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

    def document_image_parsing(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DocumentImageParsing:
        """
        Document Image Parsing is the process of analyzing and converting scanned or
photographed images of documents into structured, machine-readable formats by
identifying and extracting text, layout, and other relevant information.
        """
        return DocumentImageParsing(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def document_information_extraction(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DocumentInformationExtraction:
        """
        Document Information Extraction is the process of automatically identifying,
extracting, and structuring relevant data from unstructured or semi-structured
documents, such as invoices, receipts, contracts, and forms, to facilitate
easier data management and analysis.
        """
        return DocumentInformationExtraction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def depth_estimation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DepthEstimation:
        """
        Depth estimation is a computational process that determines the distance of
objects from a viewpoint, typically using visual data from cameras or sensors
to create a three-dimensional understanding of a scene.
        """
        return DepthEstimation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoGeneration:
        """
        Video Generation is the process of creating video content through automated or
semi-automated means, often utilizing algorithms, artificial intelligence, or
software tools to produce visual and audio elements that can range from simple
animations to complex, realistic scenes.
        """
        return VideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_audio_generation_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ReferencelessAudioGenerationMetric:
        """
        The Referenceless Audio Generation Metric is a tool designed to evaluate the
quality of generated audio content without the need for a reference or original
audio sample for comparison.
        """
        return ReferencelessAudioGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_class_image_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> MultiClassImageClassification:
        """
        Multi Class Image Classification is a machine learning task where an algorithm
is trained to categorize images into one of several predefined classes or
categories based on their visual content.
        """
        return MultiClassImageClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def semantic_segmentation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SemanticSegmentation:
        """
        Semantic segmentation is a computer vision process that involves classifying
each pixel in an image into a predefined category, effectively partitioning the
image into meaningful segments based on the objects or regions they represent.
        """
        return SemanticSegmentation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def instance_segmentation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> InstanceSegmentation:
        """
        Instance segmentation is a computer vision task that involves detecting and
delineating each distinct object within an image, assigning a unique label and
precise boundary to every individual instance of objects, even if they belong
to the same category.
        """
        return InstanceSegmentation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_colorization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageColorization:
        """
        Image colorization is a process that involves adding color to grayscale images,
transforming them from black-and-white to full-color representations, often
using advanced algorithms and machine learning techniques to predict and apply
the appropriate hues and shades.
        """
        return ImageColorization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_generation_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioGenerationMetric:
        """
        The Audio Generation Metric is a quantitative measure used to evaluate the
quality, accuracy, and overall performance of audio generated by artificial
intelligence systems, often considering factors such as fidelity,
intelligibility, and similarity to human-produced audio.
        """
        return AudioGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_impainting(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageImpainting:
        """
        Image inpainting is a process that involves filling in missing or damaged parts
of an image in a way that is visually coherent and seamlessly blends with the
surrounding areas, often using advanced algorithms and techniques to restore
the image to its original or intended appearance.
        """
        return ImageImpainting(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def style_transfer(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> StyleTransfer:
        """
        Style Transfer is a technique in artificial intelligence that applies the
visual style of one image (such as the brushstrokes of a famous painting) to
the content of another image, effectively blending the artistic elements of the
first image with the subject matter of the second.
        """
        return StyleTransfer(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_class_text_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> MultiClassTextClassification:
        """
        Multi Class Text Classification is a natural language processing task that
involves categorizing a given text into one of several predefined classes or
categories based on its content.
        """
        return MultiClassTextClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextEmbedding:
        """
        Text embedding is a process that converts text into numerical vectors,
capturing the semantic meaning and contextual relationships of words or
phrases, enabling machines to understand and analyze natural language more
effectively.
        """
        return TextEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multi_label_text_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> MultiLabelTextClassification:
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

    def speech_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechClassification:
        """
        Speech Classification is a process that involves analyzing and categorizing
spoken language into predefined categories or classes based on various features
such as tone, pitch, and linguistic content.
        """
        return SpeechClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def intent_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> IntentClassification:
        """
        Intent Classification is a natural language processing task that involves
analyzing and categorizing user text input to determine the underlying purpose
or goal behind the communication, such as booking a flight, asking for weather
information, or setting a reminder.
        """
        return IntentClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def part_of_speech_tagging(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> PartOfSpeechTagging:
        """
        Part of Speech Tagging is a natural language processing task that involves
assigning each word in a sentence its corresponding part of speech, such as
noun, verb, adjective, or adverb, based on its role and context within the
sentence.
        """
        return PartOfSpeechTagging(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def metric_aggregation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> MetricAggregation:
        """
        Metric Aggregation is a function that computes and summarizes numerical data by
applying statistical operations, such as averaging, summing, or finding the
minimum and maximum values, to provide insights and facilitate analysis of
large datasets.
        """
        return MetricAggregation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def dialect_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> DialectDetection:
        """
        Dialect Detection is a function that identifies and classifies the specific
regional or social variations of a language spoken or written by an individual,
enabling the recognition of distinct linguistic patterns and nuances associated
with different dialects.
        """
        return DialectDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

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

    def fill_text_mask(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> FillTextMask:
        """
        The "Fill Text Mask" function takes a text input with masked or placeholder
characters and replaces those placeholders with specified or contextually
appropriate characters to generate a complete and coherent text output.
        """
        return FillTextMask(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoContentModeration:
        """
        Video Content Moderation is the process of reviewing, analyzing, and filtering
video content to ensure it adheres to community guidelines, legal standards,
and platform policies, thereby preventing the dissemination of inappropriate,
harmful, or illegal material.
        """
        return VideoContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def extract_audio_from_video(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ExtractAudioFromVideo:
        """
        The "Extract Audio From Video" function allows users to separate and save the
audio track from a video file, enabling them to obtain just the sound without
the accompanying visual content.
        """
        return ExtractAudioFromVideo(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_compression(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageCompression:
        """
        Image compression is a process that reduces the file size of an image by
removing redundant or non-essential data, while maintaining an acceptable level
of visual quality.
        """
        return ImageCompression(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def multilingual_speech_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> MultilingualSpeechRecognition:
        """
        Multilingual Speech Recognition is a technology that enables the automatic
transcription of spoken language into text across multiple languages, allowing
for seamless communication and understanding in diverse linguistic contexts.
        """
        return MultilingualSpeechRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_text_generation_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ReferencelessTextGenerationMetric:
        """
        The Referenceless Text Generation Metric is a method for evaluating the quality
of generated text without requiring a reference text for comparison, often
leveraging models or algorithms to assess coherence, relevance, and fluency
based on intrinsic properties of the text itself.
        """
        return ReferencelessTextGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation_metric_default(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextGenerationMetricDefault:
        """
        The "Text Generation Metric Default" function provides a standard set of
evaluation metrics for assessing the quality and performance of text generation
models.
        """
        return TextGenerationMetricDefault(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def noise_removal(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> NoiseRemoval:
        """
        Noise Removal is a process that involves identifying and eliminating unwanted
random variations or disturbances from an audio signal to enhance the clarity
and quality of the underlying information.
        """
        return NoiseRemoval(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_reconstruction(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioReconstruction:
        """
        Audio Reconstruction is the process of restoring or recreating audio signals
from incomplete, damaged, or degraded recordings to achieve a high-quality,
accurate representation of the original sound.
        """
        return AudioReconstruction(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def voice_cloning(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VoiceCloning:
        """
        Voice cloning is a technology that uses artificial intelligence to create a
digital replica of a person's voice, allowing for the generation of speech that
mimics the tone, pitch, and speaking style of the original speaker.
        """
        return VoiceCloning(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def diacritization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Diacritization:
        """
        Diacritization is the process of adding diacritical marks to letters in a text
to indicate pronunciation, stress, tone, or meaning, often used in languages
such as Arabic, Hebrew, and Vietnamese to provide clarity and accuracy in
written communication.
        """
        return Diacritization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_emotion_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioEmotionDetection:
        """
        Audio Emotion Detection is a technology that analyzes vocal characteristics and
patterns in audio recordings to identify and classify the emotional state of
the speaker.
        """
        return AudioEmotionDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_summarization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSummarization:
        """
        Text summarization is the process of condensing a large body of text into a
shorter version, capturing the main points and essential information while
maintaining coherence and meaning.
        """
        return TextSummarization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def entity_linking(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> EntityLinking:
        """
        Entity Linking is the process of identifying and connecting mentions of
entities within a text to their corresponding entries in a structured knowledge
base, thereby enabling the disambiguation of terms and enhancing the
understanding of the text's context.
        """
        return EntityLinking(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextGenerationMetric:
        """
        A Text Generation Metric is a quantitative measure used to evaluate the quality
and effectiveness of text produced by natural language processing models, often
assessing aspects such as coherence, relevance, fluency, and adherence to given
prompts or instructions.
        """
        return TextGenerationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def split_on_linebreak(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SplitOnLinebreak:
        """
        The "Split On Linebreak" function divides a given string into a list of
substrings, using linebreaks (newline characters) as the points of separation.
        """
        return SplitOnLinebreak(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def sentiment_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SentimentAnalysis:
        """
        Sentiment Analysis is a natural language processing technique used to determine
and classify the emotional tone or subjective information expressed in a piece
of text, such as identifying whether the sentiment is positive, negative, or
neutral.
        """
        return SentimentAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def keyword_spotting(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> KeywordSpotting:
        """
        Keyword Spotting is a function that enables the detection and identification of
specific words or phrases within a stream of audio, often used in voice-
activated systems to trigger actions or commands based on recognized keywords.
        """
        return KeywordSpotting(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextClassification:
        """
        Text Classification is a natural language processing task that involves
categorizing text into predefined labels or classes based on its content,
enabling automated organization, filtering, and analysis of large volumes of
textual data.
        """
        return TextClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def other__multipurpose_(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> OtherMultipurpose:
        """
        The "Other (Multipurpose)" function serves as a versatile category designed to
accommodate a wide range of tasks and activities that do not fit neatly into
predefined classifications, offering flexibility and adaptability for various
needs.
        """
        return OtherMultipurpose(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_synthesis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechSynthesis:
        """
        Speech synthesis is the artificial production of human speech, typically
achieved through software or hardware systems that convert text into spoken
words, enabling machines to communicate verbally with users.
        """
        return SpeechSynthesis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_intent_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioIntentDetection:
        """
        Audio Intent Detection is a process that involves analyzing audio signals to
identify and interpret the underlying intentions or purposes behind spoken
words, enabling systems to understand and respond appropriately to human
speech.
        """
        return AudioIntentDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_label_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoLabelDetection:
        """
        Video Label Detection is a function that automatically identifies and tags
various objects, scenes, activities, and other relevant elements within a
video, providing descriptive labels that enhance searchability and content
organization.
        """
        return VideoLabelDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def asr_quality_estimation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AsrQualityEstimation:
        """
        ASR Quality Estimation is a process that evaluates the accuracy and reliability
of automatic speech recognition systems by analyzing their performance in
transcribing spoken language into text.
        """
        return AsrQualityEstimation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_transcript_analysis(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioTranscriptAnalysis:
        """
        Audio Transcript Analysis is a process that involves converting spoken language
from audio recordings into written text, followed by examining and interpreting
the transcribed content to extract meaningful insights, identify patterns, and
derive actionable information.
        """
        return AudioTranscriptAnalysis(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def search(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Search:
        """
        The "Search" function allows users to input keywords or phrases to quickly
locate specific information, files, or content within a database, website, or
application.
        """
        return Search(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_forced_alignment(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoForcedAlignment:
        """
        Video Forced Alignment is a process that synchronizes video footage with
corresponding audio tracks by precisely aligning the visual and auditory
elements, ensuring that the movements of speakers' lips match the spoken words.
        """
        return VideoForcedAlignment(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def viseme_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VisemeGeneration:
        """
        Viseme Generation is the process of creating visual representations of
phonemes, which are the distinct units of sound in speech, to synchronize lip
movements with spoken words in animations or virtual avatars.
        """
        return VisemeGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def topic_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TopicClassification:
        """
        Topic Classification is a natural language processing function that categorizes
text into predefined topics or subjects based on its content, enabling
efficient organization and retrieval of information.
        """
        return TopicClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def offensive_language_identification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> OffensiveLanguageIdentification:
        """
        Offensive Language Identification is a function that analyzes text to detect
and flag language that is abusive, harmful, or inappropriate, helping to
maintain a respectful and safe communication environment.
        """
        return OffensiveLanguageIdentification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechTranslation:
        """
        Speech Translation is a technology that converts spoken language in real-time
from one language to another, enabling seamless communication between speakers
of different languages.
        """
        return SpeechTranslation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speaker_diarization_audio(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeakerDiarizationAudio:
        """
        Speaker Diarization Audio is a process that involves segmenting an audio
recording into distinct sections, each corresponding to a different speaker, in
order to identify and differentiate between multiple speakers within the same
audio stream.
        """
        return SpeakerDiarizationAudio(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def audio_transcript_improvement(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> AudioTranscriptImprovement:
        """
        Audio Transcript Improvement is a function that enhances the accuracy and
clarity of transcribed audio recordings by correcting errors, refining
language, and ensuring the text faithfully represents the original spoken
content.
        """
        return AudioTranscriptImprovement(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_non_speech_classification(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechNonSpeechClassification:
        """
        The function "Speech or Non-Speech Classification" is designed to analyze audio
input and determine whether the sound is human speech or non-speech noise,
enabling applications such as voice recognition systems to filter out
irrelevant background sounds.
        """
        return SpeechNonSpeechClassification(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_denormalization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextDenormalization:
        """
        Text Denormalization is the process of converting abbreviated, contracted, or
otherwise simplified text into its full, standard form, often to improve
readability and ensure consistency in natural language processing tasks.
        """
        return TextDenormalization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def image_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ImageContentModeration:
        """
        Image Content Moderation is a process that involves analyzing and filtering
images to detect and manage inappropriate, harmful, or sensitive content,
ensuring compliance with community guidelines and legal standards.
        """
        return ImageContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def referenceless_text_generation_metric_default(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ReferencelessTextGenerationMetricDefault:
        """
        The Referenceless Text Generation Metric Default is a function designed to
evaluate the quality of generated text without relying on reference texts for
comparison.
        """
        return ReferencelessTextGenerationMetricDefault(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def named_entity_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> NamedEntityRecognition:
        """
        Named Entity Recognition (NER) is a natural language processing task that
involves identifying and classifying proper nouns in text into predefined
categories such as names of people, organizations, locations, dates, and other
entities.
        """
        return NamedEntityRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_content_moderation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextContentModeration:
        """
        Text Content Moderation is the process of reviewing, filtering, and managing
user-generated content to ensure it adheres to community guidelines, legal
standards, and platform policies, thereby maintaining a safe and respectful
online environment.
        """
        return TextContentModeration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speaker_diarization_video(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeakerDiarizationVideo:
        """
        The Speaker Diarization Video function identifies and segments different
speakers in a video, attributing portions of the audio to individual speakers
to facilitate analysis and understanding of multi-speaker conversations.
        """
        return SpeakerDiarizationVideo(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def split_on_silence(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SplitOnSilence:
        """
        The "Split On Silence" function divides an audio recording into separate
segments based on periods of silence, allowing for easier editing and analysis
of individual sections.
        """
        return SplitOnSilence(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def emotion_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> EmotionDetection:
        """
        Emotion Detection is a process that involves analyzing text to identify and
categorize the emotional states or sentiments expressed by individuals, such as
happiness, sadness, anger, or fear.
        """
        return EmotionDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_spam_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextSpamDetection:
        """
        Text Spam Detection is a process that involves analyzing and identifying
unsolicited or irrelevant messages within text communications, typically using
algorithms and machine learning techniques to filter out spam and ensure the
integrity of the communication platform.
        """
        return TextSpamDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Translation:
        """
        Translation is the process of converting text from one language into an
equivalent text in another language, preserving the original meaning and
context.
        """
        return Translation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def voice_activity_detection(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VoiceActivityDetection:
        """
        Voice Activity Detection (VAD) is a technology that identifies the presence or
absence of human speech within an audio signal, enabling systems to distinguish
between spoken words and background noise.
        """
        return VoiceActivityDetection(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_embedding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechEmbedding:
        """
        Speech Embedding is a process that transforms spoken language into a fixed-
dimensional vector representation, capturing essential features and
characteristics of the speech for tasks such as recognition, classification,
and analysis.
        """
        return SpeechEmbedding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def subtitling_translation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SubtitlingTranslation:
        """
        Subtitling Translation is the process of converting spoken dialogue from one
language into written text in another language, which is then displayed on-
screen to aid viewers in understanding the content.
        """
        return SubtitlingTranslation(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextGeneration:
        """
        Text Generation is a process in which artificial intelligence models, such as
neural networks, produce coherent and contextually relevant text based on a
given input or prompt, often mimicking human writing styles and patterns.
        """
        return TextGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def video_understanding(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> VideoUnderstanding:
        """
        Video Understanding is the process of analyzing and interpreting video content
to extract meaningful information, such as identifying objects, actions,
events, and contextual relationships within the footage.
        """
        return VideoUnderstanding(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_to_video_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextToVideoGeneration:
        """
        Text To Video Generation is a process that converts written descriptions or
scripts into dynamic, visual video content using advanced algorithms and
artificial intelligence.
        """
        return TextToVideoGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_normalization(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextNormalization:
        """
        Text normalization is the process of transforming text into a standard,
consistent format by correcting spelling errors, converting all characters to a
uniform case, removing punctuation, and expanding abbreviations to improve the
text's readability and usability for further processing or analysis.
        """
        return TextNormalization(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def speech_recognition(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> SpeechRecognition:
        """
        Speech recognition is a technology that enables a computer or device to
identify and process spoken language, converting it into text.
        """
        return SpeechRecognition(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def subtitling(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> Subtitling:
        """
        Subtitling is the process of displaying written text on a screen to represent
the spoken dialogue, narration, or other audio elements in a video, typically
to aid viewers who are deaf or hard of hearing, or to provide translations for
audiences who speak different languages.
        """
        return Subtitling(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def classification_metric(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> ClassificationMetric:
        """
        A Classification Metric is a quantitative measure used to evaluate the quality
and effectiveness of classification models.
        """
        return ClassificationMetric(*args, asset_id=asset_id, pipeline=self, **kwargs)

    def text_to_image_generation(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> TextToImageGeneration:
        """
        Text To Image Generation is a process where a system creates visual images
based on descriptive text input, translating written language into
corresponding graphical representations.
        """
        return TextToImageGeneration(*args, asset_id=asset_id, pipeline=self, **kwargs)

