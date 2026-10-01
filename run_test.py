import subprocess
try:
    result = subprocess.run(["python3", "-m", "pytest", "tests/test_research_agent_v2.py", "-v"], capture_output=True, text=True)
    print(result.stdout)
except Exception as e:
    print(e)
