"""Transcript analysis API endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TranscriptInput(BaseModel):
    title: str = ""
    company: str = ""
    text: str


class SentimentInput(BaseModel):
    text: str


@router.post("/transcripts/analyze")
def analyze_transcript(body: TranscriptInput):
    from finscrape.agents.transcript_analyst import analyze_transcript as _analyze
    result = _analyze(title=body.title, company=body.company, text=body.text)
    return {
        "title": result.title,
        "company": result.company,
        "total_segments": result.total_segments,
        "speakers": [{"name": s.name, "role": s.role.value, "title": s.title} for s in result.speakers],
        "overall_sentiment": result.overall_sentiment,
        "sentiment_score": result.sentiment_score,
        "key_quotes": result.key_quotes,
        "guidance_changes": result.guidance_changes,
        "risk_factors": result.risk_factors,
        "competitive_mentions": result.competitive_mentions,
        "insights": [
            {
                "category": i.category,
                "quote": i.quote,
                "speaker": i.speaker,
                "sentiment": i.sentiment,
                "impact": i.impact,
                "summary": i.summary,
            }
            for i in result.insights
        ],
    }


@router.post("/transcripts/insights")
def extract_insights(body: TranscriptInput):
    from finscrape.agents.transcript_analyst import extract_insights as _extract, parse_speakers
    speakers = parse_speakers(body.text)
    insights = _extract(body.text, speakers)
    return {
        "count": len(insights),
        "insights": [
            {
                "category": i.category,
                "quote": i.quote,
                "speaker": i.speaker,
                "speaker_role": i.speaker_role,
                "sentiment": i.sentiment,
                "confidence": i.confidence,
                "impact": i.impact,
                "summary": i.summary,
            }
            for i in insights
        ],
    }


@router.post("/transcripts/sentiment")
def analyze_sentiment(body: SentimentInput):
    from finscrape.agents.transcript_analyst import analyze_sentiment as _sentiment
    label, score = _sentiment(body.text)
    return {
        "sentiment": label,
        "score": round(score, 3),
    }
