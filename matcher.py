import re


class SkillMatcher:

    def calculate_similarity(
        self,
        candidate_text,
        job_description,
        required_skills
    ):
        """
        Lightweight skill-focused matching.

        Required skills are given the highest importance.
        This avoids the score being dominated by common JD words.
        """

        candidate = candidate_text.lower()

        # Normalize common variations
        candidate = candidate.replace("data structures & algorithms",
                                      "data structures and algorithms")
        candidate = candidate.replace("github", "git")

        matched_skills = 0
        total_skills = len(required_skills)

        for skill in required_skills:
            skill_clean = skill.strip().lower()

            if not skill_clean:
                continue

            # Special handling for common variations
            variations = {
                "dsa": [
                    "dsa",
                    "data structures",
                    "data structures and algorithms"
                ],
                "dbms": [
                    "dbms",
                    "database management systems"
                ],
                "ai": [
                    "ai",
                    "artificial intelligence"
                ],
                "artificial intelligence": [
                    "ai",
                    "artificial intelligence"
                ],
                "machine learning": [
                    "machine learning",
                    "ml"
                ],
                "git": [
                    "git",
                    "github"
                ],
                "github": [
                    "git",
                    "github"
                ],
                "problem solving": [
                    "problem solving",
                    "problem-solving"
                ]
            }

            possible_matches = variations.get(
                skill_clean,
                [skill_clean]
            )

            found = any(
                phrase in candidate
                for phrase in possible_matches
            )

            if found:
                matched_skills += 1

        if total_skills == 0:
            return 0.0

        # Skill-based score
        skill_score = (
            matched_skills / total_skills
        ) * 100

        # Small contribution from JD overlap
        candidate_words = set(
            re.findall(
                r"\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
                candidate
            )
        )

        job_words = set(
            re.findall(
                r"\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
                job_description.lower()
            )
        )

        common_words = candidate_words.intersection(job_words)

        generic_words = {
            "the", "and", "or", "a", "an", "to",
            "of", "in", "for", "with", "on", "is",
            "are", "be", "this", "that", "as",
            "by", "from", "will", "should", "have",
            "has", "candidate", "role", "work",
            "working", "team", "skills"
        }

        useful_common = common_words - generic_words

        if job_words - generic_words:
            text_score = (
                len(useful_common) /
                len(job_words - generic_words)
            ) * 100
        else:
            text_score = 0

        # 85% importance to actual skills
        # 15% importance to JD text
        final_score = (
            skill_score * 0.85
            + text_score * 0.15
        )

        return round(min(final_score, 100), 2)

    def find_skill_gaps(self, candidate_text, required_skills):

        candidate = candidate_text.lower()

        matched = []
        missing = []

        variations = {
            "dsa": [
                "dsa",
                "data structures",
                "data structures and algorithms"
            ],
            "dbms": [
                "dbms",
                "database management systems"
            ],
            "ai": [
                "ai",
                "artificial intelligence"
            ],
            "artificial intelligence": [
                "ai",
                "artificial intelligence"
            ],
            "machine learning": [
                "machine learning",
                "ml"
            ],
            "git": [
                "git",
                "github"
            ],
            "github": [
                "git",
                "github"
            ],
            "problem solving": [
                "problem solving",
                "problem-solving"
            ]
        }

        for skill in required_skills:

            skill_clean = skill.strip()

            if not skill_clean:
                continue

            possible_matches = variations.get(
                skill_clean.lower(),
                [skill_clean.lower()]
            )

            found = any(
                phrase in candidate
                for phrase in possible_matches
            )

            if found:
                matched.append(skill_clean)
            else:
                missing.append(skill_clean)

        return matched, missing