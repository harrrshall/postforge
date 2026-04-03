"""Unit tests for voice_extractor.py — statistical analysis layer."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from voice_extractor import extract_stats, sample_chunks, generate_layer2_prompt, generate_layer3_prompt

pytestmark = pytest.mark.unit


SAMPLE_CORPUS = """
₹2.3 lakhs per month. That's what a single Pune dermatology clinic was losing to missed
appointments, unanswered WhatsApp messages, and manual follow-ups. We set up an AI employee
in 10 hours. Now it answers patient queries 24/7 in Hindi and English. Books appointments
automatically. Sends payment reminders without being asked. Generates a daily report ready
by 7 AM. The clinic owner told us: "I didn't hire a person. I hired a system that never
takes leave." 47x ROI. In the first month. If your clinic is still answering WhatsApp
manually at 11 PM, your competitor probably isn't.

We found 512 security vulnerabilities in OpenClaw. Not a typo. Kaspersky's audit flagged 8
as critical. 9 CVEs disclosed in 4 days. The creator himself called it "a tech preview, a
hobby." So why are we building a business on it? Because the framework is phenomenal. The
security isn't. That's exactly the gap Humanless fills.

88% of Indian companies say they use AI. 6% see real returns. That's not an AI problem.
That's an implementation problem.
"""


# ─── extract_stats ───


class TestExtractStats:
    def test_returns_dict(self):
        result = extract_stats(SAMPLE_CORPUS)
        assert isinstance(result, dict)

    def test_has_required_sections(self):
        result = extract_stats(SAMPLE_CORPUS)
        assert "corpus_size" in result
        assert "sentence_patterns" in result
        assert "vocabulary" in result
        assert "punctuation" in result
        assert "voice_indicators" in result
        assert "readability" in result

    def test_word_count_positive(self):
        result = extract_stats(SAMPLE_CORPUS)
        assert result["corpus_size"]["total_words"] > 0

    def test_sentence_count_positive(self):
        result = extract_stats(SAMPLE_CORPUS)
        assert result["corpus_size"]["total_sentences"] > 0

    def test_lexical_diversity_range(self):
        result = extract_stats(SAMPLE_CORPUS)
        diversity = result["vocabulary"]["lexical_diversity"]
        assert 0 < diversity <= 1.0

    def test_question_percentage(self):
        result = extract_stats(SAMPLE_CORPUS)
        # Corpus has questions like "So why are we building...?"
        assert result["punctuation"]["question_pct_of_sentences"] >= 0

    def test_has_top_words(self):
        result = extract_stats(SAMPLE_CORPUS)
        assert len(result["vocabulary"]["top_50_words"]) > 0

    def test_has_bigrams(self):
        result = extract_stats(SAMPLE_CORPUS)
        assert len(result["vocabulary"]["top_30_bigrams"]) > 0

    def test_empty_corpus_no_crash(self):
        result = extract_stats("")
        assert isinstance(result, dict)
        assert result["corpus_size"]["total_words"] == 0

    def test_single_sentence(self):
        result = extract_stats("Hello world.")
        assert result["corpus_size"]["total_words"] == 2
        assert result["corpus_size"]["total_sentences"] >= 1


# ─── sample_chunks ───


class TestSampleChunks:
    def test_small_corpus_returns_full(self):
        small = "This is a short text."
        chunks = sample_chunks(small, num_samples=5, chunk_size=100)
        assert len(chunks) >= 1

    def test_returns_list(self):
        chunks = sample_chunks(SAMPLE_CORPUS, num_samples=3, chunk_size=50)
        assert isinstance(chunks, list)

    def test_respects_num_samples(self):
        large = SAMPLE_CORPUS * 10  # repeat to make it large
        chunks = sample_chunks(large, num_samples=5, chunk_size=20)
        assert len(chunks) <= 5


# ─── Prompt Generation ───


class TestPromptGeneration:
    def test_layer2_contains_chunk(self):
        chunk = "This is a test writing sample about AI agents."
        prompt = generate_layer2_prompt(chunk)
        assert isinstance(prompt, str)
        assert "test writing sample" in prompt

    def test_layer3_contains_stats(self):
        stats_report = "Total words: 500\nLexical diversity: 0.65"
        analysis = "Tone: direct and confident"
        prompt = generate_layer3_prompt(stats_report, analysis, 50)
        assert isinstance(prompt, str)
        assert "500" in prompt or "Lexical" in prompt or "direct" in prompt
