"""Project 4: Text File Analyzer

Setup (once):
    pip install fire

Run:
    python analyzer.py notes.txt
    python analyzer.py notes.txt --top=5 --skip_stop_words
    python analyzer.py --help
"""
import re
import sys
from collections import Counter
from pathlib import Path

import fire

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be",
    "to", "of", "in", "on", "at", "for", "with", "it", "this", "that", "as",
    "by", "from", "i", "you", "he", "she", "we", "they", "my", "your", "not",
}


def get_words(text):
    """Lowercase words with punctuation removed. Keeps apostrophes (don't, it's)."""
    return re.findall(r"[a-z0-9']+", text.lower())


def analyze(text, top, skip_stop_words):
    words = get_words(text)
    if skip_stop_words:
        counted = [w for w in words if w not in STOP_WORDS]
    else:
        counted = words

    return {
        "lines": len(text.splitlines()),
        "words": len(words),
        "characters": len(text),
        "unique_words": len(set(words)),
        "longest_word": max(words, key=len) if words else "",
        "average_length": sum(len(w) for w in words) / len(words) if words else 0,
        "most_common": Counter(counted).most_common(top),
    }


def main(path, top=10, skip_stop_words=False):
    """Analyze a text file.

    Args:
        path: text file to analyze
        top: how many common words to show
        skip_stop_words: ignore common words like 'the', 'is', 'and'
    """
    # fire turns each parameter into a CLI argument:
    #   path            -> required positional argument
    #   top=10          -> optional --top=5
    #   skip_stop_words -> flag --skip_stop_words (sets it to True)
    if not isinstance(top, int) or top < 1:
        sys.exit("Error: --top must be a positive whole number.")
    path = Path(str(path))

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        sys.exit(f"Error: file '{path}' not found.")
    except IsADirectoryError:
        sys.exit(f"Error: '{path}' is a folder, not a file.")
    except UnicodeDecodeError:
        sys.exit(f"Error: '{path}' is not a text file.")

    stats = analyze(text, top, skip_stop_words)

    print(f"File:            {path.name}")
    print(f"Lines:           {stats['lines']}")
    print(f"Words:           {stats['words']}")
    print(f"Characters:      {stats['characters']}")
    print(f"Unique words:    {stats['unique_words']}")
    print(f"Longest word:    {stats['longest_word']}")
    print(f"Avg word length: {stats['average_length']:.2f}")

    print(f"\nTop {top} words:")
    for word, count in stats["most_common"]:
        print(f"  {word:<15}{count}")


if __name__ == "__main__":
    fire.Fire(main)