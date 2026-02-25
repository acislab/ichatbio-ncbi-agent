import json

import httpx
import xmltodict
from ichatbio.agent_response import IChatBioAgentProcess, ResponseContext
from ichatbio.types import AgentEntrypoint
from pydantic import BaseModel

description = """\
Given a sequence record ID (e.g. a GenBAnk accession number, GI number, Nucleotide UID, etc.), downloads the associated
sequence record. Retrieves a human-friendly "flat file" (.gb) record and generates a machine-friendly JSON version.
"""


class Parameters(BaseModel):
    accession_number: str


entrypoint = AgentEntrypoint(
    id="get_sequence_record",
    description=description,
    parameters=Parameters
)


async def run(context: ResponseContext, parameters: Parameters):
    """
    Executes this specific entrypoint. See description above. This function yields a sequence of messages that are
    returned one-by-one to iChatBio in response to the request, logging the retrieval process in real time.
    """
    async with context.begin_process("Searching the NCBI Nucleotide database") as process:
        process: IChatBioAgentProcess

        xml_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={parameters.accession_number}&rettype=gb&retmode=xml"
        await process.log(f"Retrieving XML nucleotide record from {xml_url}")
        async with httpx.AsyncClient(follow_redirects=True) as http:
            response = await http.get(xml_url)

            if not response.is_success:
                await process.log(f"Response code: {response.status_code}")
                await context.reply(f"Failed to retrieve XML record")
                return

            await process.log("Converting XML record to JSON")
            json_record = xmltodict.parse(response.text)

        gbseq = json_record.get("GBSet", {}).get("GBSeq", {})
        record_definition = gbseq.get("GBSeq_definition")
        record_primary_accession = gbseq.get("GBSeq_primary-accession")
        record_accession_version = gbseq.get("GBSeq_accession-version")

        metadata = {"data_source": "Nucleotide"}

        if record_primary_accession:
            portal_link = f"https://www.ncbi.nlm.nih.gov/nuccore/{record_primary_accession}"
            await process.log(f"An online version of the record is available at {portal_link}")
            metadata |= {"link_to_view_record_on_ncbi_portal": portal_link}

        if record_primary_accession: metadata |= {"primary_accession": record_primary_accession}
        if record_accession_version: metadata |= {"accession_version": record_accession_version}

        await process.create_artifact(
            mimetype="application/json",
            description=f"JSON nucleotide sequence record {parameters.accession_number}: {record_definition}",
            content=json.dumps(json_record).encode("utf-8"),
            metadata=metadata | {"derived_from": xml_url}
        )

        flat_file_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={parameters.accession_number}&rettype=gb&retmode=text"
        await process.log(f"Retrieving flat file nucleotide record from {flat_file_url}")

        async with httpx.AsyncClient(follow_redirects=True) as http:
            response = await http.get(flat_file_url)

            if not response.is_success:
                await process.log(f"Response code: {response.status_code}")
                await context.reply(f"Failed to retrieve flat file record")
                return

        await process.create_artifact(
            mimetype="text/plain",
            description=f"Flat file nucleotide sequence record {parameters.accession_number}: {record_definition}",
            uris=[flat_file_url],
            metadata=metadata
        )

        await context.reply(
            text="The two artifacts contain the same data but in different formats. The flat file format is more"
                 " human-friendly, while the JSON format is more machine-friendly. The JSON format was converted from"
                 " the original XML returned by the API to make it easier to process." +
                 (f" The record is also available in the NCBI Nucleotide portal at {portal_link}"
                  if portal_link else "")
        )
