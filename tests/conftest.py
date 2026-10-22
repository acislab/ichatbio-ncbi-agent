import dotenv
import pytest_asyncio

from agent import NCBINucleotideAgent


@pytest_asyncio.fixture()
def agent():
    dotenv.load_dotenv()
    return NCBINucleotideAgent()
