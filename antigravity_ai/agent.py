import sys
import io
import os
import getpass
from dotenv import load_dotenv

load_dotenv()

from langchain.tools import tool
from langchain_community.utilities import ArxivAPIWrapper
from langchain_openai import ChatOpenAI
try:
    from langchain.agents import create_openai_tools_agent, AgentExecutor
except ImportError:
    from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

if not os.environ.get("OPENAI_API_KEY"):
    if sys.stdin.isatty():
        try:
            os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OPENAI_API_KEY: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(1)
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is required.")
        sys.exit(1)

# --- Phase 1 & 5: Deterministic REPL & Computational Engine ---
@tool
def python_computational_engine(code: str) -> str:
    """
    Executes Python/SymPy/Astropy/SciPy code for exact mathematical derivations,
    orbital mechanics, and physical constants calculation.
    Always print the final result using print().
    """
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    allowed_globals = {
        "__builtins__": __builtins__,
    }
    try:
        # Pre-import key scientific packages into the execution context
        exec("import sympy as sp\nimport numpy as np\nimport scipy as scp\nfrom astropy import units as u, constants as const", allowed_globals)
        exec(code, allowed_globals)
        output = redirected_output.getvalue()
        return output.strip() if output else "Code executed successfully with no stdout output."
    except Exception as e:
        return f"Execution Error: {str(e)}"
    finally:
        sys.stdout = old_stdout

# --- Phase 2: Scientific Research & Literature Retrieval ---
@tool
def arxiv_literature_search(query: str) -> str:
    """
    Searches arXiv for academic preprints across physics, astrophysics, 
    general relativity, and planetary science. Returns titles, authors, and abstracts.
    """
    arxiv = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=2000)
    return arxiv.run(query)

@tool
def planetary_ephemeris_and_constants(body_name: str) -> str:
    """
    Queries exact astronomical constants, planetary parameters (mass, radius, GSD,
    orbital period, gravitational parameters) using Astropy constants and units.
    """
    try:
        from astropy import constants as const, units as u
        import astropy.coordinates as coord
        
        info = {
            "G (Gravitational Constant)": f"{const.G.value:.8e} {const.G.unit}",
            "c (Speed of Light)": f"{const.c.value:.8e} {const.c.unit}",
            "R_moon (Lunar Volumetric Radius)": "1737.4 km (1.7374e6 m)",
            "M_moon (Lunar Mass)": "7.342e22 kg",
            "g_moon (Surface Gravity)": "1.62 m/s^2",
            "AU (Astronomical Unit)": f"{const.au.value:.8e} {const.au.unit}",
            "M_sun (Solar Mass)": f"{const.M_sun.value:.8e} {const.M_sun.unit}",
        }
        query_key = body_name.strip().lower()
        matched = {k: v for k, v in info.items() if query_key in k.lower() or query_key in ["all", "moon", "lunar", "constants"]}
        return str(matched if matched else info)
    except Exception as e:
        return f"Ephemeris Error: {str(e)}"

# --- Phase 4: Cognitive Routing & System Prompt ---
SYSTEM_PROMPT = """You are an advanced Research-Grade Physics, Mathematics, and Planetary Astrophysics AI engine.
You operate on ISRO, NASA, and ESA deep space mission science pipelines.

Follow these operational mandates:
1. DETERMINISTIC EXECUTION (Zero Guessing): NEVER approximate or guess analytical solutions, physical constants, or numerical integrations. Write and execute Python/SymPy/SciPy/Astropy code via `python_computational_engine`.
2. PROGRAM-AIDED LANGUAGE (PAL): Formulate complex astrophysics and celestial mechanics problems as differential equations or numerical simulations, execute them, and interpret the verified output.
3. CITATION & VERIFICATION LOOP: When citing theoretical models (e.g., Lommel-Seeliger scattering, Hapke bidirectional reflectance, Kerr metric geodesics), query `arxiv_literature_search` or reference peer-reviewed DOIs.
4. RIGOROUS LATEX REASONING: Present all derivations, tensor formulations, and equations in standard LaTeX syntax ($...$ and $$...$$).
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

tools = [python_computational_engine, arxiv_literature_search, planetary_ephemeris_and_constants]
llm = ChatOpenAI(model="gpt-4o", temperature=0)

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    print("AntiGravity AI Engine Initialized. Enter your query (or 'exit' to quit):")
    while True:
        try:
            user_input = input("\n>> ")
            if user_input.strip().lower() in ["exit", "quit"]:
                break
            if not user_input.strip():
                continue
            response = agent_executor.invoke({"input": user_input})
            print("\n" + response["output"])
        except KeyboardInterrupt:
            break
