from backend.rag.retriever import KnowledgeRetriever
from backend.services.llm_service import llm
from backend.prompts.schedule_prompt import SCHEDULE_FORMAT
from backend.services.json_parser import parse_llm_json


class SchedulingAgent:

    def run(
        self,
        audience,
        content
    ):

        context = (
            KnowledgeRetriever()
            .retrieve(
                "TV scheduling best practices"
            )
        )

        prompt = f"""
        Context:
        {context}

        Audience:
        {audience}

        Programs:
        {content}

        Build a complete 24-hour schedule from 00:00 to 24:00.

        Use these programming blocks as a guide:
        - 00:00-06:00  Late Night / Overnight: repeats, archive sports, low-cost filler
        - 06:00-09:00  Breakfast / Morning News: news, sports headlines
        - 09:00-12:00  Mid-Morning: magazines, documentaries, sports science
        - 12:00-15:00  Afternoon: sports highlights, entertainment
        - 15:00-18:00  Late Afternoon: live sports (if available), lifestyle
        - 18:00-23:00  Prime Time: live sport, premium analysis, top entertainment
        - 23:00-00:00  Late Evening: news wrap, post-match analysis, highlights

        The schedule MUST cover all 24 hours without gaps.
        Repeat programs or use archive content for low-audience periods.

        {SCHEDULE_FORMAT}
        """

        response = llm.invoke(
            prompt
        )

        return parse_llm_json(response.content)