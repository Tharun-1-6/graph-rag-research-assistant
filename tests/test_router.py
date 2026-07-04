from unittest.mock import MagicMock
from query_processor.router import QueryRouter, QueryOrchestrator
from llm.client import LLMClient

def test_query_router_classification():
    # Mock LLMClient
    mock_llm = MagicMock(spec=LLMClient)
    # Set return value for generate_json to mock a RAG route classification
    mock_llm.generate_json.return_value = '{"route": "RAG", "reasoning": "Simple keyword query"}'
    
    router = QueryRouter(llm_client=mock_llm)
    result = router.route("What is the learning rate?")
    
    assert result["route"] == "RAG"
    assert "Simple keyword query" in result["reasoning"]
    mock_llm.generate_json.assert_called_once()

def test_query_router_error_handling():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_json.side_effect = Exception("API connection error")
    
    router = QueryRouter(llm_client=mock_llm)
    result = router.route("Hello world")
    
    assert result["route"] == "COMBINED"
    assert "Failed to classify query due to error" in result["reasoning"]

def test_orchestrator_rag_only():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_json.return_value = '{"route": "RAG", "reasoning": "Keyword query"}'
    mock_llm.generate.return_value = "The learning rate is 0.001."
    
    # Mock retrievers
    mock_rag = MagicMock(return_value="Vector RAG data context")
    mock_graph_rag = MagicMock(return_value="Graph RAG data context")
    
    orchestrator = QueryOrchestrator(
        rag_retriever=mock_rag,
        graph_rag_retriever=mock_graph_rag,
        llm_client=mock_llm
    )
    
    response = orchestrator.run("What is the learning rate?")
    
    assert response["route"] == "RAG"
    assert response["rag_context"] == "Vector RAG data context"
    assert response["graph_context"] == ""
    assert response["final_context"] == "Vector RAG data context"
    assert response["answer"] == "The learning rate is 0.001."
    
    mock_rag.assert_called_once_with("What is the learning rate?")
    mock_graph_rag.assert_not_called()
    mock_llm.generate.assert_called_once()

def test_orchestrator_combined():
    mock_llm = MagicMock(spec=LLMClient)
    # First call to router (generate_json), second to consolidation (generate), third to answering (generate)
    mock_llm.generate_json.return_value = '{"route": "COMBINED", "reasoning": "Complex query"}'
    mock_llm.generate.side_effect = [
        "Consolidated result showing both RAG and Graph RAG data",
        "Method A improves upon method B."
    ]
    
    mock_rag = MagicMock(return_value="Vector RAG data")
    mock_graph_rag = MagicMock(return_value="Graph RAG data")
    
    orchestrator = QueryOrchestrator(
        rag_retriever=mock_rag,
        graph_rag_retriever=mock_graph_rag,
        llm_client=mock_llm
    )
    
    response = orchestrator.run("How does method A compare to method B?")
    
    assert response["route"] == "COMBINED"
    assert response["rag_context"] == "Vector RAG data"
    assert response["graph_context"] == "Graph RAG data"
    assert response["final_context"] == "Consolidated result showing both RAG and Graph RAG data"
    assert response["answer"] == "Method A improves upon method B."
    
    mock_rag.assert_called_once_with("How does method A compare to method B?")
    mock_graph_rag.assert_called_once_with("How does method A compare to method B?")
    assert mock_llm.generate.call_count == 2

if __name__ == "__main__":
    print("Running Router Tests...")
    test_query_router_classification()
    test_query_router_error_handling()
    test_orchestrator_rag_only()
    test_orchestrator_combined()
    print("All Router Tests Passed! OK")
