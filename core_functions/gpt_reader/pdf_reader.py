import openai
import tenacity
import tiktoken
import copy
import re

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

    def read_with_chat_gpt_pro(self, paper,
                               overall_summary_prompt_messages=OVERALL_SUMMARY_PROMPT_MESSAGES,
                               method_summary_prompt_messages=METHOD_SUMMARY_PROMPT_MESSAGES,
                               conclusion_summary_prompt_messages=CONCLUSION_SUMMARY_PROMPT_MESSAGES,
                               title_selection_prompt_messages=TITLE_SELECTION_PROMPT_MESSAGES):

        section_titles = paper.get_section_titles()
        titles_text = '"' + '", "'.join(section_titles) + '"'

        try:
            method_titles_selected = re.findall(r'"(.*?)"', self.ask_chat_gpt_select_titles(
                titles_text,
                "Method section, but not the Experiments section",
                title_selection_prompt_messages
            ))
        except Exception as e:
            print("Error in overall summary: ", e)
            method_titles_selected = []

        try:
            experiment_titles_selected = re.findall(r'"(.*?)"', self.ask_chat_gpt_select_titles(
                titles_text,
                "Experiments section, but not the Method section",
                title_selection_prompt_messages
            ))
        except Exception as e:
            print("Error in overall summary: ", e)
            experiment_titles_selected = []

        try:
            conclusion_titles_selected = re.findall(r'"(.*?)"', self.ask_chat_gpt_select_titles(
                titles_text,
                "Conclusion section",
                title_selection_prompt_messages
            ))
        except Exception as e:
            print("Error in overall summary: ", e)
            conclusion_titles_selected = []

        # Adding paper title
        title = paper.get_paper_title()
        htmls = ['<h1>{}</h1>'.format(title)]

        # Overall summary using title, abstract, paper_info, and introduction section information
        _overall_summary_text = "Title: " + paper.get_paper_title()
        _overall_summary_text += "Abstract: " + paper.section_text_dict.get('Abstract', '')
        _overall_summary_text += "Paper Info: " + paper.paper_info
        _overall_summary_text += "Introduction: " + paper.section_text_dict.get('Introduction', '')

        # print("_overall_summary_text: ", _overall_summary_text)

        try:
            overall_summary = self.ask_chat_gpt_summary(_overall_summary_text, OVERALL_SUMMARY_PROMPT_MESSAGES)
        except Exception as e:
            overall_summary = self._handle_max_token_num_error(e, _overall_summary_text, error_base='Overall summary',
                                                               prompt_messages=OVERALL_SUMMARY_PROMPT_MESSAGES)

        htmls.append('<h2>Section Summaries</h2>')
        for section_title in section_titles:
            if 'related work' in section_title.lower():
                continue
            elif 'reference' in section_title.lower():
                break
            elif 'acknowledgment' in section_title.lower():
                break
            else:
                try:
                    print(paper.section_text_dict.get(section_title, ''))
                    section_summary = self.ask_chat_gpt_for_sections(
                        section_title,
                        paper.section_text_dict.get(section_title, ''),
                        overall_summary,
                        paper.get_paper_title(),
                        SECTION_SUMMARY_PROMPT_MESSAGES
                    )
                    print(section_summary)
                except Exception as e:
                    section_summary = e

                htmls.append('<h3>{}</h3>'.format(section_title))
                htmls.append(section_summary)

        htmls.append('<h2>Overall Summary</h2>')
        htmls.append('<p>{}</p>'.format(overall_summary.replace('\n', '<br>')))
        htmls.append('<br>')

        # Method summary
        _method_text = "<Summary>:\n" + overall_summary + "\n<Methods>:\n"
        for method_key in method_titles_selected:
            if method_key != 'None':
                continue
            else:
                _method_text += paper.section_text_dict[method_key]

        try:
            method_summary = self.ask_chat_gpt_summary(_method_text, METHOD_SUMMARY_PROMPT_MESSAGES)
        except Exception as e:
            method_summary = self._handle_max_token_num_error(e, _method_text, error_base='Method summary',
                                                              prompt_messages=METHOD_SUMMARY_PROMPT_MESSAGES)
        htmls.append('<h2>Method Summary</h2>')
        htmls.append('<p>{}</p>'.format(method_summary.replace('\n', '<br>')))
        htmls.append('<br>')

        _conclusion_text = "<Summary>:\n" + overall_summary + "\n<Methods>:\n" + method_summary
        for conclusion_key in conclusion_titles_selected:
            if conclusion_key != 'None':
                continue
            else:
                _conclusion_text += paper.section_text_dict[conclusion_key]

        try:
            conclusion_summary = self.ask_chat_gpt_summary(_conclusion_text, CONCLUSION_SUMMARY_PROMPT_MESSAGES)
        except Exception as e:
            conclusion_summary = self._handle_max_token_num_error(e, _conclusion_text, error_base='Conclusion summary',
                                                                  prompt_messages=CONCLUSION_SUMMARY_PROMPT_MESSAGES)
        htmls.append('<h2>Conclusion Summary</h2>')
        htmls.append('<p>{}</p>'.format(conclusion_summary.replace('\n', '<br>')))
        htmls.append('<br>')

        print(htmls)

        html = '<html><head><title>{}</title></head><body>{}</body></html>'.format(title, ''.join(htmls))

        return html

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
            overall_summary = self.ask_chat_gpt_summary(_overall_summary_text, OVERALL_SUMMARY_PROMPT_MESSAGES)
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
                method_summary = self.ask_chat_gpt_summary(_method_text, METHOD_SUMMARY_PROMPT_MESSAGES)
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
            conclusion_summary = self.ask_chat_gpt_summary(_conclusion_text, CONCLUSION_SUMMARY_PROMPT_MESSAGES)
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
    def ask_chat_gpt_summary(self, text, prompt_message, method_prompt_token_num=950):
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

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                    stop=tenacity.stop_after_attempt(5),
                    reraise=True)
    def ask_chat_gpt_select_titles(self, titles, article_part, prompt_message):
        system_prompt, assistant_prompt, user_prompt = self._split_prompt(prompt_message)

        system_prompt['content'] = system_prompt['content'].format(key_words=self.key_words)
        assistant_prompt['content'] = assistant_prompt['content'].format(titles=titles, article_part=article_part)

        _message = [
            system_prompt,
            assistant_prompt,
            user_prompt
        ]

        response = self.model.send_msg(_message)
        result = " ".join(choice.message.content for choice in response.choices)

        return result

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                    stop=tenacity.stop_after_attempt(5),
                    reraise=True)
    def ask_chat_gpt_for_sections(self, section_title, section_text, summary, paper_title, prompt_message,
                                  method_prompt_token_num=950):

        len_text_token = len(self.encodings.encode(section_text))
        clip_text_index = int(len(section_text)*(self.max_token_num-method_prompt_token_num)/len_text_token)
        clip_text = section_text[:clip_text_index]
        system_prompt, assistant_prompt, user_prompt = self._split_prompt(prompt_message)

        system_prompt['content'] = system_prompt['content'].format(key_words=self.key_words)
        assistant_prompt['content'] = assistant_prompt['content'].format(
            section_title=section_title, section=clip_text)

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
                                    prompt_messages, main_function=None):
        print(error_base + "_error:", error)
        if "maximum context" in str(error):
            print("maximum context error")
            current_tokens_index = str(error).find("your messages resulted in") + len("your messages resulted in") + 1
            offset = int(str(error)[current_tokens_index:current_tokens_index + 4])
            method_prompt_token_num = offset + 950
            if main_function is None:
                return self.ask_chat_gpt_summary(text=text, prompt_message=prompt_messages,
                                                 method_prompt_token_num=method_prompt_token_num)
            else:
                return main_function(text=text, prompt_message=prompt_messages,
                                     method_prompt_token_num=method_prompt_token_num)
