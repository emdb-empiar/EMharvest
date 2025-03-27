import xmltodict
import re
import math

def roundup(n, decimals=0):
    """
        https://realpython.com/python-rounding/
      Rounds up a number to the specified number of decimal places.

      Args:
          n (float): The number to round up.
          decimals (int, optional): The number of decimal places to round up to. Defaults to 0.

      Returns:
          float: The rounded up number.
      """
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

def AnyXMLDataFile(xmlpath):
    """
        Reads an XML file (Overview.xml) and extracts relevant data, storing it in a dictionary.

        Args:
            xmlpath (str): The path to the XML file to read.

        Returns:
            dict: A dictionary containing the extracted data.
    """
    with open(xmlpath, "r") as xml:
        for_parsing = xml.read()
        data = xmltodict.parse(for_parsing)
    data = data["MicroscopeImage"]

    acqusition_date = data["microscopeData"]["acquisition"]["acquisitionDateTime"]
    date = acqusition_date.split("T", 1)[0]
    model_serial = data["microscopeData"]["instrument"]["InstrumentModel"]
    model_serial_split = re.split(r'(\d+)', model_serial, maxsplit=1)
    model = model_serial_split[0]
    if model == "TITAN":
        model = "TFS KRIOS"
    microscope_serial_number = model_serial_split[1]
    microscope_mode = data["microscopeData"]["optics"]["ColumnOperatingTemSubMode"]
    eV = data["microscopeData"]["gun"]["AccelerationVoltage"]
    xmlMag = data["microscopeData"]["optics"]["TemMagnification"]["NominalMagnification"]
    xmlMetrePix = data["SpatialScale"]["pixelSize"]["x"]["numericValue"]
    xmlAPix = float(xmlMetrePix) * 1e10
    xmlAPix = roundup(xmlAPix, 1)
    soft_name = data["microscopeData"]["core"]["ApplicationSoftware"]
    if soft_name == "Tomography":
        software_name = "TFS tomography"
    elif soft_name == "TemAppCommon":
        software_name = "TFS tomography"
    else:
        software_name = soft_name
    software_version = data["microscopeData"]["core"]["ApplicationSoftwareVersion"]
    illumination = data["microscopeData"]["optics"]["IlluminationMode"]

    objectiveAperture, C2_micron = "", ""
    keyValueList = data["CustomData"]["a:KeyValueOfstringanyType"]
    for i, value in enumerate(keyValueList):
        key = data["CustomData"]["a:KeyValueOfstringanyType"][i]["a:Key"]
        if key == "Aperture[OBJ].Name":
            objectiveAperture = data["CustomData"]["a:KeyValueOfstringanyType"][i]["a:Value"]["#text"]
            if objectiveAperture == "None":
                objectiveAperture = '?'
        if key == "Aperture[C2].Name":
            C2_micron = data["CustomData"]["a:KeyValueOfstringanyType"][i]["a:Value"]["#text"]

    OverViewDataDict = dict(date=date, model=model, microscope_serial_number=microscope_serial_number, microscope_mode=microscope_mode, eV=eV, xmlMag=xmlMag,
                            xmlMetrePix=xmlMetrePix, xmlAPix=xmlAPix, objectiveAperture=objectiveAperture,
                            C2_micron=C2_micron, software_name=software_name, software_version=software_version,
                            illumination=illumination)

    return OverViewDataDict

