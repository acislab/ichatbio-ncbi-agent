from typing import override, Optional

from ichatbio.agent import IChatBioAgent
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.server import build_agent_app
from ichatbio.types import AgentCard, AgentEntrypoint
from pydantic import BaseModel
from starlette.applications import Starlette

from entrypoints import find_sequence_records, get_sequence_record


class NCBINucleotideAgent(IChatBioAgent):
    @override
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="Nucleotide",
            description="Search tools for NCBI's Nucleotide (\"nuccore\") sequence database.",
            icon=None,
            entrypoints=[
                find_sequence_records.entrypoint,
                get_sequence_record.entrypoint
            ]
        )

    @override
    async def run(self, context: ResponseContext, request: str, entrypoint: str, params: Optional[BaseModel]):
        match entrypoint:
            case find_sequence_records.entrypoint.id:
                await find_sequence_records.run(context, params)
            case get_sequence_record.entrypoint.id:
                await get_sequence_record.run(context, params)
            case _:
                raise ValueError()


def create_app() -> Starlette:
    agent = HelloWorldAgent()
    app = build_agent_app(agent)
    return app
