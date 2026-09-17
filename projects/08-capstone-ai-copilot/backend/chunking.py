"""
============================================================================
 CHUNKING — document ko haath se overlapping pieces mein todna
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Poora document ek embedding model ko ek hi unit mein dena almost hamesha
bahut bada aur bahut unfocused hota hai — tumhe ek vague vector milega jo
"yeh poora document" represent karta hai, jo kaam ka nahi jab tumhe woh EK
specific paragraph dhoondhna ho jo ek specific question ka jawab deta hai.
Isliye embed hone se pehle, document CHUNK kiya jaata hai: chhote,
overlapping pieces mein kaata jaata hai, itne chhote ki har ek roughly EK
hi specific cheez ke baare mein ho.

Do settings isko control karti hain, aur yeh ek dusre ke against trade-off
karti hain:

  chunk_size    — ek chunk ka max size (characters mein). Bahut chhota
                  hoga to chunk apna surrounding context kho dega ("it"
                  hai lekin pata nahi "it" kis cheez ko refer kar raha
                  hai); bahut bada hoga to chunk multiple topics ko mix
                  kar dega, jisse embed hone par uska "about kya hai"
                  dilute ho jaata hai.

  chunk_overlap — ek chunk ke END ke kitne characters agle chunk ke START
                  mein repeat kiye jaate hain. Overlap na ho to jo sentence
                  chunk boundary par hi girta hai, woh beech mein phat
                  jaata hai, aur har half doosre ka context kho deta hai.

Project 5 se as-is reuse kiya hai, jahan yahi splitter explain kiya gaya
hai aur LangChain ke version se compare kiya gaya hai. Is project ko yeh
alag reason se chahiye: is project ke ingest.py ka pehle wala version sirf
blank lines par split karta tha bina kisi merging ke, jiske wajah se ek
markdown heading ("# What Is RAG?") jo ek lambe paragraph ke upar tha, apna
alag, content-free chunk ban jaata tha — aur search_handbook tool kabhi
kabhi asli explanation ki jagah wahi heading fragment return kar deta tha,
jo genuinely is baat ka part hai ki testing ke dauraan agent ne galat
jawab kyun diya (usne "RAG" ka matlab ek aise heading se hallucinate kar
liya jiske paas koi body text hi nahi tha kaam karne ke liye). Yeh splitter
chhote pieces ko chunk_size tak merge karta hai, taaki ek heading, uska
trailing paragraph aur diagram, saath mein hi ek jagah aa jaayein.
============================================================================
"""

# Order mein try kiye jaate hain, "sabse bada, sabse natural break" se
# "last resort" tak.
SEPARATORS = ["\n\n", "\n", ". ", " "]


def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    """`text` ko chunks ki ek list mein split karta hai, har ek max
    ~chunk_size characters ka, aur consecutive chunks ke beech
    chunk_overlap characters ka context repeat karta hai."""
    chunks = _split_recursive(text.strip(), SEPARATORS, chunk_size)
    return _add_overlap(chunks, chunk_overlap)


def _split_recursive(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Recursive wala part: pehla separator pick karo, usi par split karo,
    aur resulting pieces ko greedily wapas jod do chunk_size tak. Koi bhi
    single piece jo iske baad bhi chunk_size se bada hai, use NEXT, aur
    fine-grained separator use karke dobara recursively split kiya jaata
    hai."""
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
        # current chunk ko close karo aur fresh se shuru karo.
        if current:
            chunks.append(current)
            current = ""

        if len(piece) > chunk_size:
            # Yeh EK piece apne aap mein hi bahut bada hai (jaise koi
            # bada paragraph bina kisi line break ke) — ek fine
            # separator ke saath recurse karo, ya agar separators khatam
            # ho gaye hain to raw character count se hard-slice kar do.
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
    """Har chunk ke end wale hisse ko agle chunk ke START mein prepend kar
    deta hai, taaki do chunks ke beech ke seam par context loss na ho."""
    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        tail_of_previous = chunks[i - 1][-chunk_overlap:]
        overlapped.append(f"{tail_of_previous}{chunks[i]}")
    return overlapped
