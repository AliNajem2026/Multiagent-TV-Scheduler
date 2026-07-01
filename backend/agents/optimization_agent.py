from backend.rag.retriever import KnowledgeRetriever
from backend.services.llm_service import llm
from backend.services.json_parser import parse_llm_json
from backend.prompts.schedule_prompt import SCHEDULE_FORMAT


class OptimizationAgent:

    def run(self, schedule):

        context = (
            KnowledgeRetriever()
            .retrieve(
                "audience retention 24 hour programming"
            )
        )

        prompt = f"""
        Optimize this 24-hour schedule for maximum audience retention.
        Ensure all 24 hours are covered without gaps.
        Place premium content in prime time (18:00-23:00).
        Use archive/repeat content for overnight slots (00:00-06:00).

        Context:
        {context}

        Schedule:
        {schedule}

        {SCHEDULE_FORMAT}
        """

        response = llm.invoke(
            prompt
        )

        return parse_llm_json(response.content)
