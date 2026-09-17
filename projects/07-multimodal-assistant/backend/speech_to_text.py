"""
============================================================================
 SPEECH TO TEXT — audio transcribe karna, do tarike se
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

`faster-whisper` OpenAI ke apne Whisper model architecture ko hi chalata
hai, bas open-source hai aur pura tumhare khud ke CPU par — free, koi API
key nahi, koi audio kabhi tumhari machine se bahar nahi jaata. Yeh wahi
underlying idea hai jo OpenAI ke hosted Whisper API ki hai, bas locally
chal raha hai unke servers ki jagah, isi wajah se dono engines yahan ek
clear recording ke liye comparable output dete hain, aur dono genuinely
waisi hi cheezon se struggle karte hain (heavy accents, background noise,
cross-talk).

Hum "tiny" local model size use karte hain — CPU par responsive feel karne
laayak fast, thodi accuracy ki keemat par bade sizes ("base", "small", ...)
ke muqable mein.
============================================================================
"""

import os

_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from faster_whisper import WhisperModel

        _local_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _local_model


def transcribe_local(audio_path: str) -> str:
    model = _get_local_model()
    segments, _info = model.transcribe(audio_path)
    # `segments` time-stamped chunks ka ek generator hai — yahan humein
    # sirf plain text chahiye, isliye har chunk ka text jod dete hain.
    return " ".join(segment.text.strip() for segment in segments).strip()


async def transcribe_openai(audio_path: str, model: str = "whisper-1") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(model=model, file=f)
    return response.text
