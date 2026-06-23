from autogen import ConversableAgent
import autogen
import dotenv
import os

dotenv.load_dotenv()

# Build config list from all available API keys (supports fallback across accounts)
_api_keys = [
    os.getenv("GOOGLE_GEMINI_API_KEY"),
    os.getenv("GOOGLE_GEMINI_API_KEY_2"),
]
config_list_gemini = [
    {"model": "gemini-2.5-flash", "api_key": key, "api_type": "google"}
    for key in _api_keys
    if key and key != "your_second_api_key_here"
]
if not config_list_gemini:
    raise RuntimeError("No valid Gemini API keys found. Check your .env file.")

SYSTEM_MESSAGE_INITIAL_CFP_WRITER = """
Your task is to write a good, clean, and impactful proposal or submission for a CFP to a technical event. 
Generate only the following as part of the CFP:
- Title
- Abstract
- Key Takeaways
The following are key tenets you have to abide by:
- Stay true to the original idea or intent of the author
- Do not add in your own ideas or details that the author has not provided and do not try to elaborate on any technology
- Only rewrite the idea expressed by the author in the form of a well-structured and impactful talk proposal
- Make it technical, concise, crisp, and impactful. Output the proposal in a markdown format.
"""
initial_cfp_writer = ConversableAgent(
    name="CFP Writer",
    system_message=SYSTEM_MESSAGE_INITIAL_CFP_WRITER,
    llm_config={"config_list": config_list_gemini},
    code_execution_config=False,
    human_input_mode="NEVER",
    function_map=None,
)

SYSTEM_MESSAGE_CFP_WRITER = """
Check if there are any improvement points, and use it to improve the submission. 
Retain the points that are good and doesn't need to be changed. 
If there is no actionable feedback, then output the final submission.
"""

cfp_writer = ConversableAgent(
    name="CFP Writer",
    system_message=SYSTEM_MESSAGE_CFP_WRITER,
    llm_config={"config_list": config_list_gemini},
    code_execution_config=False,
    human_input_mode="NEVER",
    function_map=None,
)


SYSTEM_MESSAGE_CFP_REVIEWER = """
Your task is to review a submission for a technical talk.
The talk will have the following details:
- Title
- Abstract
- Key Takeaways
Review the submissions for the following:
- Clarity of thought and crisp writeup
- Showcasing value to the audience who will attend the talk
- Easy to understand what this talk is about
- Being specific about the technologies being used and why they are being used
- Clear takeaways for the audience
- Clarity on who is the Intended audience
Keeping these tenets in mind, you will review the submission and provide precise and concise, actionable feedback, that will help improve the submission.
You should not write or re-write the submission or any parts of it.
Provide clear and concise feedback that the author can work on to improve on their writeup.
If there are aspects that are good, mention them so that it can be retain and left unchanged.
"""
cfp_reviewer = ConversableAgent(
    name="CFP Reviewer",
    system_message=SYSTEM_MESSAGE_CFP_REVIEWER,
    llm_config={"config_list": config_list_gemini},
    code_execution_config=False,
    human_input_mode="NEVER",
    function_map=None,
)
user_idea = input("Enter your rough CFP idea (what your talk is about):\n")

print("\n=== [STEP 1] Generating Initial CFP Draft ===")
initial_cfp = initial_cfp_writer.generate_reply(
    messages=[{"content": user_idea, "role": "user"}]
)
initial_content = (
    initial_cfp["content"] if isinstance(initial_cfp, dict) else initial_cfp
)
print(f"\n--- [Initial CFP Draft Output] ---\n{initial_content}\n")

print("=== [STEP 2] Starting Agent Collaboration (Writer <-> Reviewer) ===")
cfp_writer.initiate_chat(
    cfp_reviewer,
    message=f"Following is a rough idea for which I would like a talk proposal that I can submit:\n{initial_content}",
    max_turns=2,
)
print("\n=== [STEP 3] Agent Collaboration Finished ===")
