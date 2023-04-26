from utils import *
from utils.paper_info import PaperInfo
from .gpt_reader.pdf_reader import PaperReader


def move_file_to_new_folder(old_folder_path: str, new_folder_path: str, old_file_title: str):
    old_title_old_folder = os.path.join(old_folder_path, old_file_title)

    # copy the file from original to new folder with its old name
    if not os.path.exists(os.path.join(new_folder_path, old_file_title)):
        shutil.copy(old_title_old_folder, new_folder_path)
    old_title_new_folder = os.path.join(new_folder_path, old_file_title)

    return old_title_new_folder


def organize_files_in_old_folder(old_folder_path: str, new_folder_name: str, paper_reader: PaperReader = None, note_type: str = 'html' or 'md') -> \
        tuple[str, list]:
    """
    Make a new folder under the past folder path
    Copy all files in the old folder into the new one and
    rename the files in the new folder
    :param paper_reader:
    :param old_folder_path:
    :param new_folder_name:
    :return: the path of the new folder
    """
    time_stamp = datetime.now().strftime("%Y-%m-%d")
    new_folder_name_with_time_stamp = new_folder_name + '_' + time_stamp
    new_folder_path = os.path.join(old_folder_path, new_folder_name_with_time_stamp)
    html_notes = []

    files_and_dirs = os.listdir(old_folder_path)

    # Create a new folder to store the renamed files
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)

    # Filter the list to include only the files and return their names
    # file_names = [f for f in files_and_dirs if f.endswith('.pdf')]
    for f in files_and_dirs:
        if f.endswith('.pdf'):
            old_title_new_folder = move_file_to_new_folder(old_folder_path, new_folder_path, f)

            # create the new file name with stored file title in the form of <Year>-<Authors>-<Title>.pdf

            if paper_reader is not None:
                paper = PaperInfo(old_title_new_folder, booster=True)
                paper.update_paper_info_use_doi()
                try:
                    _note = paper_reader.read_with_chat_gpt(paper)
                except Exception as e:
                    print(e)
                    _note = "Error: " + str(e)
                _note_dict = {
                        'Paper': paper,
                        'Notes': _note
                    }
                save_note_to_file(_note_dict, new_folder_path, note_type=note_type)
                html_notes.append(_note_dict)
            else:
                paper = PaperInfo(old_title_new_folder)
                paper.update_paper_info_use_doi()

            new_file_title = paper.get_file_title() + ".pdf"

            new_title_new_folder = os.path.join(new_folder_path, new_file_title)

            # rename the file in folder1 with the new file name
            os.rename(old_title_new_folder, new_title_new_folder)
            paper.update_paper_path(new_title_new_folder)
            print("New file title: " + new_file_title)
        break

    return new_folder_path, html_notes


def save_note_to_file(html_note: dict, folder_path: str, note_type: str = 'html' or 'md'):
    note_folder_path = os.path.join(folder_path, 'notes')
    if not os.path.exists(note_folder_path):
        os.makedirs(note_folder_path)

    paper = html_note['Paper']
    html = html_note['Notes']

    if note_type == 'md':
        html = html2text.html2text(html)
        with open(os.path.join(note_folder_path, paper.get_file_title() + '.md'), 'w') as f:
            f.write(html)
    else:
        with open(os.path.join(note_folder_path, paper.get_file_title() + '.html'), 'w') as f:
            f.write(html)


if __name__ == '__main__':
    '''
    This is a demo of how to use the pdf2doi package to extract DOI information from PDF files.
    The extracted information will be used to rename the files.
    '''

    # Get system input for the path of the folder containing the PDF files, if no input is given, use the default path
    # path = input("Please enter the path of the folder containing the PDF files: ")
    # if path == "":
    past_path = '../data/test_files'  # Left for user to change
    n_f_n = 'new_folder'  # Left for user to change

    organize_files_in_old_folder(past_path, n_f_n)

