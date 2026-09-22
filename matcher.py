import re


class SkillMatcher:

    def calculate_similarity(self, candidate_text, job_description):
        """
        Lightweight keyword-based semantic-style matching.
        Designed for low-memory deployment.
        """

        candidate_words = set(
            re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
                       candidate_text.lower())
        )

        job_words = set(
            re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
                       job_description.lower())
        )

        if not job_words:
            return 0.0

        common_words = candidate_words.intersection(job_words)

        # Ignore very common English words
        stop_words = {
            "the", "and", "or", "a", "an", "to", "of", "in",
            "for", "with", "on", "is", "are", "be", "this",
            "that", "as", "by", "from", "will", "should",
            "have", "has", "candidate", "role", "work"
        }

        useful_matches = common_words - stop_words

        score = (len(useful_matches) / max(len(job_words - stop_words), 1)) * 100

        return round(min(score, 100), 2)

    def find_skill_gaps(self, candidate_text, required_skills):

        candidate_text_lower = candidate_text.lower()

        matched = []
        missing = []

        for skill in required_skills:

            skill_clean = skill.strip()

            if not skill_clean:
                continue

            if skill_clean.lower() in candidate_text_lower:
                matched.append(skill_clean)
            else:
                missing.append(skill_clean)

        return matched, missing