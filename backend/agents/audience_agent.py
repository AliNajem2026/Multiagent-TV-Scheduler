from backend.rag.retriever import (
    KnowledgeRetriever
)

from backend.services.llm_service import (
    llm
)


class AudienceAgent:

    def run(self, day):

        context = (
            KnowledgeRetriever()
            .retrieve(
                f"{day} audience ratings"
            )
        )

        prompt = f"""
        Use this context:

        {context}

        Predict:

        - best viewing time
        - preferred content

        Day:
        {day}
        """

        response = llm.invoke(
            prompt
        )

        return response.content