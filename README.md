# Paper Organization Project
This project helps you organize your paper more efficiently.

## Installation
Before running this project, you need to install the following packages:

`pip install -r requirements.txt`

## Usage
You can run the project with the following command:

`python main.py --paper_folder_path data/demo --new_folder_name new_folder --booster True --file_format md`

The following are the arguments you can use:

- `--paper_folder_path`: the path of your paper folder
- `--new_folder_name`: the name of the new folder you want to create
- `--booster`: a boolean value, if you want to boost your paper, set it to True
- `--file_format`: the format of your paper, currently, it only supports md and pdf

## Renaming Convention
This project renames your paper to the following format:

`[year] - [author] - [title]`

The information for the paper comes from DOI information extracted from the paper.

## Booster Option
If you set booster to True, it means you will use ChatGPT to generate a summary for your paper. The summary will be saved in a new folder called notes, with the same name as the paper.

The summary is only a really vague summary, and sometimes it may be wrong, so it only works as a reference for you. It is not a good summary, but it is a summary.

## Issues and Suggestions
If you find any problems with the project or have any suggestions, please let me know.