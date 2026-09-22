from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SkillMatcher:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def calculate_similarity(self, candidate_text, job_description):

        candidate_embedding = self.model.encode([candidate_text])
        job_embedding = self.model.encode([job_description])

        similarity = cosine_similarity(
            candidate_embedding,
            job_embedding
        )[0][0]

        return round(float(similarity) * 100, 2)

    def find_skill_gaps(self, candidate_text, required_skills):

        candidate_text_lower = candidate_text.lower()

        matched = []
        missing = []

        for skill in required_skills:

            if skill.lower() in candidate_text_lower:
                matched.append(skill)
            else:
                missing.append(skill)

        return matched, missing