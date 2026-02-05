---
sidebar_label: pipeline
title: aixplain.modules.pipeline.pipeline
---

Auto-generated pipeline module containing node classes and Pipeline factory methods.

### TextNormalizationInputs Objects

```python
class TextNormalizationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L24)

Input parameters for TextNormalization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L31)

Initialize TextNormalizationInputs.

### TextNormalizationOutputs Objects

```python
class TextNormalizationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L39)

Output parameters for TextNormalization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L44)

Initialize TextNormalizationOutputs.

### TextNormalization Objects

```python
class TextNormalization(AssetNode[TextNormalizationInputs,
                                  TextNormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L50)

TextNormalization node.

Converts unstructured or non-standard textual data into a more readable and
uniform format, dealing with abbreviations, numerals, and other non-standard
words.

InputType: text
OutputType: label

### ParaphrasingInputs Objects

```python
class ParaphrasingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L69)

Input parameters for Paraphrasing.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L75)

Initialize ParaphrasingInputs.

### ParaphrasingOutputs Objects

```python
class ParaphrasingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L82)

Output parameters for Paraphrasing.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L87)

Initialize ParaphrasingOutputs.

### Paraphrasing Objects

```python
class Paraphrasing(AssetNode[ParaphrasingInputs, ParaphrasingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L93)

Paraphrasing node.

Express the meaning of the writer or speaker or something written or spoken
using different words.

InputType: text
OutputType: text

### LanguageIdentificationInputs Objects

```python
class LanguageIdentificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L111)

Input parameters for LanguageIdentification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L116)

Initialize LanguageIdentificationInputs.

### LanguageIdentificationOutputs Objects

```python
class LanguageIdentificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L122)

Output parameters for LanguageIdentification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L127)

Initialize LanguageIdentificationOutputs.

### LanguageIdentification Objects

```python
class LanguageIdentification(AssetNode[LanguageIdentificationInputs,
                                       LanguageIdentificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L133)

LanguageIdentification node.

Detects the language in which a given text is written, aiding in multilingual
platforms or content localization.

InputType: text
OutputType: text

### BenchmarkScoringAsrInputs Objects

```python
class BenchmarkScoringAsrInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L151)

Input parameters for BenchmarkScoringAsr.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L158)

Initialize BenchmarkScoringAsrInputs.

### BenchmarkScoringAsrOutputs Objects

```python
class BenchmarkScoringAsrOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L166)

Output parameters for BenchmarkScoringAsr.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L171)

Initialize BenchmarkScoringAsrOutputs.

### BenchmarkScoringAsr Objects

```python
class BenchmarkScoringAsr(AssetNode[BenchmarkScoringAsrInputs,
                                    BenchmarkScoringAsrOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L177)

BenchmarkScoringAsr node.

Benchmark Scoring ASR is a function that evaluates and compares the performance
of automatic speech recognition systems by analyzing their accuracy, speed, and
other relevant metrics against a standardized set of benchmarks.

InputType: audio
OutputType: label

### MultiClassTextClassificationInputs Objects

```python
class MultiClassTextClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L196)

Input parameters for MultiClassTextClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L202)

Initialize MultiClassTextClassificationInputs.

### MultiClassTextClassificationOutputs Objects

```python
class MultiClassTextClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L209)

Output parameters for MultiClassTextClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L214)

Initialize MultiClassTextClassificationOutputs.

### MultiClassTextClassification Objects

```python
class MultiClassTextClassification(
        AssetNode[MultiClassTextClassificationInputs,
                  MultiClassTextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L220)

MultiClassTextClassification node.

Multi Class Text Classification is a natural language processing task that
involves categorizing a given text into one of several predefined classes or
categories based on its content.

InputType: text
OutputType: label

### SpeechEmbeddingInputs Objects

```python
class SpeechEmbeddingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L239)

Input parameters for SpeechEmbedding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L247)

Initialize SpeechEmbeddingInputs.

### SpeechEmbeddingOutputs Objects

```python
class SpeechEmbeddingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L256)

Output parameters for SpeechEmbedding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L261)

Initialize SpeechEmbeddingOutputs.

### SpeechEmbedding Objects

```python
class SpeechEmbedding(AssetNode[SpeechEmbeddingInputs,
                                SpeechEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L267)

SpeechEmbedding node.

Transforms spoken content into a fixed-size vector in a high-dimensional space
that captures the content&#x27;s essence. Facilitates tasks like speech recognition
and speaker verification.

InputType: audio
OutputType: text

### DocumentImageParsingInputs Objects

```python
class DocumentImageParsingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L286)

Input parameters for DocumentImageParsing.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L291)

Initialize DocumentImageParsingInputs.

### DocumentImageParsingOutputs Objects

```python
class DocumentImageParsingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L297)

Output parameters for DocumentImageParsing.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L302)

Initialize DocumentImageParsingOutputs.

### DocumentImageParsing Objects

```python
class DocumentImageParsing(AssetNode[DocumentImageParsingInputs,
                                     DocumentImageParsingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L308)

DocumentImageParsing node.

Document Image Parsing is the process of analyzing and converting scanned or
photographed images of documents into structured, machine-readable formats by
identifying and extracting text, layout, and other relevant information.

InputType: image
OutputType: text

### TranslationInputs Objects

```python
class TranslationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L327)

Input parameters for Translation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L339)

Initialize TranslationInputs.

### TranslationOutputs Objects

```python
class TranslationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L352)

Output parameters for Translation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L357)

Initialize TranslationOutputs.

### Translation Objects

```python
class Translation(AssetNode[TranslationInputs, TranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L363)

Translation node.

Converts text from one language to another while maintaining the original
message&#x27;s essence and context. Crucial for global communication.

InputType: text
OutputType: text

### AudioSourceSeparationInputs Objects

```python
class AudioSourceSeparationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L381)

Input parameters for AudioSourceSeparation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L386)

Initialize AudioSourceSeparationInputs.

### AudioSourceSeparationOutputs Objects

```python
class AudioSourceSeparationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L392)

Output parameters for AudioSourceSeparation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L397)

Initialize AudioSourceSeparationOutputs.

### AudioSourceSeparation Objects

```python
class AudioSourceSeparation(AssetNode[AudioSourceSeparationInputs,
                                      AudioSourceSeparationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L403)

AudioSourceSeparation node.

Audio Source Separation is the process of separating a mixture (e.g. a pop band
recording) into isolated sounds from individual sources (e.g. just the lead
vocals).

InputType: audio
OutputType: audio

### SpeechRecognitionInputs Objects

```python
class SpeechRecognitionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L422)

Input parameters for SpeechRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L431)

Initialize SpeechRecognitionInputs.

### SpeechRecognitionOutputs Objects

```python
class SpeechRecognitionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L441)

Output parameters for SpeechRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L446)

Initialize SpeechRecognitionOutputs.

### SpeechRecognition Objects

```python
class SpeechRecognition(AssetNode[SpeechRecognitionInputs,
                                  SpeechRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L452)

SpeechRecognition node.

Converts spoken language into written text. Useful for transcription services,
voice assistants, and applications requiring voice-to-text capabilities.

InputType: audio
OutputType: text

### KeywordSpottingInputs Objects

```python
class KeywordSpottingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L470)

Input parameters for KeywordSpotting.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L475)

Initialize KeywordSpottingInputs.

### KeywordSpottingOutputs Objects

```python
class KeywordSpottingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L481)

Output parameters for KeywordSpotting.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L486)

Initialize KeywordSpottingOutputs.

### KeywordSpotting Objects

```python
class KeywordSpotting(AssetNode[KeywordSpottingInputs,
                                KeywordSpottingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L492)

KeywordSpotting node.

Keyword Spotting is a function that enables the detection and identification of
specific words or phrases within a stream of audio, often used in voice-
activated systems to trigger actions or commands based on recognized keywords.

InputType: audio
OutputType: label

### PartOfSpeechTaggingInputs Objects

```python
class PartOfSpeechTaggingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L511)

Input parameters for PartOfSpeechTagging.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L517)

Initialize PartOfSpeechTaggingInputs.

### PartOfSpeechTaggingOutputs Objects

```python
class PartOfSpeechTaggingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L524)

Output parameters for PartOfSpeechTagging.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L529)

Initialize PartOfSpeechTaggingOutputs.

### PartOfSpeechTagging Objects

```python
class PartOfSpeechTagging(AssetNode[PartOfSpeechTaggingInputs,
                                    PartOfSpeechTaggingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L535)

PartOfSpeechTagging node.

Part of Speech Tagging is a natural language processing task that involves
assigning each word in a sentence its corresponding part of speech, such as
noun, verb, adjective, or adverb, based on its role and context within the
sentence.

InputType: text
OutputType: label

### ReferencelessAudioGenerationMetricInputs Objects

```python
class ReferencelessAudioGenerationMetricInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L555)

Input parameters for ReferencelessAudioGenerationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L562)

Initialize ReferencelessAudioGenerationMetricInputs.

### ReferencelessAudioGenerationMetricOutputs Objects

```python
class ReferencelessAudioGenerationMetricOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L570)

Output parameters for ReferencelessAudioGenerationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L575)

Initialize ReferencelessAudioGenerationMetricOutputs.

### ReferencelessAudioGenerationMetric Objects

```python
class ReferencelessAudioGenerationMetric(
        BaseMetric[ReferencelessAudioGenerationMetricInputs,
                   ReferencelessAudioGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L581)

ReferencelessAudioGenerationMetric node.

The Referenceless Audio Generation Metric is a tool designed to evaluate the
quality of generated audio content without the need for a reference or original
audio sample for comparison.

InputType: text
OutputType: text

### VoiceActivityDetectionInputs Objects

```python
class VoiceActivityDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L602)

Input parameters for VoiceActivityDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L611)

Initialize VoiceActivityDetectionInputs.

### VoiceActivityDetectionOutputs Objects

```python
class VoiceActivityDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L621)

Output parameters for VoiceActivityDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L627)

Initialize VoiceActivityDetectionOutputs.

### VoiceActivityDetection Objects

```python
class VoiceActivityDetection(BaseSegmentor[VoiceActivityDetectionInputs,
                                           VoiceActivityDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L634)

VoiceActivityDetection node.

Determines when a person is speaking in an audio clip. It&#x27;s an essential
preprocessing step for other audio-related tasks.

InputType: audio
OutputType: audio

### SentimentAnalysisInputs Objects

```python
class SentimentAnalysisInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L652)

Input parameters for SentimentAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L660)

Initialize SentimentAnalysisInputs.

### SentimentAnalysisOutputs Objects

```python
class SentimentAnalysisOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L669)

Output parameters for SentimentAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L674)

Initialize SentimentAnalysisOutputs.

### SentimentAnalysis Objects

```python
class SentimentAnalysis(AssetNode[SentimentAnalysisInputs,
                                  SentimentAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L680)

SentimentAnalysis node.

Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
piece of text, aiding in understanding user feedback or market sentiment.

InputType: text
OutputType: label

### SubtitlingInputs Objects

```python
class SubtitlingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L698)

Input parameters for Subtitling.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L708)

Initialize SubtitlingInputs.

### SubtitlingOutputs Objects

```python
class SubtitlingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L719)

Output parameters for Subtitling.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L724)

Initialize SubtitlingOutputs.

### Subtitling Objects

```python
class Subtitling(AssetNode[SubtitlingInputs, SubtitlingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L730)

Subtitling node.

Generates accurate subtitles for videos, enhancing accessibility for diverse
audiences.

InputType: audio
OutputType: text

### MultiLabelTextClassificationInputs Objects

```python
class MultiLabelTextClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L748)

Input parameters for MultiLabelTextClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L754)

Initialize MultiLabelTextClassificationInputs.

### MultiLabelTextClassificationOutputs Objects

```python
class MultiLabelTextClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L761)

Output parameters for MultiLabelTextClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L766)

Initialize MultiLabelTextClassificationOutputs.

### MultiLabelTextClassification Objects

```python
class MultiLabelTextClassification(
        AssetNode[MultiLabelTextClassificationInputs,
                  MultiLabelTextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L772)

MultiLabelTextClassification node.

Multi Label Text Classification is a natural language processing task where a
given text is analyzed and assigned multiple relevant labels or categories from
a predefined set, allowing for the text to belong to more than one category
simultaneously.

InputType: text
OutputType: label

### VisemeGenerationInputs Objects

```python
class VisemeGenerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L792)

Input parameters for VisemeGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L800)

Initialize VisemeGenerationInputs.

### VisemeGenerationOutputs Objects

```python
class VisemeGenerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L809)

Output parameters for VisemeGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L814)

Initialize VisemeGenerationOutputs.

### VisemeGeneration Objects

```python
class VisemeGeneration(AssetNode[VisemeGenerationInputs,
                                 VisemeGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L820)

VisemeGeneration node.

Viseme Generation is the process of creating visual representations of
phonemes, which are the distinct units of sound in speech, to synchronize lip
movements with spoken words in animations or virtual avatars.

InputType: text
OutputType: label

### TextSegmenationInputs Objects

```python
class TextSegmenationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L839)

Input parameters for TextSegmenation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L845)

Initialize TextSegmenationInputs.

### TextSegmenationOutputs Objects

```python
class TextSegmenationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L852)

Output parameters for TextSegmenation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L857)

Initialize TextSegmenationOutputs.

### TextSegmenation Objects

```python
class TextSegmenation(AssetNode[TextSegmenationInputs,
                                TextSegmenationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L863)

TextSegmenation node.

Text Segmentation is the process of dividing a continuous text into meaningful
units, such as words, sentences, or topics, to facilitate easier analysis and
understanding.

InputType: text
OutputType: text

### ZeroShotClassificationInputs Objects

```python
class ZeroShotClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L882)

Input parameters for ZeroShotClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L889)

Initialize ZeroShotClassificationInputs.

### ZeroShotClassificationOutputs Objects

```python
class ZeroShotClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L897)

Output parameters for ZeroShotClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L902)

Initialize ZeroShotClassificationOutputs.

### ZeroShotClassification Objects

```python
class ZeroShotClassification(AssetNode[ZeroShotClassificationInputs,
                                       ZeroShotClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L908)

ZeroShotClassification node.

InputType: text
OutputType: text

### TextGenerationInputs Objects

```python
class TextGenerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L923)

Input parameters for TextGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L933)

Initialize TextGenerationInputs.

### TextGenerationOutputs Objects

```python
class TextGenerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L944)

Output parameters for TextGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L949)

Initialize TextGenerationOutputs.

### TextGeneration Objects

```python
class TextGeneration(AssetNode[TextGenerationInputs, TextGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L955)

TextGeneration node.

Creates coherent and contextually relevant textual content based on prompts or
certain parameters. Useful for chatbots, content creation, and data
augmentation.

InputType: text
OutputType: text

### AudioIntentDetectionInputs Objects

```python
class AudioIntentDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L974)

Input parameters for AudioIntentDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L979)

Initialize AudioIntentDetectionInputs.

### AudioIntentDetectionOutputs Objects

```python
class AudioIntentDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L985)

Output parameters for AudioIntentDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L990)

Initialize AudioIntentDetectionOutputs.

### AudioIntentDetection Objects

```python
class AudioIntentDetection(AssetNode[AudioIntentDetectionInputs,
                                     AudioIntentDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L996)

AudioIntentDetection node.

Audio Intent Detection is a process that involves analyzing audio signals to
identify and interpret the underlying intentions or purposes behind spoken
words, enabling systems to understand and respond appropriately to human
speech.

InputType: audio
OutputType: label

### EntityLinkingInputs Objects

```python
class EntityLinkingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1016)

Input parameters for EntityLinking.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1023)

Initialize EntityLinkingInputs.

### EntityLinkingOutputs Objects

```python
class EntityLinkingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1031)

Output parameters for EntityLinking.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1036)

Initialize EntityLinkingOutputs.

### EntityLinking Objects

```python
class EntityLinking(AssetNode[EntityLinkingInputs, EntityLinkingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1042)

EntityLinking node.

Associates identified entities in the text with specific entries in a knowledge
base or database.

InputType: text
OutputType: label

### ConnectionInputs Objects

```python
class ConnectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1060)

Input parameters for Connection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1065)

Initialize ConnectionInputs.

### ConnectionOutputs Objects

```python
class ConnectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1071)

Output parameters for Connection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1076)

Initialize ConnectionOutputs.

### Connection Objects

```python
class Connection(AssetNode[ConnectionInputs, ConnectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1082)

Connection node.

Connections are integration that allow you to connect your AI agents to
external tools

InputType: text
OutputType: text

### VisualQuestionAnsweringInputs Objects

```python
class VisualQuestionAnsweringInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1100)

Input parameters for VisualQuestionAnswering.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1107)

Initialize VisualQuestionAnsweringInputs.

### VisualQuestionAnsweringOutputs Objects

```python
class VisualQuestionAnsweringOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1115)

Output parameters for VisualQuestionAnswering.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1120)

Initialize VisualQuestionAnsweringOutputs.

### VisualQuestionAnswering Objects

```python
class VisualQuestionAnswering(AssetNode[VisualQuestionAnsweringInputs,
                                        VisualQuestionAnsweringOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1126)

VisualQuestionAnswering node.

Visual Question Answering (VQA) is a task in artificial intelligence that
involves analyzing an image and providing accurate, contextually relevant
answers to questions posed about the visual content of that image.

InputType: image
OutputType: video

### LoglikelihoodInputs Objects

```python
class LoglikelihoodInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1145)

Input parameters for Loglikelihood.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1150)

Initialize LoglikelihoodInputs.

### LoglikelihoodOutputs Objects

```python
class LoglikelihoodOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1156)

Output parameters for Loglikelihood.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1161)

Initialize LoglikelihoodOutputs.

### Loglikelihood Objects

```python
class Loglikelihood(AssetNode[LoglikelihoodInputs, LoglikelihoodOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1167)

Loglikelihood node.

The Log Likelihood function measures the probability of observing the given
data under a specific statistical model by taking the natural logarithm of the
likelihood function, thereby transforming the product of probabilities into a
sum, which simplifies the process of optimization and parameter estimation.

InputType: text
OutputType: number

### LanguageIdentificationAudioInputs Objects

```python
class LanguageIdentificationAudioInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1187)

Input parameters for LanguageIdentificationAudio.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1192)

Initialize LanguageIdentificationAudioInputs.

### LanguageIdentificationAudioOutputs Objects

```python
class LanguageIdentificationAudioOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1198)

Output parameters for LanguageIdentificationAudio.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1203)

Initialize LanguageIdentificationAudioOutputs.

### LanguageIdentificationAudio Objects

```python
class LanguageIdentificationAudio(AssetNode[LanguageIdentificationAudioInputs,
                                            LanguageIdentificationAudioOutputs]
                                  )
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1209)

LanguageIdentificationAudio node.

The Language Identification Audio function analyzes audio input to determine
and identify the language being spoken.

InputType: audio
OutputType: label

### FactCheckingInputs Objects

```python
class FactCheckingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1227)

Input parameters for FactChecking.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1233)

Initialize FactCheckingInputs.

### FactCheckingOutputs Objects

```python
class FactCheckingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1240)

Output parameters for FactChecking.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1245)

Initialize FactCheckingOutputs.

### FactChecking Objects

```python
class FactChecking(AssetNode[FactCheckingInputs, FactCheckingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1251)

FactChecking node.

Fact Checking is the process of verifying the accuracy and truthfulness of
information, statements, or claims by cross-referencing with reliable sources
and evidence.

InputType: text
OutputType: label

### TableQuestionAnsweringInputs Objects

```python
class TableQuestionAnsweringInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1270)

Input parameters for TableQuestionAnswering.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1276)

Initialize TableQuestionAnsweringInputs.

### TableQuestionAnsweringOutputs Objects

```python
class TableQuestionAnsweringOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1283)

Output parameters for TableQuestionAnswering.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1288)

Initialize TableQuestionAnsweringOutputs.

### TableQuestionAnswering Objects

```python
class TableQuestionAnswering(AssetNode[TableQuestionAnsweringInputs,
                                       TableQuestionAnsweringOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1294)

TableQuestionAnswering node.

The task of question answering over tables is given an input table (or a set of
tables) T and a natural language question Q (a user query), output the correct
answer A

InputType: text
OutputType: text

### SpeechClassificationInputs Objects

```python
class SpeechClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1313)

Input parameters for SpeechClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1321)

Initialize SpeechClassificationInputs.

### SpeechClassificationOutputs Objects

```python
class SpeechClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1330)

Output parameters for SpeechClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1335)

Initialize SpeechClassificationOutputs.

### SpeechClassification Objects

```python
class SpeechClassification(AssetNode[SpeechClassificationInputs,
                                     SpeechClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1341)

SpeechClassification node.

Categorizes audio clips based on their content, aiding in content organization
and targeted actions.

InputType: audio
OutputType: label

### InverseTextNormalizationInputs Objects

```python
class InverseTextNormalizationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1359)

Input parameters for InverseTextNormalization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1364)

Initialize InverseTextNormalizationInputs.

### InverseTextNormalizationOutputs Objects

```python
class InverseTextNormalizationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1370)

Output parameters for InverseTextNormalization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1375)

Initialize InverseTextNormalizationOutputs.

### InverseTextNormalization Objects

```python
class InverseTextNormalization(AssetNode[InverseTextNormalizationInputs,
                                         InverseTextNormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1381)

InverseTextNormalization node.

Inverse Text Normalization is the process of converting spoken or written
language in its normalized form, such as numbers, dates, and abbreviations,
back into their original, more complex or detailed textual representations.

InputType: text
OutputType: label

### MultiClassImageClassificationInputs Objects

```python
class MultiClassImageClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1400)

Input parameters for MultiClassImageClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1405)

Initialize MultiClassImageClassificationInputs.

### MultiClassImageClassificationOutputs Objects

```python
class MultiClassImageClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1411)

Output parameters for MultiClassImageClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1416)

Initialize MultiClassImageClassificationOutputs.

### MultiClassImageClassification Objects

```python
class MultiClassImageClassification(
        AssetNode[MultiClassImageClassificationInputs,
                  MultiClassImageClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1422)

MultiClassImageClassification node.

Multi Class Image Classification is a machine learning task where an algorithm
is trained to categorize images into one of several predefined classes or
categories based on their visual content.

InputType: image
OutputType: label

### AsrGenderClassificationInputs Objects

```python
class AsrGenderClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1443)

Input parameters for AsrGenderClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1448)

Initialize AsrGenderClassificationInputs.

### AsrGenderClassificationOutputs Objects

```python
class AsrGenderClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1454)

Output parameters for AsrGenderClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1459)

Initialize AsrGenderClassificationOutputs.

### AsrGenderClassification Objects

```python
class AsrGenderClassification(AssetNode[AsrGenderClassificationInputs,
                                        AsrGenderClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1465)

AsrGenderClassification node.

The ASR Gender Classification function analyzes audio recordings to determine
and classify the speaker&#x27;s gender based on their voice characteristics.

InputType: audio
OutputType: label

### SummarizationInputs Objects

```python
class SummarizationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1483)

Input parameters for Summarization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1491)

Initialize SummarizationInputs.

### SummarizationOutputs Objects

```python
class SummarizationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1500)

Output parameters for Summarization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1505)

Initialize SummarizationOutputs.

### Summarization Objects

```python
class Summarization(AssetNode[SummarizationInputs, SummarizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1511)

Summarization node.

Text summarization is the process of distilling the most important information
from a source (or sources) to produce an abridged version for a particular user
(or users) and task (or tasks)

InputType: text
OutputType: text

### TopicModelingInputs Objects

```python
class TopicModelingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1530)

Input parameters for TopicModeling.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1537)

Initialize TopicModelingInputs.

### TopicModelingOutputs Objects

```python
class TopicModelingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1545)

Output parameters for TopicModeling.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1550)

Initialize TopicModelingOutputs.

### TopicModeling Objects

```python
class TopicModeling(AssetNode[TopicModelingInputs, TopicModelingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1556)

TopicModeling node.

Topic modeling is a type of statistical modeling for discovering the abstract
“topics” that occur in a collection of documents.

InputType: text
OutputType: label

### AudioReconstructionInputs Objects

```python
class AudioReconstructionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1574)

Input parameters for AudioReconstruction.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1579)

Initialize AudioReconstructionInputs.

### AudioReconstructionOutputs Objects

```python
class AudioReconstructionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1585)

Output parameters for AudioReconstruction.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1590)

Initialize AudioReconstructionOutputs.

### AudioReconstruction Objects

```python
class AudioReconstruction(BaseReconstructor[AudioReconstructionInputs,
                                            AudioReconstructionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1596)

AudioReconstruction node.

Audio Reconstruction is the process of restoring or recreating audio signals
from incomplete, damaged, or degraded recordings to achieve a high-quality,
accurate representation of the original sound.

InputType: audio
OutputType: audio

### TextEmbeddingInputs Objects

```python
class TextEmbeddingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1615)

Input parameters for TextEmbedding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1623)

Initialize TextEmbeddingInputs.

### TextEmbeddingOutputs Objects

```python
class TextEmbeddingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1632)

Output parameters for TextEmbedding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1637)

Initialize TextEmbeddingOutputs.

### TextEmbedding Objects

```python
class TextEmbedding(AssetNode[TextEmbeddingInputs, TextEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1643)

TextEmbedding node.

Text embedding is a process that converts text into numerical vectors,
capturing the semantic meaning and contextual relationships of words or
phrases, enabling machines to understand and analyze natural language more
effectively.

InputType: text
OutputType: text

### DetectLanguageFromTextInputs Objects

```python
class DetectLanguageFromTextInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1663)

Input parameters for DetectLanguageFromText.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1668)

Initialize DetectLanguageFromTextInputs.

### DetectLanguageFromTextOutputs Objects

```python
class DetectLanguageFromTextOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1674)

Output parameters for DetectLanguageFromText.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1679)

Initialize DetectLanguageFromTextOutputs.

### DetectLanguageFromText Objects

```python
class DetectLanguageFromText(AssetNode[DetectLanguageFromTextInputs,
                                       DetectLanguageFromTextOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1685)

DetectLanguageFromText node.

Detect Language From Text

InputType: text
OutputType: label

### ExtractAudioFromVideoInputs Objects

```python
class ExtractAudioFromVideoInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1702)

Input parameters for ExtractAudioFromVideo.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1707)

Initialize ExtractAudioFromVideoInputs.

### ExtractAudioFromVideoOutputs Objects

```python
class ExtractAudioFromVideoOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1713)

Output parameters for ExtractAudioFromVideo.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1718)

Initialize ExtractAudioFromVideoOutputs.

### ExtractAudioFromVideo Objects

```python
class ExtractAudioFromVideo(AssetNode[ExtractAudioFromVideoInputs,
                                      ExtractAudioFromVideoOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1724)

ExtractAudioFromVideo node.

Isolates and extracts audio tracks from video files, aiding in audio analysis
or transcription tasks.

InputType: video
OutputType: audio

### SceneDetectionInputs Objects

```python
class SceneDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1742)

Input parameters for SceneDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1747)

Initialize SceneDetectionInputs.

### SceneDetectionOutputs Objects

```python
class SceneDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1753)

Output parameters for SceneDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1758)

Initialize SceneDetectionOutputs.

### SceneDetection Objects

```python
class SceneDetection(AssetNode[SceneDetectionInputs, SceneDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1764)

SceneDetection node.

Scene detection is used for detecting transitions between shots in a video to
split it into basic temporal segments.

InputType: image
OutputType: text

### TextToImageGenerationInputs Objects

```python
class TextToImageGenerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1782)

Input parameters for TextToImageGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1787)

Initialize TextToImageGenerationInputs.

### TextToImageGenerationOutputs Objects

```python
class TextToImageGenerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1793)

Output parameters for TextToImageGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1798)

Initialize TextToImageGenerationOutputs.

### TextToImageGeneration Objects

```python
class TextToImageGeneration(AssetNode[TextToImageGenerationInputs,
                                      TextToImageGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1804)

TextToImageGeneration node.

Creates a visual representation based on textual input, turning descriptions
into pictorial forms. Used in creative processes and content generation.

InputType: text
OutputType: image

### AutoMaskGenerationInputs Objects

```python
class AutoMaskGenerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1822)

Input parameters for AutoMaskGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1827)

Initialize AutoMaskGenerationInputs.

### AutoMaskGenerationOutputs Objects

```python
class AutoMaskGenerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1833)

Output parameters for AutoMaskGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1838)

Initialize AutoMaskGenerationOutputs.

### AutoMaskGeneration Objects

```python
class AutoMaskGeneration(AssetNode[AutoMaskGenerationInputs,
                                   AutoMaskGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1844)

AutoMaskGeneration node.

Auto-mask generation refers to the automated process of creating masks in image
processing or computer vision, typically for segmentation tasks. A mask is a
binary or multi-class image that labels different parts of an image, usually
separating the foreground (objects of interest) from the background, or
identifying specific object classes in an image.

InputType: image
OutputType: label

### AudioLanguageIdentificationInputs Objects

```python
class AudioLanguageIdentificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1865)

Input parameters for AudioLanguageIdentification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1870)

Initialize AudioLanguageIdentificationInputs.

### AudioLanguageIdentificationOutputs Objects

```python
class AudioLanguageIdentificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1876)

Output parameters for AudioLanguageIdentification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1881)

Initialize AudioLanguageIdentificationOutputs.

### AudioLanguageIdentification Objects

```python
class AudioLanguageIdentification(AssetNode[AudioLanguageIdentificationInputs,
                                            AudioLanguageIdentificationOutputs]
                                  )
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1887)

AudioLanguageIdentification node.

Audio Language Identification is a process that involves analyzing an audio
recording to determine the language being spoken.

InputType: audio
OutputType: label

### FacialRecognitionInputs Objects

```python
class FacialRecognitionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1905)

Input parameters for FacialRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1910)

Initialize FacialRecognitionInputs.

### FacialRecognitionOutputs Objects

```python
class FacialRecognitionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1916)

Output parameters for FacialRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1921)

Initialize FacialRecognitionOutputs.

### FacialRecognition Objects

```python
class FacialRecognition(AssetNode[FacialRecognitionInputs,
                                  FacialRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1927)

FacialRecognition node.

A facial recognition system is a technology capable of matching a human face
from a digital image or a video frame against a database of faces

InputType: image
OutputType: label

### QuestionAnsweringInputs Objects

```python
class QuestionAnsweringInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1945)

Input parameters for QuestionAnswering.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1951)

Initialize QuestionAnsweringInputs.

### QuestionAnsweringOutputs Objects

```python
class QuestionAnsweringOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1958)

Output parameters for QuestionAnswering.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1963)

Initialize QuestionAnsweringOutputs.

### QuestionAnswering Objects

```python
class QuestionAnswering(AssetNode[QuestionAnsweringInputs,
                                  QuestionAnsweringOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1969)

QuestionAnswering node.

building systems that automatically answer questions posed by humans in a
natural language usually from a given text

InputType: text
OutputType: text

### ImageImpaintingInputs Objects

```python
class ImageImpaintingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1987)

Input parameters for ImageImpainting.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1992)

Initialize ImageImpaintingInputs.

### ImageImpaintingOutputs Objects

```python
class ImageImpaintingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L1998)

Output parameters for ImageImpainting.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2003)

Initialize ImageImpaintingOutputs.

### ImageImpainting Objects

```python
class ImageImpainting(AssetNode[ImageImpaintingInputs,
                                ImageImpaintingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2009)

ImageImpainting node.

Image inpainting is a process that involves filling in missing or damaged parts
of an image in a way that is visually coherent and seamlessly blends with the
surrounding areas, often using advanced algorithms and techniques to restore
the image to its original or intended appearance.

InputType: image
OutputType: image

### TextReconstructionInputs Objects

```python
class TextReconstructionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2029)

Input parameters for TextReconstruction.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2034)

Initialize TextReconstructionInputs.

### TextReconstructionOutputs Objects

```python
class TextReconstructionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2040)

Output parameters for TextReconstruction.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2045)

Initialize TextReconstructionOutputs.

### TextReconstruction Objects

```python
class TextReconstruction(BaseReconstructor[TextReconstructionInputs,
                                           TextReconstructionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2051)

TextReconstruction node.

Text Reconstruction is a process that involves piecing together fragmented or
incomplete text data to restore it to its original, coherent form.

InputType: text
OutputType: text

### ScriptExecutionInputs Objects

```python
class ScriptExecutionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2069)

Input parameters for ScriptExecution.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2074)

Initialize ScriptExecutionInputs.

### ScriptExecutionOutputs Objects

```python
class ScriptExecutionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2080)

Output parameters for ScriptExecution.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2085)

Initialize ScriptExecutionOutputs.

### ScriptExecution Objects

```python
class ScriptExecution(AssetNode[ScriptExecutionInputs,
                                ScriptExecutionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2091)

ScriptExecution node.

Script Execution refers to the process of running a set of programmed
instructions or code within a computing environment, enabling the automated
performance of tasks, calculations, or operations as defined by the script.

InputType: text
OutputType: text

### SemanticSegmentationInputs Objects

```python
class SemanticSegmentationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2110)

Input parameters for SemanticSegmentation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2115)

Initialize SemanticSegmentationInputs.

### SemanticSegmentationOutputs Objects

```python
class SemanticSegmentationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2121)

Output parameters for SemanticSegmentation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2126)

Initialize SemanticSegmentationOutputs.

### SemanticSegmentation Objects

```python
class SemanticSegmentation(AssetNode[SemanticSegmentationInputs,
                                     SemanticSegmentationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2132)

SemanticSegmentation node.

Semantic segmentation is a computer vision process that involves classifying
each pixel in an image into a predefined category, effectively partitioning the
image into meaningful segments based on the objects or regions they represent.

InputType: image
OutputType: label

### AudioEmotionDetectionInputs Objects

```python
class AudioEmotionDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2151)

Input parameters for AudioEmotionDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2156)

Initialize AudioEmotionDetectionInputs.

### AudioEmotionDetectionOutputs Objects

```python
class AudioEmotionDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2162)

Output parameters for AudioEmotionDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2167)

Initialize AudioEmotionDetectionOutputs.

### AudioEmotionDetection Objects

```python
class AudioEmotionDetection(AssetNode[AudioEmotionDetectionInputs,
                                      AudioEmotionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2173)

AudioEmotionDetection node.

Audio Emotion Detection is a technology that analyzes vocal characteristics and
patterns in audio recordings to identify and classify the emotional state of
the speaker.

InputType: audio
OutputType: label

### ImageCaptioningInputs Objects

```python
class ImageCaptioningInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2192)

Input parameters for ImageCaptioning.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2197)

Initialize ImageCaptioningInputs.

### ImageCaptioningOutputs Objects

```python
class ImageCaptioningOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2203)

Output parameters for ImageCaptioning.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2208)

Initialize ImageCaptioningOutputs.

### ImageCaptioning Objects

```python
class ImageCaptioning(AssetNode[ImageCaptioningInputs,
                                ImageCaptioningOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2214)

ImageCaptioning node.

Image Captioning is a process that involves generating a textual description of
an image, typically using machine learning models to analyze the visual content
and produce coherent and contextually relevant sentences that describe the
objects, actions, and scenes depicted in the image.

InputType: image
OutputType: text

### SplitOnLinebreakInputs Objects

```python
class SplitOnLinebreakInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2234)

Input parameters for SplitOnLinebreak.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2239)

Initialize SplitOnLinebreakInputs.

### SplitOnLinebreakOutputs Objects

```python
class SplitOnLinebreakOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2245)

Output parameters for SplitOnLinebreak.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2251)

Initialize SplitOnLinebreakOutputs.

### SplitOnLinebreak Objects

```python
class SplitOnLinebreak(BaseSegmentor[SplitOnLinebreakInputs,
                                     SplitOnLinebreakOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2258)

SplitOnLinebreak node.

The &quot;Split On Linebreak&quot; function divides a given string into a list of
substrings, using linebreaks (newline characters) as the points of separation.

InputType: text
OutputType: text

### StyleTransferInputs Objects

```python
class StyleTransferInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2276)

Input parameters for StyleTransfer.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2281)

Initialize StyleTransferInputs.

### StyleTransferOutputs Objects

```python
class StyleTransferOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2287)

Output parameters for StyleTransfer.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2292)

Initialize StyleTransferOutputs.

### StyleTransfer Objects

```python
class StyleTransfer(AssetNode[StyleTransferInputs, StyleTransferOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2298)

StyleTransfer node.

Style Transfer is a technique in artificial intelligence that applies the
visual style of one image (such as the brushstrokes of a famous painting) to
the content of another image, effectively blending the artistic elements of the
first image with the subject matter of the second.

InputType: image
OutputType: image

### BaseModelInputs Objects

```python
class BaseModelInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2318)

Input parameters for BaseModel.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2324)

Initialize BaseModelInputs.

### BaseModelOutputs Objects

```python
class BaseModelOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2331)

Output parameters for BaseModel.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2336)

Initialize BaseModelOutputs.

### BaseModel Objects

```python
class BaseModel(AssetNode[BaseModelInputs, BaseModelOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2342)

BaseModel node.

The Base-Model function serves as a foundational framework designed to provide
essential features and capabilities upon which more specialized or advanced
models can be built and customized.

InputType: text
OutputType: text

### ImageManipulationInputs Objects

```python
class ImageManipulationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2361)

Input parameters for ImageManipulation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2367)

Initialize ImageManipulationInputs.

### ImageManipulationOutputs Objects

```python
class ImageManipulationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2374)

Output parameters for ImageManipulation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2379)

Initialize ImageManipulationOutputs.

### ImageManipulation Objects

```python
class ImageManipulation(AssetNode[ImageManipulationInputs,
                                  ImageManipulationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2385)

ImageManipulation node.

Image Manipulation refers to the process of altering or enhancing digital
images using various techniques and tools to achieve desired visual effects,
correct imperfections, or transform the image&#x27;s appearance.

InputType: image
OutputType: image

### VideoEmbeddingInputs Objects

```python
class VideoEmbeddingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2404)

Input parameters for VideoEmbedding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2410)

Initialize VideoEmbeddingInputs.

### VideoEmbeddingOutputs Objects

```python
class VideoEmbeddingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2417)

Output parameters for VideoEmbedding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2422)

Initialize VideoEmbeddingOutputs.

### VideoEmbedding Objects

```python
class VideoEmbedding(AssetNode[VideoEmbeddingInputs, VideoEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2428)

VideoEmbedding node.

Video Embedding is a process that transforms video content into a fixed-
dimensional vector representation, capturing essential features and patterns to
facilitate tasks such as retrieval, classification, and recommendation.

InputType: video
OutputType: embedding

### DialectDetectionInputs Objects

```python
class DialectDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2447)

Input parameters for DialectDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2453)

Initialize DialectDetectionInputs.

### DialectDetectionOutputs Objects

```python
class DialectDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2460)

Output parameters for DialectDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2465)

Initialize DialectDetectionOutputs.

### DialectDetection Objects

```python
class DialectDetection(AssetNode[DialectDetectionInputs,
                                 DialectDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2471)

DialectDetection node.

Identifies specific dialects within a language, aiding in localized content
creation or user experience personalization.

InputType: audio
OutputType: text

### FillTextMaskInputs Objects

```python
class FillTextMaskInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2489)

Input parameters for FillTextMask.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2497)

Initialize FillTextMaskInputs.

### FillTextMaskOutputs Objects

```python
class FillTextMaskOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2506)

Output parameters for FillTextMask.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2511)

Initialize FillTextMaskOutputs.

### FillTextMask Objects

```python
class FillTextMask(AssetNode[FillTextMaskInputs, FillTextMaskOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2517)

FillTextMask node.

Completes missing parts of a text based on the context, ideal for content
generation or data augmentation tasks.

InputType: text
OutputType: text

### ActivityDetectionInputs Objects

```python
class ActivityDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2535)

Input parameters for ActivityDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2540)

Initialize ActivityDetectionInputs.

### ActivityDetectionOutputs Objects

```python
class ActivityDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2546)

Output parameters for ActivityDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2551)

Initialize ActivityDetectionOutputs.

### ActivityDetection Objects

```python
class ActivityDetection(AssetNode[ActivityDetectionInputs,
                                  ActivityDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2557)

ActivityDetection node.

detection of the presence or absence of human speech, used in speech
processing.

InputType: audio
OutputType: label

### SelectSupplierForTranslationInputs Objects

```python
class SelectSupplierForTranslationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2575)

Input parameters for SelectSupplierForTranslation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2581)

Initialize SelectSupplierForTranslationInputs.

### SelectSupplierForTranslationOutputs Objects

```python
class SelectSupplierForTranslationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2588)

Output parameters for SelectSupplierForTranslation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2593)

Initialize SelectSupplierForTranslationOutputs.

### SelectSupplierForTranslation Objects

```python
class SelectSupplierForTranslation(
        AssetNode[SelectSupplierForTranslationInputs,
                  SelectSupplierForTranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2599)

SelectSupplierForTranslation node.

Supplier For Translation

InputType: text
OutputType: label

### ExpressionDetectionInputs Objects

```python
class ExpressionDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2616)

Input parameters for ExpressionDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2621)

Initialize ExpressionDetectionInputs.

### ExpressionDetectionOutputs Objects

```python
class ExpressionDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2627)

Output parameters for ExpressionDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2632)

Initialize ExpressionDetectionOutputs.

### ExpressionDetection Objects

```python
class ExpressionDetection(AssetNode[ExpressionDetectionInputs,
                                    ExpressionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2638)

ExpressionDetection node.

Expression Detection is the process of identifying and analyzing facial
expressions to interpret emotions or intentions using AI and computer vision
techniques.

InputType: text
OutputType: label

### VideoGenerationInputs Objects

```python
class VideoGenerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2657)

Input parameters for VideoGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2662)

Initialize VideoGenerationInputs.

### VideoGenerationOutputs Objects

```python
class VideoGenerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2668)

Output parameters for VideoGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2673)

Initialize VideoGenerationOutputs.

### VideoGeneration Objects

```python
class VideoGeneration(AssetNode[VideoGenerationInputs,
                                VideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2679)

VideoGeneration node.

Produces video content based on specific inputs or datasets. Can be used for
simulations, animations, or even deepfake detection.

InputType: text
OutputType: video

### ImageAnalysisInputs Objects

```python
class ImageAnalysisInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2697)

Input parameters for ImageAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2702)

Initialize ImageAnalysisInputs.

### ImageAnalysisOutputs Objects

```python
class ImageAnalysisOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2708)

Output parameters for ImageAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2713)

Initialize ImageAnalysisOutputs.

### ImageAnalysis Objects

```python
class ImageAnalysis(AssetNode[ImageAnalysisInputs, ImageAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2719)

ImageAnalysis node.

Image analysis is the extraction of meaningful information from images

InputType: image
OutputType: label

### NoiseRemovalInputs Objects

```python
class NoiseRemovalInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2736)

Input parameters for NoiseRemoval.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2741)

Initialize NoiseRemovalInputs.

### NoiseRemovalOutputs Objects

```python
class NoiseRemovalOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2747)

Output parameters for NoiseRemoval.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2752)

Initialize NoiseRemovalOutputs.

### NoiseRemoval Objects

```python
class NoiseRemoval(AssetNode[NoiseRemovalInputs, NoiseRemovalOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2758)

NoiseRemoval node.

Noise Removal is a process that involves identifying and eliminating unwanted
random variations or disturbances from an audio signal to enhance the clarity
and quality of the underlying information.

InputType: audio
OutputType: audio

### ImageAndVideoAnalysisInputs Objects

```python
class ImageAndVideoAnalysisInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2777)

Input parameters for ImageAndVideoAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2782)

Initialize ImageAndVideoAnalysisInputs.

### ImageAndVideoAnalysisOutputs Objects

```python
class ImageAndVideoAnalysisOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2788)

Output parameters for ImageAndVideoAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2793)

Initialize ImageAndVideoAnalysisOutputs.

### ImageAndVideoAnalysis Objects

```python
class ImageAndVideoAnalysis(AssetNode[ImageAndVideoAnalysisInputs,
                                      ImageAndVideoAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2799)

ImageAndVideoAnalysis node.

InputType: image
OutputType: text

### KeywordExtractionInputs Objects

```python
class KeywordExtractionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2814)

Input parameters for KeywordExtraction.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2822)

Initialize KeywordExtractionInputs.

### KeywordExtractionOutputs Objects

```python
class KeywordExtractionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2831)

Output parameters for KeywordExtraction.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2836)

Initialize KeywordExtractionOutputs.

### KeywordExtraction Objects

```python
class KeywordExtraction(AssetNode[KeywordExtractionInputs,
                                  KeywordExtractionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2842)

KeywordExtraction node.

It helps concise the text and obtain relevant keywords Example use-cases are
finding topics of interest from a news article and identifying the problems
based on customer reviews and so.

InputType: text
OutputType: label

### SplitOnSilenceInputs Objects

```python
class SplitOnSilenceInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2861)

Input parameters for SplitOnSilence.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2866)

Initialize SplitOnSilenceInputs.

### SplitOnSilenceOutputs Objects

```python
class SplitOnSilenceOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2872)

Output parameters for SplitOnSilence.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2877)

Initialize SplitOnSilenceOutputs.

### SplitOnSilence Objects

```python
class SplitOnSilence(AssetNode[SplitOnSilenceInputs, SplitOnSilenceOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2883)

SplitOnSilence node.

The &quot;Split On Silence&quot; function divides an audio recording into separate
segments based on periods of silence, allowing for easier editing and analysis
of individual sections.

InputType: audio
OutputType: audio

### IntentRecognitionInputs Objects

```python
class IntentRecognitionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2902)

Input parameters for IntentRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2909)

Initialize IntentRecognitionInputs.

### IntentRecognitionOutputs Objects

```python
class IntentRecognitionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2917)

Output parameters for IntentRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2922)

Initialize IntentRecognitionOutputs.

### IntentRecognition Objects

```python
class IntentRecognition(AssetNode[IntentRecognitionInputs,
                                  IntentRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2928)

IntentRecognition node.

classify the user&#x27;s utterance (provided in varied natural language)  or text
into one of several predefined classes, that is, intents.

InputType: audio
OutputType: text

### DepthEstimationInputs Objects

```python
class DepthEstimationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2946)

Input parameters for DepthEstimation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2952)

Initialize DepthEstimationInputs.

### DepthEstimationOutputs Objects

```python
class DepthEstimationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2959)

Output parameters for DepthEstimation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2964)

Initialize DepthEstimationOutputs.

### DepthEstimation Objects

```python
class DepthEstimation(AssetNode[DepthEstimationInputs,
                                DepthEstimationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2970)

DepthEstimation node.

Depth estimation is a computational process that determines the distance of
objects from a viewpoint, typically using visual data from cameras or sensors
to create a three-dimensional understanding of a scene.

InputType: image
OutputType: text

### ConnectorInputs Objects

```python
class ConnectorInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2989)

Input parameters for Connector.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L2994)

Initialize ConnectorInputs.

### ConnectorOutputs Objects

```python
class ConnectorOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3000)

Output parameters for Connector.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3005)

Initialize ConnectorOutputs.

### Connector Objects

```python
class Connector(AssetNode[ConnectorInputs, ConnectorOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3011)

Connector node.

Connectors are integration that allow you to connect your AI agents to external
tools

InputType: text
OutputType: text

### SpeakerRecognitionInputs Objects

```python
class SpeakerRecognitionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3029)

Input parameters for SpeakerRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3037)

Initialize SpeakerRecognitionInputs.

### SpeakerRecognitionOutputs Objects

```python
class SpeakerRecognitionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3046)

Output parameters for SpeakerRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3051)

Initialize SpeakerRecognitionOutputs.

### SpeakerRecognition Objects

```python
class SpeakerRecognition(AssetNode[SpeakerRecognitionInputs,
                                   SpeakerRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3057)

SpeakerRecognition node.

In speaker identification, an utterance from an unknown speaker is analyzed and
compared with speech models of known speakers.

InputType: audio
OutputType: label

### SyntaxAnalysisInputs Objects

```python
class SyntaxAnalysisInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3075)

Input parameters for SyntaxAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3082)

Initialize SyntaxAnalysisInputs.

### SyntaxAnalysisOutputs Objects

```python
class SyntaxAnalysisOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3090)

Output parameters for SyntaxAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3095)

Initialize SyntaxAnalysisOutputs.

### SyntaxAnalysis Objects

```python
class SyntaxAnalysis(AssetNode[SyntaxAnalysisInputs, SyntaxAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3101)

SyntaxAnalysis node.

Is the process of analyzing natural language with the rules of a formal
grammar. Grammatical rules are applied to categories and groups of words, not
individual words. Syntactic analysis basically assigns a semantic structure to
text.

InputType: text
OutputType: text

### EntitySentimentAnalysisInputs Objects

```python
class EntitySentimentAnalysisInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3121)

Input parameters for EntitySentimentAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3126)

Initialize EntitySentimentAnalysisInputs.

### EntitySentimentAnalysisOutputs Objects

```python
class EntitySentimentAnalysisOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3132)

Output parameters for EntitySentimentAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3137)

Initialize EntitySentimentAnalysisOutputs.

### EntitySentimentAnalysis Objects

```python
class EntitySentimentAnalysis(AssetNode[EntitySentimentAnalysisInputs,
                                        EntitySentimentAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3143)

EntitySentimentAnalysis node.

Entity Sentiment Analysis combines both entity analysis and sentiment analysis
and attempts to determine the sentiment (positive or negative) expressed about
entities within the text.

InputType: text
OutputType: label

### ClassificationMetricInputs Objects

```python
class ClassificationMetricInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3162)

Input parameters for ClassificationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3171)

Initialize ClassificationMetricInputs.

### ClassificationMetricOutputs Objects

```python
class ClassificationMetricOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3181)

Output parameters for ClassificationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3186)

Initialize ClassificationMetricOutputs.

### ClassificationMetric Objects

```python
class ClassificationMetric(BaseMetric[ClassificationMetricInputs,
                                      ClassificationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3192)

ClassificationMetric node.

A Classification Metric is a quantitative measure used to evaluate the quality
and effectiveness of classification models.

InputType: text
OutputType: text

### TextDetectionInputs Objects

```python
class TextDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3210)

Input parameters for TextDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3215)

Initialize TextDetectionInputs.

### TextDetectionOutputs Objects

```python
class TextDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3221)

Output parameters for TextDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3226)

Initialize TextDetectionOutputs.

### TextDetection Objects

```python
class TextDetection(AssetNode[TextDetectionInputs, TextDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3232)

TextDetection node.

detect text regions in the complex background and label them with bounding
boxes.

InputType: image
OutputType: text

### GuardrailsInputs Objects

```python
class GuardrailsInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3250)

Input parameters for Guardrails.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3255)

Initialize GuardrailsInputs.

### GuardrailsOutputs Objects

```python
class GuardrailsOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3261)

Output parameters for Guardrails.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3266)

Initialize GuardrailsOutputs.

### Guardrails Objects

```python
class Guardrails(AssetNode[GuardrailsInputs, GuardrailsOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3272)

Guardrails node.

 Guardrails are governance rules that enforce security, compliance, and
operational best practices, helping prevent mistakes and detect suspicious
activity

InputType: text
OutputType: text

### EmotionDetectionInputs Objects

```python
class EmotionDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3291)

Input parameters for EmotionDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3299)

Initialize EmotionDetectionInputs.

### EmotionDetectionOutputs Objects

```python
class EmotionDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3308)

Output parameters for EmotionDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3313)

Initialize EmotionDetectionOutputs.

### EmotionDetection Objects

```python
class EmotionDetection(AssetNode[EmotionDetectionInputs,
                                 EmotionDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3319)

EmotionDetection node.

Identifies human emotions from text or audio, enhancing user experience in
chatbots or customer feedback analysis.

InputType: text
OutputType: label

### VideoForcedAlignmentInputs Objects

```python
class VideoForcedAlignmentInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3337)

Input parameters for VideoForcedAlignment.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3346)

Initialize VideoForcedAlignmentInputs.

### VideoForcedAlignmentOutputs Objects

```python
class VideoForcedAlignmentOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3356)

Output parameters for VideoForcedAlignment.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3362)

Initialize VideoForcedAlignmentOutputs.

### VideoForcedAlignment Objects

```python
class VideoForcedAlignment(AssetNode[VideoForcedAlignmentInputs,
                                     VideoForcedAlignmentOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3369)

VideoForcedAlignment node.

Aligns the transcription of spoken content in a video with its corresponding
timecodes, facilitating subtitle creation.

InputType: video
OutputType: video

### ImageContentModerationInputs Objects

```python
class ImageContentModerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3387)

Input parameters for ImageContentModeration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3393)

Initialize ImageContentModerationInputs.

### ImageContentModerationOutputs Objects

```python
class ImageContentModerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3400)

Output parameters for ImageContentModeration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3405)

Initialize ImageContentModerationOutputs.

### ImageContentModeration Objects

```python
class ImageContentModeration(AssetNode[ImageContentModerationInputs,
                                       ImageContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3411)

ImageContentModeration node.

Detects and filters out inappropriate or harmful images, essential for
platforms with user-generated visual content.

InputType: image
OutputType: label

### TextSummarizationInputs Objects

```python
class TextSummarizationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3429)

Input parameters for TextSummarization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3437)

Initialize TextSummarizationInputs.

### TextSummarizationOutputs Objects

```python
class TextSummarizationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3446)

Output parameters for TextSummarization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3451)

Initialize TextSummarizationOutputs.

### TextSummarization Objects

```python
class TextSummarization(AssetNode[TextSummarizationInputs,
                                  TextSummarizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3457)

TextSummarization node.

Extracts the main points from a larger body of text, producing a concise
summary without losing the primary message.

InputType: text
OutputType: text

### ImageToVideoGenerationInputs Objects

```python
class ImageToVideoGenerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3475)

Input parameters for ImageToVideoGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3481)

Initialize ImageToVideoGenerationInputs.

### ImageToVideoGenerationOutputs Objects

```python
class ImageToVideoGenerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3488)

Output parameters for ImageToVideoGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3493)

Initialize ImageToVideoGenerationOutputs.

### ImageToVideoGeneration Objects

```python
class ImageToVideoGeneration(AssetNode[ImageToVideoGenerationInputs,
                                       ImageToVideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3499)

ImageToVideoGeneration node.

The Image To Video Generation function transforms a series of static images
into a cohesive, dynamic video sequence, often incorporating transitions,
effects, and synchronization with audio to create a visually engaging
narrative.

InputType: image
OutputType: video

### VideoUnderstandingInputs Objects

```python
class VideoUnderstandingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3519)

Input parameters for VideoUnderstanding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3528)

Initialize VideoUnderstandingInputs.

### VideoUnderstandingOutputs Objects

```python
class VideoUnderstandingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3538)

Output parameters for VideoUnderstanding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3543)

Initialize VideoUnderstandingOutputs.

### VideoUnderstanding Objects

```python
class VideoUnderstanding(AssetNode[VideoUnderstandingInputs,
                                   VideoUnderstandingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3549)

VideoUnderstanding node.

Video Understanding is the process of analyzing and interpreting video content
to extract meaningful information, such as identifying objects, actions,
events, and contextual relationships within the footage.

InputType: video
OutputType: text

### TextGenerationMetricDefaultInputs Objects

```python
class TextGenerationMetricDefaultInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3568)

Input parameters for TextGenerationMetricDefault.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3576)

Initialize TextGenerationMetricDefaultInputs.

### TextGenerationMetricDefaultOutputs Objects

```python
class TextGenerationMetricDefaultOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3585)

Output parameters for TextGenerationMetricDefault.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3590)

Initialize TextGenerationMetricDefaultOutputs.

### TextGenerationMetricDefault Objects

```python
class TextGenerationMetricDefault(
        BaseMetric[TextGenerationMetricDefaultInputs,
                   TextGenerationMetricDefaultOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3596)

TextGenerationMetricDefault node.

The &quot;Text Generation Metric Default&quot; function provides a standard set of
evaluation metrics for assessing the quality and performance of text generation
models.

InputType: text
OutputType: text

### TextToVideoGenerationInputs Objects

```python
class TextToVideoGenerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3615)

Input parameters for TextToVideoGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3621)

Initialize TextToVideoGenerationInputs.

### TextToVideoGenerationOutputs Objects

```python
class TextToVideoGenerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3628)

Output parameters for TextToVideoGeneration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3633)

Initialize TextToVideoGenerationOutputs.

### TextToVideoGeneration Objects

```python
class TextToVideoGeneration(AssetNode[TextToVideoGenerationInputs,
                                      TextToVideoGenerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3639)

TextToVideoGeneration node.

Text To Video Generation is a process that converts written descriptions or
scripts into dynamic, visual video content using advanced algorithms and
artificial intelligence.

InputType: text
OutputType: video

### VideoLabelDetectionInputs Objects

```python
class VideoLabelDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3658)

Input parameters for VideoLabelDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3664)

Initialize VideoLabelDetectionInputs.

### VideoLabelDetectionOutputs Objects

```python
class VideoLabelDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3671)

Output parameters for VideoLabelDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3676)

Initialize VideoLabelDetectionOutputs.

### VideoLabelDetection Objects

```python
class VideoLabelDetection(AssetNode[VideoLabelDetectionInputs,
                                    VideoLabelDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3682)

VideoLabelDetection node.

Identifies and tags objects, scenes, or activities within a video. Useful for
content indexing and recommendation systems.

InputType: video
OutputType: label

### TextSpamDetectionInputs Objects

```python
class TextSpamDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3700)

Input parameters for TextSpamDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3708)

Initialize TextSpamDetectionInputs.

### TextSpamDetectionOutputs Objects

```python
class TextSpamDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3717)

Output parameters for TextSpamDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3722)

Initialize TextSpamDetectionOutputs.

### TextSpamDetection Objects

```python
class TextSpamDetection(AssetNode[TextSpamDetectionInputs,
                                  TextSpamDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3728)

TextSpamDetection node.

Identifies and filters out unwanted or irrelevant text content, ideal for
moderating user-generated content or ensuring quality in communication
platforms.

InputType: text
OutputType: label

### TextContentModerationInputs Objects

```python
class TextContentModerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3747)

Input parameters for TextContentModeration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3755)

Initialize TextContentModerationInputs.

### TextContentModerationOutputs Objects

```python
class TextContentModerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3764)

Output parameters for TextContentModeration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3769)

Initialize TextContentModerationOutputs.

### TextContentModeration Objects

```python
class TextContentModeration(AssetNode[TextContentModerationInputs,
                                      TextContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3775)

TextContentModeration node.

Scans and identifies potentially harmful, offensive, or inappropriate textual
content, ensuring safer user environments.

InputType: text
OutputType: label

### AudioTranscriptImprovementInputs Objects

```python
class AudioTranscriptImprovementInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3793)

Input parameters for AudioTranscriptImprovement.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3803)

Initialize AudioTranscriptImprovementInputs.

### AudioTranscriptImprovementOutputs Objects

```python
class AudioTranscriptImprovementOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3814)

Output parameters for AudioTranscriptImprovement.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3819)

Initialize AudioTranscriptImprovementOutputs.

### AudioTranscriptImprovement Objects

```python
class AudioTranscriptImprovement(AssetNode[AudioTranscriptImprovementInputs,
                                           AudioTranscriptImprovementOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3825)

AudioTranscriptImprovement node.

Refines and corrects transcriptions generated from audio data, improving
readability and accuracy.

InputType: audio
OutputType: text

### AudioTranscriptAnalysisInputs Objects

```python
class AudioTranscriptAnalysisInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3843)

Input parameters for AudioTranscriptAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3852)

Initialize AudioTranscriptAnalysisInputs.

### AudioTranscriptAnalysisOutputs Objects

```python
class AudioTranscriptAnalysisOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3862)

Output parameters for AudioTranscriptAnalysis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3867)

Initialize AudioTranscriptAnalysisOutputs.

### AudioTranscriptAnalysis Objects

```python
class AudioTranscriptAnalysis(AssetNode[AudioTranscriptAnalysisInputs,
                                        AudioTranscriptAnalysisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3873)

AudioTranscriptAnalysis node.

Analyzes transcribed audio data for insights, patterns, or specific information
extraction.

InputType: audio
OutputType: text

### SpeechNonSpeechClassificationInputs Objects

```python
class SpeechNonSpeechClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3891)

Input parameters for SpeechNonSpeechClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3899)

Initialize SpeechNonSpeechClassificationInputs.

### SpeechNonSpeechClassificationOutputs Objects

```python
class SpeechNonSpeechClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3908)

Output parameters for SpeechNonSpeechClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3913)

Initialize SpeechNonSpeechClassificationOutputs.

### SpeechNonSpeechClassification Objects

```python
class SpeechNonSpeechClassification(
        AssetNode[SpeechNonSpeechClassificationInputs,
                  SpeechNonSpeechClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3919)

SpeechNonSpeechClassification node.

Differentiates between speech and non-speech audio segments. Great for editing
software and transcription services to exclude irrelevant audio.

InputType: audio
OutputType: label

### AudioGenerationMetricInputs Objects

```python
class AudioGenerationMetricInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3939)

Input parameters for AudioGenerationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3947)

Initialize AudioGenerationMetricInputs.

### AudioGenerationMetricOutputs Objects

```python
class AudioGenerationMetricOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3956)

Output parameters for AudioGenerationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3961)

Initialize AudioGenerationMetricOutputs.

### AudioGenerationMetric Objects

```python
class AudioGenerationMetric(BaseMetric[AudioGenerationMetricInputs,
                                       AudioGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3967)

AudioGenerationMetric node.

The Audio Generation Metric is a quantitative measure used to evaluate the
quality, accuracy, and overall performance of audio generated by artificial
intelligence systems, often considering factors such as fidelity,
intelligibility, and similarity to human-produced audio.

InputType: text
OutputType: text

### NamedEntityRecognitionInputs Objects

```python
class NamedEntityRecognitionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3987)

Input parameters for NamedEntityRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L3996)

Initialize NamedEntityRecognitionInputs.

### NamedEntityRecognitionOutputs Objects

```python
class NamedEntityRecognitionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4006)

Output parameters for NamedEntityRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4011)

Initialize NamedEntityRecognitionOutputs.

### NamedEntityRecognition Objects

```python
class NamedEntityRecognition(AssetNode[NamedEntityRecognitionInputs,
                                       NamedEntityRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4017)

NamedEntityRecognition node.

Identifies and classifies named entities (e.g., persons, organizations,
locations) within text. Useful for information extraction, content tagging, and
search enhancements.

InputType: text
OutputType: label

### SpeechSynthesisInputs Objects

```python
class SpeechSynthesisInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4036)

Input parameters for SpeechSynthesis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4047)

Initialize SpeechSynthesisInputs.

### SpeechSynthesisOutputs Objects

```python
class SpeechSynthesisOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4059)

Output parameters for SpeechSynthesis.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4064)

Initialize SpeechSynthesisOutputs.

### SpeechSynthesis Objects

```python
class SpeechSynthesis(AssetNode[SpeechSynthesisInputs,
                                SpeechSynthesisOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4070)

SpeechSynthesis node.

Generates human-like speech from written text. Ideal for text-to-speech
applications, audiobooks, and voice assistants.

InputType: text
OutputType: audio

### DocumentInformationExtractionInputs Objects

```python
class DocumentInformationExtractionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4088)

Input parameters for DocumentInformationExtraction.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4093)

Initialize DocumentInformationExtractionInputs.

### DocumentInformationExtractionOutputs Objects

```python
class DocumentInformationExtractionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4099)

Output parameters for DocumentInformationExtraction.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4104)

Initialize DocumentInformationExtractionOutputs.

### DocumentInformationExtraction Objects

```python
class DocumentInformationExtraction(
        AssetNode[DocumentInformationExtractionInputs,
                  DocumentInformationExtractionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4110)

DocumentInformationExtraction node.

Document Information Extraction is the process of automatically identifying,
extracting, and structuring relevant data from unstructured or semi-structured
documents, such as invoices, receipts, contracts, and forms, to facilitate
easier data management and analysis.

InputType: image
OutputType: text

### OcrInputs Objects

```python
class OcrInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4132)

Input parameters for Ocr.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4138)

Initialize OcrInputs.

### OcrOutputs Objects

```python
class OcrOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4145)

Output parameters for Ocr.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4150)

Initialize OcrOutputs.

### Ocr Objects

```python
class Ocr(AssetNode[OcrInputs, OcrOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4156)

Ocr node.

Converts images of typed, handwritten, or printed text into machine-encoded
text. Used in digitizing printed texts for data retrieval.

InputType: image
OutputType: text

### SubtitlingTranslationInputs Objects

```python
class SubtitlingTranslationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4174)

Input parameters for SubtitlingTranslation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4183)

Initialize SubtitlingTranslationInputs.

### SubtitlingTranslationOutputs Objects

```python
class SubtitlingTranslationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4193)

Output parameters for SubtitlingTranslation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4198)

Initialize SubtitlingTranslationOutputs.

### SubtitlingTranslation Objects

```python
class SubtitlingTranslation(AssetNode[SubtitlingTranslationInputs,
                                      SubtitlingTranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4204)

SubtitlingTranslation node.

Converts the text of subtitles from one language to another, ensuring context
and cultural nuances are maintained. Essential for global content distribution.

InputType: text
OutputType: text

### TextToAudioInputs Objects

```python
class TextToAudioInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4222)

Input parameters for TextToAudio.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4228)

Initialize TextToAudioInputs.

### TextToAudioOutputs Objects

```python
class TextToAudioOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4235)

Output parameters for TextToAudio.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4240)

Initialize TextToAudioOutputs.

### TextToAudio Objects

```python
class TextToAudio(AssetNode[TextToAudioInputs, TextToAudioOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4246)

TextToAudio node.

The Text to Audio function converts written text into spoken words, allowing
users to listen to the content instead of reading it.

InputType: text
OutputType: audio

### MultilingualSpeechRecognitionInputs Objects

```python
class MultilingualSpeechRecognitionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4264)

Input parameters for MultilingualSpeechRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4270)

Initialize MultilingualSpeechRecognitionInputs.

### MultilingualSpeechRecognitionOutputs Objects

```python
class MultilingualSpeechRecognitionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4277)

Output parameters for MultilingualSpeechRecognition.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4282)

Initialize MultilingualSpeechRecognitionOutputs.

### MultilingualSpeechRecognition Objects

```python
class MultilingualSpeechRecognition(
        AssetNode[MultilingualSpeechRecognitionInputs,
                  MultilingualSpeechRecognitionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4288)

MultilingualSpeechRecognition node.

Multilingual Speech Recognition is a technology that enables the automatic
transcription of spoken language into text across multiple languages, allowing
for seamless communication and understanding in diverse linguistic contexts.

InputType: audio
OutputType: text

### OffensiveLanguageIdentificationInputs Objects

```python
class OffensiveLanguageIdentificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4309)

Input parameters for OffensiveLanguageIdentification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4317)

Initialize OffensiveLanguageIdentificationInputs.

### OffensiveLanguageIdentificationOutputs Objects

```python
class OffensiveLanguageIdentificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4326)

Output parameters for OffensiveLanguageIdentification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4331)

Initialize OffensiveLanguageIdentificationOutputs.

### OffensiveLanguageIdentification Objects

```python
class OffensiveLanguageIdentification(
        AssetNode[OffensiveLanguageIdentificationInputs,
                  OffensiveLanguageIdentificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4337)

OffensiveLanguageIdentification node.

Detects language or phrases that might be considered offensive, aiding in
content moderation and creating respectful user interactions.

InputType: text
OutputType: label

### BenchmarkScoringMtInputs Objects

```python
class BenchmarkScoringMtInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4357)

Input parameters for BenchmarkScoringMt.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4364)

Initialize BenchmarkScoringMtInputs.

### BenchmarkScoringMtOutputs Objects

```python
class BenchmarkScoringMtOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4372)

Output parameters for BenchmarkScoringMt.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4377)

Initialize BenchmarkScoringMtOutputs.

### BenchmarkScoringMt Objects

```python
class BenchmarkScoringMt(AssetNode[BenchmarkScoringMtInputs,
                                   BenchmarkScoringMtOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4383)

BenchmarkScoringMt node.

Benchmark Scoring MT is a function designed to evaluate and score machine
translation systems by comparing their output against a set of predefined
benchmarks, thereby assessing their accuracy and performance.

InputType: text
OutputType: label

### SpeakerDiarizationAudioInputs Objects

```python
class SpeakerDiarizationAudioInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4402)

Input parameters for SpeakerDiarizationAudio.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4410)

Initialize SpeakerDiarizationAudioInputs.

### SpeakerDiarizationAudioOutputs Objects

```python
class SpeakerDiarizationAudioOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4419)

Output parameters for SpeakerDiarizationAudio.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4425)

Initialize SpeakerDiarizationAudioOutputs.

### SpeakerDiarizationAudio Objects

```python
class SpeakerDiarizationAudio(BaseSegmentor[SpeakerDiarizationAudioInputs,
                                            SpeakerDiarizationAudioOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4432)

SpeakerDiarizationAudio node.

Identifies individual speakers and their respective speech segments within an
audio clip. Ideal for multi-speaker recordings or conference calls.

InputType: audio
OutputType: label

### VoiceCloningInputs Objects

```python
class VoiceCloningInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4450)

Input parameters for VoiceCloning.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4461)

Initialize VoiceCloningInputs.

### VoiceCloningOutputs Objects

```python
class VoiceCloningOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4473)

Output parameters for VoiceCloning.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4478)

Initialize VoiceCloningOutputs.

### VoiceCloning Objects

```python
class VoiceCloning(AssetNode[VoiceCloningInputs, VoiceCloningOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4484)

VoiceCloning node.

Replicates a person&#x27;s voice based on a sample, allowing for the generation of
speech in that person&#x27;s tone and style. Used cautiously due to ethical
considerations.

InputType: text
OutputType: audio

### SearchInputs Objects

```python
class SearchInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4503)

Input parameters for Search.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4508)

Initialize SearchInputs.

### SearchOutputs Objects

```python
class SearchOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4514)

Output parameters for Search.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4519)

Initialize SearchOutputs.

### Search Objects

```python
class Search(AssetNode[SearchInputs, SearchOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4525)

Search node.

An algorithm that identifies and returns data or items that match particular
keywords or conditions from a dataset. A fundamental tool for databases and
websites.

InputType: text
OutputType: text

### ObjectDetectionInputs Objects

```python
class ObjectDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4544)

Input parameters for ObjectDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4549)

Initialize ObjectDetectionInputs.

### ObjectDetectionOutputs Objects

```python
class ObjectDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4555)

Output parameters for ObjectDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4560)

Initialize ObjectDetectionOutputs.

### ObjectDetection Objects

```python
class ObjectDetection(AssetNode[ObjectDetectionInputs,
                                ObjectDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4566)

ObjectDetection node.

Object Detection is a computer vision technology that identifies and locates
objects within an image, typically by drawing bounding boxes around the
detected objects and classifying them into predefined categories.

InputType: video
OutputType: text

### DiacritizationInputs Objects

```python
class DiacritizationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4585)

Input parameters for Diacritization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4593)

Initialize DiacritizationInputs.

### DiacritizationOutputs Objects

```python
class DiacritizationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4602)

Output parameters for Diacritization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4607)

Initialize DiacritizationOutputs.

### Diacritization Objects

```python
class Diacritization(AssetNode[DiacritizationInputs, DiacritizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4613)

Diacritization node.

Adds diacritical marks to text, essential for languages where meaning can
change based on diacritics.

InputType: text
OutputType: text

### SpeakerDiarizationVideoInputs Objects

```python
class SpeakerDiarizationVideoInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4631)

Input parameters for SpeakerDiarizationVideo.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4639)

Initialize SpeakerDiarizationVideoInputs.

### SpeakerDiarizationVideoOutputs Objects

```python
class SpeakerDiarizationVideoOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4648)

Output parameters for SpeakerDiarizationVideo.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4653)

Initialize SpeakerDiarizationVideoOutputs.

### SpeakerDiarizationVideo Objects

```python
class SpeakerDiarizationVideo(AssetNode[SpeakerDiarizationVideoInputs,
                                        SpeakerDiarizationVideoOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4659)

SpeakerDiarizationVideo node.

Segments a video based on different speakers, identifying when each individual
speaks. Useful for transcriptions and understanding multi-person conversations.

InputType: video
OutputType: label

### AudioForcedAlignmentInputs Objects

```python
class AudioForcedAlignmentInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4677)

Input parameters for AudioForcedAlignment.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4686)

Initialize AudioForcedAlignmentInputs.

### AudioForcedAlignmentOutputs Objects

```python
class AudioForcedAlignmentOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4696)

Output parameters for AudioForcedAlignment.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4702)

Initialize AudioForcedAlignmentOutputs.

### AudioForcedAlignment Objects

```python
class AudioForcedAlignment(AssetNode[AudioForcedAlignmentInputs,
                                     AudioForcedAlignmentOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4709)

AudioForcedAlignment node.

Synchronizes phonetic and phonological text with the corresponding segments in
an audio file. Useful in linguistic research and detailed transcription tasks.

InputType: audio
OutputType: audio

### TokenClassificationInputs Objects

```python
class TokenClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4727)

Input parameters for TokenClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4734)

Initialize TokenClassificationInputs.

### TokenClassificationOutputs Objects

```python
class TokenClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4742)

Output parameters for TokenClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4747)

Initialize TokenClassificationOutputs.

### TokenClassification Objects

```python
class TokenClassification(AssetNode[TokenClassificationInputs,
                                    TokenClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4753)

TokenClassification node.

Token-level classification means that each token will be given a label, for
example a part-of-speech tagger will classify each word as one particular part
of speech.

InputType: text
OutputType: label

### TopicClassificationInputs Objects

```python
class TopicClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4772)

Input parameters for TopicClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4780)

Initialize TopicClassificationInputs.

### TopicClassificationOutputs Objects

```python
class TopicClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4789)

Output parameters for TopicClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4794)

Initialize TopicClassificationOutputs.

### TopicClassification Objects

```python
class TopicClassification(AssetNode[TopicClassificationInputs,
                                    TopicClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4800)

TopicClassification node.

Assigns categories or topics to a piece of text based on its content,
facilitating content organization and retrieval.

InputType: text
OutputType: label

### IntentClassificationInputs Objects

```python
class IntentClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4818)

Input parameters for IntentClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4824)

Initialize IntentClassificationInputs.

### IntentClassificationOutputs Objects

```python
class IntentClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4831)

Output parameters for IntentClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4836)

Initialize IntentClassificationOutputs.

### IntentClassification Objects

```python
class IntentClassification(AssetNode[IntentClassificationInputs,
                                     IntentClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4842)

IntentClassification node.

Intent Classification is a natural language processing task that involves
analyzing and categorizing user text input to determine the underlying purpose
or goal behind the communication, such as booking a flight, asking for weather
information, or setting a reminder.

InputType: text
OutputType: label

### VideoContentModerationInputs Objects

```python
class VideoContentModerationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4862)

Input parameters for VideoContentModeration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4868)

Initialize VideoContentModerationInputs.

### VideoContentModerationOutputs Objects

```python
class VideoContentModerationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4875)

Output parameters for VideoContentModeration.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4880)

Initialize VideoContentModerationOutputs.

### VideoContentModeration Objects

```python
class VideoContentModeration(AssetNode[VideoContentModerationInputs,
                                       VideoContentModerationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4886)

VideoContentModeration node.

Automatically reviews video content to detect and possibly remove inappropriate
or harmful material. Essential for user-generated content platforms.

InputType: video
OutputType: label

### TextGenerationMetricInputs Objects

```python
class TextGenerationMetricInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4904)

Input parameters for TextGenerationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4912)

Initialize TextGenerationMetricInputs.

### TextGenerationMetricOutputs Objects

```python
class TextGenerationMetricOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4921)

Output parameters for TextGenerationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4926)

Initialize TextGenerationMetricOutputs.

### TextGenerationMetric Objects

```python
class TextGenerationMetric(BaseMetric[TextGenerationMetricInputs,
                                      TextGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4932)

TextGenerationMetric node.

A Text Generation Metric is a quantitative measure used to evaluate the quality
and effectiveness of text produced by natural language processing models, often
assessing aspects such as coherence, relevance, fluency, and adherence to given
prompts or instructions.

InputType: text
OutputType: text

### ImageEmbeddingInputs Objects

```python
class ImageEmbeddingInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4952)

Input parameters for ImageEmbedding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4958)

Initialize ImageEmbeddingInputs.

### ImageEmbeddingOutputs Objects

```python
class ImageEmbeddingOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4965)

Output parameters for ImageEmbedding.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4970)

Initialize ImageEmbeddingOutputs.

### ImageEmbedding Objects

```python
class ImageEmbedding(AssetNode[ImageEmbeddingInputs, ImageEmbeddingOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4976)

ImageEmbedding node.

Image Embedding is a process that transforms an image into a fixed-dimensional
vector representation, capturing its essential features and enabling efficient
comparison, retrieval, and analysis in various machine learning and computer
vision tasks.

InputType: image
OutputType: text

### ImageLabelDetectionInputs Objects

```python
class ImageLabelDetectionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L4996)

Input parameters for ImageLabelDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5002)

Initialize ImageLabelDetectionInputs.

### ImageLabelDetectionOutputs Objects

```python
class ImageLabelDetectionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5009)

Output parameters for ImageLabelDetection.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5014)

Initialize ImageLabelDetectionOutputs.

### ImageLabelDetection Objects

```python
class ImageLabelDetection(AssetNode[ImageLabelDetectionInputs,
                                    ImageLabelDetectionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5020)

ImageLabelDetection node.

Identifies objects, themes, or topics within images, useful for image
categorization, search, and recommendation systems.

InputType: image
OutputType: label

### ImageColorizationInputs Objects

```python
class ImageColorizationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5038)

Input parameters for ImageColorization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5043)

Initialize ImageColorizationInputs.

### ImageColorizationOutputs Objects

```python
class ImageColorizationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5049)

Output parameters for ImageColorization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5054)

Initialize ImageColorizationOutputs.

### ImageColorization Objects

```python
class ImageColorization(AssetNode[ImageColorizationInputs,
                                  ImageColorizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5060)

ImageColorization node.

Image colorization is a process that involves adding color to grayscale images,
transforming them from black-and-white to full-color representations, often
using advanced algorithms and machine learning techniques to predict and apply
the appropriate hues and shades.

InputType: image
OutputType: image

### MetricAggregationInputs Objects

```python
class MetricAggregationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5080)

Input parameters for MetricAggregation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5085)

Initialize MetricAggregationInputs.

### MetricAggregationOutputs Objects

```python
class MetricAggregationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5091)

Output parameters for MetricAggregation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5096)

Initialize MetricAggregationOutputs.

### MetricAggregation Objects

```python
class MetricAggregation(BaseMetric[MetricAggregationInputs,
                                   MetricAggregationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5102)

MetricAggregation node.

Metric Aggregation is a function that computes and summarizes numerical data by
applying statistical operations, such as averaging, summing, or finding the
minimum and maximum values, to provide insights and facilitate analysis of
large datasets.

InputType: text
OutputType: text

### InstanceSegmentationInputs Objects

```python
class InstanceSegmentationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5122)

Input parameters for InstanceSegmentation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5127)

Initialize InstanceSegmentationInputs.

### InstanceSegmentationOutputs Objects

```python
class InstanceSegmentationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5133)

Output parameters for InstanceSegmentation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5138)

Initialize InstanceSegmentationOutputs.

### InstanceSegmentation Objects

```python
class InstanceSegmentation(AssetNode[InstanceSegmentationInputs,
                                     InstanceSegmentationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5144)

InstanceSegmentation node.

Instance segmentation is a computer vision task that involves detecting and
delineating each distinct object within an image, assigning a unique label and
precise boundary to every individual instance of objects, even if they belong
to the same category.

InputType: image
OutputType: label

### OtherMultipurposeInputs Objects

```python
class OtherMultipurposeInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5164)

Input parameters for OtherMultipurpose.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5170)

Initialize OtherMultipurposeInputs.

### OtherMultipurposeOutputs Objects

```python
class OtherMultipurposeOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5177)

Output parameters for OtherMultipurpose.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5182)

Initialize OtherMultipurposeOutputs.

### OtherMultipurpose Objects

```python
class OtherMultipurpose(AssetNode[OtherMultipurposeInputs,
                                  OtherMultipurposeOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5188)

OtherMultipurpose node.

The &quot;Other (Multipurpose)&quot; function serves as a versatile category designed to
accommodate a wide range of tasks and activities that do not fit neatly into
predefined classifications, offering flexibility and adaptability for various
needs.

InputType: text
OutputType: text

### SpeechTranslationInputs Objects

```python
class SpeechTranslationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5208)

Input parameters for SpeechTranslation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5218)

Initialize SpeechTranslationInputs.

### SpeechTranslationOutputs Objects

```python
class SpeechTranslationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5229)

Output parameters for SpeechTranslation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5234)

Initialize SpeechTranslationOutputs.

### SpeechTranslation Objects

```python
class SpeechTranslation(AssetNode[SpeechTranslationInputs,
                                  SpeechTranslationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5240)

SpeechTranslation node.

Speech Translation is a technology that converts spoken language in real-time
from one language to another, enabling seamless communication between speakers
of different languages.

InputType: audio
OutputType: text

### ReferencelessTextGenerationMetricDefaultInputs Objects

```python
class ReferencelessTextGenerationMetricDefaultInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5259)

Input parameters for ReferencelessTextGenerationMetricDefault.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5266)

Initialize ReferencelessTextGenerationMetricDefaultInputs.

### ReferencelessTextGenerationMetricDefaultOutputs Objects

```python
class ReferencelessTextGenerationMetricDefaultOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5274)

Output parameters for ReferencelessTextGenerationMetricDefault.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5279)

Initialize ReferencelessTextGenerationMetricDefaultOutputs.

### ReferencelessTextGenerationMetricDefault Objects

```python
class ReferencelessTextGenerationMetricDefault(
        BaseMetric[ReferencelessTextGenerationMetricDefaultInputs,
                   ReferencelessTextGenerationMetricDefaultOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5285)

ReferencelessTextGenerationMetricDefault node.

The Referenceless Text Generation Metric Default is a function designed to
evaluate the quality of generated text without relying on reference texts for
comparison.

InputType: text
OutputType: text

### ReferencelessTextGenerationMetricInputs Objects

```python
class ReferencelessTextGenerationMetricInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5306)

Input parameters for ReferencelessTextGenerationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5313)

Initialize ReferencelessTextGenerationMetricInputs.

### ReferencelessTextGenerationMetricOutputs Objects

```python
class ReferencelessTextGenerationMetricOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5321)

Output parameters for ReferencelessTextGenerationMetric.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5326)

Initialize ReferencelessTextGenerationMetricOutputs.

### ReferencelessTextGenerationMetric Objects

```python
class ReferencelessTextGenerationMetric(
        BaseMetric[ReferencelessTextGenerationMetricInputs,
                   ReferencelessTextGenerationMetricOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5332)

ReferencelessTextGenerationMetric node.

The Referenceless Text Generation Metric is a method for evaluating the quality
of generated text without requiring a reference text for comparison, often
leveraging models or algorithms to assess coherence, relevance, and fluency
based on intrinsic properties of the text itself.

InputType: text
OutputType: text

### TextDenormalizationInputs Objects

```python
class TextDenormalizationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5354)

Input parameters for TextDenormalization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5363)

Initialize TextDenormalizationInputs.

### TextDenormalizationOutputs Objects

```python
class TextDenormalizationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5375)

Output parameters for TextDenormalization.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5380)

Initialize TextDenormalizationOutputs.

### TextDenormalization Objects

```python
class TextDenormalization(AssetNode[TextDenormalizationInputs,
                                    TextDenormalizationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5386)

TextDenormalization node.

Converts standardized or normalized text into its original, often more
readable, form. Useful in natural language generation tasks.

InputType: text
OutputType: label

### ImageCompressionInputs Objects

```python
class ImageCompressionInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5404)

Input parameters for ImageCompression.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5410)

Initialize ImageCompressionInputs.

### ImageCompressionOutputs Objects

```python
class ImageCompressionOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5417)

Output parameters for ImageCompression.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5422)

Initialize ImageCompressionOutputs.

### ImageCompression Objects

```python
class ImageCompression(AssetNode[ImageCompressionInputs,
                                 ImageCompressionOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5428)

ImageCompression node.

Reduces the size of image files without significantly compromising their visual
quality. Useful for optimizing storage and improving webpage load times.

InputType: image
OutputType: image

### TextClassificationInputs Objects

```python
class TextClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5446)

Input parameters for TextClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5454)

Initialize TextClassificationInputs.

### TextClassificationOutputs Objects

```python
class TextClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5463)

Output parameters for TextClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5468)

Initialize TextClassificationOutputs.

### TextClassification Objects

```python
class TextClassification(AssetNode[TextClassificationInputs,
                                   TextClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5474)

TextClassification node.

Categorizes text into predefined groups or topics, facilitating content
organization and targeted actions.

InputType: text
OutputType: label

### AsrAgeClassificationInputs Objects

```python
class AsrAgeClassificationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5492)

Input parameters for AsrAgeClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5497)

Initialize AsrAgeClassificationInputs.

### AsrAgeClassificationOutputs Objects

```python
class AsrAgeClassificationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5503)

Output parameters for AsrAgeClassification.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5508)

Initialize AsrAgeClassificationOutputs.

### AsrAgeClassification Objects

```python
class AsrAgeClassification(AssetNode[AsrAgeClassificationInputs,
                                     AsrAgeClassificationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5514)

AsrAgeClassification node.

The ASR Age Classification function is designed to analyze audio recordings of
speech to determine the speaker&#x27;s age group by leveraging automatic speech
recognition (ASR) technology and machine learning algorithms.

InputType: audio
OutputType: label

### AsrQualityEstimationInputs Objects

```python
class AsrQualityEstimationInputs(Inputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5533)

Input parameters for AsrQualityEstimation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5539)

Initialize AsrQualityEstimationInputs.

### AsrQualityEstimationOutputs Objects

```python
class AsrQualityEstimationOutputs(Outputs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5546)

Output parameters for AsrQualityEstimation.

#### \_\_init\_\_

```python
def __init__(node=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5551)

Initialize AsrQualityEstimationOutputs.

### AsrQualityEstimation Objects

```python
class AsrQualityEstimation(AssetNode[AsrQualityEstimationInputs,
                                     AsrQualityEstimationOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5557)

AsrQualityEstimation node.

ASR Quality Estimation is a process that evaluates the accuracy and reliability
of automatic speech recognition systems by analyzing their performance in
transcribing spoken language into text.

InputType: text
OutputType: label

### Pipeline Objects

```python
class Pipeline(DefaultPipeline)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5576)

Pipeline class for creating and managing AI processing pipelines.

#### text\_normalization

```python
def text_normalization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> TextNormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5579)

Create a TextNormalization node.

Converts unstructured or non-standard textual data into a more readable and
uniform format, dealing with abbreviations, numerals, and other non-standard
words.

#### paraphrasing

```python
def paraphrasing(asset_id: Union[str, asset.Asset], *args,
                 **kwargs) -> Paraphrasing
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5588)

Create a Paraphrasing node.

Express the meaning of the writer or speaker or something written or spoken
using different words.

#### language\_identification

```python
def language_identification(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> LanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5596)

Create a LanguageIdentification node.

Detects the language in which a given text is written, aiding in multilingual
platforms or content localization.

#### benchmark\_scoring\_asr

```python
def benchmark_scoring_asr(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> BenchmarkScoringAsr
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5604)

Create a BenchmarkScoringAsr node.

Benchmark Scoring ASR is a function that evaluates and compares the performance
of automatic speech recognition systems by analyzing their accuracy, speed, and
other relevant metrics against a standardized set of benchmarks.

#### multi\_class\_text\_classification

```python
def multi_class_text_classification(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultiClassTextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5613)

Create a MultiClassTextClassification node.

Multi Class Text Classification is a natural language processing task that
involves categorizing a given text into one of several predefined classes or
categories based on its content.

#### speech\_embedding

```python
def speech_embedding(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SpeechEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5624)

Create a SpeechEmbedding node.

Transforms spoken content into a fixed-size vector in a high-dimensional space
that captures the content&#x27;s essence. Facilitates tasks like speech recognition
and speaker verification.

#### document\_image\_parsing

```python
def document_image_parsing(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> DocumentImageParsing
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5633)

Create a DocumentImageParsing node.

Document Image Parsing is the process of analyzing and converting scanned or
photographed images of documents into structured, machine-readable formats by
identifying and extracting text, layout, and other relevant information.

#### translation

```python
def translation(asset_id: Union[str, asset.Asset], *args,
                **kwargs) -> Translation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5642)

Create a Translation node.

Converts text from one language to another while maintaining the original
message&#x27;s essence and context. Crucial for global communication.

#### audio\_source\_separation

```python
def audio_source_separation(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> AudioSourceSeparation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5650)

Create a AudioSourceSeparation node.

Audio Source Separation is the process of separating a mixture (e.g. a pop band
recording) into isolated sounds from individual sources (e.g. just the lead
vocals).

#### speech\_recognition

```python
def speech_recognition(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SpeechRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5659)

Create a SpeechRecognition node.

Converts spoken language into written text. Useful for transcription services,
voice assistants, and applications requiring voice-to-text capabilities.

#### keyword\_spotting

```python
def keyword_spotting(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> KeywordSpotting
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5667)

Create a KeywordSpotting node.

Keyword Spotting is a function that enables the detection and identification of
specific words or phrases within a stream of audio, often used in voice-
activated systems to trigger actions or commands based on recognized keywords.

#### part\_of\_speech\_tagging

```python
def part_of_speech_tagging(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> PartOfSpeechTagging
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5676)

Create a PartOfSpeechTagging node.

Part of Speech Tagging is a natural language processing task that involves
assigning each word in a sentence its corresponding part of speech, such as
noun, verb, adjective, or adverb, based on its role and context within the
sentence.

#### referenceless\_audio\_generation\_metric

```python
def referenceless_audio_generation_metric(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessAudioGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5686)

Create a ReferencelessAudioGenerationMetric node.

The Referenceless Audio Generation Metric is a tool designed to evaluate the
quality of generated audio content without the need for a reference or original
audio sample for comparison.

#### voice\_activity\_detection

```python
def voice_activity_detection(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> VoiceActivityDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5697)

Create a VoiceActivityDetection node.

Determines when a person is speaking in an audio clip. It&#x27;s an essential
preprocessing step for other audio-related tasks.

#### sentiment\_analysis

```python
def sentiment_analysis(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SentimentAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5705)

Create a SentimentAnalysis node.

Determines the sentiment or emotion (e.g., positive, negative, neutral) of a
piece of text, aiding in understanding user feedback or market sentiment.

#### subtitling

```python
def subtitling(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> Subtitling
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5713)

Create a Subtitling node.

Generates accurate subtitles for videos, enhancing accessibility for diverse
audiences.

#### multi\_label\_text\_classification

```python
def multi_label_text_classification(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultiLabelTextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5721)

Create a MultiLabelTextClassification node.

Multi Label Text Classification is a natural language processing task where a
given text is analyzed and assigned multiple relevant labels or categories from
a predefined set, allowing for the text to belong to more than one category
simultaneously.

#### viseme\_generation

```python
def viseme_generation(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> VisemeGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5733)

Create a VisemeGeneration node.

Viseme Generation is the process of creating visual representations of
phonemes, which are the distinct units of sound in speech, to synchronize lip
movements with spoken words in animations or virtual avatars.

#### text\_segmenation

```python
def text_segmenation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> TextSegmenation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5742)

Create a TextSegmenation node.

Text Segmentation is the process of dividing a continuous text into meaningful
units, such as words, sentences, or topics, to facilitate easier analysis and
understanding.

#### zero\_shot\_classification

```python
def zero_shot_classification(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ZeroShotClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5751)

Create a ZeroShotClassification node.

#### text\_generation

```python
def text_generation(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> TextGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5755)

Create a TextGeneration node.

Creates coherent and contextually relevant textual content based on prompts or
certain parameters. Useful for chatbots, content creation, and data
augmentation.

#### audio\_intent\_detection

```python
def audio_intent_detection(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AudioIntentDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5764)

Create a AudioIntentDetection node.

Audio Intent Detection is a process that involves analyzing audio signals to
identify and interpret the underlying intentions or purposes behind spoken
words, enabling systems to understand and respond appropriately to human
speech.

#### entity\_linking

```python
def entity_linking(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> EntityLinking
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5774)

Create a EntityLinking node.

Associates identified entities in the text with specific entries in a knowledge
base or database.

#### connection

```python
def connection(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> Connection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5782)

Create a Connection node.

Connections are integration that allow you to connect your AI agents to
external tools

#### visual\_question\_answering

```python
def visual_question_answering(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> VisualQuestionAnswering
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5790)

Create a VisualQuestionAnswering node.

Visual Question Answering (VQA) is a task in artificial intelligence that
involves analyzing an image and providing accurate, contextually relevant
answers to questions posed about the visual content of that image.

#### loglikelihood

```python
def loglikelihood(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> Loglikelihood
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5799)

Create a Loglikelihood node.

The Log Likelihood function measures the probability of observing the given
data under a specific statistical model by taking the natural logarithm of the
likelihood function, thereby transforming the product of probabilities into a
sum, which simplifies the process of optimization and parameter estimation.

#### language\_identification\_audio

```python
def language_identification_audio(asset_id: Union[str, asset.Asset], *args,
                                  **kwargs) -> LanguageIdentificationAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5809)

Create a LanguageIdentificationAudio node.

The Language Identification Audio function analyzes audio input to determine
and identify the language being spoken.

#### fact\_checking

```python
def fact_checking(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> FactChecking
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5819)

Create a FactChecking node.

Fact Checking is the process of verifying the accuracy and truthfulness of
information, statements, or claims by cross-referencing with reliable sources
and evidence.

#### table\_question\_answering

```python
def table_question_answering(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> TableQuestionAnswering
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5828)

Create a TableQuestionAnswering node.

The task of question answering over tables is given an input table (or a set of
tables) T and a natural language question Q (a user query), output the correct
answer A

#### speech\_classification

```python
def speech_classification(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> SpeechClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5837)

Create a SpeechClassification node.

Categorizes audio clips based on their content, aiding in content organization
and targeted actions.

#### inverse\_text\_normalization

```python
def inverse_text_normalization(asset_id: Union[str, asset.Asset], *args,
                               **kwargs) -> InverseTextNormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5845)

Create a InverseTextNormalization node.

Inverse Text Normalization is the process of converting spoken or written
language in its normalized form, such as numbers, dates, and abbreviations,
back into their original, more complex or detailed textual representations.

#### multi\_class\_image\_classification

```python
def multi_class_image_classification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> MultiClassImageClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5856)

Create a MultiClassImageClassification node.

Multi Class Image Classification is a machine learning task where an algorithm
is trained to categorize images into one of several predefined classes or
categories based on their visual content.

#### asr\_gender\_classification

```python
def asr_gender_classification(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> AsrGenderClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5867)

Create a AsrGenderClassification node.

The ASR Gender Classification function analyzes audio recordings to determine
and classify the speaker&#x27;s gender based on their voice characteristics.

#### summarization

```python
def summarization(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> Summarization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5875)

Create a Summarization node.

Text summarization is the process of distilling the most important information
from a source (or sources) to produce an abridged version for a particular user
(or users) and task (or tasks)

#### topic\_modeling

```python
def topic_modeling(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> TopicModeling
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5884)

Create a TopicModeling node.

Topic modeling is a type of statistical modeling for discovering the abstract
“topics” that occur in a collection of documents.

#### audio\_reconstruction

```python
def audio_reconstruction(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> AudioReconstruction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5892)

Create a AudioReconstruction node.

Audio Reconstruction is the process of restoring or recreating audio signals
from incomplete, damaged, or degraded recordings to achieve a high-quality,
accurate representation of the original sound.

#### text\_embedding

```python
def text_embedding(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> TextEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5901)

Create a TextEmbedding node.

Text embedding is a process that converts text into numerical vectors,
capturing the semantic meaning and contextual relationships of words or
phrases, enabling machines to understand and analyze natural language more
effectively.

#### detect\_language\_from\_text

```python
def detect_language_from_text(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> DetectLanguageFromText
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5911)

Create a DetectLanguageFromText node.

Detect Language From Text

#### extract\_audio\_from\_video

```python
def extract_audio_from_video(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ExtractAudioFromVideo
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5918)

Create a ExtractAudioFromVideo node.

Isolates and extracts audio tracks from video files, aiding in audio analysis
or transcription tasks.

#### scene\_detection

```python
def scene_detection(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> SceneDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5926)

Create a SceneDetection node.

Scene detection is used for detecting transitions between shots in a video to
split it into basic temporal segments.

#### text\_to\_image\_generation

```python
def text_to_image_generation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> TextToImageGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5934)

Create a TextToImageGeneration node.

Creates a visual representation based on textual input, turning descriptions
into pictorial forms. Used in creative processes and content generation.

#### auto\_mask\_generation

```python
def auto_mask_generation(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> AutoMaskGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5942)

Create a AutoMaskGeneration node.

Auto-mask generation refers to the automated process of creating masks in image
processing or computer vision, typically for segmentation tasks. A mask is a
binary or multi-class image that labels different parts of an image, usually
separating the foreground (objects of interest) from the background, or
identifying specific object classes in an image.

#### audio\_language\_identification

```python
def audio_language_identification(asset_id: Union[str, asset.Asset], *args,
                                  **kwargs) -> AudioLanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5953)

Create a AudioLanguageIdentification node.

Audio Language Identification is a process that involves analyzing an audio
recording to determine the language being spoken.

#### facial\_recognition

```python
def facial_recognition(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> FacialRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5963)

Create a FacialRecognition node.

A facial recognition system is a technology capable of matching a human face
from a digital image or a video frame against a database of faces

#### question\_answering

```python
def question_answering(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> QuestionAnswering
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5971)

Create a QuestionAnswering node.

building systems that automatically answer questions posed by humans in a
natural language usually from a given text

#### image\_impainting

```python
def image_impainting(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ImageImpainting
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5979)

Create a ImageImpainting node.

Image inpainting is a process that involves filling in missing or damaged parts
of an image in a way that is visually coherent and seamlessly blends with the
surrounding areas, often using advanced algorithms and techniques to restore
the image to its original or intended appearance.

#### text\_reconstruction

```python
def text_reconstruction(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextReconstruction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5989)

Create a TextReconstruction node.

Text Reconstruction is a process that involves piecing together fragmented or
incomplete text data to restore it to its original, coherent form.

#### script\_execution

```python
def script_execution(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ScriptExecution
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L5997)

Create a ScriptExecution node.

Script Execution refers to the process of running a set of programmed
instructions or code within a computing environment, enabling the automated
performance of tasks, calculations, or operations as defined by the script.

#### semantic\_segmentation

```python
def semantic_segmentation(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> SemanticSegmentation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6006)

Create a SemanticSegmentation node.

Semantic segmentation is a computer vision process that involves classifying
each pixel in an image into a predefined category, effectively partitioning the
image into meaningful segments based on the objects or regions they represent.

#### audio\_emotion\_detection

```python
def audio_emotion_detection(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> AudioEmotionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6015)

Create a AudioEmotionDetection node.

Audio Emotion Detection is a technology that analyzes vocal characteristics and
patterns in audio recordings to identify and classify the emotional state of
the speaker.

#### image\_captioning

```python
def image_captioning(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ImageCaptioning
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6024)

Create a ImageCaptioning node.

Image Captioning is a process that involves generating a textual description of
an image, typically using machine learning models to analyze the visual content
and produce coherent and contextually relevant sentences that describe the
objects, actions, and scenes depicted in the image.

#### split\_on\_linebreak

```python
def split_on_linebreak(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SplitOnLinebreak
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6034)

Create a SplitOnLinebreak node.

The &quot;Split On Linebreak&quot; function divides a given string into a list of
substrings, using linebreaks (newline characters) as the points of separation.

#### style\_transfer

```python
def style_transfer(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> StyleTransfer
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6042)

Create a StyleTransfer node.

Style Transfer is a technique in artificial intelligence that applies the
visual style of one image (such as the brushstrokes of a famous painting) to
the content of another image, effectively blending the artistic elements of the
first image with the subject matter of the second.

#### base\_model

```python
def base_model(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> BaseModel
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6052)

Create a BaseModel node.

The Base-Model function serves as a foundational framework designed to provide
essential features and capabilities upon which more specialized or advanced
models can be built and customized.

#### image\_manipulation

```python
def image_manipulation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> ImageManipulation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6061)

Create a ImageManipulation node.

Image Manipulation refers to the process of altering or enhancing digital
images using various techniques and tools to achieve desired visual effects,
correct imperfections, or transform the image&#x27;s appearance.

#### video\_embedding

```python
def video_embedding(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> VideoEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6070)

Create a VideoEmbedding node.

Video Embedding is a process that transforms video content into a fixed-
dimensional vector representation, capturing essential features and patterns to
facilitate tasks such as retrieval, classification, and recommendation.

#### dialect\_detection

```python
def dialect_detection(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> DialectDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6079)

Create a DialectDetection node.

Identifies specific dialects within a language, aiding in localized content
creation or user experience personalization.

#### fill\_text\_mask

```python
def fill_text_mask(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> FillTextMask
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6087)

Create a FillTextMask node.

Completes missing parts of a text based on the context, ideal for content
generation or data augmentation tasks.

#### activity\_detection

```python
def activity_detection(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> ActivityDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6095)

Create a ActivityDetection node.

detection of the presence or absence of human speech, used in speech
processing.

#### select\_supplier\_for\_translation

```python
def select_supplier_for_translation(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> SelectSupplierForTranslation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6103)

Create a SelectSupplierForTranslation node.

Supplier For Translation

#### expression\_detection

```python
def expression_detection(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> ExpressionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6112)

Create a ExpressionDetection node.

Expression Detection is the process of identifying and analyzing facial
expressions to interpret emotions or intentions using AI and computer vision
techniques.

#### video\_generation

```python
def video_generation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> VideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6121)

Create a VideoGeneration node.

Produces video content based on specific inputs or datasets. Can be used for
simulations, animations, or even deepfake detection.

#### image\_analysis

```python
def image_analysis(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> ImageAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6129)

Create a ImageAnalysis node.

Image analysis is the extraction of meaningful information from images

#### noise\_removal

```python
def noise_removal(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> NoiseRemoval
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6136)

Create a NoiseRemoval node.

Noise Removal is a process that involves identifying and eliminating unwanted
random variations or disturbances from an audio signal to enhance the clarity
and quality of the underlying information.

#### image\_and\_video\_analysis

```python
def image_and_video_analysis(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ImageAndVideoAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6145)

Create a ImageAndVideoAnalysis node.

#### keyword\_extraction

```python
def keyword_extraction(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> KeywordExtraction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6149)

Create a KeywordExtraction node.

It helps concise the text and obtain relevant keywords Example use-cases are
finding topics of interest from a news article and identifying the problems
based on customer reviews and so.

#### split\_on\_silence

```python
def split_on_silence(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SplitOnSilence
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6158)

Create a SplitOnSilence node.

The &quot;Split On Silence&quot; function divides an audio recording into separate
segments based on periods of silence, allowing for easier editing and analysis
of individual sections.

#### intent\_recognition

```python
def intent_recognition(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> IntentRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6167)

Create a IntentRecognition node.

classify the user&#x27;s utterance (provided in varied natural language)  or text
into one of several predefined classes, that is, intents.

#### depth\_estimation

```python
def depth_estimation(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> DepthEstimation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6175)

Create a DepthEstimation node.

Depth estimation is a computational process that determines the distance of
objects from a viewpoint, typically using visual data from cameras or sensors
to create a three-dimensional understanding of a scene.

#### connector

```python
def connector(asset_id: Union[str, asset.Asset], *args, **kwargs) -> Connector
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6184)

Create a Connector node.

Connectors are integration that allow you to connect your AI agents to external
tools

#### speaker\_recognition

```python
def speaker_recognition(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> SpeakerRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6192)

Create a SpeakerRecognition node.

In speaker identification, an utterance from an unknown speaker is analyzed and
compared with speech models of known speakers.

#### syntax\_analysis

```python
def syntax_analysis(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> SyntaxAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6200)

Create a SyntaxAnalysis node.

Is the process of analyzing natural language with the rules of a formal
grammar. Grammatical rules are applied to categories and groups of words, not
individual words. Syntactic analysis basically assigns a semantic structure to
text.

#### entity\_sentiment\_analysis

```python
def entity_sentiment_analysis(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> EntitySentimentAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6210)

Create a EntitySentimentAnalysis node.

Entity Sentiment Analysis combines both entity analysis and sentiment analysis
and attempts to determine the sentiment (positive or negative) expressed about
entities within the text.

#### classification\_metric

```python
def classification_metric(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> ClassificationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6219)

Create a ClassificationMetric node.

A Classification Metric is a quantitative measure used to evaluate the quality
and effectiveness of classification models.

#### text\_detection

```python
def text_detection(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> TextDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6227)

Create a TextDetection node.

detect text regions in the complex background and label them with bounding
boxes.

#### guardrails

```python
def guardrails(asset_id: Union[str, asset.Asset], *args,
               **kwargs) -> Guardrails
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6235)

Create a Guardrails node.

 Guardrails are governance rules that enforce security, compliance, and
operational best practices, helping prevent mistakes and detect suspicious
activity

#### emotion\_detection

```python
def emotion_detection(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> EmotionDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6244)

Create a EmotionDetection node.

Identifies human emotions from text or audio, enhancing user experience in
chatbots or customer feedback analysis.

#### video\_forced\_alignment

```python
def video_forced_alignment(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> VideoForcedAlignment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6252)

Create a VideoForcedAlignment node.

Aligns the transcription of spoken content in a video with its corresponding
timecodes, facilitating subtitle creation.

#### image\_content\_moderation

```python
def image_content_moderation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> ImageContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6260)

Create a ImageContentModeration node.

Detects and filters out inappropriate or harmful images, essential for
platforms with user-generated visual content.

#### text\_summarization

```python
def text_summarization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> TextSummarization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6268)

Create a TextSummarization node.

Extracts the main points from a larger body of text, producing a concise
summary without losing the primary message.

#### image\_to\_video\_generation

```python
def image_to_video_generation(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> ImageToVideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6276)

Create a ImageToVideoGeneration node.

The Image To Video Generation function transforms a series of static images
into a cohesive, dynamic video sequence, often incorporating transitions,
effects, and synchronization with audio to create a visually engaging
narrative.

#### video\_understanding

```python
def video_understanding(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> VideoUnderstanding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6286)

Create a VideoUnderstanding node.

Video Understanding is the process of analyzing and interpreting video content
to extract meaningful information, such as identifying objects, actions,
events, and contextual relationships within the footage.

#### text\_generation\_metric\_default

```python
def text_generation_metric_default(asset_id: Union[str, asset.Asset], *args,
                                   **kwargs) -> TextGenerationMetricDefault
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6295)

Create a TextGenerationMetricDefault node.

The &quot;Text Generation Metric Default&quot; function provides a standard set of
evaluation metrics for assessing the quality and performance of text generation
models.

#### text\_to\_video\_generation

```python
def text_to_video_generation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> TextToVideoGeneration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6306)

Create a TextToVideoGeneration node.

Text To Video Generation is a process that converts written descriptions or
scripts into dynamic, visual video content using advanced algorithms and
artificial intelligence.

#### video\_label\_detection

```python
def video_label_detection(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> VideoLabelDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6315)

Create a VideoLabelDetection node.

Identifies and tags objects, scenes, or activities within a video. Useful for
content indexing and recommendation systems.

#### text\_spam\_detection

```python
def text_spam_detection(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextSpamDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6323)

Create a TextSpamDetection node.

Identifies and filters out unwanted or irrelevant text content, ideal for
moderating user-generated content or ensuring quality in communication
platforms.

#### text\_content\_moderation

```python
def text_content_moderation(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> TextContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6332)

Create a TextContentModeration node.

Scans and identifies potentially harmful, offensive, or inappropriate textual
content, ensuring safer user environments.

#### audio\_transcript\_improvement

```python
def audio_transcript_improvement(asset_id: Union[str, asset.Asset], *args,
                                 **kwargs) -> AudioTranscriptImprovement
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6340)

Create a AudioTranscriptImprovement node.

Refines and corrects transcriptions generated from audio data, improving
readability and accuracy.

#### audio\_transcript\_analysis

```python
def audio_transcript_analysis(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> AudioTranscriptAnalysis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6350)

Create a AudioTranscriptAnalysis node.

Analyzes transcribed audio data for insights, patterns, or specific information
extraction.

#### speech\_non\_speech\_classification

```python
def speech_non_speech_classification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> SpeechNonSpeechClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6358)

Create a SpeechNonSpeechClassification node.

Differentiates between speech and non-speech audio segments. Great for editing
software and transcription services to exclude irrelevant audio.

#### audio\_generation\_metric

```python
def audio_generation_metric(asset_id: Union[str, asset.Asset], *args,
                            **kwargs) -> AudioGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6368)

Create a AudioGenerationMetric node.

The Audio Generation Metric is a quantitative measure used to evaluate the
quality, accuracy, and overall performance of audio generated by artificial
intelligence systems, often considering factors such as fidelity,
intelligibility, and similarity to human-produced audio.

#### named\_entity\_recognition

```python
def named_entity_recognition(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> NamedEntityRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6378)

Create a NamedEntityRecognition node.

Identifies and classifies named entities (e.g., persons, organizations,
locations) within text. Useful for information extraction, content tagging, and
search enhancements.

#### speech\_synthesis

```python
def speech_synthesis(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> SpeechSynthesis
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6387)

Create a SpeechSynthesis node.

Generates human-like speech from written text. Ideal for text-to-speech
applications, audiobooks, and voice assistants.

#### document\_information\_extraction

```python
def document_information_extraction(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> DocumentInformationExtraction
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6395)

Create a DocumentInformationExtraction node.

Document Information Extraction is the process of automatically identifying,
extracting, and structuring relevant data from unstructured or semi-structured
documents, such as invoices, receipts, contracts, and forms, to facilitate
easier data management and analysis.

#### ocr

```python
def ocr(asset_id: Union[str, asset.Asset], *args, **kwargs) -> Ocr
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6407)

Create a Ocr node.

Converts images of typed, handwritten, or printed text into machine-encoded
text. Used in digitizing printed texts for data retrieval.

#### subtitling\_translation

```python
def subtitling_translation(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> SubtitlingTranslation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6415)

Create a SubtitlingTranslation node.

Converts the text of subtitles from one language to another, ensuring context
and cultural nuances are maintained. Essential for global content distribution.

#### text\_to\_audio

```python
def text_to_audio(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> TextToAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6423)

Create a TextToAudio node.

The Text to Audio function converts written text into spoken words, allowing
users to listen to the content instead of reading it.

#### multilingual\_speech\_recognition

```python
def multilingual_speech_recognition(asset_id: Union[str, asset.Asset], *args,
                                    **kwargs) -> MultilingualSpeechRecognition
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6431)

Create a MultilingualSpeechRecognition node.

Multilingual Speech Recognition is a technology that enables the automatic
transcription of spoken language into text across multiple languages, allowing
for seamless communication and understanding in diverse linguistic contexts.

#### offensive\_language\_identification

```python
def offensive_language_identification(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> OffensiveLanguageIdentification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6442)

Create a OffensiveLanguageIdentification node.

Detects language or phrases that might be considered offensive, aiding in
content moderation and creating respectful user interactions.

#### benchmark\_scoring\_mt

```python
def benchmark_scoring_mt(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> BenchmarkScoringMt
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6452)

Create a BenchmarkScoringMt node.

Benchmark Scoring MT is a function designed to evaluate and score machine
translation systems by comparing their output against a set of predefined
benchmarks, thereby assessing their accuracy and performance.

#### speaker\_diarization\_audio

```python
def speaker_diarization_audio(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> SpeakerDiarizationAudio
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6461)

Create a SpeakerDiarizationAudio node.

Identifies individual speakers and their respective speech segments within an
audio clip. Ideal for multi-speaker recordings or conference calls.

#### voice\_cloning

```python
def voice_cloning(asset_id: Union[str, asset.Asset], *args,
                  **kwargs) -> VoiceCloning
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6469)

Create a VoiceCloning node.

Replicates a person&#x27;s voice based on a sample, allowing for the generation of
speech in that person&#x27;s tone and style. Used cautiously due to ethical
considerations.

#### search

```python
def search(asset_id: Union[str, asset.Asset], *args, **kwargs) -> Search
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6478)

Create a Search node.

An algorithm that identifies and returns data or items that match particular
keywords or conditions from a dataset. A fundamental tool for databases and
websites.

#### object\_detection

```python
def object_detection(asset_id: Union[str, asset.Asset], *args,
                     **kwargs) -> ObjectDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6487)

Create a ObjectDetection node.

Object Detection is a computer vision technology that identifies and locates
objects within an image, typically by drawing bounding boxes around the
detected objects and classifying them into predefined categories.

#### diacritization

```python
def diacritization(asset_id: Union[str, asset.Asset], *args,
                   **kwargs) -> Diacritization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6496)

Create a Diacritization node.

Adds diacritical marks to text, essential for languages where meaning can
change based on diacritics.

#### speaker\_diarization\_video

```python
def speaker_diarization_video(asset_id: Union[str, asset.Asset], *args,
                              **kwargs) -> SpeakerDiarizationVideo
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6504)

Create a SpeakerDiarizationVideo node.

Segments a video based on different speakers, identifying when each individual
speaks. Useful for transcriptions and understanding multi-person conversations.

#### audio\_forced\_alignment

```python
def audio_forced_alignment(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AudioForcedAlignment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6512)

Create a AudioForcedAlignment node.

Synchronizes phonetic and phonological text with the corresponding segments in
an audio file. Useful in linguistic research and detailed transcription tasks.

#### token\_classification

```python
def token_classification(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> TokenClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6520)

Create a TokenClassification node.

Token-level classification means that each token will be given a label, for
example a part-of-speech tagger will classify each word as one particular part
of speech.

#### topic\_classification

```python
def topic_classification(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> TopicClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6529)

Create a TopicClassification node.

Assigns categories or topics to a piece of text based on its content,
facilitating content organization and retrieval.

#### intent\_classification

```python
def intent_classification(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> IntentClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6537)

Create a IntentClassification node.

Intent Classification is a natural language processing task that involves
analyzing and categorizing user text input to determine the underlying purpose
or goal behind the communication, such as booking a flight, asking for weather
information, or setting a reminder.

#### video\_content\_moderation

```python
def video_content_moderation(asset_id: Union[str, asset.Asset], *args,
                             **kwargs) -> VideoContentModeration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6547)

Create a VideoContentModeration node.

Automatically reviews video content to detect and possibly remove inappropriate
or harmful material. Essential for user-generated content platforms.

#### text\_generation\_metric

```python
def text_generation_metric(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> TextGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6555)

Create a TextGenerationMetric node.

A Text Generation Metric is a quantitative measure used to evaluate the quality
and effectiveness of text produced by natural language processing models, often
assessing aspects such as coherence, relevance, fluency, and adherence to given
prompts or instructions.

#### image\_embedding

```python
def image_embedding(asset_id: Union[str, asset.Asset], *args,
                    **kwargs) -> ImageEmbedding
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6565)

Create a ImageEmbedding node.

Image Embedding is a process that transforms an image into a fixed-dimensional
vector representation, capturing its essential features and enabling efficient
comparison, retrieval, and analysis in various machine learning and computer
vision tasks.

#### image\_label\_detection

```python
def image_label_detection(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> ImageLabelDetection
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6575)

Create a ImageLabelDetection node.

Identifies objects, themes, or topics within images, useful for image
categorization, search, and recommendation systems.

#### image\_colorization

```python
def image_colorization(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> ImageColorization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6583)

Create a ImageColorization node.

Image colorization is a process that involves adding color to grayscale images,
transforming them from black-and-white to full-color representations, often
using advanced algorithms and machine learning techniques to predict and apply
the appropriate hues and shades.

#### metric\_aggregation

```python
def metric_aggregation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> MetricAggregation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6593)

Create a MetricAggregation node.

Metric Aggregation is a function that computes and summarizes numerical data by
applying statistical operations, such as averaging, summing, or finding the
minimum and maximum values, to provide insights and facilitate analysis of
large datasets.

#### instance\_segmentation

```python
def instance_segmentation(asset_id: Union[str, asset.Asset], *args,
                          **kwargs) -> InstanceSegmentation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6603)

Create a InstanceSegmentation node.

Instance segmentation is a computer vision task that involves detecting and
delineating each distinct object within an image, assigning a unique label and
precise boundary to every individual instance of objects, even if they belong
to the same category.

#### other\_\_multipurpose\_

```python
def other__multipurpose_(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> OtherMultipurpose
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6613)

Create a OtherMultipurpose node.

The &quot;Other (Multipurpose)&quot; function serves as a versatile category designed to
accommodate a wide range of tasks and activities that do not fit neatly into
predefined classifications, offering flexibility and adaptability for various
needs.

#### speech\_translation

```python
def speech_translation(asset_id: Union[str, asset.Asset], *args,
                       **kwargs) -> SpeechTranslation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6623)

Create a SpeechTranslation node.

Speech Translation is a technology that converts spoken language in real-time
from one language to another, enabling seamless communication between speakers
of different languages.

#### referenceless\_text\_generation\_metric\_default

```python
def referenceless_text_generation_metric_default(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessTextGenerationMetricDefault
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6632)

Create a ReferencelessTextGenerationMetricDefault node.

The Referenceless Text Generation Metric Default is a function designed to
evaluate the quality of generated text without relying on reference texts for
comparison.

#### referenceless\_text\_generation\_metric

```python
def referenceless_text_generation_metric(
        asset_id: Union[str, asset.Asset], *args,
        **kwargs) -> ReferencelessTextGenerationMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6643)

Create a ReferencelessTextGenerationMetric node.

The Referenceless Text Generation Metric is a method for evaluating the quality
of generated text without requiring a reference text for comparison, often
leveraging models or algorithms to assess coherence, relevance, and fluency
based on intrinsic properties of the text itself.

#### text\_denormalization

```python
def text_denormalization(asset_id: Union[str, asset.Asset], *args,
                         **kwargs) -> TextDenormalization
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6655)

Create a TextDenormalization node.

Converts standardized or normalized text into its original, often more
readable, form. Useful in natural language generation tasks.

#### image\_compression

```python
def image_compression(asset_id: Union[str, asset.Asset], *args,
                      **kwargs) -> ImageCompression
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6663)

Create a ImageCompression node.

Reduces the size of image files without significantly compromising their visual
quality. Useful for optimizing storage and improving webpage load times.

#### text\_classification

```python
def text_classification(asset_id: Union[str, asset.Asset], *args,
                        **kwargs) -> TextClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6671)

Create a TextClassification node.

Categorizes text into predefined groups or topics, facilitating content
organization and targeted actions.

#### asr\_age\_classification

```python
def asr_age_classification(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AsrAgeClassification
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6679)

Create a AsrAgeClassification node.

The ASR Age Classification function is designed to analyze audio recordings of
speech to determine the speaker&#x27;s age group by leveraging automatic speech
recognition (ASR) technology and machine learning algorithms.

#### asr\_quality\_estimation

```python
def asr_quality_estimation(asset_id: Union[str, asset.Asset], *args,
                           **kwargs) -> AsrQualityEstimation
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/pipeline.py#L6688)

Create a AsrQualityEstimation node.

ASR Quality Estimation is a process that evaluates the accuracy and reliability
of automatic speech recognition systems by analyzing their performance in
transcribing spoken language into text.

