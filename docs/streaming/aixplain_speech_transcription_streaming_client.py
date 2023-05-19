# Copyright 2023 aiXplain authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the aiXplain speech transcription streaming client."""

import argparse
import sys
import time
from typing import List
import grpc
import logging

import aixplain_speech_transcription_streaming_pb2 as pb
import aixplain_speech_transcription_streaming_pb2_grpc

FRAME_RATE = 16000
FFMPEG_FORMAT = 'wav'

PS_SUBTITLE = 'subtitle'
PS_LOG = 'log'
RED = "\033[0;31m"
GREEN = "\033[0;32m"
DEFAULT = "\033[0;97m"

def grpc_duration_to_seconds(duration):
    seconds = float(duration.seconds)
    nanos = float(duration.nanos) / 1e9
    return seconds + nanos

def generate_payloads(file_path):
    # uncomment this if your audio file is not compatible
    stream_configuration = pb.SpeechRecognitionRequest(
        config=pb.AudioConfig(encoding="LINEAR16", hertz=FRAME_RATE, language_code="en"),
    )
    yield stream_configuration
    # Iterate over the raw bytes in chunks
    chunk_size = 16000 # half a second of audio
    chunk_period = 0.5
    logging.info(f'Sending chunks...')
    with open(file_path, "rb") as audio_file:
        i = 0
        while True:
            chunk = audio_file.read(chunk_size)
            if not chunk:
                break
            time.sleep((len(chunk)/chunk_size)*chunk_period) # simulate streaming by introducing sleep
            logging.debug(f'Sending chunk {i}')
            payload = pb.SpeechRecognitionRequest(audio_content=chunk)
            yield payload
            i += 1

def consume_results(response: List[pb.SpeechRecognitionResponse], print_style):
    for i, inference in enumerate(response):
        if i == 0:
            logging.info(f'Detected language {inference.language_code=}')
        if len(inference.hypotheses):
            # get the top hypothesis
            hypothesis = inference.hypotheses[0]
            transcript, confidence = hypothesis.transcript, hypothesis.confidence
            if inference.is_final:
                logging.info(f't={grpc_duration_to_seconds(inference.end_time):.3f}  conf={confidence:.2f} FINAL="{transcript}"')
                if print_style == PS_SUBTITLE:
                    sys.stdout.write(GREEN)
                    sys.stdout.write("\033[K")
                    sys.stdout.write(f'{grpc_duration_to_seconds(inference.end_time):.3f}' + ": " + transcript + "\n")
            else:
                logging.info(f't={grpc_duration_to_seconds(inference.end_time):.3f}  conf={confidence:.2f} chunk="{transcript}"')
                if print_style == PS_SUBTITLE:
                    sys.stdout.write(RED)
                    sys.stdout.write("\033[K")
                    sys.stdout.write(f'{grpc_duration_to_seconds(inference.end_time):.3f}' + ": " + transcript + "\r")

            for word in hypothesis.words:
                logging.info(f'Word: {word.word.ljust(12)} '
                    f'Start-End: {grpc_duration_to_seconds(word.start_time):.3f}-{grpc_duration_to_seconds(word.end_time):.3f} '
                    f'Confidence: {word.confidence:.3f} ')
        else:  # called at the end
            logging.info(f'{inference.is_final=} server processing_time={grpc_duration_to_seconds(inference.end_time):.3f}')
            if print_style == PS_SUBTITLE:
                sys.stdout.write(DEFAULT)
                sys.stdout.write("Exiting...\n")

def _stream_file(channel, file_path, print_style):
    stub = aixplain_speech_transcription_streaming_pb2_grpc.AixplainSpeechStreamingStub(channel)
    response = stub.SpeechRecognize(generate_payloads(file_path))
    consume_results(response, print_style)

def run_insecure(host, file_path, print_style):
    with grpc.insecure_channel(host, options=(('grpc.ssl_target_name_override', host),)) as channel:
        _stream_file(channel, file_path, print_style)

def run(host, client_cert, client_key, ca_cert, file_path, print_style):
    def create_secure_channel(host, client_cert, client_key, ca_cert):
        with open(client_cert, 'rb') as f:
            client_cert_data = f.read()

        with open(client_key, 'rb') as f:
            client_key_data = f.read()

        with open(ca_cert, 'rb') as f:
            ca_cert_data = f.read()

        credentials = grpc.ssl_channel_credentials(
            root_certificates=ca_cert_data,
            private_key=client_key_data,
            certificate_chain=client_cert_data
        )
        return grpc.secure_channel(host, credentials)
    with create_secure_channel(host, client_cert, client_key, ca_cert) as channel:
        _stream_file(channel, file_path, print_style)


if __name__ == "__main__":
    log_format = "%(asctime)s - %(levelname)-7s - P%(process)d: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    parser = argparse.ArgumentParser(description="aiXplain speech recognition streaming client.")

    parser.add_argument('--print-style', default='log', choices=[PS_SUBTITLE, PS_LOG], help='The print style, either "log" or "subtitle"')
    parser.add_argument('--addr', default='localhost:50051', help='the address to connect to (default "localhost:50051")')
    parser.add_argument('--cacert', default='./client-crt/ca.crt', help='ca cert for mTLS (default "./client-crt/ca.crt")')
    parser.add_argument('--cert', default='./client-crt/tls.crt', help='client cert for mTLS (default "./client-crt/tls.crt")')
    parser.add_argument('--key', default='./client-crt/tls.key', help='client key for mTLS (default "./client-crt/tls.key")')
    parser.add_argument('--insecure', action='store_true', help='use insecure connection (no mTLS)')
    parser.add_argument('--file-path', default="resources/conv.wav", help='audio file to stream from')

    args = parser.parse_args()

    if args.print_style == PS_SUBTITLE:
        logging.getLogger('').setLevel(logging.ERROR)

    if args.insecure:
        run_insecure(args.addr, args.file_path, args.print_style)
    else:
        run(args.addr, args.cert, args.key, args.cacert, args.file_path,  args.print_style)
