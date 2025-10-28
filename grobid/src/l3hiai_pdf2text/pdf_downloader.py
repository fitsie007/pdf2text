import argparse
from doi2pdf import doi2pdf
import pandas as pd
import re
import json
import requests
import sys


# This code is a simple utility to download PDF files using the DOIs or URLs.
# It uses the doi2pdf package to download using teh DOIs.
# It was tested using 2 handcrafted datasets: transfer-learning.xlsx file and llm_paper_list.json.
# llm_paper_list.json was created by web-scraping https://github.com/Hannibal046/Awesome-LLM
# Usage: python pdf_downloader.py --excel_file datasets/Transfer_Learning_Survey.xlsx --output_dir datasets/samples/pdf/llms
# or python pdf_downloader.py --json_file datasets/llm_paper_list.json --output_dir datasets/samples/pdf/llms

# How to setup and use a virtual environment
# ============================================
# pip install virtualenv to install virtualenv (if not installed already)
# virtualenv venv to create your new environment
# source venv/bin/activate to enter the virtual environment
# echo $VIRTUAL_ENV to make sure the venv is active
# pip install -r requirements.txt
def get_dois_list(dataset, directory):
    df = pd.read_excel(dataset)
    df = df.dropna(subset=["DOI"])
    filelist = []

    for index, row in df.iterrows():
        doi = row["DOI"]
        year = row["Publication Year"]
        title = row["Title"]
        filename = f"{directory}/{year}-{truncate(title)}.pdf"
        filelist.append((doi, filename))
    return filelist


def truncate(the_str):
    the_str = re.sub("[^a-zA-Z0-9- ]+", "", the_str)
    if len(the_str) > 25:
        return f"{the_str[:25]}"
    else:
        return the_str


def download_pdf_by_doi(doi, filename):
    doi2pdf(doi, output=filename)


def download_pdf_from_url(url, filename):
    res = requests.get(url, stream=True)
    data = res.content

    with open(filename, "wb") as f:
        f.write(data)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--excel_file", help="An excel file with a list of PDFs with a DOI column ",
                        required=False)
    parser.add_argument("--json_file", help="A JSON file with a list of PDFs with a url column ",
                        required=False)

    parser.add_argument("--output_dir", help="An output directory to store the downloaded files ",
                        required=True)

    parser.usage = parser.format_help()
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    excel_file = args.excel_file
    json_file = args.json_file
    output_dir = args.output_dir
    data_file = excel_file or json_file
    file_format = data_file.split(".")[-1].lower()

    if file_format == "json":
        with open(data_file, "r") as f:
            llm_papers = json.load(f)
            for record in llm_papers:
                filename = f'{output_dir}/{record["date"]}-{truncate(record["paper_title"])}.pdf'
                download_pdf_from_url(record["url"], filename)
                print(f'Downloaded {record["paper_title"]:100}', end="\r")
    elif file_format == "xlsx":
        dois = get_dois_list(data_file, output_dir)
        for doi, filename in dois:
            download_pdf_by_doi(doi, filename)


main()
