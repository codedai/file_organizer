import argparse
import configparser
from core_functions import file_orgnizer, PaperReader


from core_functions import file_orgnizer

from utils import *


def test():
    folder_path = 'demo'
    i = 0
    for f in os.listdir(folder_path):
        i+=1
        if f.endswith('.pdf'):
            print(f)
            paper = PaperInfo(os.path.join(folder_path, f))
            paper.parse_pdf()

            print("Old", paper.section_text_dict)
            print("Old", paper.section_page_dict)
            print("======")

            paper.parse_pdf_beta()

            # print("New", paper.section_text_dict)
            print("New", paper.section_text_dict.keys())
            print("=============================")

            config = configparser.ConfigParser()
            config.read('api_key.ini')
            chat_api = config.get('OpenAI', 'OPENAI_API_KEY')
            paper_reader = PaperReader(chat_api)

            paper_reader.read_with_chat_gpt_pro(paper)
        if i > 10:
            break

if __name__ == '__main__':
    test()
