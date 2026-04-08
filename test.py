from app import analyze_contract_with_agent, get_rag_context

def main():
    print("=== Testing Contrat Skema C (with indexation) ===")
    ctx = get_rag_context("Contrat Skema C")
    res = analyze_contract_with_agent(ctx)
    print("RESULT:")
    print(res)

    print("\n=== Testing Contrat Skema B (no indexation) ===")
    ctx = get_rag_context("Contrat Skema B")
    res = analyze_contract_with_agent(ctx)
    print("RESULT:")
    print(res)

if __name__ == "__main__":
    main()
