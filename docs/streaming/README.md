# aiXplain Client Streaming Sample

This guide will walk you through the process of connecting to and using the aiXplain streaming services.

## Prerequisites

Ensure you have Python and pip installed on your system.

## Installation

To install necessary requirements, navigate to the project directory and run the following command:


```sh
pip install -r requirements.txt
```

## Generating Stubs

We use Protocol Buffers (protobuf) to define our service interface. To generate the stubs from .proto files, use the following commands:

```bash
# For diarization
python -m grpc_tools.protoc -I./proto --python_out=. --pyi_out=. --grpc_python_out=. proto/aixplain_diarization_streaming.proto

# For speech transcription
python -m grpc_tools.protoc -I./proto --python_out=. --pyi_out=. --grpc_python_out=. proto/aixplain_speech_transcription_streaming.proto
```

Note: You can generate the stubs in any language of your choice as long as you have the protobuf compiler (protoc) installed and configured.

## Running the Client

aiXplain provides the necessary certificates for mTLS. You can pass them to the client when running it. Here's an example of how to use the diarization client:

```bash
python3.8 aixplain_speech_transcription_streaming_client.py --file-path=test_dia.wav --cacert=./client-crt/ca.crt --cert=./client-crt/tls.crt --key=./client-crt/tls.key --addr <host>:<port>
```
For transcription, you can also enable subtitle like print style with argument `--print-style=subtitle`.

```bash
python3.8 aixplain_diarization_streaming_client.py --file-path=test_dia.wav --cacert=./client-crt/ca.crt --cert=./client-crt/tls.crt --key=./client-crt/tls.key --addr <host>:<port>
```

The arguments --cacert, --cert, and --key are used to provide the paths to the necessary certificate files for mTLS.

The --file-path argument is used to specify the path to the input file.

You can configure the model's latency by setting the `--latency` argument. Values between 0.5 and 5.0 seconds are supported.

## Audio requirements

Our service is configured to process audio streamed as a single channel with a sampling rate of 16000Hz.

If the audio does not meet these specifications, the service may yield unexpected results.

To ensure compatibility, we provide a helper script that adjusts your audio files to meet these requirements.

### Installing Dependencies to run the helper script

The helper script relies on the pydub package. If you need to use the script to adjust your audio files, install pydub using pip:

```sh
pip install pydub==0.25.1
```

### Using the Helper Script

If your audio files need to be converted to meet our service's specifications, you can do this with our helper script as follows:

`python make_audio_compatible.py --source_path=input.wav --dest_path=test_dia.wav`

If your audio files already meet the specifications, you don't need to use this script or install its dependencies.
