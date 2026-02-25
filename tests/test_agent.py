import pytest
import pytest_asyncio
from ichatbio.agent_response import ArtifactResponse

from agent import NCBINucleotideAgent
from entrypoints import find_sequence_records, get_sequence_record


@pytest_asyncio.fixture()
def agent():
    return NCBINucleotideAgent()


@pytest.mark.asyncio
async def test_find_sequence_records(agent, context, messages):
    await agent.run(
        context,
        "Blah blah blah",
        "find_sequence_records",
        find_sequence_records.Parameters(search_terms="Rattus rattus")
    )

    artifacts = [m for m in messages if isinstance(m, ArtifactResponse)]

    assert artifacts[0].mimetype == "application/json"


@pytest.mark.asyncio
async def test_get_sequence_record(agent, context, messages):
    await agent.run(
        context,
        "Blah blah blah",
        "get_sequence_record",
        get_sequence_record.Parameters(accession_number="JQ814272")
    )

    artifacts = [m for m in messages if isinstance(m, ArtifactResponse)]

    assert artifacts[0].mimetype == "application/json"
    assert artifacts[1].mimetype == "text/plain"
