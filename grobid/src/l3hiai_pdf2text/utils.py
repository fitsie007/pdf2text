import os

from langchain_community.document_loaders import PyPDFium2Loader
import re
import pandas as pd
from urllib.parse import urlparse
import logging
import string
import socket
import time
import builtins
import requests
from IPython.display import display

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)

CONTRACTION_MAP = {
    "ain't": "is not",
    "aren't": "are not",
    "can't": "cannot",
    "can't've": "cannot have",
    "'cause": "because",
    "could've": "could have",
    "couldn't": "could not",
    "couldn't've": "could not have",
    "didn't": "did not",
    "doesn't": "does not",
    "don't": "do not",
    "hadn't": "had not",
    "hadn't've": "had not have",
    "hasn't": "has not",
    "haven't": "have not",
    "he'd": "he would",
    "he'd've": "he would have",
    "he'll": "he will",
    "he'll've": "he he will have",
    "he's": "he is",
    "how'd": "how did",
    "how'd'y": "how do you",
    "how'll": "how will",
    "how's": "how is",
    "I'd": "I would",
    "I'd've": "I would have",
    "I'll": "I will",
    "I'll've": "I will have",
    "I'm": "I am",
    "I've": "I have",
    "i'd": "i would",
    "i'd've": "i would have",
    "i'll": "i will",
    "i'll've": "i will have",
    "i'm": "i am",
    "i've": "i have",
    "isn't": "is not",
    "it'd": "it would",
    "it'd've": "it would have",
    "it'll": "it will",
    "it'll've": "it will have",
    "it's": "it is",
    "let's": "let us",
    "ma'am": "madam",
    "mayn't": "may not",
    "might've": "might have",
    "mightn't": "might not",
    "mightn't've": "might not have",
    "must've": "must have",
    "mustn't": "must not",
    "mustn't've": "must not have",
    "needn't": "need not",
    "needn't've": "need not have",
    "o'clock": "of the clock",
    "oughtn't": "ought not",
    "oughtn't've": "ought not have",
    "shan't": "shall not",
    "sha'n't": "shall not",
    "shan't've": "shall not have",
    "she'd": "she would",
    "she'd've": "she would have",
    "she'll": "she will",
    "she'll've": "she will have",
    "she's": "she is",
    "should've": "should have",
    "shouldn't": "should not",
    "shouldn't've": "should not have",
    "so've": "so have",
    "so's": "so as",
    "that'd": "that would",
    "that'd've": "that would have",
    "that's": "that is",
    "there'd": "there would",
    "there'd've": "there would have",
    "there's": "there is",
    "they'd": "they would",
    "they'd've": "they would have",
    "they'll": "they will",
    "they'll've": "they will have",
    "they're": "they are",
    "they've": "they have",
    "to've": "to have",
    "wasn't": "was not",
    "we'd": "we would",
    "we'd've": "we would have",
    "we'll": "we will",
    "we'll've": "we will have",
    "we're": "we are",
    "we've": "we have",
    "weren't": "were not",
    "what'll": "what will",
    "what'll've": "what will have",
    "what're": "what are",
    "what's": "what is",
    "what've": "what have",
    "when's": "when is",
    "when've": "when have",
    "where'd": "where did",
    "where's": "where is",
    "where've": "where have",
    "who'll": "who will",
    "who'll've": "who will have",
    "who's": "who is",
    "who've": "who have",
    "why's": "why is",
    "why've": "why have",
    "will've": "will have",
    "won't": "will not",
    "won't've": "will not have",
    "would've": "would have",
    "wouldn't": "would not",
    "wouldn't've": "would not have",
    "y'all": "you all",
    "y'all'd": "you all would",
    "y'all'd've": "you all would have",
    "y'all're": "you all are",
    "y'all've": "you all have",
    "you'd": "you would",
    "you'd've": "you would have",
    "you'll": "you will",
    "you'll've": "you will have",
    "you're": "you are",
    "you've": "you have"
}


class IPConnectionException(Exception):
    """ Exception raised when there is an error connecting to the server """
    pass


class Utils:
    def __init__(self):
        self._pairs = None
        self._text = None
        self._terminal_colors = {
            "red": f"\33[31m",
            "gray": f"\33[100m",
            "reset": f"\33[0m",
            "blue": f"\33[34m"
        }

    def replace_contractions(self, text, contraction_map):
        for contraction, replacement in contraction_map.items():
            text = re.sub(r'\b' + re.escape(contraction) + r'\b', replacement, text)
        return text

    def remove_text_before_abstract(self, in_text):
        abstract_pattern = '.* *ABSTRACT[:.\-\n\r ]*'
        match = re.search(abstract_pattern, in_text, flags=re.IGNORECASE)
        if match is not None:
            start, stop = match.span()
            if start == 0:
                in_text = re.sub(abstract_pattern, '', in_text, flags=re.IGNORECASE)
        return in_text

    def clean_pdf_text(self, text):
        # replace non-printable characters such as "between" -> "be\x02tween"
        text = ''.join(filter(lambda x: x in string.printable, text))

        # Replace newline characters with empty string
        # text = text.replace('\n', '')

        # Remove parenthesized text
        text = re.sub(r'\([^)]*\)', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\{.*?\}', '', text)
        text = re.sub(r'\<.*?\>', '', text)

        # Replace '&' with 'and'
        text = text.replace('&', 'and')
        text = re.sub(r'-\s+', '', text)
        text = re.sub(r'\s-+', '', text)

        pattern = r'\b(\w+)-(\w+)\b'
        text = re.sub(pattern, r'\1\2', text)  # remove hyphens from words
        # Replace 'Fig.  X' with 'FigX' where X is any number
        text = re.sub(r'Fig\. *(\d+)', r'Fig\1', text)

        # Replace contractions
        text = self.replace_contractions(text, CONTRACTION_MAP)

        # Use regex to replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)

        # Strip any leading or trailing spaces
        text = text.strip()

        return text

    def get_text_from_file(self, filename):
        with open(filename) as f:
            return f.read()

    def get_xml_file_list(self, root_dir):
        xml_files = []
        for file in os.listdir(root_dir):
            # select files with xml extension
            if file.endswith(".xml"):
                xml_files.append(os.path.join(root_dir, file))
        return xml_files

    def get_text_from_pdf(self, url):
        loader = PyPDFium2Loader(url)
        pages = loader.load()
        page_content = []

        ## Extract text content by excluding all content after the references section
        for page in pages:
            page_text = page.page_content
            references_found = re.search("[\r\n]*References *[\n\r]+", page_text)

            if references_found:
                text = page_text[0: references_found.start()]
                text = self.clean_pdf_text(text)
                page_content.append(text)
                break
            else:
                page_text = self.clean_pdf_text(page_text)
                page_content.append(page_text)
        info = "\n\n".join(page_content)
        info = self.remove_text_before_abstract(info)
        self._text = info
        return info

    def set_text(self, text):
        self._text = text


    def uri_validator(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except AttributeError:
            return False

    def parse_env_file(self, env_file):
        env_vars = {}
        if os.path.isfile(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                        # Remove leading `export `
                    if line.lower().startswith('export '):
                        key, value = line.replace('export ', '', 1).strip().split('=', 1)
                    else:
                        try:
                            key, value = line.strip().split('=', 1)
                        except ValueError:
                            logging.error(f"ENV: error parsing line: '{line}'")

                        env_vars[key] = value  # Save to dictionary
        return env_vars

    def is_open(self, ip, port, timeout=5):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            # ip = socket.gethostbyname(ip)
            s.connect((ip, int(port)))
            s.shutdown(socket.SHUT_RDWR)
            return True
        except IPConnectionException:
            return False
        except builtins.ConnectionRefusedError:
            return False
        except requests.exceptions.ConnectionError:
            return False
        finally:
            s.close()

    def check_host(self, ip, port, retry=5, delay=10):
        ip_up = False
        for i in range(retry):
            if self.is_open(ip, port):
                ip_up = True
                break
            else:
                time.sleep(delay)
        return ip_up

    def color(self, color_name):
        return self._terminal_colors[color_name]

    def dataframe_from_articles(self, articles):
        for article in articles:
            # convert date to pandas date to aid in error-free conversion to SQL
            article["date_published"] = pd.to_datetime(article["date_published"])
            article["authors"] = str(article["authors"])
        df = pd.DataFrame.from_records(articles)
        return df
