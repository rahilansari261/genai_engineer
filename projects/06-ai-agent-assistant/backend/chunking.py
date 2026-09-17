"""
============================================================================
 CHUNKING — document ko haath se overlapping pieces mein todna
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Poora document embedding model ko ek unit ki tarah dene ke liye almost
hamesha bahut bada aur bahut unfocused hota hai — tumhe "yeh poora
document" ka ek vague vector milega, jo us ek specific paragraph ko dhoondhne
ke liye bekaar hai jo actually ek specific sawaal ka jawab deta hai. Isliye
kuch bhi embed hone se pehle, use CHUNK kiya jaata hai: chhote,
overlapping pieces mein kaata jaata hai, itne chhote ki har piece roughly
EK specific cheez ke baare mein ho.

Do settings isko control karti hain, aur yeh dono ek dusre ke against
trade-off karti hain:

  chunk_size    — ek chunk ka max size (characters mein). Bahut chhota
                  hoga to chunk surrounding context kho dega ("it" hai
                  lekin pata nahi "it" kiska reference hai); bahut bada
                  hoga to chunk multiple topics ko mix kar dega, jisse
                  embed hone par woh "kis baare mein hai" dilute ho jaata
                  hai.

  chunk_overlap — ek chunk ke END ke kitne characters agle chunk ke START
                  mein repeat hote hain. Overlap ke bina, jo sentence
                  chance se ek chunk boundary par hi aa jaata hai, woh
                  beech mein se phat jaata hai, aur har half dusre ka
                  context kho deta hai.

Project 5 se as-is reuse kiya gaya hai, jahan yeh exact splitter explain
kiya gaya hai aur LangChain ke version se compare kiya gaya hai. Is
project ko yeh alag reason se chahiye: is project ke ingest.py ka ek
pehle wala version sirf blank lines par split karta tha, bina kisi
merging ke, jiski wajah se ek markdown heading ("# What Is RAG?") jo ek
lambe paragraph ke bilkul upar hota tha, apna hi ek chhota, content-free
chunk ban jaata tha — aur search_handbook tool kabhi-kabhi asli
explanation ke bajaye woh heading fragment hi return kar deta tha, jo
genuinely is baat ka hissa hai ki testing ke waqt agent ne galat answer
kyun diya (usne "RAG" ka matlab ek heading se hallucinate kar diya jiske
paas kaam karne ke liye koi body text nahi tha). Yeh splitter chhote
pieces ko chunk_size tak merge karta hai, taaki ek heading, uske baad ka
paragraph aur diagram, saath mein ek hi chunk mein rahein.
============================================================================
"""

# Order mein try kiya jaata hai, "sabse bada, sabse natural break" se
# "last resort" tak.
SEPARATORS = ["\n\n", "\n", ". ", " "]


def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    """`text` ko chunks ki ek list mein split karta hai, har chunk max
    ~chunk_size characters ka, aur consecutive chunks ke beech
    chunk_overlap characters ka context repeat hota hai."""
    chunks = _split_recursive(text.strip(), SEPARATORS, chunk_size)
    return _add_overlap(chunks, chunk_overlap)


def _split_recursive(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Recursive wala hissa: pehla separator pick karo, usi par split
    karo, aur resulting pieces ko greedily wapas chunk_size tak merge
    karo. Koi bhi single piece jo iske baad bhi chunk_size se bada hai,
    use recursively phir se AGLE, aur zyada fine-grained separator se
    split kiya jaata hai."""
    if len(text) <= chunk_size:
        return [text] if text else []

    separator = separators[0] if separators else ""
    remaining_separators = separators[1:]
    pieces = text.split(separator) if separator else list(text)

    chunks: list[str] = []
    current = ""

    for piece in pieces:
        candidate = f"{current}{separator}{piece}" if current else piece

        if len(candidate) <= chunk_size:
            # Abhi bhi fit ho raha hai — pieces ko current chunk mein
            # merge karte raho.
            current = candidate
            continue

        # Yeh piece add karne se current chunk overflow ho jaayega —
        # current chunk ko close karo aur fresh start karo.
        if current:
            chunks.append(current)
            current = ""

        if len(piece) > chunk_size:
            # Yeh EK piece apne aap mein hi bahut bada hai (jaise ek huge
            # paragraph jisme koi line break nahi hai) — finer separator
            # se recurse karo, ya agar try karne ke liye separators khatam
            # ho gaye hain to raw character count se hard-slice karo.
            if remaining_separators:
                chunks.extend(_split_recursive(piece, remaining_separators, chunk_size))
            else:
                for i in range(0, len(piece), chunk_size):
                    chunks.append(piece[i : i + chunk_size])
        else:
            current = piece

    if current:
        chunks.append(current)

    return chunks


def _add_overlap(chunks: list[str], chunk_overlap: int) -> list[str]:
    """Har chunk ke tail end ko agle chunk ke START par prepend karta hai,
    taaki do chunks ke beech ke seam par context kho na jaaye."""
    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        tail_of_previous = chunks[i - 1][-chunk_overlap:]
        overlapped.append(f"{tail_of_previous}{chunks[i]}")
    return overlapped
