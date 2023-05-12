import argparse
import logging
from pydub import AudioSegment

FRAME_RATE = 16000

def create_compatible_audio(source_path, dest_path):
    """
    Function to resample an audio file and change the number of channels if there are more than 1.
    """
    # Load the audio file
    sound_file = AudioSegment.from_file(source_path)
    updated = False
    if sound_file.frame_rate != FRAME_RATE:
        # Resample the audio file
        logging.info(f'Resampling {sound_file.frame_rate} -> {FRAME_RATE}')
        sound_file = sound_file.set_frame_rate(FRAME_RATE)
        updated = True
    # If the audio file has more than one channel, convert it to mono
    if sound_file.channels > 1:
        logging.info(f'Changing no. channels {sound_file.channels} -> 1')
        sound_file = sound_file.set_channels(1)
        updated = True
    if updated:
        # Export the processed audio file
        sound_file.export(dest_path, format="wav")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some audio files.')
    parser.add_argument('--source_path', required=True, help='Source path for the audio file')
    parser.add_argument('--dest_path', required=True, help='Destination path for the processed audio file')

    args = parser.parse_args()

    create_compatible_audio(args.source_path, args.dest_path)
