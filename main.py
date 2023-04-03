import argparse
import configparser

from core_functions import file_orgnizer, PaperReader


def main(args):
    if args.booster == 'True':
        config = configparser.ConfigParser()
        config.read('api_key.ini')
        chat_api = config.get('OpenAI', 'OPENAI_API_KEY')
        paper_reader = PaperReader(chat_api)
        print("Booster is on! It will take a while to read all the papers.")
    else:
        paper_reader = None

    file_orgnizer.organize_files_in_old_folder(old_folder_path=args.paper_folder_path,
                                               new_folder_name=args.new_folder_name,
                                               paper_reader=paper_reader,
                                               note_type=args.file_format)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper_folder_path", type=str, default='demo',
                        help="if none, the script will read the file in the demo folder")
    parser.add_argument("--new_folder_name", type=str, default='new_folder',
                        help="the prefix of the new fold name, holding the renamed pdf files, (and notes), "
                             "the full name will be <new_folder_name>_<date>")
    parser.add_argument("--booster", type=str, default='True',
                        help="If True, the bot will use the booster model (ChatGPT) to generate the summary. "
                             "If set to True, you should have the API key of the ChatGPT model in the file "
                             "api_key.ini")
    parser.add_argument("--file_format", type=str, default='md', help="The format of the notes, md or html")

    args = parser.parse_args()
    main(args=args)
