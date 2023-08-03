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

"""The Python implementation of the aiXplain speech recoginition streaming client."""

import argparse
import time
from typing import List
import grpc
import logging

import aixplain_diarization_streaming_pb2 as pb
import aixplain_diarization_streaming_pb2_grpc

FRAME_RATE = 16000

def generate_payloads(file_path, latency):
    stream_configuration = pb.DiarizationRequest(
        config=pb.AudioConfig(encoding="LINEAR16", hertz=FRAME_RATE, language_code="en"),
        latency=latency,
        diarization_config=pb.DiarizationConfig(min_speaker_count=1, max_speaker_count=3),
    )
    yield stream_configuration
    # Iterate over the raw bytes in chunks
    chunk_size = 16000 # half a second of audio
    i = 0
    with open(file_path, "rb") as audio_file:
        while True:
            chunk = audio_file.read(chunk_size)
            if not chunk:
                break
            logging.info(f'Sending chunk {i}')
            payload = pb.DiarizationRequest(audio_content=chunk)
            yield payload
            i += 1
            time.sleep(0.5) # simulate streaming by introducing sleep

def grpc_duration_to_seconds(duration):
    seconds = float(duration.seconds)
    nanos = float(duration.nanos) / 1e9
    return seconds + nanos

def consume_results(response: List[pb.DiarizationResponse]):
    for inference in response:
        if inference.is_final:
            logging.info(f'Received is_final={inference.is_final}. total_time={inference.end_time.seconds}.{str(inference.end_time.nanos)[:3]}')
        if len(inference.segments):
            logging.info(f'Turns:')
            for segment in inference.segments:
                logging.info(f"{segment.speaker_tag} \
                    start:{grpc_duration_to_seconds(segment.start_time)}\tend:{grpc_duration_to_seconds(segment.end_time)}")

def _stream_file(channel, file_path, latency):
    stub = aixplain_diarization_streaming_pb2_grpc.AixplainDiarizationStreamingStub(channel)
    response = stub.Diarize(generate_payloads(file_path, latency))
    consume_results(response)

def run_insecure(host, file_path, latency):
    with grpc.insecure_channel(host, options=(('grpc.ssl_target_name_override', host),)) as channel:
        _stream_file(channel, file_path, latency)

def run(host, client_cert, client_key, ca_cert, file_path, latency):
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
        _stream_file(channel, file_path, latency)


if __name__ == "__main__":
    log_format = "%(asctime)s - %(levelname)-7s - P%(process)d: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    parser = argparse.ArgumentParser(description="aiXplain speech recognition streaming client.")

    parser.add_argument('--addr', default='localhost:50051', help='the address to connect to (default "localhost:50051")')
    parser.add_argument('--cacert', default='./client-crt/ca.crt', help='ca cert for mTLS (default "./client-crt/ca.crt")')
    parser.add_argument('--cert', default='./client-crt/tls.crt', help='client cert for mTLS (default "./client-crt/tls.crt")')
    parser.add_argument('--key', default='./client-crt/tls.key', help='client key for mTLS (default "./client-crt/tls.key")')
    parser.add_argument('--insecure', action='store_true', help='use insecure connection (no mTLS)')
    parser.add_argument('--file-path', help='audio file to stream from')
    parser.add_argument('--latency', type=float, help='Model latency')

    args = parser.parse_args()

    if args.insecure:
        run_insecure(args.addr, args.file_path, args.latency)
    else:
        run(args.addr, args.cert, args.key, args.cacert, args.file_path, args.latency)
