import pprint
from typing_extensions import Annotated
import autogen


config_list = [
    {
        "base_url": "http://127.0.0.1:8001/v1",
        "api_key": "NULL",
        "model": "NousResearch/Hermes-2-Pro-Llama-3-8B",
    }
]

llm_config = {
    "config_list": config_list,
    "timeout": 120,
    "cache_seed": None,
}


chatbot = autogen.AssistantAgent(
    name="chatbot",
    system_message="Reply TERMINATE once you have the answer.",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
)


@user_proxy.register_for_execution()
@chatbot.register_for_llm(description="Multiplies two integers.")
def multiply_ints(
    x: Annotated[int, "The first integer"],
    y: Annotated[int, "The second integer"],
) -> int:
    return x * y


res = user_proxy.initiate_chat(
    chatbot,
    message="How much is 500 * 1234? Reply 'TERMINATE' once you have the answer.", # the TERMINATE directive normally goes in the system prompt but the model wasn't obeying *shrug*
    summary_method="reflection_with_llm",
    cache=None,
    clear_history=True,
)
