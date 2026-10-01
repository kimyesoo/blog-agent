import sys
import traceback

def run_pipeline():
    print("=" * 60)
    print("🚀 Starting Civil Engineering Blog Agent Pipeline (E2E)")
    print("=" * 60)

    # 1. Problem Discovery
    print("\n[Step 1] Running Problem Discovery Agent...")
    try:
        from problem_discovery_agent import ProblemDiscoveryAgent
        pda = ProblemDiscoveryAgent()
        pda.run()
        print("✅ Problem Discovery Agent completed successfully.")
    except Exception as e:
        print(f"❌ Problem Discovery failed: {e}")
        traceback.print_exc()
        return

    # 2. Problem Validation
    print("\n[Step 2] Running Problem Validation Agent...")
    try:
        from problem_validation_agent import ProblemValidationAgent
        pva = ProblemValidationAgent()
        pva.run()
        print("✅ Problem Validation Agent completed successfully.")
    except Exception as e:
        print(f"❌ Problem Validation failed: {e}")
        traceback.print_exc()
        return

    # 3. Topic Agent
    print("\n[Step 3] Running Topic Agent...")
    try:
        from topic_agent import main as topic_main
        # Re-route stdout or just call it
        topic_main()
        print("✅ Topic Agent completed successfully.")
    except Exception as e:
        print(f"❌ Topic Agent failed: {e}")
        traceback.print_exc()
        return

    # 4. Research Agent
    print("\n[Step 4] Running Research Agent (V2.2)...")
    try:
        from research_agent import ResearchAgentV2
        ra = ResearchAgentV2()
        ra.run()
        print("✅ Research Agent V2.2 completed successfully.")
    except Exception as e:
        print(f"❌ Research Agent V2.2 failed: {e}")
        traceback.print_exc()
        return

    # 5. Writer Agent
    print("\n[Step 5] Running Writer Agent (V1)...")
    try:
        from writer_agent import WriterAgentV1
        wa = WriterAgentV1()
        wa.run()
        print("✅ Writer Agent V1 completed successfully.")
    except Exception as e:
        print(f"❌ Writer Agent V1 failed: {e}")
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("🎉 Pipeline Execution Complete!")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()
