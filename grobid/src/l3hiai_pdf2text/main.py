import argparse
import sys
from text_processing import GROBIDTextProcessor
from text_processing import GROBIDProcessLauncher


## This driver demonstrates how to use the PDFtoText utility, which is based on
# GROBID (GeneRation Of BIbliographic Data), an open source library to extract text from scientific PDFs.
# GROBIB uses Deep Learning (Bidirectional-LSTM) to extract text from any formatted scientific PDF.
# It outputs an XML File of the PDF.
# We then use lxml to  extract the text from the XML from GROBIB.
# to extract text from scientific PDF.
## Example usage:
## .venv/bin/python main.py --input_dir datasets/samples/pdf/llms --output_dir datasets/samples/xml --output_format sqlite --grobid_config=grobid/grobid_config.json

def main():
    output_formats = ["sqlite", "json"]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--grobid_config", help="A config file with GROBID properties including the host ",
                        required=True)
    parser.add_argument("--input_dir", help="Directory of PDFs to convert to text ", required=True)
    parser.add_argument("--output_dir", help="An output directory ", required=True)
    parser.add_argument("--output_format", help=f"An output format {output_formats} ", required=True)

    # parser.print_help()
    parser.usage = parser.format_help()
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    data_dir = args.input_dir
    output_dir = args.output_dir
    grobid_config = args.grobid_config
    output_format = args.output_format

    if grobid_config and data_dir and output_dir and output_format in output_formats:
        grobid_launcher = GROBIDProcessLauncher()
        grobid_launcher.run_grobid_process(grobid_config=grobid_config,
                                           input_dir=data_dir,
                                           output_dir=output_dir)
        grobid_processor = GROBIDTextProcessor(output_format=output_format)
        grobid_processor.process_grobid_xmls()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
