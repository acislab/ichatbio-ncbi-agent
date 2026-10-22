import json

import pytest
from ichatbio.agent_response import ArtifactResponse

from entrypoints import find_sequence_records, get_sequence_record


@pytest.mark.asyncio
async def test_find_sequence_records(agent, context, messages):
    await agent.run(
        context,
        "Blah blah blah",
        "find_sequence_records",
        find_sequence_records.Parameters(search_terms="Rattus rattus")
    )

    artifacts = [m for m in messages if isinstance(m, ArtifactResponse)]
    assert artifacts

    artifact = artifacts[0]
    assert artifact.mimetype == "application/json"

    data = json.loads(artifact.content.decode())
    assert len(data["sequence_ids"]) > 0



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
    json_data = json.loads(artifacts[0].content.decode())
    assert "GBSet" in json_data

    assert artifacts[1].mimetype == "text/plain"
    assert artifacts[1].uris == ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=JQ814272&rettype=gb&retmode=text"]
