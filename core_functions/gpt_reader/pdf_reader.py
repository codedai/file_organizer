import openai
import tenacity
import tiktoken
import copy

from .model_interface import OpenAIModel
from .prompt import *


# Setting the API key to use the OpenAI API
class PaperReader:
    """
    A class for summarizing research papers using the OpenAI API.

    Attributes:
        openai_key (str): The API key to use the OpenAI API.
        model (str): The GPT model to use for summarization.
    """

    def __init__(self, openai_key, key_words="AI", model="gpt-3.5-turbo"):

        # Setting the API key to use the OpenAI API
        openai.api_key = openai_key

        # Initializing prompts for the conversation
        self.model = model  # Setting the GPT model to use
        self.model = OpenAIModel(api_key=openai_key, model=model)
        self.key_words = key_words

        self.encodings = tiktoken.get_encoding("gpt2")
        self.max_token_num = 4096

    def send_msg(self, msg):
        return self.model.send_msg(msg)

    def read_with_chat_gpt(self, paper):
        # Adding paper title
        title = paper.get_paper_title()
        htmls = ['<h1>{}</h1>'.format(title)]

        # Overall summary using title, abstract, paper_info, and introduction section information
        _overall_summary_text = "Title: " + paper.get_paper_title()
        _overall_summary_text += "Abstract: " + paper.section_text_dict['Abstract']
        _overall_summary_text += "Paper Info: " + paper.section_text_dict['paper_info']
        _overall_summary_text += "Introduction: " + paper.section_text_dict['Introduction']

        # print("_overall_summary_text: ", _overall_summary_text)

        try:
            overall_summary = self.ask_chat_gpt(_overall_summary_text, OVERALL_SUMMARY_PROMPT_MESSAGES)
        except Exception as e:
            overall_summary = self._handle_max_token_num_error(e, _overall_summary_text, error_base='Overall summary',
                                                               prompt_messages=OVERALL_SUMMARY_PROMPT_MESSAGES)

        htmls.append('<h2>Overall Summary</h2>')
        htmls.append('<p>{}</p>'.format(overall_summary.replace('\n', '<br>')))
        htmls.append('<br>')

        # Method summary
        method_key = ''
        method_summary = ''
        for parse_key in paper.section_text_dict.keys():
            if 'method' in parse_key.lower() or 'approach' in parse_key.lower():
                method_key = parse_key
                break

        if method_key != '':
            _method_text = "<Summary>:\n" + overall_summary + "\n<Methods>:\n" +\
                paper.section_text_dict[method_key]

            try:
                method_summary = self.ask_chat_gpt(_method_text, METHOD_SUMMARY_PROMPT_MESSAGES)
            except Exception as e:
                method_summary = self._handle_max_token_num_error(e, _method_text, error_base='Method summary',
                                                                  prompt_messages=METHOD_SUMMARY_PROMPT_MESSAGES)
            htmls.append('<h2>Method Summary</h2>')
            htmls.append('<p>{}</p>'.format(method_summary.replace('\n', '<br>')))
            htmls.append('<br>')

        # Conclusion summary
        conclusion_key = ''
        for parse_key in paper.section_text_dict.keys():
            if 'conclu' in parse_key.lower():
                conclusion_key = parse_key
                break

        if conclusion_key != '':
            _conclusion_text = "<Summary>:\n" + overall_summary + "\n<Methods>:\n" +\
                method_summary + "\n<Conclusion>:\n" + paper.section_text_dict[conclusion_key]
        else:
            _conclusion_text = "<Summary>:\n" + overall_summary + "\n<Methods>:\n" +\
                method_summary

        try:
            conclusion_summary = self.ask_chat_gpt(_conclusion_text, CONCLUSION_SUMMARY_PROMPT_MESSAGES)
        except Exception as e:
            conclusion_summary = self._handle_max_token_num_error(e, _conclusion_text, error_base='Conclusion summary',
                                                                  prompt_messages=CONCLUSION_SUMMARY_PROMPT_MESSAGES)
        htmls.append('<h2>Conclusion Summary</h2>')
        htmls.append('<p>{}</p>'.format(conclusion_summary.replace('\n', '<br>')))
        htmls.append('<br>')

        html = '<html><head><title>{}</title></head><body>{}</body></html>'.format(title, ''.join(htmls))

        return html

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                    stop=tenacity.stop_after_attempt(5),
                    reraise=True)
    def ask_chat_gpt(self, text, prompt_message, method_prompt_token_num=950):
        len_text_token = len(self.encodings.encode(text))
        clip_text_index = int(len(text)*(self.max_token_num-method_prompt_token_num)/len_text_token)
        clip_text = text[:clip_text_index]
        system_prompt, assistant_prompt, user_prompt = self._split_prompt(prompt_message)

        system_prompt['content'] = system_prompt['content'].format(key_words=self.key_words)
        assistant_prompt['content'] = assistant_prompt['content'].format(clip_text=clip_text)

        _message = [
            system_prompt,
            assistant_prompt,
            user_prompt
        ]

        response = self.model.send_msg(_message)
        result = " ".join(choice.message.content for choice in response.choices)

        return result

    @staticmethod
    def _split_prompt(prompt_message) -> tuple[dict, dict, dict]:
        system_prompt, assistant_prompt, user_prompt = copy.deepcopy(prompt_message)
        if system_prompt['role'] != 'system':
            raise ValueError("system_prompt['role'] should be 'system'")
        if assistant_prompt['role'] != 'assistant':
            raise ValueError("assistant_prompt['role'] should be 'assistant'")
        if user_prompt['role'] != 'user':
            raise ValueError("user_prompt['role'] should be 'user'")
        return system_prompt, assistant_prompt, user_prompt

    def _handle_max_token_num_error(self, error, text, error_base,
                                    prompt_messages):
        print(error_base + "_error:", error)
        if "maximum context" in str(error):
            print("maximum context error")
            current_tokens_index = str(error).find("your messages resulted in") + len("your messages resulted in") + 1
            offset = int(str(error)[current_tokens_index:current_tokens_index + 4])
            method_prompt_token_num = offset + 950
            return self.ask_chat_gpt(text=text, prompt_message=prompt_messages,
                                     method_prompt_token_num=method_prompt_token_num)