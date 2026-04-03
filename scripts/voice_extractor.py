#!/usr/bin/env python3
"""
PostForge Voice Extractor — 3-Layer Voice Fingerprint Pipeline

Layer 1: Statistical Analysis (spaCy, NLTK, textstat) — runs on ALL text, no LLM
Layer 2: Sampled LLM Analysis — LLM (fast tier) on ~50 random chunks
Layer 3: Synthesis — LLM (reasoning tier) distills into voice_profile.md

Usage:
    python voice_extractor.py --input <text_file_or_directory> --output <output_directory>
    python voice_extractor.py --input ./samples/ --output ./config/
"""

import os
import sys
import json
import random
import re
import argparse
from pathlib import Path
from collections import Counter
from datetime import datetime

# ─── Layer 1: Statistical Analysis ───

def load_corpus(input_path: str) -> str:
    """Load all text from a file or directory of files."""
    path = Path(input_path)
    texts = []

    if path.is_file():
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            texts.append(f.read())
    elif path.is_dir():
        for file in sorted(path.rglob('*')):
            if file.suffix in ('.txt', '.md', '.text'):
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    texts.append(f.read())
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        sys.exit(1)

    corpus = '\n\n'.join(texts)
    print(f"Loaded corpus: {len(corpus)} characters, ~{len(corpus.split())} words from {len(texts)} file(s)")
    return corpus


def extract_stats(corpus: str) -> dict:
    """Layer 1: Statistical analysis of writing style. No LLM needed."""

    words = corpus.split()
    sentences = re.split(r'[.!?]+', corpus)
    sentences = [s.strip() for s in sentences if s.strip()]
    paragraphs = [p.strip() for p in corpus.split('\n\n') if p.strip()]

    # Basic counts
    total_words = len(words)
    total_sentences = len(sentences)
    total_paragraphs = len(paragraphs)

    # Sentence length distribution
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_sentence_length = sum(sentence_lengths) / max(len(sentence_lengths), 1)

    # Paragraph length distribution
    paragraph_lengths = [len(p.split()) for p in paragraphs]
    avg_paragraph_length = sum(paragraph_lengths) / max(len(paragraph_lengths), 1)

    # Word frequency
    lower_words = [w.lower().strip('.,!?;:\"\'()[]{}') for w in words]
    lower_words = [w for w in lower_words if w and len(w) > 1]
    word_freq = Counter(lower_words)

    # N-grams for pet phrases
    bigrams = [f"{lower_words[i]} {lower_words[i+1]}" for i in range(len(lower_words)-1)]
    trigrams = [f"{lower_words[i]} {lower_words[i+1]} {lower_words[i+2]}" for i in range(len(lower_words)-2)]

    # Punctuation patterns
    punctuation_counts = {
        'questions': corpus.count('?'),
        'exclamations': corpus.count('!'),
        'dashes': corpus.count('—') + corpus.count('–') + corpus.count(' - '),
        'ellipses': corpus.count('...') + corpus.count('…'),
        'semicolons': corpus.count(';'),
        'colons': corpus.count(':'),
        'parentheses': corpus.count('('),
    }

    # Contraction ratio
    contractions = sum(1 for w in lower_words if "'" in w and w not in ["'s", "'t", "'re", "'ve", "'ll", "'d", "'m"])
    common_contractions = sum(1 for w in lower_words if w in ["don't", "can't", "won't", "isn't", "aren't", "doesn't", "didn't", "couldn't", "shouldn't", "wouldn't", "i'm", "i've", "i'll", "i'd", "we're", "we've", "we'll", "they're", "they've", "that's", "it's", "here's", "there's", "what's", "who's", "let's"])

    # First person ratio
    first_person = sum(1 for w in lower_words if w in ['i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'])
    third_person = sum(1 for w in lower_words if w in ['he', 'she', 'they', 'them', 'his', 'her', 'their', 'it', 'its'])

    # Question frequency
    question_freq = corpus.count('?') / max(total_sentences, 1) * 100

    # Emoji detection
    emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001f900-\U0001f9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]')
    emojis = emoji_pattern.findall(corpus)

    # Lexical diversity
    unique_words = len(set(lower_words))
    lexical_diversity = unique_words / max(total_words, 1)

    # Readability (simple approximation without textstat dependency)
    avg_word_length = sum(len(w) for w in lower_words) / max(len(lower_words), 1)
    # Flesch-Kincaid approximation
    fk_grade = 0.39 * avg_sentence_length + 11.8 * (avg_word_length / 4.7) - 15.59

    stats = {
        "corpus_size": {
            "total_characters": len(corpus),
            "total_words": total_words,
            "total_sentences": total_sentences,
            "total_paragraphs": total_paragraphs,
        },
        "sentence_patterns": {
            "avg_sentence_length_words": round(avg_sentence_length, 1),
            "min_sentence_length": min(sentence_lengths) if sentence_lengths else 0,
            "max_sentence_length": max(sentence_lengths) if sentence_lengths else 0,
            "short_sentences_pct": round(sum(1 for l in sentence_lengths if l < 8) / max(len(sentence_lengths), 1) * 100, 1),
            "long_sentences_pct": round(sum(1 for l in sentence_lengths if l > 25) / max(len(sentence_lengths), 1) * 100, 1),
        },
        "paragraph_patterns": {
            "avg_paragraph_length_words": round(avg_paragraph_length, 1),
            "short_paragraphs_pct": round(sum(1 for l in paragraph_lengths if l < 30) / max(len(paragraph_lengths), 1) * 100, 1),
        },
        "vocabulary": {
            "unique_words": unique_words,
            "lexical_diversity": round(lexical_diversity, 3),
            "avg_word_length_chars": round(avg_word_length, 1),
            "top_50_words": word_freq.most_common(50),
            "top_30_bigrams": Counter(bigrams).most_common(30),
            "top_20_trigrams": Counter(trigrams).most_common(20),
        },
        "punctuation": {
            **punctuation_counts,
            "question_pct_of_sentences": round(question_freq, 1),
            "exclamation_per_1000_words": round(punctuation_counts['exclamations'] / max(total_words, 1) * 1000, 1),
            "dash_per_1000_words": round(punctuation_counts['dashes'] / max(total_words, 1) * 1000, 1),
        },
        "voice_indicators": {
            "contraction_count": common_contractions,
            "contraction_per_1000_words": round(common_contractions / max(total_words, 1) * 1000, 1),
            "first_person_per_1000_words": round(first_person / max(total_words, 1) * 1000, 1),
            "third_person_per_1000_words": round(third_person / max(total_words, 1) * 1000, 1),
            "first_to_third_ratio": round(first_person / max(third_person, 1), 2),
        },
        "formatting": {
            "emoji_count": len(emojis),
            "emoji_types": list(set(emojis))[:20],
            "emoji_per_1000_words": round(len(emojis) / max(total_words, 1) * 1000, 1),
        },
        "readability": {
            "flesch_kincaid_grade_approx": round(fk_grade, 1),
            "lexical_diversity": round(lexical_diversity, 3),
        },
        "extracted_at": datetime.now().isoformat(),
    }

    return stats


def generate_layer1_report(stats: dict) -> str:
    """Generate a human-readable report from Layer 1 stats."""

    report = f"""# Voice Statistics Report (Layer 1)
Generated: {stats['extracted_at']}

## Corpus Size
- {stats['corpus_size']['total_words']:,} words across {stats['corpus_size']['total_paragraphs']} paragraphs
- {stats['corpus_size']['total_sentences']} sentences

## Sentence Patterns
- Average sentence length: {stats['sentence_patterns']['avg_sentence_length_words']} words
- Short sentences (<8 words): {stats['sentence_patterns']['short_sentences_pct']}%
- Long sentences (>25 words): {stats['sentence_patterns']['long_sentences_pct']}%
- Range: {stats['sentence_patterns']['min_sentence_length']} to {stats['sentence_patterns']['max_sentence_length']} words

## Paragraph Patterns
- Average paragraph length: {stats['paragraph_patterns']['avg_paragraph_length_words']} words
- Short paragraphs (<30 words): {stats['paragraph_patterns']['short_paragraphs_pct']}%

## Vocabulary
- Unique words: {stats['vocabulary']['unique_words']:,}
- Lexical diversity: {stats['vocabulary']['lexical_diversity']} (>0.6 = high variety)
- Average word length: {stats['vocabulary']['avg_word_length_chars']} characters

### Top 20 Most Used Words
{chr(10).join(f'  {i+1}. "{word}" ({count})' for i, (word, count) in enumerate(stats['vocabulary']['top_50_words'][:20]))}

### Top 10 Pet Phrases (Bigrams)
{chr(10).join(f'  {i+1}. "{phrase}" ({count})' for i, (phrase, count) in enumerate(stats['vocabulary']['top_30_bigrams'][:10]))}

### Top 10 Pet Phrases (Trigrams)
{chr(10).join(f'  {i+1}. "{phrase}" ({count})' for i, (phrase, count) in enumerate(stats['vocabulary']['top_20_trigrams'][:10]))}

## Punctuation Style
- Questions: {stats['punctuation']['question_pct_of_sentences']}% of sentences are questions
- Exclamations: {stats['punctuation']['exclamation_per_1000_words']} per 1000 words
- Dashes: {stats['punctuation']['dash_per_1000_words']} per 1000 words
- Semicolons: {stats['punctuation']['semicolons']} total
- Ellipses: {stats['punctuation']['ellipses']} total

## Voice Indicators
- Contractions: {stats['voice_indicators']['contraction_per_1000_words']} per 1000 words ({'high' if stats['voice_indicators']['contraction_per_1000_words'] > 10 else 'moderate' if stats['voice_indicators']['contraction_per_1000_words'] > 5 else 'low'} usage)
- First person (I/we/my/our): {stats['voice_indicators']['first_person_per_1000_words']} per 1000 words
- Third person (he/she/they): {stats['voice_indicators']['third_person_per_1000_words']} per 1000 words
- First-to-third ratio: {stats['voice_indicators']['first_to_third_ratio']}:1

## Formatting
- Emojis: {stats['formatting']['emoji_per_1000_words']} per 1000 words ({'heavy' if stats['formatting']['emoji_per_1000_words'] > 5 else 'moderate' if stats['formatting']['emoji_per_1000_words'] > 1 else 'minimal'} usage)

## Readability
- Flesch-Kincaid Grade (approx): {stats['readability']['flesch_kincaid_grade_approx']}
- Lexical Diversity: {stats['readability']['lexical_diversity']}
"""
    return report


# ─── Layer 2: Sampled LLM Analysis ───

LAYER2_PROMPT = """Analyze this writing sample for voice characteristics. Be specific and cite examples from the text.

Analyze:
1. **Tone:** Warm/direct/analytical/casual/authoritative/irreverent? Mix?
2. **Humor style:** Sarcastic/dry/wholesome/none? Give an example if present.
3. **Argument structure:** Does the author use claim→evidence→conclusion? Story→lesson? Data→insight?
4. **Opening patterns:** How do they start sections? Question/stat/story/bold claim/scenario?
5. **Closing patterns:** How do they end? CTA/reflection/challenge/summary?
6. **Emotional register:** High energy/measured/contemplative/intense?
7. **Metaphor/analogy preferences:** What kind of comparisons do they make?
8. **How they handle disagreement:** Confrontational/diplomatic/data-driven/dismissive?
9. **How they introduce data/statistics:** Embedded in narrative? Standalone? With context?
10. **Cultural references / domain jargon:** What domain-specific language appears?

WRITING SAMPLE:
{chunk}

Respond in structured markdown with specific quotes from the text as evidence."""


def sample_chunks(corpus: str, num_samples: int = 50, chunk_size: int = 2000) -> list:
    """Extract random chunks from the corpus for LLM analysis."""
    words = corpus.split()
    chunks = []

    if len(words) < chunk_size:
        # Corpus is smaller than chunk size — use the whole thing
        return [corpus]

    for _ in range(num_samples):
        start = random.randint(0, len(words) - chunk_size)
        chunk = " ".join(words[start:start + chunk_size])
        chunks.append(chunk)

    print(f"Sampled {len(chunks)} chunks of ~{chunk_size} words each")
    return chunks


def generate_layer2_prompt(chunk: str) -> str:
    """Generate the analysis prompt for a single chunk."""
    return LAYER2_PROMPT.format(chunk=chunk)


# ─── Layer 3: Synthesis ───

LAYER3_PROMPT = """You are creating a voice_profile.md for a LinkedIn post generation system.

Based on the statistical analysis and sampled LLM analysis below, synthesize a complete voice profile.

STATISTICAL ANALYSIS:
{stats_report}

LLM ANALYSIS CONSENSUS (aggregated from {num_samples} samples):
{analysis_summary}

Generate a voice_profile.md with these EXACT sections:

## TONE
2-3 sentences describing the overall tone.

## RHYTHM
Sentence length patterns, pacing, paragraph structure.

## VOCABULARY
### Signature Words (use naturally)
### Words to AVOID

## STRUCTURE
How arguments and narratives are built.

## OPENINGS (5 Patterns)
5 specific opening patterns with examples.

## TRANSITIONS (5 Bridge Phrases)
5 transition phrases from the actual writing.

## CLOSINGS (5 Ending Patterns)
5 closing patterns with examples.

## PERSONALITY MARKERS
Humor, empathy, directness level, quirks.

## ANTI-PATTERNS (Never Do These)
Specific things this writer never does.

## SENTENCE PALETTE (10 Reusable Templates)
10 sentence structures from the actual writing.

## FEW-SHOT EXAMPLES
3-5 best paragraphs from the corpus that exemplify the voice.

Be specific. Use real examples from the data. This profile will be used to generate LinkedIn posts that sound exactly like this writer."""


def generate_layer3_prompt(stats_report: str, analysis_summary: str, num_samples: int) -> str:
    """Generate the synthesis prompt for Layer 3."""
    return LAYER3_PROMPT.format(
        stats_report=stats_report,
        analysis_summary=analysis_summary,
        num_samples=num_samples
    )


# ─── Main Pipeline ───

def run_pipeline(input_path: str, output_dir: str, num_samples: int = 50):
    """Run the full 3-layer voice extraction pipeline."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PostForge Voice Extractor — 3-Layer Pipeline")
    print("=" * 60)

    # ─── Layer 1 ───
    print("\n[Layer 1] Statistical Analysis...")
    corpus = load_corpus(input_path)
    stats = extract_stats(corpus)

    # Save stats JSON
    stats_path = output_path / "voice_stats.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        # Convert tuples to lists for JSON serialization
        serializable_stats = json.loads(json.dumps(stats, default=str))
        json.dump(serializable_stats, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {stats_path}")

    # Save human-readable report
    report = generate_layer1_report(stats)
    report_path = output_path / "voice_stats_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  Saved: {report_path}")

    # ─── Layer 2 ───
    print(f"\n[Layer 2] Sampling {num_samples} chunks for LLM analysis...")
    chunks = sample_chunks(corpus, num_samples)

    # Save prompts for manual LLM analysis
    prompts_dir = output_path / "layer2_prompts"
    prompts_dir.mkdir(exist_ok=True)

    for i, chunk in enumerate(chunks):
        prompt = generate_layer2_prompt(chunk)
        prompt_path = prompts_dir / f"chunk_{i+1:03d}.md"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
    print(f"  Saved {len(chunks)} analysis prompts to {prompts_dir}/")

    # ─── Layer 3 ───
    print(f"\n[Layer 3] Synthesis prompt ready.")
    synthesis_prompt = generate_layer3_prompt(
        stats_report=report,
        analysis_summary="[Aggregate Layer 2 results here after running LLM analysis]",
        num_samples=len(chunks)
    )
    synthesis_path = output_path / "layer3_synthesis_prompt.md"
    with open(synthesis_path, 'w', encoding='utf-8') as f:
        f.write(synthesis_prompt)
    print(f"  Saved: {synthesis_path}")

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"  1. Run Layer 2 prompts through your LLM fast tier (in {prompts_dir}/)")
    print(f"  2. Aggregate Layer 2 results")
    print(f"  3. Feed into Layer 3 synthesis prompt ({synthesis_path})")
    print(f"  4. Save final output as voice_profile.md")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PostForge Voice Extractor")
    parser.add_argument("--input", "-i", required=True, help="Path to text file or directory of text files")
    parser.add_argument("--output", "-o", default="./config/", help="Output directory for voice analysis files")
    parser.add_argument("--samples", "-n", type=int, default=50, help="Number of chunks to sample for Layer 2")

    args = parser.parse_args()
    run_pipeline(args.input, args.output, args.samples)
