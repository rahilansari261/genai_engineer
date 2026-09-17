"""
============================================================================
 MODERATION — text ko OpenAI ke Moderation API ke against check karna
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

OpenAI ek alag, FREE, purpose-built model chalata hai jiska bas ek hi kaam
hai: "kya yeh text kisi content policy (violence, self-harm, hate, minors
wala sexual content, etc.) ko violate karta hua lagta hai?" Yahi Moderation
API hai.

Is project ka important design idea: hum conversation ke DONO sides check
karte hain —
  - USER ka message, use main chat model ko bhejne se PEHLE
  - AI ka reply, use user ko wapas dikhane se PEHLE
Ek bad request ko early pakadna (expensive chat model ko call karne ka
paisa kharch karne se pehle) "input moderation" hai. Ek bad REPLY ko user
ke dekhne se pehle pakadna (agar chat model khud hi kuch aisa bol de jo
usko nahi bolna chahiye tha) "output moderation" hai. Real production apps
generally dono karte hain.
============================================================================
"""

import os
from dataclasses import dataclass


@dataclass
class ModerationResult:
    """Ek simple container is baat ke liye ki "yeh flag hua ya nahi, aur
    kis wajah se"."""

    flagged: bool
    categories: list[str]


async def moderate(text: str) -> ModerationResult:
    """
    `text` ko OpenAI ke Moderation API ko bhejta hai aur bata deta hai ki
    woh flag hua ya nahi, aur konsi specific categories (jaise "violence",
    "harassment") ne flag trip kiya.

    Agar koi OpenAI key configure nahi hai to RuntimeError raise karta
    hai — main.py mein caller isko "moderation unavailable" treat karta
    hai (yeh "check kiya aur sab theek hai" wali situation se bilkul alag
    hai), taaki UI yeh jhooth na bole ki usne kuch aisa check kiya jo woh
    kar hi nahi paya.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — moderation requires it, even if you're chatting with a different provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    # omni-moderation-latest OpenAI ka current moderation model hai — yeh
    # free hai use karne ke liye aur us model se bilkul alag hai jisse tum
    # chat karte ho.
    response = await client.moderations.create(model="omni-moderation-latest", input=text)
    result = response.results[0]

    # `result.categories` ek object hai jisme har category ke liye ek
    # True/False field hai (jaise .violence, .harassment, .self_harm). Hum
    # sirf True waali cheezon ko category names ki ek plain list mein badal
    # dete hain, jo raw object dikhane ke muqable UI mein dikhana kahin
    # zyada aasan hai.
    flagged_categories = [
        category
        for category, is_flagged in result.categories.model_dump().items()
        if is_flagged
    ]

    return ModerationResult(flagged=result.flagged, categories=flagged_categories)
