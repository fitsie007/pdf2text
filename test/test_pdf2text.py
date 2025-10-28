from l3hiai_pdf2text.text_processing import GROBIDProcessLauncher
from l3hiai_pdf2text.text_processing import GROBIDTextProcessor

def main():
    grobid_launcher = GROBIDProcessLauncher()
    grobid_config = "grobid/config.json"
    data_dir = "../datasets/samples/pdf/llms"  # The directory containing PDF files
    output_dir = "src/datasets/samples/xml"  # The output directory to store XMLs produced by GROBID
    output_format = "json"  # or sqlite -> The output format for the processed XMLs

    grobid_launcher.run_grobid_process(grobid_config=grobid_config,
                                       input_dir=data_dir,
                                       output_dir=output_dir)

    # output_dir is the location of the XML files from GROBID
    grobid_processor = GROBIDTextProcessor(output_format=output_format, output_dir=output_dir)
    grobid_processor.process_grobid_xmls()


main()