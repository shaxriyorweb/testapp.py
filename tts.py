# tts.py
import sys
from gtts import gTTS

def main():
    if len(sys.argv) < 3:
        print("Usage: python tts.py 'text' lang_code")
        sys.exit(1)

    text = sys.argv[1]
    lang = sys.argv[2]

    tts = gTTS(text=text, lang=lang)
    tts.save("greeting.mp3")

if __name__ == "__main__":
    main()
