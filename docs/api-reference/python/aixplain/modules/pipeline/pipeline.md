---
sidebar_label: pipeline
title: aixplain.modules.pipeline.pipeline
---

### ActivityDetection Objects

```python
class ActivityDetection(AssetNode[ActivityDetectionInputs,
                                  ActivityDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L46)

detection of the presence or absence of human speech, used in speech
processing.

    InputType: audio
    OutputType: label

### ScriptExecution Objects

```python
class ScriptExecution(AssetNode[ScriptExecutionInputs,
                                ScriptExecutionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L85)

Script Execution refers to the process of running a set of programmed
instructions or code within a computing environment, enabling the automated
performance of tasks, calculations, or operations as defined by the script.

    InputType: text
    OutputType: text

### TextDetection Objects

```python
class TextDetection(AssetNode[TextDetectionInputs, TextDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L125)

detect text regions in the complex background and label them with bounding
boxes.

    InputType: image
    OutputType: text

### AudioSourceSeparation Objects

```python
class AudioSourceSeparation(AssetNode[AudioSourceSeparationInputs,
                                      AudioSourceSeparationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L164)

Audio Source Separation is the process of separating a mixture (e.g. a pop band
recording) into isolated sounds from individual sources (e.g. just the lead
vocals).

    InputType: audio
    OutputType: audio

### MultiClassTextClassification Objects

```python
class MultiClassTextClassification(
        AssetNode[MultiClassTextClassificationInputs,
                  MultiClassTextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L210)

Multi Class Text Classification is a natural language processing task that
involves categorizing a given text into one of several predefined classes or
categories based on its content.

    InputType: text
    OutputType: label

### ImageImpainting Objects

```python
class ImageImpainting(AssetNode[ImageImpaintingInputs,
                                ImageImpaintingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L250)

Image inpainting is a process that involves filling in missing or damaged parts
of an image in a way that is visually coherent and seamlessly blends with the
surrounding areas, often using advanced algorithms and techniques to restore
the image to its original or intended appearance.

    InputType: image
    OutputType: image

### SceneDetection Objects

```python
class SceneDetection(AssetNode[SceneDetectionInputs, SceneDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L291)

Scene detection is used for detecting transitions between shots in a video to
split it into basic temporal segments.

    InputType: image
    OutputType: text

### ZeroShotClassification Objects

```python
class ZeroShotClassification(AssetNode[ZeroShotClassificationInputs,
                                       ZeroShotClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L342)

InputType: text
OutputType: text

### AudioIntentDetection Objects

```python
class AudioIntentDetection(AssetNode[AudioIntentDetectionInputs,
                                     AudioIntentDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L380)

Audio Intent Detection is a process that involves analyzing audio signals to
identify and interpret the underlying intentions or purposes behind spoken
words, enabling systems to understand and respond appropriately to human
speech.

    InputType: audio
    OutputType: label

### Ocr Objects

```python
class Ocr(AssetNode[OcrInputs, OcrOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L427)

Converts images of typed, handwritten, or printed text into machine-encoded
text. Used in digitizing printed texts for data retrieval.

    InputType: image
    OutputType: text

### IntentRecognition Objects

```python
class IntentRecognition(AssetNode[IntentRecognitionInputs,
                                  IntentRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L478)

classify the user&#x27;s utterance (provided in varied natural language)  or text
into one of several predefined classes, that is, intents.

    InputType: audio
    OutputType: text

### VideoEmbedding Objects

```python
class VideoEmbedding(AssetNode[VideoEmbeddingInputs, VideoEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L523)

Video Embedding is a process that transforms video content into a fixed-
dimensional vector representation, capturing essential features and patterns to
facilitate tasks such as retrieval, classification, and recommendation.

    InputType: video
    OutputType: embedding

### ExtractAudioFromVideo Objects

```python
class ExtractAudioFromVideo(AssetNode[ExtractAudioFromVideoInputs,
                                      ExtractAudioFromVideoOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L563)

Isolates and extracts audio tracks from video files, aiding in audio analysis
or transcription tasks.

    InputType: video
    OutputType: audio

### ImageCaptioning Objects

```python
class ImageCaptioning(AssetNode[ImageCaptioningInputs,
                                ImageCaptioningOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L602)

Image Captioning is a process that involves generating a textual description of
an image, typically using machine learning models to analyze the visual content
and produce coherent and contextually relevant sentences that describe the
objects, actions, and scenes depicted in the image.

    InputType: image
    OutputType: text

### ImageAnalysis Objects

```python
class ImageAnalysis(AssetNode[ImageAnalysisInputs, ImageAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L643)

Image analysis is the extraction of meaningful information from images

InputType: image
OutputType: label

### BenchmarkScoringMt Objects

```python
class BenchmarkScoringMt(AssetNode[BenchmarkScoringMtInputs,
                                   BenchmarkScoringMtOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L693)

Benchmark Scoring MT is a function designed to evaluate and score machine
translation systems by comparing their output against a set of predefined
benchmarks, thereby assessing their accuracy and performance.

    InputType: text
    OutputType: label

### SpeakerDiarizationAudio Objects

```python
class SpeakerDiarizationAudio(BaseSegmentor[SpeakerDiarizationAudioInputs,
                                            SpeakerDiarizationAudioOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L753)

Identifies individual speakers and their respective speech segments within an
audio clip. Ideal for multi-speaker recordings or conference calls.

    InputType: audio
    OutputType: label

### Connection Objects

```python
class Connection(AssetNode[ConnectionInputs, ConnectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L792)

Connections are integration that allow you to connect your AI agents to
external tools

    InputType: text
    OutputType: text

### Connector Objects

```python
class Connector(AssetNode[ConnectorInputs, ConnectorOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L831)

Connectors are integration that allow you to connect your AI agents to external
tools

    InputType: text
    OutputType: text

### ImageContentModeration Objects

```python
class ImageContentModeration(AssetNode[ImageContentModerationInputs,
                                       ImageContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L876)

Detects and filters out inappropriate or harmful images, essential for
platforms with user-generated visual content.

    InputType: image
    OutputType: label

### ImageColorization Objects

```python
class ImageColorization(AssetNode[ImageColorizationInputs,
                                  ImageColorizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L915)

Image colorization is a process that involves adding color to grayscale images,
transforming them from black-and-white to full-color representations, often
using advanced algorithms and machine learning techniques to predict and apply
the appropriate hues and shades.

    InputType: image
    OutputType: image

### ImageAndVideoAnalysis Objects

```python
class ImageAndVideoAnalysis(AssetNode[ImageAndVideoAnalysisInputs,
                                      ImageAndVideoAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L956)

InputType: image
OutputType: text

### BenchmarkScoringAsr Objects

```python
class BenchmarkScoringAsr(AssetNode[BenchmarkScoringAsrInputs,
                                    BenchmarkScoringAsrOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1006)

Benchmark Scoring ASR is a function that evaluates and compares the performance
of automatic speech recognition systems by analyzing their accuracy, speed, and
other relevant metrics against a standardized set of benchmarks.

    InputType: audio
    OutputType: label

### VideoContentModeration Objects

```python
class VideoContentModeration(AssetNode[VideoContentModerationInputs,
                                       VideoContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1052)

Automatically reviews video content to detect and possibly remove inappropriate
or harmful material. Essential for user-generated content platforms.

    InputType: video
    OutputType: label

### MultilingualSpeechRecognition Objects

```python
class MultilingualSpeechRecognition(
        AssetNode[MultilingualSpeechRecognitionInputs,
                  MultilingualSpeechRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1097)

Multilingual Speech Recognition is a technology that enables the automatic
transcription of spoken language into text across multiple languages, allowing
for seamless communication and understanding in diverse linguistic contexts.

    InputType: audio
    OutputType: text

### TopicModeling Objects

```python
class TopicModeling(AssetNode[TopicModelingInputs, TopicModelingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1149)

Topic modeling is a type of statistical modeling for discovering the abstract
“topics” that occur in a collection of documents.

    InputType: text
    OutputType: label

### VisualQuestionAnswering Objects

```python
class VisualQuestionAnswering(AssetNode[VisualQuestionAnsweringInputs,
                                        VisualQuestionAnsweringOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1200)

Visual Question Answering (VQA) is a task in artificial intelligence that
involves analyzing an image and providing accurate, contextually relevant
answers to questions posed about the visual content of that image.

    InputType: image
    OutputType: video

### DocumentImageParsing Objects

```python
class DocumentImageParsing(AssetNode[DocumentImageParsingInputs,
                                     DocumentImageParsingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1240)

Document Image Parsing is the process of analyzing and converting scanned or
photographed images of documents into structured, machine-readable formats by
identifying and extracting text, layout, and other relevant information.

    InputType: image
    OutputType: text

### TextReconstruction Objects

```python
class TextReconstruction(BaseReconstructor[TextReconstructionInputs,
                                           TextReconstructionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1280)

Text Reconstruction is a process that involves piecing together fragmented or
incomplete text data to restore it to its original, coherent form.

    InputType: text
    OutputType: text

### AudioEmotionDetection Objects

```python
class AudioEmotionDetection(AssetNode[AudioEmotionDetectionInputs,
                                      AudioEmotionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1319)

Audio Emotion Detection is a technology that analyzes vocal characteristics and
patterns in audio recordings to identify and classify the emotional state of
the speaker.

    InputType: audio
    OutputType: label

### KeywordSpotting Objects

```python
class KeywordSpotting(AssetNode[KeywordSpottingInputs,
                                KeywordSpottingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1359)

Keyword Spotting is a function that enables the detection and identification of
specific words or phrases within a stream of audio, often used in voice-
activated systems to trigger actions or commands based on recognized keywords.

    InputType: audio
    OutputType: label

### NamedEntityRecognition Objects

```python
class NamedEntityRecognition(AssetNode[NamedEntityRecognitionInputs,
                                       NamedEntityRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1423)

Identifies and classifies named entities (e.g., persons, organizations,
locations) within text. Useful for information extraction, content tagging, and
search enhancements.

    InputType: text
    OutputType: label

### SplitOnSilence Objects

```python
class SplitOnSilence(AssetNode[SplitOnSilenceInputs, SplitOnSilenceOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1463)

The &quot;Split On Silence&quot; function divides an audio recording into separate
segments based on periods of silence, allowing for easier editing and analysis
of individual sections.

    InputType: audio
    OutputType: audio

### DocumentInformationExtraction Objects

```python
class DocumentInformationExtraction(
        AssetNode[DocumentInformationExtractionInputs,
                  DocumentInformationExtractionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1503)

Document Information Extraction is the process of automatically identifying,
extracting, and structuring relevant data from unstructured or semi-structured
documents, such as invoices, receipts, contracts, and forms, to facilitate
easier data management and analysis.

    InputType: image
    OutputType: text

### TextToVideoGeneration Objects

```python
class TextToVideoGeneration(AssetNode[TextToVideoGenerationInputs,
                                      TextToVideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1550)

Text To Video Generation is a process that converts written descriptions or
scripts into dynamic, visual video content using advanced algorithms and
artificial intelligence.

    InputType: text
    OutputType: video

### VideoGeneration Objects

```python
class VideoGeneration(AssetNode[VideoGenerationInputs,
                                VideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1590)

Produces video content based on specific inputs or datasets. Can be used for
simulations, animations, or even deepfake detection.

    InputType: text
    OutputType: video

### TextToImageGeneration Objects

```python
class TextToImageGeneration(AssetNode[TextToImageGenerationInputs,
                                      TextToImageGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1629)

Creates a visual representation based on textual input, turning descriptions
into pictorial forms. Used in creative processes and content generation.

    InputType: text
    OutputType: image

### DialectDetection Objects

```python
class DialectDetection(AssetNode[DialectDetectionInputs,
                                 DialectDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1674)

Identifies specific dialects within a language, aiding in localized content
creation or user experience personalization.

    InputType: audio
    OutputType: text

### SpeakerRecognition Objects

```python
class SpeakerRecognition(AssetNode[SpeakerRecognitionInputs,
                                   SpeakerRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1731)

In speaker identification, an utterance from an unknown speaker is analyzed and
compared with speech models of known speakers.

    InputType: audio
    OutputType: label

### SyntaxAnalysis Objects

```python
class SyntaxAnalysis(AssetNode[SyntaxAnalysisInputs, SyntaxAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1782)

Is the process of analyzing natural language with the rules of a formal
grammar. Grammatical rules are applied to categories and groups of words, not
individual words. Syntactic analysis basically assigns a semantic structure to
text.

    InputType: text
    OutputType: text

### QuestionAnswering Objects

```python
class QuestionAnswering(AssetNode[QuestionAnsweringInputs,
                                  QuestionAnsweringOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1829)

building systems that automatically answer questions posed by humans in a
natural language usually from a given text

    InputType: text
    OutputType: text

### ReferencelessTextGenerationMetric Objects

```python
class ReferencelessTextGenerationMetric(
        BaseMetric[ReferencelessTextGenerationMetricInputs,
                   ReferencelessTextGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1880)

The Referenceless Text Generation Metric is a method for evaluating the quality
of generated text without requiring a reference text for comparison, often
leveraging models or algorithms to assess coherence, relevance, and fluency
based on intrinsic properties of the text itself.

    InputType: text
    OutputType: text

### DetectLanguageFromText Objects

```python
class DetectLanguageFromText(AssetNode[DetectLanguageFromTextInputs,
                                       DetectLanguageFromTextOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1921)

Detect Language From Text

InputType: text
OutputType: label

### AudioLanguageIdentification Objects

```python
class AudioLanguageIdentification(AssetNode[AudioLanguageIdentificationInputs,
                                            AudioLanguageIdentificationOutputs]
                                  )
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1959)

Audio Language Identification is a process that involves analyzing an audio
recording to determine the language being spoken.

    InputType: audio
    OutputType: label

### BaseModel Objects

```python
class BaseModel(AssetNode[BaseModelInputs, BaseModelOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2004)

The Base-Model function serves as a foundational framework designed to provide
essential features and capabilities upon which more specialized or advanced
models can be built and customized.

    InputType: text
    OutputType: text

### LanguageIdentificationAudio Objects

```python
class LanguageIdentificationAudio(AssetNode[LanguageIdentificationAudioInputs,
                                            LanguageIdentificationAudioOutputs]
                                  )
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2044)

The Language Identification Audio function analyzes audio input to determine
and identify the language being spoken.

    InputType: audio
    OutputType: label

### MultiClassImageClassification Objects

```python
class MultiClassImageClassification(
        AssetNode[MultiClassImageClassificationInputs,
                  MultiClassImageClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2083)

Multi Class Image Classification is a machine learning task where an algorithm
is trained to categorize images into one of several predefined classes or
categories based on their visual content.

    InputType: image
    OutputType: label

### SemanticSegmentation Objects

```python
class SemanticSegmentation(AssetNode[SemanticSegmentationInputs,
                                     SemanticSegmentationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2123)

Semantic segmentation is a computer vision process that involves classifying
each pixel in an image into a predefined category, effectively partitioning the
image into meaningful segments based on the objects or regions they represent.

    InputType: image
    OutputType: label

### AudioGenerationMetric Objects

```python
class AudioGenerationMetric(BaseMetric[AudioGenerationMetricInputs,
                                       AudioGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2181)

The Audio Generation Metric is a quantitative measure used to evaluate the
quality, accuracy, and overall performance of audio generated by artificial
intelligence systems, often considering factors such as fidelity,
intelligibility, and similarity to human-produced audio.

    InputType: text
    OutputType: text

### AutoMaskGeneration Objects

```python
class AutoMaskGeneration(AssetNode[AutoMaskGenerationInputs,
                                   AutoMaskGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2222)

Auto-mask generation refers to the automated process of creating masks in image
processing or computer vision, typically for segmentation tasks. A mask is a
binary or multi-class image that labels different parts of an image, usually
separating the foreground (objects of interest) from the background, or
identifying specific object classes in an image.

    InputType: image
    OutputType: label

### FactChecking Objects

```python
class FactChecking(AssetNode[FactCheckingInputs, FactCheckingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2270)

Fact Checking is the process of verifying the accuracy and truthfulness of
information, statements, or claims by cross-referencing with reliable sources
and evidence.

    InputType: text
    OutputType: label

### TextToAudio Objects

```python
class TextToAudio(AssetNode[TextToAudioInputs, TextToAudioOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2316)

The Text to Audio function converts written text into spoken words, allowing
users to listen to the content instead of reading it.

    InputType: text
    OutputType: audio

### TableQuestionAnswering Objects

```python
class TableQuestionAnswering(AssetNode[TableQuestionAnsweringInputs,
                                       TableQuestionAnsweringOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2361)

The task of question answering over tables is given an input table (or a set of
tables) T and a natural language question Q (a user query), output the correct
answer A

    InputType: text
    OutputType: text

### ClassificationMetric Objects

```python
class ClassificationMetric(BaseMetric[ClassificationMetricInputs,
                                      ClassificationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2425)

A Classification Metric is a quantitative measure used to evaluate the quality
and effectiveness of classification models.

    InputType: text
    OutputType: text

### TextGenerationMetric Objects

```python
class TextGenerationMetric(BaseMetric[TextGenerationMetricInputs,
                                      TextGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2482)

A Text Generation Metric is a quantitative measure used to evaluate the quality
and effectiveness of text produced by natural language processing models, often
assessing aspects such as coherence, relevance, fluency, and adherence to given
prompts or instructions.

    InputType: text
    OutputType: text

### AsrGenderClassification Objects

```python
class AsrGenderClassification(AssetNode[AsrGenderClassificationInputs,
                                        AsrGenderClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2523)

The ASR Gender Classification function analyzes audio recordings to determine
and classify the speaker&#x27;s gender based on their voice characteristics.

    InputType: audio
    OutputType: label

### EntityLinking Objects

```python
class EntityLinking(AssetNode[EntityLinkingInputs, EntityLinkingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2574)

Associates identified entities in the text with specific entries in a knowledge
base or database.

    InputType: text
    OutputType: label

### PartOfSpeechTagging Objects

```python
class PartOfSpeechTagging(AssetNode[PartOfSpeechTaggingInputs,
                                    PartOfSpeechTaggingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2619)

Part of Speech Tagging is a natural language processing task that involves
assigning each word in a sentence its corresponding part of speech, such as
noun, verb, adjective, or adverb, based on its role and context within the
sentence.

    InputType: text
    OutputType: label

### FillTextMask Objects

```python
class FillTextMask(AssetNode[FillTextMaskInputs, FillTextMaskOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2678)

Completes missing parts of a text based on the context, ideal for content
generation or data augmentation tasks.

    InputType: text
    OutputType: text

### TextEmbedding Objects

```python
class TextEmbedding(AssetNode[TextEmbeddingInputs, TextEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2735)

Text embedding is a process that converts text into numerical vectors,
capturing the semantic meaning and contextual relationships of words or
phrases, enabling machines to understand and analyze natural language more
effectively.

    InputType: text
    OutputType: text

### OtherMultipurpose Objects

```python
class OtherMultipurpose(AssetNode[OtherMultipurposeInputs,
                                  OtherMultipurposeOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2782)

The &quot;Other (Multipurpose)&quot; function serves as a versatile category designed to
accommodate a wide range of tasks and activities that do not fit neatly into
predefined classifications, offering flexibility and adaptability for various
needs.

    InputType: text
    OutputType: text

### VideoLabelDetection Objects

```python
class VideoLabelDetection(AssetNode[VideoLabelDetectionInputs,
                                    VideoLabelDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2829)

Identifies and tags objects, scenes, or activities within a video. Useful for
content indexing and recommendation systems.

    InputType: video
    OutputType: label

### NoiseRemoval Objects

```python
class NoiseRemoval(AssetNode[NoiseRemovalInputs, NoiseRemovalOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2868)

Noise Removal is a process that involves identifying and eliminating unwanted
random variations or disturbances from an audio signal to enhance the clarity
and quality of the underlying information.

    InputType: audio
    OutputType: audio

### ImageEmbedding Objects

```python
class ImageEmbedding(AssetNode[ImageEmbeddingInputs, ImageEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2914)

Image Embedding is a process that transforms an image into a fixed-dimensional
vector representation, capturing its essential features and enabling efficient
comparison, retrieval, and analysis in various machine learning and computer
vision tasks.

    InputType: image
    OutputType: text

### InverseTextNormalization Objects

```python
class InverseTextNormalization(AssetNode[InverseTextNormalizationInputs,
                                         InverseTextNormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2955)

Inverse Text Normalization is the process of converting spoken or written
language in its normalized form, such as numbers, dates, and abbreviations,
back into their original, more complex or detailed textual representations.

    InputType: text
    OutputType: label

### ImageToVideoGeneration Objects

```python
class ImageToVideoGeneration(AssetNode[ImageToVideoGenerationInputs,
                                       ImageToVideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3001)

The Image To Video Generation function transforms a series of static images
into a cohesive, dynamic video sequence, often incorporating transitions,
effects, and synchronization with audio to create a visually engaging
narrative.

    InputType: image
    OutputType: video

### FacialRecognition Objects

```python
class FacialRecognition(AssetNode[FacialRecognitionInputs,
                                  FacialRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3042)

A facial recognition system is a technology capable of matching a human face
from a digital image or a video frame against a database of faces

    InputType: image
    OutputType: label

### SpeechClassification Objects

```python
class SpeechClassification(AssetNode[SpeechClassificationInputs,
                                     SpeechClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3099)

Categorizes audio clips based on their content, aiding in content organization
and targeted actions.

    InputType: audio
    OutputType: label

### VoiceCloning Objects

```python
class VoiceCloning(AssetNode[VoiceCloningInputs, VoiceCloningOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3174)

Replicates a person&#x27;s voice based on a sample, allowing for the generation of
speech in that person&#x27;s tone and style. Used cautiously due to ethical
considerations.

    InputType: text
    OutputType: audio

### IntentClassification Objects

```python
class IntentClassification(AssetNode[IntentClassificationInputs,
                                     IntentClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3220)

Intent Classification is a natural language processing task that involves
analyzing and categorizing user text input to determine the underlying purpose
or goal behind the communication, such as booking a flight, asking for weather
information, or setting a reminder.

    InputType: text
    OutputType: label

### ImageLabelDetection Objects

```python
class ImageLabelDetection(AssetNode[ImageLabelDetectionInputs,
                                    ImageLabelDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3267)

Identifies objects, themes, or topics within images, useful for image
categorization, search, and recommendation systems.

    InputType: image
    OutputType: label

### Summarization Objects

```python
class Summarization(AssetNode[SummarizationInputs, SummarizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3324)

Text summarization is the process of distilling the most important information
from a source (or sources) to produce an abridged version for a particular user
(or users) and task (or tasks)

    InputType: text
    OutputType: text

### TopicClassification Objects

```python
class TopicClassification(AssetNode[TopicClassificationInputs,
                                    TopicClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3382)

Assigns categories or topics to a piece of text based on its content,
facilitating content organization and retrieval.

    InputType: text
    OutputType: label

### TextDenormalization Objects

```python
class TextDenormalization(AssetNode[TextDenormalizationInputs,
                                    TextDenormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3445)

Converts standardized or normalized text into its original, often more
readable, form. Useful in natural language generation tasks.

    InputType: text
    OutputType: label

### SpeechTranslation Objects

```python
class SpeechTranslation(AssetNode[SpeechTranslationInputs,
                                  SpeechTranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3514)

Speech Translation is a technology that converts spoken language in real-time
from one language to another, enabling seamless communication between speakers
of different languages.

    InputType: audio
    OutputType: text

### SpeechSynthesis Objects

```python
class SpeechSynthesis(AssetNode[SpeechSynthesisInputs,
                                SpeechSynthesisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3590)

Generates human-like speech from written text. Ideal for text-to-speech
applications, audiobooks, and voice assistants.

    InputType: text
    OutputType: audio

### SpeechNonSpeechClassification Objects

```python
class SpeechNonSpeechClassification(
        AssetNode[SpeechNonSpeechClassificationInputs,
                  SpeechNonSpeechClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3647)

Differentiates between speech and non-speech audio segments. Great for editing
software and transcription services to exclude irrelevant audio.

    InputType: audio
    OutputType: label

### ObjectDetection Objects

```python
class ObjectDetection(AssetNode[ObjectDetectionInputs,
                                ObjectDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3686)

Object Detection is a computer vision technology that identifies and locates
objects within an image, typically by drawing bounding boxes around the
detected objects and classifying them into predefined categories.

    InputType: video
    OutputType: text

### AudioReconstruction Objects

```python
class AudioReconstruction(BaseReconstructor[AudioReconstructionInputs,
                                            AudioReconstructionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3726)

Audio Reconstruction is the process of restoring or recreating audio signals
from incomplete, damaged, or degraded recordings to achieve a high-quality,
accurate representation of the original sound.

    InputType: audio
    OutputType: audio

### StyleTransfer Objects

```python
class StyleTransfer(AssetNode[StyleTransferInputs, StyleTransferOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3766)

Style Transfer is a technique in artificial intelligence that applies the
visual style of one image (such as the brushstrokes of a famous painting) to
the content of another image, effectively blending the artistic elements of the
first image with the subject matter of the second.

    InputType: image
    OutputType: image

### SelectSupplierForTranslation Objects

```python
class SelectSupplierForTranslation(
        AssetNode[SelectSupplierForTranslationInputs,
                  SelectSupplierForTranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3813)

Supplier For Translation

InputType: text
OutputType: label

### KeywordExtraction Objects

```python
class KeywordExtraction(AssetNode[KeywordExtractionInputs,
                                  KeywordExtractionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3869)

It helps concise the text and obtain relevant keywords Example use-cases are
finding topics of interest from a news article and identifying the problems
based on customer reviews and so.

    InputType: text
    OutputType: label

### TextGenerationMetricDefault Objects

```python
class TextGenerationMetricDefault(
        BaseMetric[TextGenerationMetricDefaultInputs,
                   TextGenerationMetricDefaultOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3927)

The &quot;Text Generation Metric Default&quot; function provides a standard set of
evaluation metrics for assessing the quality and performance of text generation
models.

    InputType: text
    OutputType: text

### TokenClassification Objects

```python
class TokenClassification(AssetNode[TokenClassificationInputs,
                                    TokenClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3979)

Token-level classification means that each token will be given a label, for
example a part-of-speech tagger will classify each word as one particular part
of speech.

    InputType: text
    OutputType: label

### DepthEstimation Objects

```python
class DepthEstimation(AssetNode[DepthEstimationInputs,
                                DepthEstimationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4025)

Depth estimation is a computational process that determines the distance of
objects from a viewpoint, typically using visual data from cameras or sensors
to create a three-dimensional understanding of a scene.

    InputType: image
    OutputType: text

### InstanceSegmentation Objects

```python
class InstanceSegmentation(AssetNode[InstanceSegmentationInputs,
                                     InstanceSegmentationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4065)

Instance segmentation is a computer vision task that involves detecting and
delineating each distinct object within an image, assigning a unique label and
precise boundary to every individual instance of objects, even if they belong
to the same category.

    InputType: image
    OutputType: label

### ReferencelessTextGenerationMetricDefault Objects

```python
class ReferencelessTextGenerationMetricDefault(
        BaseMetric[ReferencelessTextGenerationMetricDefaultInputs,
                   ReferencelessTextGenerationMetricDefaultOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4118)

The Referenceless Text Generation Metric Default is a function designed to
evaluate the quality of generated text without relying on reference texts for
comparison.

    InputType: text
    OutputType: text

### SubtitlingTranslation Objects

```python
class SubtitlingTranslation(AssetNode[SubtitlingTranslationInputs,
                                      SubtitlingTranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4182)

Converts the text of subtitles from one language to another, ensuring context
and cultural nuances are maintained. Essential for global content distribution.

    InputType: text
    OutputType: text

### VisemeGeneration Objects

```python
class VisemeGeneration(AssetNode[VisemeGenerationInputs,
                                 VisemeGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4239)

Viseme Generation is the process of creating visual representations of
phonemes, which are the distinct units of sound in speech, to synchronize lip
movements with spoken words in animations or virtual avatars.

    InputType: text
    OutputType: label

### MetricAggregation Objects

```python
class MetricAggregation(BaseMetric[MetricAggregationInputs,
                                   MetricAggregationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4279)

Metric Aggregation is a function that computes and summarizes numerical data by
applying statistical operations, such as averaging, summing, or finding the
minimum and maximum values, to provide insights and facilitate analysis of
large datasets.

    InputType: text
    OutputType: text

### LanguageIdentification Objects

```python
class LanguageIdentification(AssetNode[LanguageIdentificationInputs,
                                       LanguageIdentificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4320)

Detects the language in which a given text is written, aiding in multilingual
platforms or content localization.

    InputType: text
    OutputType: text

### AudioForcedAlignment Objects

```python
class AudioForcedAlignment(AssetNode[AudioForcedAlignmentInputs,
                                     AudioForcedAlignmentOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4388)

Synchronizes phonetic and phonological text with the corresponding segments in
an audio file. Useful in linguistic research and detailed transcription tasks.

    InputType: audio
    OutputType: audio

### EmotionDetection Objects

```python
class EmotionDetection(AssetNode[EmotionDetectionInputs,
                                 EmotionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4445)

Identifies human emotions from text or audio, enhancing user experience in
chatbots or customer feedback analysis.

    InputType: text
    OutputType: label

### Diacritization Objects

```python
class Diacritization(AssetNode[DiacritizationInputs, DiacritizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4502)

Adds diacritical marks to text, essential for languages where meaning can
change based on diacritics.

    InputType: text
    OutputType: text

### Loglikelihood Objects

```python
class Loglikelihood(AssetNode[LoglikelihoodInputs, LoglikelihoodOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4541)

The Log Likelihood function measures the probability of observing the given
data under a specific statistical model by taking the natural logarithm of the
likelihood function, thereby transforming the product of probabilities into a
sum, which simplifies the process of optimization and parameter estimation.

    InputType: text
    OutputType: number

### OffensiveLanguageIdentification Objects

```python
class OffensiveLanguageIdentification(
        AssetNode[OffensiveLanguageIdentificationInputs,
                  OffensiveLanguageIdentificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4600)

Detects language or phrases that might be considered offensive, aiding in
content moderation and creating respectful user interactions.

    InputType: text
    OutputType: label

### ExpressionDetection Objects

```python
class ExpressionDetection(AssetNode[ExpressionDetectionInputs,
                                    ExpressionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4639)

Expression Detection is the process of identifying and analyzing facial
expressions to interpret emotions or intentions using AI and computer vision
techniques.

    InputType: text
    OutputType: label

### TextContentModeration Objects

```python
class TextContentModeration(AssetNode[TextContentModerationInputs,
                                      TextContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4697)

Scans and identifies potentially harmful, offensive, or inappropriate textual
content, ensuring safer user environments.

    InputType: text
    OutputType: label

### ReferencelessAudioGenerationMetric Objects

```python
class ReferencelessAudioGenerationMetric(
        BaseMetric[ReferencelessAudioGenerationMetricInputs,
                   ReferencelessAudioGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4748)

The Referenceless Audio Generation Metric is a tool designed to evaluate the
quality of generated audio content without the need for a reference or original
audio sample for comparison.

    InputType: text
    OutputType: text

### TextClassification Objects

```python
class TextClassification(AssetNode[TextClassificationInputs,
                                   TextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4806)

Categorizes text into predefined groups or topics, facilitating content
organization and targeted actions.

    InputType: text
    OutputType: label

### MultiLabelTextClassification Objects

```python
class MultiLabelTextClassification(
        AssetNode[MultiLabelTextClassificationInputs,
                  MultiLabelTextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4851)

Multi Label Text Classification is a natural language processing task where a
given text is analyzed and assigned multiple relevant labels or categories from
a predefined set, allowing for the text to belong to more than one category
simultaneously.

    InputType: text
    OutputType: label

### VideoForcedAlignment Objects

```python
class VideoForcedAlignment(AssetNode[VideoForcedAlignmentInputs,
                                     VideoForcedAlignmentOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4921)

Aligns the transcription of spoken content in a video with its corresponding
timecodes, facilitating subtitle creation.

    InputType: video
    OutputType: video

### SpeechEmbedding Objects

```python
class SpeechEmbedding(AssetNode[SpeechEmbeddingInputs,
                                SpeechEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4978)

Transforms spoken content into a fixed-size vector in a high-dimensional space
that captures the content&#x27;s essence. Facilitates tasks like speech recognition
and speaker verification.

    InputType: audio
    OutputType: text

### AudioTranscriptAnalysis Objects

```python
class AudioTranscriptAnalysis(AssetNode[AudioTranscriptAnalysisInputs,
                                        AudioTranscriptAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5042)

Analyzes transcribed audio data for insights, patterns, or specific information
extraction.

    InputType: audio
    OutputType: text

### SpeakerDiarizationVideo Objects

```python
class SpeakerDiarizationVideo(AssetNode[SpeakerDiarizationVideoInputs,
                                        SpeakerDiarizationVideoOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5099)

Segments a video based on different speakers, identifying when each individual
speaks. Useful for transcriptions and understanding multi-person conversations.

    InputType: video
    OutputType: label

### Paraphrasing Objects

```python
class Paraphrasing(AssetNode[ParaphrasingInputs, ParaphrasingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5144)

Express the meaning of the writer or speaker or something written or spoken
using different words.

    InputType: text
    OutputType: text

### TextSummarization Objects

```python
class TextSummarization(AssetNode[TextSummarizationInputs,
                                  TextSummarizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5201)

Extracts the main points from a larger body of text, producing a concise
summary without losing the primary message.

    InputType: text
    OutputType: text

### SentimentAnalysis Objects

```python
class SentimentAnalysis(AssetNode[SentimentAnalysisInputs,
                                  SentimentAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5258)

Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
piece of text, aiding in understanding user feedback or market sentiment.

    InputType: text
    OutputType: label

### ImageCompression Objects

```python
class ImageCompression(AssetNode[ImageCompressionInputs,
                                 ImageCompressionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5303)

Reduces the size of image files without significantly compromising their visual
quality. Useful for optimizing storage and improving webpage load times.

    InputType: image
    OutputType: image

### TextNormalization Objects

```python
class TextNormalization(AssetNode[TextNormalizationInputs,
                                  TextNormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5354)

Converts unstructured or non-standard textual data into a more readable and
uniform format, dealing with abbreviations, numerals, and other non-standard
words.

    InputType: text
    OutputType: label

### TextGeneration Objects

```python
class TextGeneration(AssetNode[TextGenerationInputs, TextGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5424)

Creates coherent and contextually relevant textual content based on prompts or
certain parameters. Useful for chatbots, content creation, and data
augmentation.

    InputType: text
    OutputType: text

### Translation Objects

```python
class Translation(AssetNode[TranslationInputs, TranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5506)

Converts text from one language to another while maintaining the original
message&#x27;s essence and context. Crucial for global communication.

    InputType: text
    OutputType: text

### TextSpamDetection Objects

```python
class TextSpamDetection(AssetNode[TextSpamDetectionInputs,
                                  TextSpamDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5563)

Identifies and filters out unwanted or irrelevant text content, ideal for
moderating user-generated content or ensuring quality in communication
platforms.

    InputType: text
    OutputType: label

### VideoUnderstanding Objects

```python
class VideoUnderstanding(AssetNode[VideoUnderstandingInputs,
                                   VideoUnderstandingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5627)

Video Understanding is the process of analyzing and interpreting video content
to extract meaningful information, such as identifying objects, actions,
events, and contextual relationships within the footage.

    InputType: video
    OutputType: text

### AudioTranscriptImprovement Objects

```python
class AudioTranscriptImprovement(AssetNode[AudioTranscriptImprovementInputs,
                                           AudioTranscriptImprovementOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5697)

Refines and corrects transcriptions generated from audio data, improving
readability and accuracy.

    InputType: audio
    OutputType: text

### VoiceActivityDetection Objects

```python
class VoiceActivityDetection(BaseSegmentor[VoiceActivityDetectionInputs,
                                           VoiceActivityDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5762)

Determines when a person is speaking in an audio clip. It&#x27;s an essential
preprocessing step for other audio-related tasks.

    InputType: audio
    OutputType: audio

### Subtitling Objects

```python
class Subtitling(AssetNode[SubtitlingInputs, SubtitlingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5831)

Generates accurate subtitles for videos, enhancing accessibility for diverse
audiences.

    InputType: audio
    OutputType: text

### SpeechRecognition Objects

```python
class SpeechRecognition(AssetNode[SpeechRecognitionInputs,
                                  SpeechRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5894)

Converts spoken language into written text. Useful for transcription services,
voice assistants, and applications requiring voice-to-text capabilities.

    InputType: audio
    OutputType: text

### SplitOnLinebreak Objects

```python
class SplitOnLinebreak(BaseSegmentor[SplitOnLinebreakInputs,
                                     SplitOnLinebreakOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5935)

The &quot;Split On Linebreak&quot; function divides a given string into a list of
substrings, using linebreaks (newline characters) as the points of separation.

    InputType: text
    OutputType: text

### Search Objects

```python
class Search(AssetNode[SearchInputs, SearchOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5974)

An algorithm that identifies and returns data or items that match particular
keywords or conditions from a dataset. A fundamental tool for databases and
websites.

    InputType: text
    OutputType: text

### AsrQualityEstimation Objects

```python
class AsrQualityEstimation(AssetNode[AsrQualityEstimationInputs,
                                     AsrQualityEstimationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6020)

ASR Quality Estimation is a process that evaluates the accuracy and reliability
of automatic speech recognition systems by analyzing their performance in
transcribing spoken language into text.

    InputType: text
    OutputType: label

### AsrAgeClassification Objects

```python
class AsrAgeClassification(AssetNode[AsrAgeClassificationInputs,
                                     AsrAgeClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6060)

The ASR Age Classification function is designed to analyze audio recordings of
speech to determine the speaker&#x27;s age group by leveraging automatic speech
recognition (ASR) technology and machine learning algorithms.

    InputType: audio
    OutputType: label

### TextSegmenation Objects

```python
class TextSegmenation(AssetNode[TextSegmenationInputs,
                                TextSegmenationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6106)

Text Segmentation is the process of dividing a continuous text into meaningful
units, such as words, sentences, or topics, to facilitate easier analysis and
understanding.

    InputType: text
    OutputType: text

### ImageManipulation Objects

```python
class ImageManipulation(AssetNode[ImageManipulationInputs,
                                  ImageManipulationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6152)

Image Manipulation refers to the process of altering or enhancing digital
images using various techniques and tools to achieve desired visual effects,
correct imperfections, or transform the image&#x27;s appearance.

    InputType: image
    OutputType: image

### EntitySentimentAnalysis Objects

```python
class EntitySentimentAnalysis(AssetNode[EntitySentimentAnalysisInputs,
                                        EntitySentimentAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6192)

Entity Sentiment Analysis combines both entity analysis and sentiment analysis
and attempts to determine the sentiment (positive or negative) expressed about
entities within the text.

    InputType: text
    OutputType: label

### Guardrails Objects

```python
class Guardrails(AssetNode[GuardrailsInputs, GuardrailsOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6232)

Guardrails are governance rules that enforce security, compliance, and
operational best practices, helping prevent mistakes and detect suspicious
activity

    InputType: text
    OutputType: text

### Pipeline Objects

```python
class Pipeline(DefaultPipeline)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6250)

#### activity\_detection

```python
def activity_detection(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> ActivityDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6252)

detection of the presence or absence of human speech, used in speech
processing.

#### script\_execution

```python
def script_execution(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ScriptExecution
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6259)

Script Execution refers to the process of running a set of programmed
instructions or code within a computing environment, enabling the automated
performance of tasks, calculations, or operations as defined by the script.

#### text\_detection

```python
def text_detection(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> TextDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6267)

detect text regions in the complex background and label them with bounding
boxes.

#### audio\_source\_separation

```python
def audio_source_separation(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> AudioSourceSeparation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6274)

Audio Source Separation is the process of separating a mixture (e.g. a pop band
recording) into isolated sounds from individual sources (e.g. just the lead
vocals).

#### multi\_class\_text\_classification

```python
def multi_class_text_classification(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultiClassTextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6282)

Multi Class Text Classification is a natural language processing task that
involves categorizing a given text into one of several predefined classes or
categories based on its content.

#### image\_impainting

```python
def image_impainting(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ImageImpainting
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6290)

Image inpainting is a process that involves filling in missing or damaged parts
of an image in a way that is visually coherent and seamlessly blends with the
surrounding areas, often using advanced algorithms and techniques to restore
the image to its original or intended appearance.

#### scene\_detection

```python
def scene_detection(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> SceneDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6299)

Scene detection is used for detecting transitions between shots in a video to
split it into basic temporal segments.

#### zero\_shot\_classification

```python
def zero_shot_classification(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ZeroShotClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6306)



#### audio\_intent\_detection

```python
def audio_intent_detection(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AudioIntentDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6312)

Audio Intent Detection is a process that involves analyzing audio signals to
identify and interpret the underlying intentions or purposes behind spoken
words, enabling systems to understand and respond appropriately to human
speech.

#### ocr

```python
def ocr(asset_id: Union[str, asset.Asset], *args, **kwargs) -> Ocr
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6321)

Converts images of typed, handwritten, or printed text into machine-encoded
text. Used in digitizing printed texts for data retrieval.

#### intent\_recognition

```python
def intent_recognition(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> IntentRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6328)

classify the user&#x27;s utterance (provided in varied natural language)  or text
into one of several predefined classes, that is, intents.

#### video\_embedding

```python
def video_embedding(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> VideoEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6335)

Video Embedding is a process that transforms video content into a fixed-
dimensional vector representation, capturing essential features and patterns to
facilitate tasks such as retrieval, classification, and recommendation.

#### extract\_audio\_from\_video

```python
def extract_audio_from_video(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ExtractAudioFromVideo
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6343)

Isolates and extracts audio tracks from video files, aiding in audio analysis
or transcription tasks.

#### image\_captioning

```python
def image_captioning(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ImageCaptioning
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6350)

Image Captioning is a process that involves generating a textual description of
an image, typically using machine learning models to analyze the visual content
and produce coherent and contextually relevant sentences that describe the
objects, actions, and scenes depicted in the image.

#### image\_analysis

```python
def image_analysis(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> ImageAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6359)

Image analysis is the extraction of meaningful information from images

#### benchmark\_scoring\_mt

```python
def benchmark_scoring_mt(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> BenchmarkScoringMt
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6365)

Benchmark Scoring MT is a function designed to evaluate and score machine
translation systems by comparing their output against a set of predefined
benchmarks, thereby assessing their accuracy and performance.

#### speaker\_diarization\_audio

```python
def speaker_diarization_audio(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> SpeakerDiarizationAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6373)

Identifies individual speakers and their respective speech segments within an
audio clip. Ideal for multi-speaker recordings or conference calls.

#### connection

```python
def connection(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> Connection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6380)

Connections are integration that allow you to connect your AI agents to
external tools

#### connector

```python
def connector(asset_id: Union[str, asset.Asset], *args, **kwargs) -> Connector
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6387)

Connectors are integration that allow you to connect your AI agents to external
tools

#### image\_content\_moderation

```python
def image_content_moderation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ImageContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6394)

Detects and filters out inappropriate or harmful images, essential for
platforms with user-generated visual content.

#### image\_colorization

```python
def image_colorization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> ImageColorization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6401)

Image colorization is a process that involves adding color to grayscale images,
transforming them from black-and-white to full-color representations, often
using advanced algorithms and machine learning techniques to predict and apply
the appropriate hues and shades.

#### image\_and\_video\_analysis

```python
def image_and_video_analysis(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ImageAndVideoAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6410)



#### benchmark\_scoring\_asr

```python
def benchmark_scoring_asr(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> BenchmarkScoringAsr
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6416)

Benchmark Scoring ASR is a function that evaluates and compares the performance
of automatic speech recognition systems by analyzing their accuracy, speed, and
other relevant metrics against a standardized set of benchmarks.

#### video\_content\_moderation

```python
def video_content_moderation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> VideoContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6424)

Automatically reviews video content to detect and possibly remove inappropriate
or harmful material. Essential for user-generated content platforms.

#### multilingual\_speech\_recognition

```python
def multilingual_speech_recognition(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultilingualSpeechRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6431)

Multilingual Speech Recognition is a technology that enables the automatic
transcription of spoken language into text across multiple languages, allowing
for seamless communication and understanding in diverse linguistic contexts.

#### topic\_modeling

```python
def topic_modeling(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> TopicModeling
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6439)

Topic modeling is a type of statistical modeling for discovering the abstract
“topics” that occur in a collection of documents.

#### visual\_question\_answering

```python
def visual_question_answering(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> VisualQuestionAnswering
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6446)

Visual Question Answering (VQA) is a task in artificial intelligence that
involves analyzing an image and providing accurate, contextually relevant
answers to questions posed about the visual content of that image.

#### document\_image\_parsing

```python
def document_image_parsing(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> DocumentImageParsing
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6454)

Document Image Parsing is the process of analyzing and converting scanned or
photographed images of documents into structured, machine-readable formats by
identifying and extracting text, layout, and other relevant information.

#### text\_reconstruction

```python
def text_reconstruction(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextReconstruction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6462)

Text Reconstruction is a process that involves piecing together fragmented or
incomplete text data to restore it to its original, coherent form.

#### audio\_emotion\_detection

```python
def audio_emotion_detection(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> AudioEmotionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6469)

Audio Emotion Detection is a technology that analyzes vocal characteristics and
patterns in audio recordings to identify and classify the emotional state of
the speaker.

#### keyword\_spotting

```python
def keyword_spotting(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> KeywordSpotting
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6477)

Keyword Spotting is a function that enables the detection and identification of
specific words or phrases within a stream of audio, often used in voice-
activated systems to trigger actions or commands based on recognized keywords.

#### named\_entity\_recognition

```python
def named_entity_recognition(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> NamedEntityRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6485)

Identifies and classifies named entities (e.g., persons, organizations,
locations) within text. Useful for information extraction, content tagging, and
search enhancements.

#### split\_on\_silence

```python
def split_on_silence(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SplitOnSilence
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6493)

The &quot;Split On Silence&quot; function divides an audio recording into separate
segments based on periods of silence, allowing for easier editing and analysis
of individual sections.

#### document\_information\_extraction

```python
def document_information_extraction(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> DocumentInformationExtraction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6501)

Document Information Extraction is the process of automatically identifying,
extracting, and structuring relevant data from unstructured or semi-structured
documents, such as invoices, receipts, contracts, and forms, to facilitate
easier data management and analysis.

#### text\_to\_video\_generation

```python
def text_to_video_generation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> TextToVideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6510)

Text To Video Generation is a process that converts written descriptions or
scripts into dynamic, visual video content using advanced algorithms and
artificial intelligence.

#### video\_generation

```python
def video_generation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> VideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6518)

Produces video content based on specific inputs or datasets. Can be used for
simulations, animations, or even deepfake detection.

#### text\_to\_image\_generation

```python
def text_to_image_generation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> TextToImageGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6525)

Creates a visual representation based on textual input, turning descriptions
into pictorial forms. Used in creative processes and content generation.

#### dialect\_detection

```python
def dialect_detection(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> DialectDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6532)

Identifies specific dialects within a language, aiding in localized content
creation or user experience personalization.

#### speaker\_recognition

```python
def speaker_recognition(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> SpeakerRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6539)

In speaker identification, an utterance from an unknown speaker is analyzed and
compared with speech models of known speakers.

#### syntax\_analysis

```python
def syntax_analysis(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> SyntaxAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6546)

Is the process of analyzing natural language with the rules of a formal
grammar. Grammatical rules are applied to categories and groups of words, not
individual words. Syntactic analysis basically assigns a semantic structure to
text.

#### question\_answering

```python
def question_answering(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> QuestionAnswering
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6555)

building systems that automatically answer questions posed by humans in a
natural language usually from a given text

#### referenceless\_text\_generation\_metric

```python
def referenceless_text_generation_metric(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessTextGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6562)

The Referenceless Text Generation Metric is a method for evaluating the quality
of generated text without requiring a reference text for comparison, often
leveraging models or algorithms to assess coherence, relevance, and fluency
based on intrinsic properties of the text itself.

#### detect\_language\_from\_text

```python
def detect_language_from_text(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> DetectLanguageFromText
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6571)

Detect Language From Text

#### audio\_language\_identification

```python
def audio_language_identification(asset_id: Union[str, asset.Asset], *args,
                                  **kwargs) -> AudioLanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6577)

Audio Language Identification is a process that involves analyzing an audio
recording to determine the language being spoken.

#### base\_model

```python
def base_model(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> BaseModel
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6584)

The Base-Model function serves as a foundational framework designed to provide
essential features and capabilities upon which more specialized or advanced
models can be built and customized.

#### language\_identification\_audio

```python
def language_identification_audio(asset_id: Union[str, asset.Asset], *args,
                                  **kwargs) -> LanguageIdentificationAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6592)

The Language Identification Audio function analyzes audio input to determine
and identify the language being spoken.

#### multi\_class\_image\_classification

```python
def multi_class_image_classification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> MultiClassImageClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6599)

Multi Class Image Classification is a machine learning task where an algorithm
is trained to categorize images into one of several predefined classes or
categories based on their visual content.

#### semantic\_segmentation

```python
def semantic_segmentation(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> SemanticSegmentation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6607)

Semantic segmentation is a computer vision process that involves classifying
each pixel in an image into a predefined category, effectively partitioning the
image into meaningful segments based on the objects or regions they represent.

#### audio\_generation\_metric

```python
def audio_generation_metric(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> AudioGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6615)

The Audio Generation Metric is a quantitative measure used to evaluate the
quality, accuracy, and overall performance of audio generated by artificial
intelligence systems, often considering factors such as fidelity,
intelligibility, and similarity to human-produced audio.

#### auto\_mask\_generation

```python
def auto_mask_generation(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> AutoMaskGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6624)

Auto-mask generation refers to the automated process of creating masks in image
processing or computer vision, typically for segmentation tasks. A mask is a
binary or multi-class image that labels different parts of an image, usually
separating the foreground (objects of interest) from the background, or
identifying specific object classes in an image.

#### fact\_checking

```python
def fact_checking(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> FactChecking
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6634)

Fact Checking is the process of verifying the accuracy and truthfulness of
information, statements, or claims by cross-referencing with reliable sources
and evidence.

#### text\_to\_audio

```python
def text_to_audio(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> TextToAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6642)

The Text to Audio function converts written text into spoken words, allowing
users to listen to the content instead of reading it.

#### table\_question\_answering

```python
def table_question_answering(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> TableQuestionAnswering
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6649)

The task of question answering over tables is given an input table (or a set of
tables) T and a natural language question Q (a user query), output the correct
answer A

#### classification\_metric

```python
def classification_metric(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> ClassificationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6657)

A Classification Metric is a quantitative measure used to evaluate the quality
and effectiveness of classification models.

#### text\_generation\_metric

```python
def text_generation_metric(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> TextGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6664)

A Text Generation Metric is a quantitative measure used to evaluate the quality
and effectiveness of text produced by natural language processing models, often
assessing aspects such as coherence, relevance, fluency, and adherence to given
prompts or instructions.

#### asr\_gender\_classification

```python
def asr_gender_classification(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> AsrGenderClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6673)

The ASR Gender Classification function analyzes audio recordings to determine
and classify the speaker&#x27;s gender based on their voice characteristics.

#### entity\_linking

```python
def entity_linking(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> EntityLinking
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6680)

Associates identified entities in the text with specific entries in a knowledge
base or database.

#### part\_of\_speech\_tagging

```python
def part_of_speech_tagging(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> PartOfSpeechTagging
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6687)

Part of Speech Tagging is a natural language processing task that involves
assigning each word in a sentence its corresponding part of speech, such as
noun, verb, adjective, or adverb, based on its role and context within the
sentence.

#### fill\_text\_mask

```python
def fill_text_mask(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> FillTextMask
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6696)

Completes missing parts of a text based on the context, ideal for content
generation or data augmentation tasks.

#### text\_embedding

```python
def text_embedding(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> TextEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6703)

Text embedding is a process that converts text into numerical vectors,
capturing the semantic meaning and contextual relationships of words or
phrases, enabling machines to understand and analyze natural language more
effectively.

#### other\_\_multipurpose\_

```python
def other__multipurpose_(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> OtherMultipurpose
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6712)

The &quot;Other (Multipurpose)&quot; function serves as a versatile category designed to
accommodate a wide range of tasks and activities that do not fit neatly into
predefined classifications, offering flexibility and adaptability for various
needs.

#### video\_label\_detection

```python
def video_label_detection(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> VideoLabelDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6721)

Identifies and tags objects, scenes, or activities within a video. Useful for
content indexing and recommendation systems.

#### noise\_removal

```python
def noise_removal(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> NoiseRemoval
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6728)

Noise Removal is a process that involves identifying and eliminating unwanted
random variations or disturbances from an audio signal to enhance the clarity
and quality of the underlying information.

#### image\_embedding

```python
def image_embedding(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> ImageEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6736)

Image Embedding is a process that transforms an image into a fixed-dimensional
vector representation, capturing its essential features and enabling efficient
comparison, retrieval, and analysis in various machine learning and computer
vision tasks.

#### inverse\_text\_normalization

```python
def inverse_text_normalization(asset_id: Union[str, asset.Asset], *args,
                               **kwargs) -> InverseTextNormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6745)

Inverse Text Normalization is the process of converting spoken or written
language in its normalized form, such as numbers, dates, and abbreviations,
back into their original, more complex or detailed textual representations.

#### image\_to\_video\_generation

```python
def image_to_video_generation(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> ImageToVideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6753)

The Image To Video Generation function transforms a series of static images
into a cohesive, dynamic video sequence, often incorporating transitions,
effects, and synchronization with audio to create a visually engaging
narrative.

#### facial\_recognition

```python
def facial_recognition(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> FacialRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6762)

A facial recognition system is a technology capable of matching a human face
from a digital image or a video frame against a database of faces

#### speech\_classification

```python
def speech_classification(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> SpeechClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6769)

Categorizes audio clips based on their content, aiding in content organization
and targeted actions.

#### voice\_cloning

```python
def voice_cloning(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> VoiceCloning
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6776)

Replicates a person&#x27;s voice based on a sample, allowing for the generation of
speech in that person&#x27;s tone and style. Used cautiously due to ethical
considerations.

#### intent\_classification

```python
def intent_classification(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> IntentClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6784)

Intent Classification is a natural language processing task that involves
analyzing and categorizing user text input to determine the underlying purpose
or goal behind the communication, such as booking a flight, asking for weather
information, or setting a reminder.

#### image\_label\_detection

```python
def image_label_detection(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> ImageLabelDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6793)

Identifies objects, themes, or topics within images, useful for image
categorization, search, and recommendation systems.

#### summarization

```python
def summarization(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> Summarization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6800)

Text summarization is the process of distilling the most important information
from a source (or sources) to produce an abridged version for a particular user
(or users) and task (or tasks)

#### topic\_classification

```python
def topic_classification(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> TopicClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6808)

Assigns categories or topics to a piece of text based on its content,
facilitating content organization and retrieval.

#### text\_denormalization

```python
def text_denormalization(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> TextDenormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6815)

Converts standardized or normalized text into its original, often more
readable, form. Useful in natural language generation tasks.

#### speech\_translation

```python
def speech_translation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SpeechTranslation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6822)

Speech Translation is a technology that converts spoken language in real-time
from one language to another, enabling seamless communication between speakers
of different languages.

#### speech\_synthesis

```python
def speech_synthesis(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SpeechSynthesis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6830)

Generates human-like speech from written text. Ideal for text-to-speech
applications, audiobooks, and voice assistants.

#### speech\_non\_speech\_classification

```python
def speech_non_speech_classification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> SpeechNonSpeechClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6837)

Differentiates between speech and non-speech audio segments. Great for editing
software and transcription services to exclude irrelevant audio.

#### object\_detection

```python
def object_detection(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ObjectDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6844)

Object Detection is a computer vision technology that identifies and locates
objects within an image, typically by drawing bounding boxes around the
detected objects and classifying them into predefined categories.

#### audio\_reconstruction

```python
def audio_reconstruction(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> AudioReconstruction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6852)

Audio Reconstruction is the process of restoring or recreating audio signals
from incomplete, damaged, or degraded recordings to achieve a high-quality,
accurate representation of the original sound.

#### style\_transfer

```python
def style_transfer(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> StyleTransfer
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6860)

Style Transfer is a technique in artificial intelligence that applies the
visual style of one image (such as the brushstrokes of a famous painting) to
the content of another image, effectively blending the artistic elements of the
first image with the subject matter of the second.

#### select\_supplier\_for\_translation

```python
def select_supplier_for_translation(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> SelectSupplierForTranslation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6869)

Supplier For Translation

#### keyword\_extraction

```python
def keyword_extraction(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> KeywordExtraction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6875)

It helps concise the text and obtain relevant keywords Example use-cases are
finding topics of interest from a news article and identifying the problems
based on customer reviews and so.

#### text\_generation\_metric\_default

```python
def text_generation_metric_default(asset_id: Union[str, asset.Asset], *args,
                                   **kwargs) -> TextGenerationMetricDefault
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6883)

The &quot;Text Generation Metric Default&quot; function provides a standard set of
evaluation metrics for assessing the quality and performance of text generation
models.

#### token\_classification

```python
def token_classification(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> TokenClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6891)

Token-level classification means that each token will be given a label, for
example a part-of-speech tagger will classify each word as one particular part
of speech.

#### depth\_estimation

```python
def depth_estimation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> DepthEstimation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6899)

Depth estimation is a computational process that determines the distance of
objects from a viewpoint, typically using visual data from cameras or sensors
to create a three-dimensional understanding of a scene.

#### instance\_segmentation

```python
def instance_segmentation(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> InstanceSegmentation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6907)

Instance segmentation is a computer vision task that involves detecting and
delineating each distinct object within an image, assigning a unique label and
precise boundary to every individual instance of objects, even if they belong
to the same category.

#### referenceless\_text\_generation\_metric\_default

```python
def referenceless_text_generation_metric_default(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessTextGenerationMetricDefault
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6916)

The Referenceless Text Generation Metric Default is a function designed to
evaluate the quality of generated text without relying on reference texts for
comparison.

#### subtitling\_translation

```python
def subtitling_translation(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> SubtitlingTranslation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6924)

Converts the text of subtitles from one language to another, ensuring context
and cultural nuances are maintained. Essential for global content distribution.

#### viseme\_generation

```python
def viseme_generation(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> VisemeGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6931)

Viseme Generation is the process of creating visual representations of
phonemes, which are the distinct units of sound in speech, to synchronize lip
movements with spoken words in animations or virtual avatars.

#### metric\_aggregation

```python
def metric_aggregation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> MetricAggregation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6939)

Metric Aggregation is a function that computes and summarizes numerical data by
applying statistical operations, such as averaging, summing, or finding the
minimum and maximum values, to provide insights and facilitate analysis of
large datasets.

#### language\_identification

```python
def language_identification(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> LanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6948)

Detects the language in which a given text is written, aiding in multilingual
platforms or content localization.

#### audio\_forced\_alignment

```python
def audio_forced_alignment(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AudioForcedAlignment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6955)

Synchronizes phonetic and phonological text with the corresponding segments in
an audio file. Useful in linguistic research and detailed transcription tasks.

#### emotion\_detection

```python
def emotion_detection(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> EmotionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6962)

Identifies human emotions from text or audio, enhancing user experience in
chatbots or customer feedback analysis.

#### diacritization

```python
def diacritization(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> Diacritization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6969)

Adds diacritical marks to text, essential for languages where meaning can
change based on diacritics.

#### loglikelihood

```python
def loglikelihood(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> Loglikelihood
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6976)

The Log Likelihood function measures the probability of observing the given
data under a specific statistical model by taking the natural logarithm of the
likelihood function, thereby transforming the product of probabilities into a
sum, which simplifies the process of optimization and parameter estimation.

#### offensive\_language\_identification

```python
def offensive_language_identification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> OffensiveLanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6985)

Detects language or phrases that might be considered offensive, aiding in
content moderation and creating respectful user interactions.

#### expression\_detection

```python
def expression_detection(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> ExpressionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6992)

Expression Detection is the process of identifying and analyzing facial
expressions to interpret emotions or intentions using AI and computer vision
techniques.

#### text\_content\_moderation

```python
def text_content_moderation(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> TextContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7000)

Scans and identifies potentially harmful, offensive, or inappropriate textual
content, ensuring safer user environments.

#### referenceless\_audio\_generation\_metric

```python
def referenceless_audio_generation_metric(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessAudioGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7007)

The Referenceless Audio Generation Metric is a tool designed to evaluate the
quality of generated audio content without the need for a reference or original
audio sample for comparison.

#### text\_classification

```python
def text_classification(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7015)

Categorizes text into predefined groups or topics, facilitating content
organization and targeted actions.

#### multi\_label\_text\_classification

```python
def multi_label_text_classification(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultiLabelTextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7022)

Multi Label Text Classification is a natural language processing task where a
given text is analyzed and assigned multiple relevant labels or categories from
a predefined set, allowing for the text to belong to more than one category
simultaneously.

#### video\_forced\_alignment

```python
def video_forced_alignment(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> VideoForcedAlignment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7031)

Aligns the transcription of spoken content in a video with its corresponding
timecodes, facilitating subtitle creation.

#### speech\_embedding

```python
def speech_embedding(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SpeechEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7038)

Transforms spoken content into a fixed-size vector in a high-dimensional space
that captures the content&#x27;s essence. Facilitates tasks like speech recognition
and speaker verification.

#### audio\_transcript\_analysis

```python
def audio_transcript_analysis(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> AudioTranscriptAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7046)

Analyzes transcribed audio data for insights, patterns, or specific information
extraction.

#### speaker\_diarization\_video

```python
def speaker_diarization_video(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> SpeakerDiarizationVideo
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7053)

Segments a video based on different speakers, identifying when each individual
speaks. Useful for transcriptions and understanding multi-person conversations.

#### paraphrasing

```python
def paraphrasing(asset_id: Union[str, asset.Asset], *args,
                 **kwargs) -> Paraphrasing
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7060)

Express the meaning of the writer or speaker or something written or spoken
using different words.

#### text\_summarization

```python
def text_summarization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> TextSummarization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7067)

Extracts the main points from a larger body of text, producing a concise
summary without losing the primary message.

#### sentiment\_analysis

```python
def sentiment_analysis(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SentimentAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7074)

Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
piece of text, aiding in understanding user feedback or market sentiment.

#### image\_compression

```python
def image_compression(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> ImageCompression
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7081)

Reduces the size of image files without significantly compromising their visual
quality. Useful for optimizing storage and improving webpage load times.

#### text\_normalization

```python
def text_normalization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> TextNormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7088)

Converts unstructured or non-standard textual data into a more readable and
uniform format, dealing with abbreviations, numerals, and other non-standard
words.

#### text\_generation

```python
def text_generation(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> TextGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7096)

Creates coherent and contextually relevant textual content based on prompts or
certain parameters. Useful for chatbots, content creation, and data
augmentation.

#### translation

```python
def translation(asset_id: Union[str, asset.Asset], *args,
                **kwargs) -> Translation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7104)

Converts text from one language to another while maintaining the original
message&#x27;s essence and context. Crucial for global communication.

#### text\_spam\_detection

```python
def text_spam_detection(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextSpamDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7111)

Identifies and filters out unwanted or irrelevant text content, ideal for
moderating user-generated content or ensuring quality in communication
platforms.

#### video\_understanding

```python
def video_understanding(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> VideoUnderstanding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7119)

Video Understanding is the process of analyzing and interpreting video content
to extract meaningful information, such as identifying objects, actions,
events, and contextual relationships within the footage.

#### audio\_transcript\_improvement

```python
def audio_transcript_improvement(asset_id: Union[str, asset.Asset], *args,
                                 **kwargs) -> AudioTranscriptImprovement
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7127)

Refines and corrects transcriptions generated from audio data, improving
readability and accuracy.

#### voice\_activity\_detection

```python
def voice_activity_detection(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> VoiceActivityDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7134)

Determines when a person is speaking in an audio clip. It&#x27;s an essential
preprocessing step for other audio-related tasks.

#### subtitling

```python
def subtitling(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> Subtitling
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7141)

Generates accurate subtitles for videos, enhancing accessibility for diverse
audiences.

#### speech\_recognition

```python
def speech_recognition(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SpeechRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7148)

Converts spoken language into written text. Useful for transcription services,
voice assistants, and applications requiring voice-to-text capabilities.

#### split\_on\_linebreak

```python
def split_on_linebreak(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SplitOnLinebreak
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7155)

The &quot;Split On Linebreak&quot; function divides a given string into a list of
substrings, using linebreaks (newline characters) as the points of separation.

#### search

```python
def search(asset_id: Union[str, asset.Asset], *args, **kwargs) -> Search
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7162)

An algorithm that identifies and returns data or items that match particular
keywords or conditions from a dataset. A fundamental tool for databases and
websites.

#### asr\_quality\_estimation

```python
def asr_quality_estimation(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AsrQualityEstimation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7170)

ASR Quality Estimation is a process that evaluates the accuracy and reliability
of automatic speech recognition systems by analyzing their performance in
transcribing spoken language into text.

#### asr\_age\_classification

```python
def asr_age_classification(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AsrAgeClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7178)

The ASR Age Classification function is designed to analyze audio recordings of
speech to determine the speaker&#x27;s age group by leveraging automatic speech
recognition (ASR) technology and machine learning algorithms.

#### text\_segmenation

```python
def text_segmenation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> TextSegmenation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7186)

Text Segmentation is the process of dividing a continuous text into meaningful
units, such as words, sentences, or topics, to facilitate easier analysis and
understanding.

#### image\_manipulation

```python
def image_manipulation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> ImageManipulation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7194)

Image Manipulation refers to the process of altering or enhancing digital
images using various techniques and tools to achieve desired visual effects,
correct imperfections, or transform the image&#x27;s appearance.

#### entity\_sentiment\_analysis

```python
def entity_sentiment_analysis(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> EntitySentimentAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7202)

Entity Sentiment Analysis combines both entity analysis and sentiment analysis
and attempts to determine the sentiment (positive or negative) expressed about
entities within the text.

#### guardrails

```python
def guardrails(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> Guardrails
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L7210)

Guardrails are governance rules that enforce security, compliance, and
operational best practices, helping prevent mistakes and detect suspicious
activity

