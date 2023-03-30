import re

from utils import *


class PaperInfo:
    def __init__(self, paper_path: str, booster: bool = False):
        self.paper_path = paper_path  # Full file path: /path/to/file.pdf

        with open(self.paper_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfFileReader(f)
            self._authors = self._regularize_authors(re.split(r',|\band\b', pdf_reader.getDocumentInfo().author or ""))
            self._title = pdf_reader.getDocumentInfo().title or ""
            self._num_pages = pdf_reader.getNumPages()

        self._doi_info = None
        self._year = 8888
        self._date = ""
        self._event = ""

        self._file_title = self._create_file_title()  # File name: <Year>-<Authors>-<Title>.pdf

        # Variables for section reading
        self.section_names = []
        self.title_page = None
        self.section_text_dict = None
        self.section_page_dict = None
        self.all_text = None
        self.text_list = None
        self.pdf = None
        self.abs = ''

        if booster:
            # Build up the base for applying ChatGPT
            self.parse_pdf()

    def get_paper_title(self):
        return self._title

    def get_file_title(self):
        return self._file_title

    def get_num_pages(self):
        return self._num_pages

    def update_paper_path(self, new_path: str):
        # TODO: varify the content of the new file is the same as the old one
        self.paper_path = new_path

    def update_paper_info_use_doi(self):
        self._doi_info = json.loads(pdf2doi.pdf2doi(self.paper_path)['validation_info'])
        self._authors = self._validate_author_info(self._doi_info.get('author', []))
        self._title = self._validate_title_info(self._doi_info.get('title', ""))
        self._year = self._doi_info.get('published-print', {}).get('date-parts', [[None]])[0][0] or 8888
        self._date = "-".join(
            str(i) for i in self._doi_info.get('published-print', {}).get('date-parts', [[None]])[0][:2])
        self._event = self._doi_info.get('container-title') or self._doi_info.get('event') or ""

        self._file_title = self._create_file_title()

    def parse_pdf(self):
        """
        With reference to git https://github.com/kaixindelele/ChatPaper
        :return:
        """

        self.pdf = fitz.open(self.paper_path)
        self._title = self.get_title()
        self.text_list = [page.get_text().replace("A B S T R A C T", "Abstract") for page in self.pdf]
        self.all_text = ' '.join(self.text_list)
        self.section_page_dict = self._get_all_page_index()
        # print("section_page_dict", self.section_page_dict)
        self.section_text_dict = self._get_all_page()
        self.section_text_dict.update({"title": self._title})
        self.section_text_dict.update({"paper_info": self.get_paper_info()})
        self._file_title = self._create_file_title()
        self.pdf.close()

    def get_paper_info(self):
        first_page_text = self.pdf[self.title_page].get_text()
        if "Abstract" in self.section_text_dict.keys():
            abstract_text = self.section_text_dict['Abstract']
        else:
            abstract_text = self.abs
        first_page_text = first_page_text.replace(abstract_text, "")
        return first_page_text

    def get_title(self):
        max_font_size = 0 # Initialize the maximum font size to 0

        max_font_sizes = [0]
        for page in self.pdf: # Iterate over each page
            blocks = page.get_text("dict")["blocks"] # Get the list of text blocks
            for block in blocks: # Iterate over each text block
                if block["type"] == 0 and len(block['lines']): # If it is a text type
                    if len(block["lines"][0]["spans"]):
                        font_size = block["lines"][0]["spans"][0]["size"] # Get the font size of the first line and
                        # the first paragraph of text
                        max_font_sizes.append(font_size)
                        if font_size > max_font_size: # If the font size is greater than the current maximum value
                            max_font_size = font_size # Update the maximum value

        max_font_sizes.sort()
        # print("max_font_sizes", max_font_sizes[-10:])
        cur_title = ''
        for page in self.pdf: # Iterate over each page
            blocks = page.get_text("dict")["blocks"] # Get the list of text blocks
            for block in blocks: # Iterate over each text block
                if block["type"] == 0 and len(block['lines']): # If it is a text type
                    if len(block["lines"][0]["spans"]):
                        # Update the string corresponding to the maximum value
                        cur_string = block["lines"][0]["spans"][0]["text"]
                        # Get the font size of the first line and the first paragraph of text
                        font_size = block["lines"][0]["spans"][0]["size"]
                        # print(font_size)
                        if abs(font_size - max_font_sizes[-1]) < 0.3 or abs(font_size - max_font_sizes[-2]) < 0.3:
                            if len(cur_string) > 4 and "arXiv" not in cur_string:
                                if cur_title == '':
                                    cur_title += cur_string
                                else:
                                    cur_title += ' ' + cur_string
                            self.title_page = page.number
                            # break
        title = cur_title.replace('\n', ' ')
        return title

    def _get_all_page_index(self):
        # Define a list of section names to be found
        section_list = ["Abstract",
                        'Introduction', 'Related Work', 'Background',
                        "Preliminary", "Problem Formulation",
                        'Methods', 'Methodology', "Method", 'Approach', 'Approaches',
                        # exp
                        "Materials and Methods", "Experiment Settings",
                        'Experiment',  "Experimental Results", "Evaluation", "Experiments",
                        "Results", 'Findings', 'Data Analysis',
                        "Discussion", "Results and Discussion", "Conclusion", "Conclusions",
                        "Conclusion and Future Work",
                        'References']
        # Initialize a dictionary to store the section names and their corresponding page numbers
        section_page_dict = {}
        # Iterate through each page of the document
        for page_index, cur_text in enumerate(self.text_list):
            # Iterate through the list of section names
            for section_name in section_list:
                # Convert the section name to uppercase
                section_name_upper = section_name.upper()
                section_regex = re.compile(rf"{section_name}\s*\n|\s{2,}|{section_name_upper}\s*\n|\s{2,}")
                if section_regex.search(cur_text):
                    section_page_dict[section_name] = page_index

                # If the section name is "Abstract", check for its presence in the current page
                if section_name == "Abstract" or section_name == "A B S T R A C T":
                    if section_name in cur_text:
                        section_page_dict[section_name] = page_index

        # Return all the section names found and their corresponding page numbers
        return section_page_dict

    def _get_all_page(self):
        section_dict = {}

        for sec_index, sec_name in enumerate(self.section_page_dict):
            if sec_index == 0 and self.abs:
                continue
            else:

                start_page = self.section_page_dict[sec_name]
                if sec_index < len(self.section_page_dict) - 1:
                    end_page = self.section_page_dict[list(self.section_page_dict.keys())[sec_index + 1]]
                else:
                    end_page = len(self.text_list)
                cur_sec_text = ''
                if end_page - start_page == 0:
                    if sec_index < len(self.section_page_dict) - 1:
                        next_sec = list(self.section_page_dict.keys())[sec_index + 1]
                        start_regex = r'({0}|{1})'.format(sec_name, sec_name.upper())
                        next_regex = r'({0}|{1})'.format(next_sec, next_sec.upper())
                        sec_matches = re.findall(start_regex, self.text_list[start_page])
                        next_matches = re.findall(next_regex, self.text_list[start_page])

                        if sec_matches and next_matches:
                            start_i = self.text_list[start_page].find(sec_matches[-1])
                            end_i = self.text_list[start_page].find(next_matches[0])
                            cur_sec_text += self.text_list[start_page][start_i:end_i]
                else:
                    for page_i in range(start_page, end_page):
                        if page_i == start_page:
                            regex = r'({0}|{1})'.format(sec_name, sec_name.upper())
                            sec_matches = re.findall(regex, self.text_list[start_page])
                            if sec_matches:
                                start_i = self.text_list[start_page].find(sec_matches[-1])
                                cur_sec_text += self.text_list[page_i][start_i:]
                        elif page_i < end_page:
                            cur_sec_text += self.text_list[page_i]
                        elif page_i == end_page:
                            if sec_index < len(self.section_page_dict) - 1:
                                next_sec = list(self.section_page_dict.keys())[sec_index + 1]
                                regex = r'({0}|{1})'.format(next_sec, next_sec.upper())
                                next_matches = re.findall(regex, self.text_list[start_page])
                                if next_matches:
                                    end_i = self.text_list[start_page].find(next_matches[0])
                                    cur_sec_text += self.text_list[page_i][:end_i]
                section_dict[sec_name] = cur_sec_text.replace('-\n', '').replace('\n', ' ')
        return section_dict

    def _validate_title_info(self, title_from_doi: str) -> str:
        _pdf_title = self._title
        _title_from_pdf = _pdf_title if _pdf_title else ""
        _title_final = title_from_doi if len(title_from_doi) > len(_title_from_pdf) else _title_from_pdf
        if _title_final == "":
            return "Untitled"
        return _title_final.replace(":", "-")

    def _validate_author_info(self, author_from_doi: list) -> list[list[str]]:
        authors = []
        # Get authors info from doi validation info
        if author_from_doi is not None and len(author_from_doi) > 0:
            authors = [[aut.get("given", ""), aut.get("middle", ""), aut.get("family", "")] for aut in author_from_doi]

        # Get authors info from pdf
        if len(authors) == 0:
            return self._authors

        return authors

    @staticmethod
    def _regularize_authors(authors: list[str]) -> list[list[str]]:
        if authors is None or len(authors) == 0:
            return []

        # Regular expression to match author names
        r_auts = []
        author_re = r'(?P<first_name>\b\w+\b)\s+(?P<mid_name>\w\.\s)?(?P<last_name>\b\w+\b)'
        for author in authors:
            match = re.search(author_re, author.strip())
            if match:
                author_info = [
                    match.group('first_name') or '',
                    match.group('mid_name') or '',
                    match.group('last_name') or ''
                ]
                r_auts.append(author_info)
        return r_auts

    def _create_file_title(self):
        # Creat file tile in the form of <Year>-<Authors>-<Title>
        # Extract authors info
        if self._authors is None or len(self._authors) == 0:
            authors_in_title = "<None>"
        else:
            authors_in_title = ""
            aut_list_len = len(self._authors)
            if 0 < aut_list_len < 3:
                authors_in_title = " and ".join(aut[-1] for aut in self._authors)
            elif aut_list_len >= 3:
                authors_in_title = self._authors[0][-1] + " et al"

        return str(self._year) + ' - ' + authors_in_title + ' - ' + self._title
