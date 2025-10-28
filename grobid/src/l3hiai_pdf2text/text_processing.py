from urllib.parse import urlparse

from utils import Utils
import os
import sys
from lxml import etree
import re
import pandas as pd
import json
from grobid_client.grobid_client import GrobidClient
from sqlalchemy import create_engine
from IPython.display import display
from datetime import datetime


# This class provides methods for extracting text from PDF. It is based on
# GROBID (GeneRation Of BIbliographic Data), an open source library to extract text from scientific PDFs.
# GROBIB uses Deep Learning (Bidirectional-LSTM) to extract text from any formatted scientific PDF.
# It outputs an XML File of the PDF.
# We then use lxml to  extract the text from the XML produced by GROBIB.

class GROBIDProcessLauncher:
    def run_grobid_process(self, grobid_config="grobid/grobid_config.json",
                           input_dir=".",
                           output_dir="."):
        with open(grobid_config) as grobid_config_file:
            grobid_config_json = json.load(grobid_config_file)

        grobid_server = grobid_config_json['grobid_server']
        result = urlparse(grobid_server)
        utils = Utils()

        # Make sure GROBID Server is running in docker
        if not utils.is_open(result.hostname, result.port):
            print(f'{"-" * 30}')
            print(f'{utils.color("red")}Error:{utils.color("reset")}'
                  f' Could not connect to GROBID Server. ')
            print(f'Make sure GROBID is running at {grobid_server}')
            print("Here are example docker commands to get GROBID running: ")
            print(f'╰─>{utils.color("gray")}docker pull grobid/grobid:0.8.0')
            print(f'   docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0{utils.color("reset")}')
        else:
            if os.path.isdir(input_dir) and os.path.isfile(grobid_config):
                client = GrobidClient(config_path=grobid_config)
                client.process("processFulltextDocument", input_path=input_dir, output=output_dir, n=20)


class GROBIDTextProcessor:
    def __init__(self, output_dir=".", output_format="json"):
        self.output_dir = output_dir
        self.output_format = output_format

    def process_grobid_xmls(self):
        util = Utils()
        xml_files = util.get_xml_file_list(self.output_dir)
        articles = []
        out_folder = os.path.dirname(os.path.abspath(sys.argv[0]))

        for file in xml_files:
            extracted_data = self.extract_text_from_grobid_xml(file)
            articles.append(extracted_data)
        if self.output_format == "sqlite":
            db_name = f"{out_folder}/pdf_to_text_store_{datetime.now()}.db"
            sqlite_engine = create_engine(f'sqlite:///{db_name}')
            df = util.dataframe_from_articles(articles)
            df.to_sql('pdf_articles', sqlite_engine, if_exists='append', index=False)
            print(f"Data exported to Sqlite database ({db_name})")
            display(df)
        elif self.output_format == "json":
            filename = f"{out_folder}/pdf_to_text_{datetime.now()}.json"
            with open(filename, "w") as outfile:
                json.dump(articles, outfile)
    def extract_text_from_grobid_xml(self, file_path, remove_headings=True, remove_parenthethicals=True):
        tree = etree.parse(file_path)
        root = tree.getroot()
        ns = re.match(r'{(.*)}', root.tag).group(1)
        nsmap = {'default_ns': ns}
        date_published = ""
        authors_list = []
        body_text = ""
        abstract = ""

        tei_header = root.find(f"{{{ns}}}teiHeader")
        file_desc = tei_header.find(f"{{{ns}}}fileDesc")
        title_stmt = file_desc.find(f"{{{ns}}}titleStmt")
        title_node = title_stmt.find(f"{{{ns}}}title")
        paper_title = title_node.text

        profile_desc = tei_header.find(f"{{{ns}}}profileDesc")
        abstract_node = profile_desc.find(f"{{{ns}}}abstract")
        abstract = ''.join([x.strip() for x in abstract_node.itertext()])

        publication_stmt = file_desc.find(f"{{{ns}}}publicationStmt")
        publication_date = publication_stmt.find(f"{{{ns}}}date")
        publisher = publication_stmt.find(f"{{{ns}}}publisher").text

        if publication_date is not None:
            date_published = publication_date.get("when")

        source_desc = file_desc.find(f"{{{ns}}}sourceDesc")
        authors = source_desc.findall(".//default_ns:author", namespaces=nsmap)

        full_affiliation = ""

        for author in authors:
            author_full_name = ""
            author_name = author.find(f"{{{ns}}}persName")

            if author_name is not None:
                author_full_name = ' '.join(author_name.itertext())
            affiliation = author.find(f"{{{ns}}}affiliation")

            if affiliation is not None:
                full_affiliation = ', '.join([x.strip() for x in affiliation.itertext() if len(x.strip()) > 0])

            if author_full_name:
                authors_list.append({"author_name": f"{author_full_name}",
                                     "affiliation": f"{full_affiliation}"})

        if all(author["affiliation"] == "" for author in authors_list):
            for author in authors_list:
                author["affiliation"] = full_affiliation
        body_text = root.find(f"{{{ns}}}text")
        body = body_text.find(f"{{{ns}}}body")

        if remove_headings:
            headings_to_remove = body.xpath('//default_ns:head', namespaces=nsmap)
            for node in headings_to_remove:
                self.remove_element(node)

                # Remove references, formulas, and tables from body text
        nodes_to_remove = body.xpath(
            '//default_ns:ref | //default_ns:head | //default_ns:figure | //default_ns:formula',
            namespaces=nsmap)
        for node in nodes_to_remove:
            self.remove_element(node)

        full_text = ' '.join(body.itertext())

        if remove_parenthethicals:
            utils = Utils()
            full_text = utils.clean_pdf_text(full_text)
            abstract = utils.clean_pdf_text(abstract)

        data = {
            "paper_title": paper_title,
            "publisher": publisher,
            "date_published": date_published,
            "authors": authors_list,
            "abstract": abstract,
            "full_text": full_text
        }

        return data


    def add_article_metadata(self, df, article):
        df["date_published"] = article["date_published"]
        df["publisher"] = article["publisher"]
        df["date_published"] = pd.to_datetime(df["date_published"])
        df["paper_title"] = article["paper_title"]
        df["authors"] = str(article["authors"])
        return df

    def remove_element(self, el):
        if el is not None:
            parent = el.getparent()
            if el.tail is not None and el.tail.strip():
                prev = el.getprevious()
                if prev:
                    prev.tail = (prev.tail or '') + el.tail
                else:
                    parent.text = (parent.text or '') + el.tail
            parent.remove(el)

