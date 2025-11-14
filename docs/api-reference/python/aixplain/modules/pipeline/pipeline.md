---
sidebar_label: pipeline
title: aixplain.modules.pipeline.pipeline
---

### ObjectDetection Objects

```python
class ObjectDetection(AssetNode[ObjectDetectionInputs,
                                ObjectDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L28)

Object Detection is a computer vision technology that identifies and locates
objects within an image, typically by drawing bounding boxes around the
detected objects and classifying them into predefined categories.

    InputType: video
    OutputType: text

### TextEmbedding Objects

```python
class TextEmbedding(AssetNode[TextEmbeddingInputs, TextEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L68)

Text embedding is a process that converts text into numerical vectors,
capturing the semantic meaning and contextual relationships of words or
phrases, enabling machines to understand and analyze natural language more
effectively.

        InputType: text
        OutputType: text

### SemanticSegmentation Objects

```python
class SemanticSegmentation(AssetNode[SemanticSegmentationInputs,
                                     SemanticSegmentationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L103)

Semantic segmentation is a computer vision process that involves classifying
each pixel in an image into a predefined category, effectively partitioning the
image into meaningful segments based on the objects or regions they represent.

    InputType: image
    OutputType: label

### ReferencelessAudioGenerationMetric Objects

```python
class ReferencelessAudioGenerationMetric(
        BaseMetric[ReferencelessAudioGenerationMetricInputs,
                   ReferencelessAudioGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L141)

The Referenceless Audio Generation Metric is a tool designed to evaluate the
quality of generated audio content without the need for a reference or original
audio sample for comparison.

    InputType: text
    OutputType: text

### ScriptExecution Objects

```python
class ScriptExecution(AssetNode[ScriptExecutionInputs,
                                ScriptExecutionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L177)

Script Execution refers to the process of running a set of programmed
instructions or code within a computing environment, enabling the automated
performance of tasks, calculations, or operations as defined by the script.

    InputType: text
    OutputType: text

### ImageImpainting Objects

```python
class ImageImpainting(AssetNode[ImageImpaintingInputs,
                                ImageImpaintingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L211)

Image inpainting is a process that involves filling in missing or damaged parts
of an image in a way that is visually coherent and seamlessly blends with the
surrounding areas, often using advanced algorithms and techniques to restore
the image to its original or intended appearance.

    InputType: image
    OutputType: image

### ImageEmbedding Objects

```python
class ImageEmbedding(AssetNode[ImageEmbeddingInputs, ImageEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L248)

Image Embedding is a process that transforms an image into a fixed-dimensional
vector representation, capturing its essential features and enabling efficient
comparison, retrieval, and analysis in various machine learning and computer
vision tasks.

    InputType: image
    OutputType: text

### MetricAggregation Objects

```python
class MetricAggregation(BaseMetric[MetricAggregationInputs,
                                   MetricAggregationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L283)

Metric Aggregation is a function that computes and summarizes numerical data by
applying statistical operations, such as averaging, summing, or finding the
minimum and maximum values, to provide insights and facilitate analysis of
large datasets.

    InputType: text
    OutputType: text

### SpeechTranslation Objects

```python
class SpeechTranslation(AssetNode[SpeechTranslationInputs,
                                  SpeechTranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L328)

Speech Translation is a technology that converts spoken language in real-time
from one language to another, enabling seamless communication between speakers
of different languages.

    InputType: audio
    OutputType: text

### DepthEstimation Objects

```python
class DepthEstimation(AssetNode[DepthEstimationInputs,
                                DepthEstimationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L364)

Depth estimation is a computational process that determines the distance of
objects from a viewpoint, typically using visual data from cameras or sensors
to create a three-dimensional understanding of a scene.

    InputType: image
    OutputType: text

### NoiseRemoval Objects

```python
class NoiseRemoval(AssetNode[NoiseRemovalInputs, NoiseRemovalOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L398)

Noise Removal is a process that involves identifying and eliminating unwanted
random variations or disturbances from an audio signal to enhance the clarity
and quality of the underlying information.

        InputType: audio
        OutputType: audio

### Diacritization Objects

```python
class Diacritization(AssetNode[DiacritizationInputs, DiacritizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L438)

Adds diacritical marks to text, essential for languages where meaning can
change based on diacritics.

    InputType: text
    OutputType: text

### AudioTranscriptAnalysis Objects

```python
class AudioTranscriptAnalysis(AssetNode[AudioTranscriptAnalysisInputs,
                                        AudioTranscriptAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L479)

Analyzes transcribed audio data for insights, patterns, or specific information
extraction.

    InputType: audio
    OutputType: text

### ExtractAudioFromVideo Objects

```python
class ExtractAudioFromVideo(AssetNode[ExtractAudioFromVideoInputs,
                                      ExtractAudioFromVideoOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L512)

Isolates and extracts audio tracks from video files, aiding in audio analysis
or transcription tasks.

    InputType: video
    OutputType: audio

### AudioReconstruction Objects

```python
class AudioReconstruction(BaseReconstructor[AudioReconstructionInputs,
                                            AudioReconstructionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L545)

Audio Reconstruction is the process of restoring or recreating audio signals
from incomplete, damaged, or degraded recordings to achieve a high-quality,
accurate representation of the original sound.

    InputType: audio
    OutputType: audio

### ClassificationMetric Objects

```python
class ClassificationMetric(BaseMetric[ClassificationMetricInputs,
                                      ClassificationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L587)

A Classification Metric is a quantitative measure used to evaluate the quality
and effectiveness of classification models.

    InputType: text
    OutputType: text

### TextGenerationMetric Objects

```python
class TextGenerationMetric(BaseMetric[TextGenerationMetricInputs,
                                      TextGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L626)

A Text Generation Metric is a quantitative measure used to evaluate the quality
and effectiveness of text produced by natural language processing models, often
assessing aspects such as coherence, relevance, fluency, and adherence to given
prompts or instructions.

        InputType: text
        OutputType: text

### TextSpamDetection Objects

```python
class TextSpamDetection(AssetNode[TextSpamDetectionInputs,
                                  TextSpamDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L667)

Identifies and filters out unwanted or irrelevant text content, ideal for
moderating user-generated content or ensuring quality in communication
platforms.

    InputType: text
    OutputType: label

### TextToImageGeneration Objects

```python
class TextToImageGeneration(AssetNode[TextToImageGenerationInputs,
                                      TextToImageGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L701)

Creates a visual representation based on textual input, turning descriptions
into pictorial forms. Used in creative processes and content generation.

    InputType: text
    OutputType: image

### VoiceCloning Objects

```python
class VoiceCloning(AssetNode[VoiceCloningInputs, VoiceCloningOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L746)

Replicates a person&#x27;s voice based on a sample, allowing for the generation of
speech in that person&#x27;s tone and style. Used cautiously due to ethical
considerations.

    InputType: text
    OutputType: audio

### TextSegmenation Objects

```python
class TextSegmenation(AssetNode[TextSegmenationInputs,
                                TextSegmenationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L782)

Text Segmentation is the process of dividing a continuous text into meaningful
units, such as words, sentences, or topics, to facilitate easier analysis and
understanding.

        InputType: text
        OutputType: text

### BenchmarkScoringMt Objects

```python
class BenchmarkScoringMt(AssetNode[BenchmarkScoringMtInputs,
                                   BenchmarkScoringMtOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L820)

Benchmark Scoring MT is a function designed to evaluate and score machine
translation systems by comparing their output against a set of predefined
benchmarks, thereby assessing their accuracy and performance.

    InputType: text
    OutputType: label

### ImageManipulation Objects

```python
class ImageManipulation(AssetNode[ImageManipulationInputs,
                                  ImageManipulationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L856)

Image Manipulation refers to the process of altering or enhancing digital
images using various techniques and tools to achieve desired visual effects,
correct imperfections, or transform the image&#x27;s appearance.

    InputType: image
    OutputType: image

### NamedEntityRecognition Objects

```python
class NamedEntityRecognition(AssetNode[NamedEntityRecognitionInputs,
                                       NamedEntityRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L898)

Identifies and classifies named entities (e.g., persons, organizations,
locations) within text. Useful for information extraction, content tagging, and
search enhancements.

    InputType: text
    OutputType: label

### OffensiveLanguageIdentification Objects

```python
class OffensiveLanguageIdentification(
        AssetNode[OffensiveLanguageIdentificationInputs,
                  OffensiveLanguageIdentificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L938)

Detects language or phrases that might be considered offensive, aiding in
content moderation and creating respectful user interactions.

    InputType: text
    OutputType: label

### Search Objects

```python
class Search(AssetNode[SearchInputs, SearchOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L971)

An algorithm that identifies and returns data or items that match particular
keywords or conditions from a dataset. A fundamental tool for databases and
websites.

    InputType: text
    OutputType: text

### SentimentAnalysis Objects

```python
class SentimentAnalysis(AssetNode[SentimentAnalysisInputs,
                                  SentimentAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1011)

Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
piece of text, aiding in understanding user feedback or market sentiment.

    InputType: text
    OutputType: label

### ImageColorization Objects

```python
class ImageColorization(AssetNode[ImageColorizationInputs,
                                  ImageColorizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1044)

Image colorization is a process that involves adding color to grayscale images,
transforming them from black-and-white to full-color representations, often
using advanced algorithms and machine learning techniques to predict and apply
the appropriate hues and shades.

    InputType: image
    OutputType: image

### SpeechClassification Objects

```python
class SpeechClassification(AssetNode[SpeechClassificationInputs,
                                     SpeechClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1085)

Categorizes audio clips based on their content, aiding in content organization
and targeted actions.

    InputType: audio
    OutputType: label

### DialectDetection Objects

```python
class DialectDetection(AssetNode[DialectDetectionInputs,
                                 DialectDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1120)

Identifies specific dialects within a language, aiding in localized content
creation or user experience personalization.

        InputType: audio
        OutputType: text

### VideoLabelDetection Objects

```python
class VideoLabelDetection(AssetNode[VideoLabelDetectionInputs,
                                    VideoLabelDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1155)

Identifies and tags objects, scenes, or activities within a video. Useful for
content indexing and recommendation systems.

    InputType: video
    OutputType: label

### SpeechSynthesis Objects

```python
class SpeechSynthesis(AssetNode[SpeechSynthesisInputs,
                                SpeechSynthesisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1200)

Generates human-like speech from written text. Ideal for text-to-speech
applications, audiobooks, and voice assistants.

    InputType: text
    OutputType: audio

### SplitOnSilence Objects

```python
class SplitOnSilence(AssetNode[SplitOnSilenceInputs, SplitOnSilenceOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1233)

The &quot;Split On Silence&quot; function divides an audio recording into separate
segments based on periods of silence, allowing for easier editing and analysis
of individual sections.

    InputType: audio
    OutputType: audio

### ExpressionDetection Objects

```python
class ExpressionDetection(AssetNode[ExpressionDetectionInputs,
                                    ExpressionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1267)

Expression Detection is the process of identifying and analyzing facial
expressions to interpret emotions or intentions using AI and computer vision
techniques.

    InputType: text
    OutputType: label

### AutoMaskGeneration Objects

```python
class AutoMaskGeneration(AssetNode[AutoMaskGenerationInputs,
                                   AutoMaskGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1301)

Auto-mask generation refers to the automated process of creating masks in image
processing or computer vision, typically for segmentation tasks. A mask is a
binary or multi-class image that labels different parts of an image, usually
separating the foreground (objects of interest) from the background, or
identifying specific object classes in an image.

    InputType: image
    OutputType: label

### DocumentImageParsing Objects

```python
class DocumentImageParsing(AssetNode[DocumentImageParsingInputs,
                                     DocumentImageParsingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1337)

Document Image Parsing is the process of analyzing and converting scanned or
photographed images of documents into structured, machine-readable formats by
identifying and extracting text, layout, and other relevant information.

    InputType: image
    OutputType: text

### EntityLinking Objects

```python
class EntityLinking(AssetNode[EntityLinkingInputs, EntityLinkingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1375)

Associates identified entities in the text with specific entries in a knowledge
base or database.

    InputType: text
    OutputType: label

### ReferencelessTextGenerationMetricDefault Objects

```python
class ReferencelessTextGenerationMetricDefault(
        BaseMetric[ReferencelessTextGenerationMetricDefaultInputs,
                   ReferencelessTextGenerationMetricDefaultOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1412)

The Referenceless Text Generation Metric Default is a function designed to
evaluate the quality of generated text without relying on reference texts for
comparison.

    InputType: text
    OutputType: text

### FillTextMask Objects

```python
class FillTextMask(AssetNode[FillTextMaskInputs, FillTextMaskOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1454)

Completes missing parts of a text based on the context, ideal for content
generation or data augmentation tasks.

    InputType: text
    OutputType: text

### SubtitlingTranslation Objects

```python
class SubtitlingTranslation(AssetNode[SubtitlingTranslationInputs,
                                      SubtitlingTranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1495)

Converts the text of subtitles from one language to another, ensuring context
and cultural nuances are maintained. Essential for global content distribution.

    InputType: text
    OutputType: text

### InstanceSegmentation Objects

```python
class InstanceSegmentation(AssetNode[InstanceSegmentationInputs,
                                     InstanceSegmentationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1528)

Instance segmentation is a computer vision task that involves detecting and
delineating each distinct object within an image, assigning a unique label and
precise boundary to every individual instance of objects, even if they belong
to the same category.

    InputType: image
    OutputType: label

### VisemeGeneration Objects

```python
class VisemeGeneration(AssetNode[VisemeGenerationInputs,
                                 VisemeGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1569)

Viseme Generation is the process of creating visual representations of
phonemes, which are the distinct units of sound in speech, to synchronize lip
movements with spoken words in animations or virtual avatars.

    InputType: text
    OutputType: label

### AudioGenerationMetric Objects

```python
class AudioGenerationMetric(BaseMetric[AudioGenerationMetricInputs,
                                       AudioGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1609)

The Audio Generation Metric is a quantitative measure used to evaluate the
quality, accuracy, and overall performance of audio generated by artificial
intelligence systems, often considering factors such as fidelity,
intelligibility, and similarity to human-produced audio.

        InputType: text
        OutputType: text

### VideoUnderstanding Objects

```python
class VideoUnderstanding(AssetNode[VideoUnderstandingInputs,
                                   VideoUnderstandingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1652)

Video Understanding is the process of analyzing and interpreting video content
to extract meaningful information, such as identifying objects, actions,
events, and contextual relationships within the footage.

    InputType: video
    OutputType: text

### TextNormalization Objects

```python
class TextNormalization(AssetNode[TextNormalizationInputs,
                                  TextNormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1690)

Converts unstructured or non-standard textual data into a more readable and
uniform format, dealing with abbreviations, numerals, and other non-standard
words.

    InputType: text
    OutputType: label

### AsrQualityEstimation Objects

```python
class AsrQualityEstimation(AssetNode[AsrQualityEstimationInputs,
                                     AsrQualityEstimationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1726)

ASR Quality Estimation is a process that evaluates the accuracy and reliability
of automatic speech recognition systems by analyzing their performance in
transcribing spoken language into text.

    InputType: text
    OutputType: label

### VoiceActivityDetection Objects

```python
class VoiceActivityDetection(BaseSegmentor[VoiceActivityDetectionInputs,
                                           VoiceActivityDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1770)

Determines when a person is speaking in an audio clip. It&#x27;s an essential
preprocessing step for other audio-related tasks.

    InputType: audio
    OutputType: audio

### SpeechNonSpeechClassification Objects

```python
class SpeechNonSpeechClassification(
        AssetNode[SpeechNonSpeechClassificationInputs,
                  SpeechNonSpeechClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1809)

Differentiates between speech and non-speech audio segments. Great for editing
software and transcription services to exclude irrelevant audio.

    InputType: audio
    OutputType: label

### AudioTranscriptImprovement Objects

```python
class AudioTranscriptImprovement(AssetNode[AudioTranscriptImprovementInputs,
                                           AudioTranscriptImprovementOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1852)

Refines and corrects transcriptions generated from audio data, improving
readability and accuracy.

    InputType: audio
    OutputType: text

### TextContentModeration Objects

```python
class TextContentModeration(AssetNode[TextContentModerationInputs,
                                      TextContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1891)

Scans and identifies potentially harmful, offensive, or inappropriate textual
content, ensuring safer user environments.

    InputType: text
    OutputType: label

### EmotionDetection Objects

```python
class EmotionDetection(AssetNode[EmotionDetectionInputs,
                                 EmotionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1930)

Identifies human emotions from text or audio, enhancing user experience in
chatbots or customer feedback analysis.

    InputType: text
    OutputType: label

### AudioForcedAlignment Objects

```python
class AudioForcedAlignment(AssetNode[AudioForcedAlignmentInputs,
                                     AudioForcedAlignmentOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1973)

Synchronizes phonetic and phonological text with the corresponding segments in
an audio file. Useful in linguistic research and detailed transcription tasks.

    InputType: audio
    OutputType: audio

### VideoContentModeration Objects

```python
class VideoContentModeration(AssetNode[VideoContentModerationInputs,
                                       VideoContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2008)

Automatically reviews video content to detect and possibly remove inappropriate
or harmful material. Essential for user-generated content platforms.

    InputType: video
    OutputType: label

### ImageLabelDetection Objects

```python
class ImageLabelDetection(AssetNode[ImageLabelDetectionInputs,
                                    ImageLabelDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2043)

Identifies objects, themes, or topics within images, useful for image
categorization, search, and recommendation systems.

    InputType: image
    OutputType: label

### VideoForcedAlignment Objects

```python
class VideoForcedAlignment(AssetNode[VideoForcedAlignmentInputs,
                                     VideoForcedAlignmentOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2086)

Aligns the transcription of spoken content in a video with its corresponding
timecodes, facilitating subtitle creation.

    InputType: video
    OutputType: video

### TextGeneration Objects

```python
class TextGeneration(AssetNode[TextGenerationInputs, TextGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2127)

Creates coherent and contextually relevant textual content based on prompts or
certain parameters. Useful for chatbots, content creation, and data
augmentation.

    InputType: text
    OutputType: text

### TextClassification Objects

```python
class TextClassification(AssetNode[TextClassificationInputs,
                                   TextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2167)

Categorizes text into predefined groups or topics, facilitating content
organization and targeted actions.

    InputType: text
    OutputType: label

### SpeechEmbedding Objects

```python
class SpeechEmbedding(AssetNode[SpeechEmbeddingInputs,
                                SpeechEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2206)

Transforms spoken content into a fixed-size vector in a high-dimensional space
that captures the content&#x27;s essence. Facilitates tasks like speech recognition
and speaker verification.

    InputType: audio
    OutputType: text

### TopicClassification Objects

```python
class TopicClassification(AssetNode[TopicClassificationInputs,
                                    TopicClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2246)

Assigns categories or topics to a piece of text based on its content,
facilitating content organization and retrieval.

    InputType: text
    OutputType: label

### Translation Objects

```python
class Translation(AssetNode[TranslationInputs, TranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2293)

Converts text from one language to another while maintaining the original
message&#x27;s essence and context. Crucial for global communication.

    InputType: text
    OutputType: text

### SpeechRecognition Objects

```python
class SpeechRecognition(AssetNode[SpeechRecognitionInputs,
                                  SpeechRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2334)

Converts spoken language into written text. Useful for transcription services,
voice assistants, and applications requiring voice-to-text capabilities.

    InputType: audio
    OutputType: text

### Subtitling Objects

```python
class Subtitling(AssetNode[SubtitlingInputs, SubtitlingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2377)

Generates accurate subtitles for videos, enhancing accessibility for diverse
audiences.

    InputType: audio
    OutputType: text

### ImageCaptioning Objects

```python
class ImageCaptioning(AssetNode[ImageCaptioningInputs,
                                ImageCaptioningOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2410)

Image Captioning is a process that involves generating a textual description of
an image, typically using machine learning models to analyze the visual content
and produce coherent and contextually relevant sentences that describe the
objects, actions, and scenes depicted in the image.

    InputType: image
    OutputType: text

### AudioLanguageIdentification Objects

```python
class AudioLanguageIdentification(AssetNode[AudioLanguageIdentificationInputs,
                                            AudioLanguageIdentificationOutputs]
                                  )
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2445)

Audio Language Identification is a process that involves analyzing an audio
recording to determine the language being spoken.

    InputType: audio
    OutputType: label

### VideoEmbedding Objects

```python
class VideoEmbedding(AssetNode[VideoEmbeddingInputs, VideoEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2480)

Video Embedding is a process that transforms video content into a fixed-
dimensional vector representation, capturing essential features and patterns to
facilitate tasks such as retrieval, classification, and recommendation.

    InputType: video
    OutputType: embedding

### AsrAgeClassification Objects

```python
class AsrAgeClassification(AssetNode[AsrAgeClassificationInputs,
                                     AsrAgeClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2514)

The ASR Age Classification function is designed to analyze audio recordings of
speech to determine the speaker&#x27;s age group by leveraging automatic speech
recognition (ASR) technology and machine learning algorithms.

    InputType: audio
    OutputType: label

### AudioIntentDetection Objects

```python
class AudioIntentDetection(AssetNode[AudioIntentDetectionInputs,
                                     AudioIntentDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2548)

Audio Intent Detection is a process that involves analyzing audio signals to
identify and interpret the underlying intentions or purposes behind spoken
words, enabling systems to understand and respond appropriately to human
speech.

    InputType: audio
    OutputType: label

### LanguageIdentification Objects

```python
class LanguageIdentification(AssetNode[LanguageIdentificationInputs,
                                       LanguageIdentificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2583)

Detects the language in which a given text is written, aiding in multilingual
platforms or content localization.

    InputType: text
    OutputType: text

### Ocr Objects

```python
class Ocr(AssetNode[OcrInputs, OcrOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2618)

Converts images of typed, handwritten, or printed text into machine-encoded
text. Used in digitizing printed texts for data retrieval.

    InputType: image
    OutputType: text

### AsrGenderClassification Objects

```python
class AsrGenderClassification(AssetNode[AsrGenderClassificationInputs,
                                        AsrGenderClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2651)

The ASR Gender Classification function analyzes audio recordings to determine
and classify the speaker&#x27;s gender based on their voice characteristics.

    InputType: audio
    OutputType: label

### LanguageIdentificationAudio Objects

```python
class LanguageIdentificationAudio(AssetNode[LanguageIdentificationAudioInputs,
                                            LanguageIdentificationAudioOutputs]
                                  )
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2684)

The Language Identification Audio function analyzes audio input to determine
and identify the language being spoken.

    InputType: audio
    OutputType: label

### BaseModel Objects

```python
class BaseModel(AssetNode[BaseModelInputs, BaseModelOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2719)

The Base-Model function serves as a foundational framework designed to provide
essential features and capabilities upon which more specialized or advanced
models can be built and customized.

    InputType: text
    OutputType: text

### Loglikelihood Objects

```python
class Loglikelihood(AssetNode[LoglikelihoodInputs, LoglikelihoodOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2753)

The Log Likelihood function measures the probability of observing the given
data under a specific statistical model by taking the natural logarithm of the
likelihood function, thereby transforming the product of probabilities into a
sum, which simplifies the process of optimization and parameter estimation.

    InputType: text
    OutputType: number

### ImageToVideoGeneration Objects

```python
class ImageToVideoGeneration(AssetNode[ImageToVideoGenerationInputs,
                                       ImageToVideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2790)

The Image To Video Generation function transforms a series of static images
into a cohesive, dynamic video sequence, often incorporating transitions,
effects, and synchronization with audio to create a visually engaging
narrative.

    InputType: image
    OutputType: video

### PartOfSpeechTagging Objects

```python
class PartOfSpeechTagging(AssetNode[PartOfSpeechTaggingInputs,
                                    PartOfSpeechTaggingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2827)

Part of Speech Tagging is a natural language processing task that involves
assigning each word in a sentence its corresponding part of speech, such as
noun, verb, adjective, or adverb, based on its role and context within the
sentence.

    InputType: text
    OutputType: label

### BenchmarkScoringAsr Objects

```python
class BenchmarkScoringAsr(AssetNode[BenchmarkScoringAsrInputs,
                                    BenchmarkScoringAsrOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2866)

Benchmark Scoring ASR is a function that evaluates and compares the performance
of automatic speech recognition systems by analyzing their accuracy, speed, and
other relevant metrics against a standardized set of benchmarks.

    InputType: audio
    OutputType: label

### VisualQuestionAnswering Objects

```python
class VisualQuestionAnswering(AssetNode[VisualQuestionAnsweringInputs,
                                        VisualQuestionAnsweringOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2904)

Visual Question Answering (VQA) is a task in artificial intelligence that
involves analyzing an image and providing accurate, contextually relevant
answers to questions posed about the visual content of that image.

    InputType: image
    OutputType: video

### DocumentInformationExtraction Objects

```python
class DocumentInformationExtraction(
        AssetNode[DocumentInformationExtractionInputs,
                  DocumentInformationExtractionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2938)

Document Information Extraction is the process of automatically identifying,
extracting, and structuring relevant data from unstructured or semi-structured
documents, such as invoices, receipts, contracts, and forms, to facilitate
easier data management and analysis.

    InputType: image
    OutputType: text

### VideoGeneration Objects

```python
class VideoGeneration(AssetNode[VideoGenerationInputs,
                                VideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2973)

Produces video content based on specific inputs or datasets. Can be used for
simulations, animations, or even deepfake detection.

    InputType: text
    OutputType: video

### MultiClassImageClassification Objects

```python
class MultiClassImageClassification(
        AssetNode[MultiClassImageClassificationInputs,
                  MultiClassImageClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3006)

Multi Class Image Classification is a machine learning task where an algorithm
is trained to categorize images into one of several predefined classes or
categories based on their visual content.

    InputType: image
    OutputType: label

### StyleTransfer Objects

```python
class StyleTransfer(AssetNode[StyleTransferInputs, StyleTransferOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3040)

Style Transfer is a technique in artificial intelligence that applies the
visual style of one image (such as the brushstrokes of a famous painting) to
the content of another image, effectively blending the artistic elements of the
first image with the subject matter of the second.

    InputType: image
    OutputType: image

### MultiClassTextClassification Objects

```python
class MultiClassTextClassification(
        AssetNode[MultiClassTextClassificationInputs,
                  MultiClassTextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3077)

Multi Class Text Classification is a natural language processing task that
involves categorizing a given text into one of several predefined classes or
categories based on its content.

    InputType: text
    OutputType: label

### IntentClassification Objects

```python
class IntentClassification(AssetNode[IntentClassificationInputs,
                                     IntentClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3113)

Intent Classification is a natural language processing task that involves
analyzing and categorizing user text input to determine the underlying purpose
or goal behind the communication, such as booking a flight, asking for weather
information, or setting a reminder.

    InputType: text
    OutputType: label

### MultiLabelTextClassification Objects

```python
class MultiLabelTextClassification(
        AssetNode[MultiLabelTextClassificationInputs,
                  MultiLabelTextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3150)

Multi Label Text Classification is a natural language processing task where a
given text is analyzed and assigned multiple relevant labels or categories from
a predefined set, allowing for the text to belong to more than one category
simultaneously.

    InputType: text
    OutputType: label

### TextReconstruction Objects

```python
class TextReconstruction(BaseReconstructor[TextReconstructionInputs,
                                           TextReconstructionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3185)

Text Reconstruction is a process that involves piecing together fragmented or
incomplete text data to restore it to its original, coherent form.

    InputType: text
    OutputType: text

### FactChecking Objects

```python
class FactChecking(AssetNode[FactCheckingInputs, FactCheckingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3220)

Fact Checking is the process of verifying the accuracy and truthfulness of
information, statements, or claims by cross-referencing with reliable sources
and evidence.

    InputType: text
    OutputType: label

### InverseTextNormalization Objects

```python
class InverseTextNormalization(AssetNode[InverseTextNormalizationInputs,
                                         InverseTextNormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3254)

Inverse Text Normalization is the process of converting spoken or written
language in its normalized form, such as numbers, dates, and abbreviations,
back into their original, more complex or detailed textual representations.

    InputType: text
    OutputType: label

### TextToAudio Objects

```python
class TextToAudio(AssetNode[TextToAudioInputs, TextToAudioOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3290)

The Text to Audio function converts written text into spoken words, allowing
users to listen to the content instead of reading it.

    InputType: text
    OutputType: audio

### ImageCompression Objects

```python
class ImageCompression(AssetNode[ImageCompressionInputs,
                                 ImageCompressionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3325)

Reduces the size of image files without significantly compromising their visual
quality. Useful for optimizing storage and improving webpage load times.

    InputType: image
    OutputType: image

### MultilingualSpeechRecognition Objects

```python
class MultilingualSpeechRecognition(
        AssetNode[MultilingualSpeechRecognitionInputs,
                  MultilingualSpeechRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3360)

Multilingual Speech Recognition is a technology that enables the automatic
transcription of spoken language into text across multiple languages, allowing
for seamless communication and understanding in diverse linguistic contexts.

    InputType: audio
    OutputType: text

### TextGenerationMetricDefault Objects

```python
class TextGenerationMetricDefault(
        BaseMetric[TextGenerationMetricDefaultInputs,
                   TextGenerationMetricDefaultOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3400)

The &quot;Text Generation Metric Default&quot; function provides a standard set of
evaluation metrics for assessing the quality and performance of text generation
models.

    InputType: text
    OutputType: text

### ReferencelessTextGenerationMetric Objects

```python
class ReferencelessTextGenerationMetric(
        BaseMetric[ReferencelessTextGenerationMetricInputs,
                   ReferencelessTextGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3438)

The Referenceless Text Generation Metric is a method for evaluating the quality
of generated text without requiring a reference text for comparison, often
leveraging models or algorithms to assess coherence, relevance, and fluency
based on intrinsic properties of the text itself.

    InputType: text
    OutputType: text

### AudioEmotionDetection Objects

```python
class AudioEmotionDetection(AssetNode[AudioEmotionDetectionInputs,
                                      AudioEmotionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3475)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3509)

Keyword Spotting is a function that enables the detection and identification of
specific words or phrases within a stream of audio, often used in voice-
activated systems to trigger actions or commands based on recognized keywords.

    InputType: audio
    OutputType: label

### TextSummarization Objects

```python
class TextSummarization(AssetNode[TextSummarizationInputs,
                                  TextSummarizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3549)

Extracts the main points from a larger body of text, producing a concise
summary without losing the primary message.

    InputType: text
    OutputType: text

### SplitOnLinebreak Objects

```python
class SplitOnLinebreak(BaseSegmentor[SplitOnLinebreakInputs,
                                     SplitOnLinebreakOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3584)

The &quot;Split On Linebreak&quot; function divides a given string into a list of
substrings, using linebreaks (newline characters) as the points of separation.

    InputType: text
    OutputType: text

### OtherMultipurpose Objects

```python
class OtherMultipurpose(AssetNode[OtherMultipurposeInputs,
                                  OtherMultipurposeOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3619)

The &quot;Other (Multipurpose)&quot; function serves as a versatile category designed to
accommodate a wide range of tasks and activities that do not fit neatly into
predefined classifications, offering flexibility and adaptability for various
needs.

    InputType: text
    OutputType: text

### SpeakerDiarizationAudio Objects

```python
class SpeakerDiarizationAudio(BaseSegmentor[SpeakerDiarizationAudioInputs,
                                            SpeakerDiarizationAudioOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3662)

Identifies individual speakers and their respective speech segments within an
audio clip. Ideal for multi-speaker recordings or conference calls.

    InputType: audio
    OutputType: label

### ImageContentModeration Objects

```python
class ImageContentModeration(AssetNode[ImageContentModerationInputs,
                                       ImageContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3697)

Detects and filters out inappropriate or harmful images, essential for
platforms with user-generated visual content.

    InputType: image
    OutputType: label

### TextDenormalization Objects

```python
class TextDenormalization(AssetNode[TextDenormalizationInputs,
                                    TextDenormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3738)

Converts standardized or normalized text into its original, often more
readable, form. Useful in natural language generation tasks.

    InputType: text
    OutputType: label

### SpeakerDiarizationVideo Objects

```python
class SpeakerDiarizationVideo(AssetNode[SpeakerDiarizationVideoInputs,
                                        SpeakerDiarizationVideoOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3777)

Segments a video based on different speakers, identifying when each individual
speaks. Useful for transcriptions and understanding multi-person conversations.

    InputType: video
    OutputType: label

### TextToVideoGeneration Objects

```python
class TextToVideoGeneration(AssetNode[TextToVideoGenerationInputs,
                                      TextToVideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3812)

Text To Video Generation is a process that converts written descriptions or
scripts into dynamic, visual video content using advanced algorithms and
artificial intelligence.

    InputType: text
    OutputType: video

### Pipeline Objects

```python
class Pipeline(DefaultPipeline)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3830)

#### object\_detection

```python
def object_detection(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ObjectDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3831)

Object Detection is a computer vision technology that identifies and locates
objects within an image, typically by drawing bounding boxes around the
detected objects and classifying them into predefined categories.

#### text\_embedding

```python
def text_embedding(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> TextEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3839)

Text embedding is a process that converts text into numerical vectors,
capturing the semantic meaning and contextual relationships of words or
phrases, enabling machines to understand and analyze natural language more
effectively.

#### semantic\_segmentation

```python
def semantic_segmentation(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> SemanticSegmentation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3848)

Semantic segmentation is a computer vision process that involves classifying
each pixel in an image into a predefined category, effectively partitioning the
image into meaningful segments based on the objects or regions they represent.

#### referenceless\_audio\_generation\_metric

```python
def referenceless_audio_generation_metric(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessAudioGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3856)

The Referenceless Audio Generation Metric is a tool designed to evaluate the
quality of generated audio content without the need for a reference or original
audio sample for comparison.

#### script\_execution

```python
def script_execution(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ScriptExecution
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3866)

Script Execution refers to the process of running a set of programmed
instructions or code within a computing environment, enabling the automated
performance of tasks, calculations, or operations as defined by the script.

#### image\_impainting

```python
def image_impainting(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ImageImpainting
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3874)

Image inpainting is a process that involves filling in missing or damaged parts
of an image in a way that is visually coherent and seamlessly blends with the
surrounding areas, often using advanced algorithms and techniques to restore
the image to its original or intended appearance.

#### image\_embedding

```python
def image_embedding(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> ImageEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3883)

Image Embedding is a process that transforms an image into a fixed-dimensional
vector representation, capturing its essential features and enabling efficient
comparison, retrieval, and analysis in various machine learning and computer
vision tasks.

#### metric\_aggregation

```python
def metric_aggregation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> MetricAggregation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3892)

Metric Aggregation is a function that computes and summarizes numerical data by
applying statistical operations, such as averaging, summing, or finding the
minimum and maximum values, to provide insights and facilitate analysis of
large datasets.

#### speech\_translation

```python
def speech_translation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SpeechTranslation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3901)

Speech Translation is a technology that converts spoken language in real-time
from one language to another, enabling seamless communication between speakers
of different languages.

#### depth\_estimation

```python
def depth_estimation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> DepthEstimation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3909)

Depth estimation is a computational process that determines the distance of
objects from a viewpoint, typically using visual data from cameras or sensors
to create a three-dimensional understanding of a scene.

#### noise\_removal

```python
def noise_removal(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> NoiseRemoval
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3917)

Noise Removal is a process that involves identifying and eliminating unwanted
random variations or disturbances from an audio signal to enhance the clarity
and quality of the underlying information.

#### diacritization

```python
def diacritization(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> Diacritization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3925)

Adds diacritical marks to text, essential for languages where meaning can
change based on diacritics.

#### audio\_transcript\_analysis

```python
def audio_transcript_analysis(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> AudioTranscriptAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3932)

Analyzes transcribed audio data for insights, patterns, or specific information
extraction.

#### extract\_audio\_from\_video

```python
def extract_audio_from_video(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ExtractAudioFromVideo
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3939)

Isolates and extracts audio tracks from video files, aiding in audio analysis
or transcription tasks.

#### audio\_reconstruction

```python
def audio_reconstruction(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> AudioReconstruction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3946)

Audio Reconstruction is the process of restoring or recreating audio signals
from incomplete, damaged, or degraded recordings to achieve a high-quality,
accurate representation of the original sound.

#### classification\_metric

```python
def classification_metric(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> ClassificationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3954)

A Classification Metric is a quantitative measure used to evaluate the quality
and effectiveness of classification models.

#### text\_generation\_metric

```python
def text_generation_metric(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> TextGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3961)

A Text Generation Metric is a quantitative measure used to evaluate the quality
and effectiveness of text produced by natural language processing models, often
assessing aspects such as coherence, relevance, fluency, and adherence to given
prompts or instructions.

#### text\_spam\_detection

```python
def text_spam_detection(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextSpamDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3970)

Identifies and filters out unwanted or irrelevant text content, ideal for
moderating user-generated content or ensuring quality in communication
platforms.

#### text\_to\_image\_generation

```python
def text_to_image_generation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> TextToImageGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3978)

Creates a visual representation based on textual input, turning descriptions
into pictorial forms. Used in creative processes and content generation.

#### voice\_cloning

```python
def voice_cloning(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> VoiceCloning
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3985)

Replicates a person&#x27;s voice based on a sample, allowing for the generation of
speech in that person&#x27;s tone and style. Used cautiously due to ethical
considerations.

#### text\_segmenation

```python
def text_segmenation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> TextSegmenation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3993)

Text Segmentation is the process of dividing a continuous text into meaningful
units, such as words, sentences, or topics, to facilitate easier analysis and
understanding.

#### benchmark\_scoring\_mt

```python
def benchmark_scoring_mt(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> BenchmarkScoringMt
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4001)

Benchmark Scoring MT is a function designed to evaluate and score machine
translation systems by comparing their output against a set of predefined
benchmarks, thereby assessing their accuracy and performance.

#### image\_manipulation

```python
def image_manipulation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> ImageManipulation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4009)

Image Manipulation refers to the process of altering or enhancing digital
images using various techniques and tools to achieve desired visual effects,
correct imperfections, or transform the image&#x27;s appearance.

#### named\_entity\_recognition

```python
def named_entity_recognition(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> NamedEntityRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4017)

Identifies and classifies named entities (e.g., persons, organizations,
locations) within text. Useful for information extraction, content tagging, and
search enhancements.

#### offensive\_language\_identification

```python
def offensive_language_identification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> OffensiveLanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4025)

Detects language or phrases that might be considered offensive, aiding in
content moderation and creating respectful user interactions.

#### search

```python
def search(asset_id: Union[str, asset.Asset], *args, **kwargs) -> Search
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4034)

An algorithm that identifies and returns data or items that match particular
keywords or conditions from a dataset. A fundamental tool for databases and
websites.

#### sentiment\_analysis

```python
def sentiment_analysis(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SentimentAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4042)

Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
piece of text, aiding in understanding user feedback or market sentiment.

#### image\_colorization

```python
def image_colorization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> ImageColorization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4049)

Image colorization is a process that involves adding color to grayscale images,
transforming them from black-and-white to full-color representations, often
using advanced algorithms and machine learning techniques to predict and apply
the appropriate hues and shades.

#### speech\_classification

```python
def speech_classification(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> SpeechClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4058)

Categorizes audio clips based on their content, aiding in content organization
and targeted actions.

#### dialect\_detection

```python
def dialect_detection(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> DialectDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4065)

Identifies specific dialects within a language, aiding in localized content
creation or user experience personalization.

#### video\_label\_detection

```python
def video_label_detection(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> VideoLabelDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4072)

Identifies and tags objects, scenes, or activities within a video. Useful for
content indexing and recommendation systems.

#### speech\_synthesis

```python
def speech_synthesis(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SpeechSynthesis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4079)

Generates human-like speech from written text. Ideal for text-to-speech
applications, audiobooks, and voice assistants.

#### split\_on\_silence

```python
def split_on_silence(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SplitOnSilence
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4086)

The &quot;Split On Silence&quot; function divides an audio recording into separate
segments based on periods of silence, allowing for easier editing and analysis
of individual sections.

#### expression\_detection

```python
def expression_detection(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> ExpressionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4094)

Expression Detection is the process of identifying and analyzing facial
expressions to interpret emotions or intentions using AI and computer vision
techniques.

#### auto\_mask\_generation

```python
def auto_mask_generation(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> AutoMaskGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4102)

Auto-mask generation refers to the automated process of creating masks in image
processing or computer vision, typically for segmentation tasks. A mask is a
binary or multi-class image that labels different parts of an image, usually
separating the foreground (objects of interest) from the background, or
identifying specific object classes in an image.

#### document\_image\_parsing

```python
def document_image_parsing(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> DocumentImageParsing
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4112)

Document Image Parsing is the process of analyzing and converting scanned or
photographed images of documents into structured, machine-readable formats by
identifying and extracting text, layout, and other relevant information.

#### entity\_linking

```python
def entity_linking(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> EntityLinking
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4120)

Associates identified entities in the text with specific entries in a knowledge
base or database.

#### referenceless\_text\_generation\_metric\_default

```python
def referenceless_text_generation_metric_default(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessTextGenerationMetricDefault
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4127)

The Referenceless Text Generation Metric Default is a function designed to
evaluate the quality of generated text without relying on reference texts for
comparison.

#### fill\_text\_mask

```python
def fill_text_mask(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> FillTextMask
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4137)

Completes missing parts of a text based on the context, ideal for content
generation or data augmentation tasks.

#### subtitling\_translation

```python
def subtitling_translation(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> SubtitlingTranslation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4144)

Converts the text of subtitles from one language to another, ensuring context
and cultural nuances are maintained. Essential for global content distribution.

#### instance\_segmentation

```python
def instance_segmentation(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> InstanceSegmentation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4151)

Instance segmentation is a computer vision task that involves detecting and
delineating each distinct object within an image, assigning a unique label and
precise boundary to every individual instance of objects, even if they belong
to the same category.

#### viseme\_generation

```python
def viseme_generation(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> VisemeGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4160)

Viseme Generation is the process of creating visual representations of
phonemes, which are the distinct units of sound in speech, to synchronize lip
movements with spoken words in animations or virtual avatars.

#### audio\_generation\_metric

```python
def audio_generation_metric(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> AudioGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4168)

The Audio Generation Metric is a quantitative measure used to evaluate the
quality, accuracy, and overall performance of audio generated by artificial
intelligence systems, often considering factors such as fidelity,
intelligibility, and similarity to human-produced audio.

#### video\_understanding

```python
def video_understanding(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> VideoUnderstanding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4177)

Video Understanding is the process of analyzing and interpreting video content
to extract meaningful information, such as identifying objects, actions,
events, and contextual relationships within the footage.

#### text\_normalization

```python
def text_normalization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> TextNormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4185)

Converts unstructured or non-standard textual data into a more readable and
uniform format, dealing with abbreviations, numerals, and other non-standard
words.

#### asr\_quality\_estimation

```python
def asr_quality_estimation(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AsrQualityEstimation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4193)

ASR Quality Estimation is a process that evaluates the accuracy and reliability
of automatic speech recognition systems by analyzing their performance in
transcribing spoken language into text.

#### voice\_activity\_detection

```python
def voice_activity_detection(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> VoiceActivityDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4201)

Determines when a person is speaking in an audio clip. It&#x27;s an essential
preprocessing step for other audio-related tasks.

#### speech\_non\_speech\_classification

```python
def speech_non_speech_classification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> SpeechNonSpeechClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4208)

Differentiates between speech and non-speech audio segments. Great for editing
software and transcription services to exclude irrelevant audio.

#### audio\_transcript\_improvement

```python
def audio_transcript_improvement(asset_id: Union[str, asset.Asset], *args,
                                 **kwargs) -> AudioTranscriptImprovement
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4217)

Refines and corrects transcriptions generated from audio data, improving
readability and accuracy.

#### text\_content\_moderation

```python
def text_content_moderation(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> TextContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4224)

Scans and identifies potentially harmful, offensive, or inappropriate textual
content, ensuring safer user environments.

#### emotion\_detection

```python
def emotion_detection(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> EmotionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4231)

Identifies human emotions from text or audio, enhancing user experience in
chatbots or customer feedback analysis.

#### audio\_forced\_alignment

```python
def audio_forced_alignment(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AudioForcedAlignment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4238)

Synchronizes phonetic and phonological text with the corresponding segments in
an audio file. Useful in linguistic research and detailed transcription tasks.

#### video\_content\_moderation

```python
def video_content_moderation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> VideoContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4245)

Automatically reviews video content to detect and possibly remove inappropriate
or harmful material. Essential for user-generated content platforms.

#### image\_label\_detection

```python
def image_label_detection(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> ImageLabelDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4252)

Identifies objects, themes, or topics within images, useful for image
categorization, search, and recommendation systems.

#### video\_forced\_alignment

```python
def video_forced_alignment(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> VideoForcedAlignment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4259)

Aligns the transcription of spoken content in a video with its corresponding
timecodes, facilitating subtitle creation.

#### text\_generation

```python
def text_generation(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> TextGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4266)

Creates coherent and contextually relevant textual content based on prompts or
certain parameters. Useful for chatbots, content creation, and data
augmentation.

#### text\_classification

```python
def text_classification(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4274)

Categorizes text into predefined groups or topics, facilitating content
organization and targeted actions.

#### speech\_embedding

```python
def speech_embedding(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SpeechEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4281)

Transforms spoken content into a fixed-size vector in a high-dimensional space
that captures the content&#x27;s essence. Facilitates tasks like speech recognition
and speaker verification.

#### topic\_classification

```python
def topic_classification(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> TopicClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4289)

Assigns categories or topics to a piece of text based on its content,
facilitating content organization and retrieval.

#### translation

```python
def translation(asset_id: Union[str, asset.Asset], *args,
                **kwargs) -> Translation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4296)

Converts text from one language to another while maintaining the original
message&#x27;s essence and context. Crucial for global communication.

#### speech\_recognition

```python
def speech_recognition(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SpeechRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4303)

Converts spoken language into written text. Useful for transcription services,
voice assistants, and applications requiring voice-to-text capabilities.

#### subtitling

```python
def subtitling(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> Subtitling
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4310)

Generates accurate subtitles for videos, enhancing accessibility for diverse
audiences.

#### image\_captioning

```python
def image_captioning(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ImageCaptioning
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4317)

Image Captioning is a process that involves generating a textual description of
an image, typically using machine learning models to analyze the visual content
and produce coherent and contextually relevant sentences that describe the
objects, actions, and scenes depicted in the image.

#### audio\_language\_identification

```python
def audio_language_identification(asset_id: Union[str, asset.Asset], *args,
                                  **kwargs) -> AudioLanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4326)

Audio Language Identification is a process that involves analyzing an audio
recording to determine the language being spoken.

#### video\_embedding

```python
def video_embedding(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> VideoEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4333)

Video Embedding is a process that transforms video content into a fixed-
dimensional vector representation, capturing essential features and patterns to
facilitate tasks such as retrieval, classification, and recommendation.

#### asr\_age\_classification

```python
def asr_age_classification(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AsrAgeClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4341)

The ASR Age Classification function is designed to analyze audio recordings of
speech to determine the speaker&#x27;s age group by leveraging automatic speech
recognition (ASR) technology and machine learning algorithms.

#### audio\_intent\_detection

```python
def audio_intent_detection(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AudioIntentDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4349)

Audio Intent Detection is a process that involves analyzing audio signals to
identify and interpret the underlying intentions or purposes behind spoken
words, enabling systems to understand and respond appropriately to human
speech.

#### language\_identification

```python
def language_identification(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> LanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4358)

Detects the language in which a given text is written, aiding in multilingual
platforms or content localization.

#### ocr

```python
def ocr(asset_id: Union[str, asset.Asset], *args, **kwargs) -> Ocr
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4365)

Converts images of typed, handwritten, or printed text into machine-encoded
text. Used in digitizing printed texts for data retrieval.

#### asr\_gender\_classification

```python
def asr_gender_classification(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> AsrGenderClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4372)

The ASR Gender Classification function analyzes audio recordings to determine
and classify the speaker&#x27;s gender based on their voice characteristics.

#### language\_identification\_audio

```python
def language_identification_audio(asset_id: Union[str, asset.Asset], *args,
                                  **kwargs) -> LanguageIdentificationAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4379)

The Language Identification Audio function analyzes audio input to determine
and identify the language being spoken.

#### base\_model

```python
def base_model(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> BaseModel
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4386)

The Base-Model function serves as a foundational framework designed to provide
essential features and capabilities upon which more specialized or advanced
models can be built and customized.

#### loglikelihood

```python
def loglikelihood(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> Loglikelihood
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4394)

The Log Likelihood function measures the probability of observing the given
data under a specific statistical model by taking the natural logarithm of the
likelihood function, thereby transforming the product of probabilities into a
sum, which simplifies the process of optimization and parameter estimation.

#### image\_to\_video\_generation

```python
def image_to_video_generation(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> ImageToVideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4403)

The Image To Video Generation function transforms a series of static images
into a cohesive, dynamic video sequence, often incorporating transitions,
effects, and synchronization with audio to create a visually engaging
narrative.

#### part\_of\_speech\_tagging

```python
def part_of_speech_tagging(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> PartOfSpeechTagging
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4412)

Part of Speech Tagging is a natural language processing task that involves
assigning each word in a sentence its corresponding part of speech, such as
noun, verb, adjective, or adverb, based on its role and context within the
sentence.

#### benchmark\_scoring\_asr

```python
def benchmark_scoring_asr(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> BenchmarkScoringAsr
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4421)

Benchmark Scoring ASR is a function that evaluates and compares the performance
of automatic speech recognition systems by analyzing their accuracy, speed, and
other relevant metrics against a standardized set of benchmarks.

#### visual\_question\_answering

```python
def visual_question_answering(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> VisualQuestionAnswering
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4429)

Visual Question Answering (VQA) is a task in artificial intelligence that
involves analyzing an image and providing accurate, contextually relevant
answers to questions posed about the visual content of that image.

#### document\_information\_extraction

```python
def document_information_extraction(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> DocumentInformationExtraction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4437)

Document Information Extraction is the process of automatically identifying,
extracting, and structuring relevant data from unstructured or semi-structured
documents, such as invoices, receipts, contracts, and forms, to facilitate
easier data management and analysis.

#### video\_generation

```python
def video_generation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> VideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4448)

Produces video content based on specific inputs or datasets. Can be used for
simulations, animations, or even deepfake detection.

#### multi\_class\_image\_classification

```python
def multi_class_image_classification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> MultiClassImageClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4455)

Multi Class Image Classification is a machine learning task where an algorithm
is trained to categorize images into one of several predefined classes or
categories based on their visual content.

#### style\_transfer

```python
def style_transfer(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> StyleTransfer
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4465)

Style Transfer is a technique in artificial intelligence that applies the
visual style of one image (such as the brushstrokes of a famous painting) to
the content of another image, effectively blending the artistic elements of the
first image with the subject matter of the second.

#### multi\_class\_text\_classification

```python
def multi_class_text_classification(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultiClassTextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4474)

Multi Class Text Classification is a natural language processing task that
involves categorizing a given text into one of several predefined classes or
categories based on its content.

#### intent\_classification

```python
def intent_classification(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> IntentClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4484)

Intent Classification is a natural language processing task that involves
analyzing and categorizing user text input to determine the underlying purpose
or goal behind the communication, such as booking a flight, asking for weather
information, or setting a reminder.

#### multi\_label\_text\_classification

```python
def multi_label_text_classification(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultiLabelTextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4493)

Multi Label Text Classification is a natural language processing task where a
given text is analyzed and assigned multiple relevant labels or categories from
a predefined set, allowing for the text to belong to more than one category
simultaneously.

#### text\_reconstruction

```python
def text_reconstruction(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextReconstruction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4504)

Text Reconstruction is a process that involves piecing together fragmented or
incomplete text data to restore it to its original, coherent form.

#### fact\_checking

```python
def fact_checking(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> FactChecking
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4511)

Fact Checking is the process of verifying the accuracy and truthfulness of
information, statements, or claims by cross-referencing with reliable sources
and evidence.

#### inverse\_text\_normalization

```python
def inverse_text_normalization(asset_id: Union[str, asset.Asset], *args,
                               **kwargs) -> InverseTextNormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4519)

Inverse Text Normalization is the process of converting spoken or written
language in its normalized form, such as numbers, dates, and abbreviations,
back into their original, more complex or detailed textual representations.

#### text\_to\_audio

```python
def text_to_audio(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> TextToAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4527)

The Text to Audio function converts written text into spoken words, allowing
users to listen to the content instead of reading it.

#### image\_compression

```python
def image_compression(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> ImageCompression
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4534)

Reduces the size of image files without significantly compromising their visual
quality. Useful for optimizing storage and improving webpage load times.

#### multilingual\_speech\_recognition

```python
def multilingual_speech_recognition(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultilingualSpeechRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4541)

Multilingual Speech Recognition is a technology that enables the automatic
transcription of spoken language into text across multiple languages, allowing
for seamless communication and understanding in diverse linguistic contexts.

#### text\_generation\_metric\_default

```python
def text_generation_metric_default(asset_id: Union[str, asset.Asset], *args,
                                   **kwargs) -> TextGenerationMetricDefault
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4551)

The &quot;Text Generation Metric Default&quot; function provides a standard set of
evaluation metrics for assessing the quality and performance of text generation
models.

#### referenceless\_text\_generation\_metric

```python
def referenceless_text_generation_metric(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessTextGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4559)

The Referenceless Text Generation Metric is a method for evaluating the quality
of generated text without requiring a reference text for comparison, often
leveraging models or algorithms to assess coherence, relevance, and fluency
based on intrinsic properties of the text itself.

#### audio\_emotion\_detection

```python
def audio_emotion_detection(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> AudioEmotionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4570)

Audio Emotion Detection is a technology that analyzes vocal characteristics and
patterns in audio recordings to identify and classify the emotional state of
the speaker.

#### keyword\_spotting

```python
def keyword_spotting(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> KeywordSpotting
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4578)

Keyword Spotting is a function that enables the detection and identification of
specific words or phrases within a stream of audio, often used in voice-
activated systems to trigger actions or commands based on recognized keywords.

#### text\_summarization

```python
def text_summarization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> TextSummarization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4586)

Extracts the main points from a larger body of text, producing a concise
summary without losing the primary message.

#### split\_on\_linebreak

```python
def split_on_linebreak(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SplitOnLinebreak
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4593)

The &quot;Split On Linebreak&quot; function divides a given string into a list of
substrings, using linebreaks (newline characters) as the points of separation.

#### other\_\_multipurpose\_

```python
def other__multipurpose_(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> OtherMultipurpose
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4600)

The &quot;Other (Multipurpose)&quot; function serves as a versatile category designed to
accommodate a wide range of tasks and activities that do not fit neatly into
predefined classifications, offering flexibility and adaptability for various
needs.

#### speaker\_diarization\_audio

```python
def speaker_diarization_audio(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> SpeakerDiarizationAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4609)

Identifies individual speakers and their respective speech segments within an
audio clip. Ideal for multi-speaker recordings or conference calls.

#### image\_content\_moderation

```python
def image_content_moderation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ImageContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4616)

Detects and filters out inappropriate or harmful images, essential for
platforms with user-generated visual content.

#### text\_denormalization

```python
def text_denormalization(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> TextDenormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4623)

Converts standardized or normalized text into its original, often more
readable, form. Useful in natural language generation tasks.

#### speaker\_diarization\_video

```python
def speaker_diarization_video(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> SpeakerDiarizationVideo
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4630)

Segments a video based on different speakers, identifying when each individual
speaks. Useful for transcriptions and understanding multi-person conversations.

#### text\_to\_video\_generation

```python
def text_to_video_generation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> TextToVideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4637)

Text To Video Generation is a process that converts written descriptions or
scripts into dynamic, visual video content using advanced algorithms and
artificial intelligence.

