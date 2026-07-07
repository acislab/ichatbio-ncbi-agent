# ichatbio-ncbi-agent

An iChatBio agent that accesses GenBank data and more through NCBI's Datasets API:

> O’Leary NA, Cox E, Holmes JB, Anderson WR, Falk R, Hem V, Tsuchiya MTN, Schuler GD, Zhang X, Torcivia J, Ketter A, Breen L, Cothran J, Bajwa H, Tinne J, Meric PA, Hlavina W, Schneider VA. [Exploring and retrieving sequence and metadata for species across the tree of life with NCBI Datasets](https://www.nature.com/articles/s41597-024-03571-y). Sci Data. 2024 Jul 5;11(1):732. doi: 10.1038/s41597-024-03571-y. PMID: 38969627; PMCID: PMC11226681.

## Quickstart

*Requires python 3.10 or higher*

Set up your development environment:

```bash
pip3 install uv
uv sync
source .venv/bin/activate
```

Run the server:

```bash
uvicorn --app-dir src agent:create_app --factory --reload --host "0.0.0.0" --port 9999
```

You can also run the agent server as a Docker container:

```bash
docker compose up --build
```

If everything worked, you should be able to find your agent card at http://localhost:9999/.well-known/agent.json.


## Funding

This work is funded by grants from the National Science Foundation (DBI 2027654) and the AT&T Foundation.