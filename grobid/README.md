# PDF to Text
This code converts PDF to Text. It is based on
GROBID (GeneRation Of BIbliographic Data), an open source library to extract text from scientific PDFs.
GROBIB uses Deep Learning (Bidirectional-LSTM) to extract text from any formatted scientific PDF.
It outputs an XML File of the PDF.

We then use lxml to extract the text from the XML produced by GROBIB.

## Preliminaries
Make sure GROBID is installed and running as a docker container as follows:
* ```docker pull grobid/grobid:0.8.0```
* ```docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0```

## Set up a virtual environment to keep your Python packages separate from the required packages
```pip install virtualenv``` to install virtualenv (if not installed already)<br>
You may also use ```python3 -m venv .venv``` to create a virtual environment (See https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)<br>
```virtualenv venv``` to create your new environment.<br>
```source venv\bin\activate``` to enter the virtual environment<br>
```echo $VIRTUAL_ENV``` to make sure the venv is active

## Execution Modes
### As a Standalone package
Download the files in the dist folder<br>
Run ```venv\bin\python -m pip install l3hiai_pdf2text*.whl```<br>or<br> 
 ```venv\bin\python -m pip install l3hiai_pdf2text*.gz```

### As a package from the source code 
* Download the entire project
* Run ```venv\bin\python -m pip install``` 

### As raw source code
* First, install the dependencies ```venv\bin\pip install -r requirements.txt```<br>

#### To test this project from the raw files:
```venv/bin/python main.py --input_dir datasets/samples/pdf/llms --output_dir datasets/samples/xml --output_format sqlite --grobid_config=grobid/grobid_config.json```
* ```--input_dir```: Directory of PDFs to convert to text
* ```--output_dir```: An output directory for the GROBID XML files
* ```--output_format```: 'json' or 'sqlite'. A JSON file will be created with a user-friendly output or written to an SQLite database file.
* ```--grobid_config```: A config file with GROBID properties including the host

## How to use the package
* After installing the package,
**See example ```test/test_pdf2text.py``` for help using the package**

## How to Build the Source Files
* Make sure you have the latest version of PyPA’s build installed:
```.venv/bin/python -m pip install build```
* Build the source distribution: 
```.venv/bin/python -m build --sdist```
* Now run this command from the same directory where pyproject.toml is located:
* ```.venv/bin/python -m build --wheel```
