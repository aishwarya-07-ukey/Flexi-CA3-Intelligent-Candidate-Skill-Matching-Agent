import os
from openai import OpenAI
from matcher import SkillMatcher


class CandidateMatchingAgent:
    def __init__(self):
        self.matcher = SkillMatcher()

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set in the .env file."
            )

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

    def analyze(self, candidate_text, job_description, required_skills):

        score = self.matcher.calculate_similarity(
            candidate_text,
            job_description,
            required_skills
        )

        matched_skills, missing_skills = (
            self.matcher.find_skill_gaps(
                candidate_text,
                required_skills
            )
        )

        prompt = f"""
You are TALENTMATCH AI, an intelligent recruitment assistant.

Analyze the candidate against the job description.

JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS:
{", ".join(required_skills)}

CANDIDATE RESUME:
{candidate_text}

SEMANTIC MATCH SCORE:
{score}%

MATCHED SKILLS:
{", ".join(matched_skills)}

MISSING SKILLS:
{", ".join(missing_skills)}

Provide the following:

## Candidate Summary
Give a short professional summary.

## Why the Candidate Matches
Explain the strongest matching areas.

## Important Skill Gaps
Explain the missing skills.

## Recommended Skills to Learn
Suggest practical skills based only on the job requirements.

## Recruiter Insight
Give a concise professional assessment.

Important:
- Do not invent qualifications.
- Use only information available in the resume.
- Keep the response professional and concise.
"""

        response = self.client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        ai_analysis = response.choices[0].message.content

        return {
            "score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "ai_analysis": ai_analysis
        }