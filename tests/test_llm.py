from llm.config import (
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_API_KEY,
)

from llm.provider.factory import get_provider
from llm.client import LLMClient

def divider(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------

def test_config():
    divider("CONFIG TEST")
    print("Provider :", LLM_PROVIDER)
    print("Model    :", LLM_MODEL)
    if LLM_API_KEY:
        print("API Key  : Loaded ✅")
    else:
        print("API Key  : Missing ❌")


# -------------------------------------------------------
# FACTORY
# -------------------------------------------------------

def test_factory():
    divider("FACTORY TEST")
    provider = get_provider()
    print(provider)
    print("Returned:", type(provider).__name__)


# -------------------------------------------------------
# PROVIDER
# -------------------------------------------------------

def test_provider():
    divider("PROVIDER TEST")
    provider = get_provider()
    response = provider.generate(
        "Explain Transformers in one sentence."
    )
    print(response)


# -------------------------------------------------------
# CLIENT
# -------------------------------------------------------

def test_client():
    divider("LLM CLIENT TEST")
    client = LLMClient()
    print(client)
    response = client.generate(
        "What is GraphRAG? Explain in two sentences."
    )
    print(response)


# -------------------------------------------------------
# JSON
# -------------------------------------------------------

def test_json():

    divider("JSON TEST")

    client = LLMClient()

    prompt = """
Return ONLY JSON.
{
    "animal":"",
    "legs":0
}
Animal:
Dog
"""

    response = client.generate_json(prompt)

    print(response)


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":

    divider("TESTING LLM LAYER")
    test_config()
    test_factory()
    test_provider()
    test_client()
    test_json()
    divider("ALL TESTS FINISHED")