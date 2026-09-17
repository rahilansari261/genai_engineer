"""
============================================================================
 MODERATION — text ko OpenAI ke Moderation API se check karna
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

OpenAI ek alag, FREE, purpose-built model chalata hai jiska bas ek hi kaam
hai: "kya yeh text kisi content policy (violence, self-harm, hate, minors
involving sexual content, etc.) ko violate karta hua lagta hai?" Yahi
Moderation API hai.

Is project ka important design idea: hum conversation ke DONO sides check
karte hain —
  - USER ka message, isse main chat model ko bhejne se PEHLE
  - AI ka reply, isse user ko kabhi dikhane se PEHLE
Ek bura request jaldi pakadna (expensive chat model ko call karke paisa
kharch karne se pehle) "input moderation" hai. Ek buri REPLY ko user ke
dekhne se pehle pakadna (agar chat model ne khud kuch aisa bol diya jo
usse nahi bolna chahiye tha) "output moderation" hai. Real production apps
typically dono karte hain.
============================================================================
"""

import os
from dataclasses import dataclass


@dataclass
class ModerationResult:
    """Ek simple container: "yeh flag hua tha ya nahi, aur kis wajah se"."""

    flagged: bool
    categories: list[str]


async def moderate(text: str) -> ModerationResult:
    """
    `text` ko OpenAI ke Moderation API ko bhejta hai aur wapas batata hai ki
    yeh flag hua ya nahi, aur kaunsi specific categories (jaise "violence",
    "harassment") ki wajah se flag laga.

    Agar koi OpenAI key configured nahi hai to RuntimeError raise karta
    hai — main.py mein caller isko "moderation unavailable" maanta hai
    (ek alag situation "check kiya aur sab theek hai" se), taaki UI jhooth
    na bole ki usne kuch check kiya jo woh actually check hi nahi kar
    paayi.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — moderation requires it, even if you're chatting with a different provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    # omni-moderation-latest OpenAI ka current moderation model hai — yeh
    # use karna free hai aur us model se bilkul alag hai jisse tum chat
    # karte ho.
    response = await client.moderations.create(model="omni-moderation-latest", input=text)
    result = response.results[0]

    # `result.categories` ek object hai jismein har category ke liye ek
    # True/False field hota hai (jaise .violence, .harassment, .self_harm).
    # Hum sirf True wali ko ek plain list of category names mein badal
    # dete hain, jo UI mein dikhana raw object se kahin zyada aasan hai.
    flagged_categories = [
        category
        for category, is_flagged in result.categories.model_dump().items()
        if is_flagged
    ]

    return ModerationResult(flagged=result.flagged, categories=flagged_categories)
