from xml.etree.ElementTree import ElementTree

import httpx
import xmltodict
from defusedxml import DefusedXmlException
from ichatbio.agent_response import IChatBioAgentProcess, ResponseContext
from ichatbio.types import AgentEntrypoint
from pydantic import BaseModel

# See https://www.ncbi.nlm.nih.gov/books/NBK3837/, section "Nucleotide"
description = """\
Use full-text search to find sequence record IDs in NCBI's Nucleotide ("nuccore") database. The records come from 
sequence databases like GenBank, RefSeq, TPA, and PDB.
"""


# https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch
class Parameters(BaseModel):
    search_terms: str
    # TODO: tags
    # TODO: proximity search


entrypoint = AgentEntrypoint(
    id="find_sequence_records",
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

        async with httpx.AsyncClient(follow_redirects=True) as http:
            # TODO: what characters are allowed? Does the API support percent encoding?
            parameters.search_terms = parameters.search_terms.replace(" ", "+")
            search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term={parameters.search_terms}"
            await process.log(f"Sending GET request to {search_url}")
            response = await http.get(search_url)

            if not response.is_success:
                await process.log(f"Response code: {response.status_code}")
                return

            try:
                results = _parse_search_results(response.text)
            except DefusedXmlException as e:
                await process.log(f"Failed to process search results: {str(e)}")
                return
            except ValueError as e:
                await process.log(str(e))
                return

        if results.count == 0:
            await process.log("No matching records found in the NCBI Nucleotide database.")
            if results.errors:
                await process.log(f"NCBI reported: {', '.join(results.errors)}")
            if results.warnings:
                await process.log(f"Note: {', '.join(results.warnings)}")

        await process.create_artifact(
            mimetype="application/json",
            description=f"Nucleotide IDs for sequence records matching \"{parameters.search_terms}\"",
            content=results.model_dump_json().encode("utf-8"),
            metadata={
                "data_source": "Nucleotide database",
                "api_search_terms": {parameters.search_terms},
                "derived_from": search_url
            }
        )
        
        if any(error.startswith("Phrase not found") for error in results.errors):
            await context.reply(
                "The search failed with the error: 'Phrase not found'. This means the search terms did not match any indexed metadata fields. "
                "The agent's capabilities are limited to: (1) find_sequence_records - searches text metadata like organism names, titles, and authors; "
                "(2) get_sequence_record - retrieves a record by known accession number."
            )


class SearchResults(BaseModel):
    count: int
    page: int
    page_size: int
    sequence_ids: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []


def _parse_search_results(xml: str):
    parsed = xmltodict.parse(xml)
    data = parsed.get("eSearchResult")
    
    if not data:
        raise ValueError("Invalid response from NCBI: missing eSearchResult element")
    
    errors = []
    error_list = data.get("ErrorList")
    if error_list:
        phrase_not_found = error_list.get("PhraseNotFound")
        if phrase_not_found:
            phrase = phrase_not_found if len(phrase_not_found) <= 100 else phrase_not_found[:100] + "..."
            errors.append(f"Phrase not found: {phrase}")
    
    warnings = []
    warning_list = data.get("WarningList")
    if warning_list:
        output_message = warning_list.get("OutputMessage")
        if output_message:
            warnings.append(output_message)
    
    return SearchResults(
        count=int(data.get("Count", 0)),
        page=int(data.get("RetStart", 0)),
        page_size=int(data.get("RetMax", 0)),
        errors=errors,
        warnings=warnings
    )


def _get_property_value_by_tag(tree: ElementTree, tag: str):
    node = next(tree.iter(tag), None)
    return node.text if node else None


def _list_property_values_by_tag(tree: ElementTree, tag: str):
    nodes = list(tree.iter(tag))
    return [node.text for node in nodes]
