"""Minimal WSL audio probe for PyAudio devices and stream open checks."""

from __future__ import annotations

import math
import struct
import sys
import time

import pyaudio


RATE = 48_000
CHANNELS = 1
CHUNK = 1024


def main() -> int:
    pa = pyaudio.PyAudio()
    print("PyAudio device probe")
    print(f"device_count={pa.get_device_count()}")

    for index in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(index)
        print(
            "device",
            index,
            f"name={info.get('name')!r}",
            f"in={info.get('maxInputChannels')}",
            f"out={info.get('maxOutputChannels')}",
            f"default_rate={info.get('defaultSampleRate')}",
        )

    try:
        out_stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            frames_per_buffer=CHUNK,
        )
        print("output_open_ok")
    except Exception as exc:
        print(f"output_open_failed={exc!r}")
        pa.terminate()
        return 1

    try:
        in_stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        print("input_open_ok")
    except Exception as exc:
        print(f"input_open_failed={exc!r}")
        out_stream.stop_stream()
        out_stream.close()
        pa.terminate()
        return 1

    frames = []
    for i in range(CHUNK):
        sample = int(0.2 * 32767 * math.sin(2 * math.pi * 440 * i / RATE))
        frames.append(struct.pack("<h", sample))
    tone = b"".join(frames)

    try:
        out_stream.write(tone)
        print("tone_write_ok")
    except Exception as exc:
        print(f"tone_write_failed={exc!r}")

    try:
        data = in_stream.read(CHUNK, exception_on_overflow=False)
        print(f"input_read_ok={len(data)}")
    except Exception as exc:
        print(f"input_read_failed={exc!r}")

    time.sleep(0.2)
    in_stream.stop_stream()
    in_stream.close()
    out_stream.stop_stream()
    out_stream.close()
    pa.terminate()
    print("probe_done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
