"""
============================================================================
 SPEECH TO TEXT — audio transcribe karna, do tareeke se
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

`faster-whisper` OpenAI ke apne Whisper model ka architecture hi chalata
hai, bas open-source aur poori tarah tumhare khud ke CPU par — free, koi
API key nahi, koi audio tumhari machine se bahar nahi jaata. Yeh wahi
underlying idea hai jo OpenAI ke hosted Whisper API ka hai, bas unke
servers ki jagah locally chal raha hai, isliye dono engines ek clear
recording ke liye comparable output dete hain, aur dono genuinely same
cheezon se struggle karte hain (heavy accents, background noise,
cross-talk).

Hum "tiny" wala local model size use karte hain — CPU par responsive feel
karne jitna fast hai, bade sizes ("base", "small", ...) ke comparison mein
thodi accuracy ki keemat par.
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
    # `segments` time-stamped chunks ka ek generator hai — humein yahan
    # sirf plain text chahiye, isliye har chunk ke text ko jod dete hain.
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
