"""
============================================================================
 CHUNKING — ek document ko overlapping pieces mein todna, haath se
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Ek poora document almost hamesha itna bada aur unfocused hota hai ki use
embedding model ko ek hi unit mein dena theek nahi — tumhe ek vague vector
milega jo "poore document" ko represent karta hai, jo kisi specific
question ka jawab dene wale ek particular paragraph ko dhoondhne ke liye
bekaar hai. Isliye kuch bhi embed hone se pehle, usko CHUNK kiya jaata hai:
chhote, overlapping pieces mein kaata jaata hai, itne chhote ki har piece
lagbhag EK hi specific cheez ke baare mein ho.

Do settings isko control karti hain, aur dono ek dusre ke against trade-off
karti hain:

  chunk_size    — ek chunk ka max size (characters mein). Bahut chhota ho to
                  chunk apne aas-paas ka context kho deta hai ("it" hai
                  lekin pata hi nahi "it" kiska reference hai); bahut bada
                  ho to chunk multiple topics mix kar deta hai, jisse embed
                  karte waqt "yeh kis baare mein hai" wala matlab dilute
                  ho jaata hai.

  chunk_overlap — ek chunk ke END ke kitne characters agle chunk ke START
                  mein repeat kiye jaate hain. Overlap ke bina, agar koi
                  sentence chunk boundary par hi aa kar gir jaaye to woh
                  beech mein se phat jaata hai, aur dono halves ek dusre
                  ka context kho dete hain.

Yeh hand-rolled splitter conceptually bilkul waise hi kaam karta hai jaise
LangChain ka apna RecursiveCharacterTextSplitter karta hai (framework wala
version dekhne ke liye rag_langchain.py dekho, jo isi ke saath side-by-side
banaya gaya hai jaan-bujh kar): pehle paragraph breaks par split karne ki
koshish karo, aur sirf tab hi ek chhoti separator (single newlines, phir
sentences, phir raw characters) par fallback karo jab koi piece us baad bhi
STILL bahut bada ho. Isse natural boundaries (paragraphs, sentences) jitna
ho sake intact rehti hain, hamesha ek fixed character count par slice karne
ki jagah, chahe wahan kuch bhi ho.
============================================================================
"""

# Order mein try kiya jaata hai, "sabse bada, sabse natural break" se lekar
# "last resort" tak.
SEPARATORS = ["\n\n", "\n", ". ", " "]


def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    """`text` ko chunks ki ek list mein split karta hai, har chunk max
    ~chunk_size characters ka, aur consecutive chunks ke beech chunk_overlap
    characters ka context repeat hota hai."""
    chunks = _split_recursive(text.strip(), SEPARATORS, chunk_size)
    return _add_overlap(chunks, chunk_overlap)


def _split_recursive(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Recursive wala part: pehla separator pick karo, usi par split karo,
    aur result mein aaye pieces ko greedily wapas jod ke chunk_size tak le
    jaao. Koi bhi ek piece jo us ke baad bhi chunk_size se STILL bada hai,
    usko recursively phir se split kiya jaata hai, is baar NEXT, aur zyada
    fine-grained separator use karke."""
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

        # Is piece ko add karne se current chunk overflow ho jaayega —
        # current chunk ko close karo aur fresh start karo.
        if current:
            chunks.append(current)
            current = ""

        if len(piece) > chunk_size:
            # Yeh EK piece apne aap mein hi bahut bada hai (jaise ek huge
            # paragraph jisme koi line break nahi hai) — ek aur fine
            # separator ke saath recurse karo, ya agar separators khatam ho
            # gaye hain to raw character count par hard-slice kar do.
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
    """Har chunk ke tail (end) ko agle chunk ke START mein prepend karta
    hai, taaki do chunks ke beech ki seam par context na khoye."""
    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        tail_of_previous = chunks[i - 1][-chunk_overlap:]
        overlapped.append(f"{tail_of_previous}{chunks[i]}")
    return overlapped
