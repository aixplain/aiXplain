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
python3.8 aixplain_diarization_streaming_client.py --file-path=test_dia.wav --cacert=./client-crt/ca.crt --cert=./client-crt/tls.crt --key=./client-crt/tls.key
```

The arguments --cacert, --cert, and --key are used to provide the paths to the necessary certificate files for mTLS.

The --file-path argument is used to specify the path to the input file.
