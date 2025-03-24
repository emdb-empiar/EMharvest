### EMharvest

# Background

EMharvest is a Python-based tool designed to extract metadata from experimental data collected using cryo-EM microscopes for both micrograph and tilt-series data collections. It ingests microscope metadata files and converts them into a series of files that can be used with downstream processes, including an mmCIF file that can be uploaded directly into OneDep. The output files are generated in mmCIF, JSON, and CSV formats. The CSV output includes additional information such as JSON key-value pairs, mmCIF items, Microscopy XML Path, and EMDB XML Path. EMharvest may be extended to support metadata extraction from commonly used cryo-EM processing software across different facilities worldwide.

# Scope and Functionality

Included Features:
- Harvesting metadata from a TFS EPU session and exporting it in mmCIF, JSON, and CSV formats.
- Harvesting metadata from SerialEM sessions and exporting it in mmCIF, JSON, and CSV formats.
- Parsing collection metadata regardless of the directory structure used by a collection facility.
- The script supports batch processing of multiple data collection sessions.
- Validation of the mmCIF file using the latest or a previously available mmCIF dictionary.


# Installation

Clone the repository to your local machine:  
$ git clone https://github.com/emdb-empiar/EMharvest.git  
$ cd EMharvest  

Set up a virtual environment for EMharvest:  
$ python -m venv python  
$ source python/bin/activate  
$ pip install .

Each time you use EMharvest, activate the virtual environment:  
$ source python/bin/activate

Usage Instructions:

Run a harvest on a single visit directory:  
$ python emh.py --help  
$ python emh.py  

# Usage

EMharvest is used to extract metadata from cryo-EM microscopy files to help streamline OneDep deposition. It supports both EPU and SerialEM for both SPA and TOMO datasets.

python emh.py [OPTIONS]  

Arguments:

|Argument|	short|	Required|	Description|      
|--------|------|---------|------------|
|--mode|	-m|	Yes|	Mode selection: SPA for Single Particle Analysis or TOMO for Tomography|  
|--category|	-c|	Yes (for SPA)|	Type of microscopy input files: epu, epu_no_dm, or serialEM|  
|--input_file|	-i|	Yes (for SPA, epu_no_dm)|	Input SPA file in XML format (missing EpuSession.dm files)|  
|--epu|		-e|	Yes (for SPA, epu)|	EPU session file (ScreeningSession.dm)|  
|--atlas|	-a|	Yes (for SPA, epu)|	Atlas session file (Atlas*.xml)|  
|--output|	-o|	Yes|	Output directory for generated reports|  
|--print|	-p|	No|	If Y, only prints XML and exits|  
|--tomogram_file|	-t|	Yes (for TOMO)|	Input tomography file (Overview.xml)|  
|--mdoc_file|	-d|	Yes (for TOMO)|	Tomography .mdoc file|  
|--download_dict|	-y|	 No|	Download latest mmCIF dictionary (yes or no, default: yes)|  

The repository supports the following file formats as of now:  
- EPU session metadata from xml and dm files (Example: Atlas*.xml, ScreeningSession.dm and EpuSession.dm)
- EPU session metadata (without DM files) only from xml files (Example: GridSquare*.xml)
- SerialEM micrograph metadata from mdoc files (Example: *.eer.mdoc)
- SerialEM tomogram metadata from mdoc files (Example: Position*.mdoc)

Example Usage:

1. Running EMharvest for an EPU session:  
python emh.py -m SPA -c epu -e <path/to/EPU_SESSION_FILE> -a <path/to/ATLAS_SESSION_FILE> -o <path/to/OUTPUT_DIRECTORY>

2. Running EMharvest for EPU in the absence of ScreeningSession.dm files:  
python emh.py -m SPA -c epu_no_dm -i <path/to/GRID_SQUARE_XML_FILE> -o <path/to/OUTPUT_DIRECTORY>

3. Running EMharvest for SerialEM tilt Series session:  
python emh.py -m TOMO -c serialEM -t <path/to/OVERVIEW_XML_FILE> -d <path/to/MDOC_FILE> -o <path/to/OUTPUT_DIRECTORY> -l no

# Validation

EMharvest includes built-in validation for mmCIF files to ensure compliance with the mmCIF dictionary using the Gemmi tool. 

Features:  
- Validate mmCIF files for dictionary compliance.
- Automatically download the latest mmCIF dictionary, until specified not to.
- Save detailed results to a file.

Requirements:  
- Python 3 or higher
- Gemmi library (pip install gemmi)
- Network access (for dictionary download)

Installation:  
$ pip install gemmi

Output:
The results are saved in the same directory as the input mmCIF file with the filename <input_file>_val.txt.

Error Handling:
Ensures input files exist.
Provides meaningful error messages for missing files, dictionary download issues, or Gemmi command failures.

# License
This project is licensed under the BSD 3-Clause License.
