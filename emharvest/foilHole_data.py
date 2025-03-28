import xmltodict
import math

# def FoilHoleData(xmlpath: Path) -> Dict[str, Any]:
def FoilHoleData(xmlpath):
    # This will fetch the first micrograph xml data
    with open(xmlpath, "r") as xml:
        for_parsing = xml.read()
        data = xmltodict.parse(for_parsing)
    data = data["MicroscopeImage"]

    sessionName = data["uniqueID"]

    # The values are not always in the same list position in a:KeyValueOfstringanyType
    keyValueList = data["CustomData"]["a:KeyValueOfstringanyType"]

    keyMicroscopeList = data["microscopeData"]["acquisition"]["camera"]["CameraSpecificInput"][
        "a:KeyValueOfstringanyType"]

    # Loop through the list to find the DoseRate list position
    keyvalue = 0
    detectorName, detectorMode, counting, superResolution, objectiveAperture = "", "", "", "", "?"
    detector_keys = [
        "Detectors[EF-CCD].CommercialName",
        "Detectors[EF-Falcon].CommercialName"
    ]

    for i, value in enumerate(keyValueList):
        key = data["CustomData"]["a:KeyValueOfstringanyType"][i]["a:Key"]

        if key == "Detectors[BM-Falcon].DoseRate" or key == "Detectors[EF-Falcon].DoseRate":
            keyvalue = i

        if key in detector_keys:
            detectorName = data["CustomData"]["a:KeyValueOfstringanyType"][i]["a:Value"]["#text"]
            if detectorName == "BioQuantum K3":
                detectorName = "GATAN K3 BIOQUANTUM (6k x 4k)"
            elif detectorName == "Falcon 4i":
                detectorName = "TFS FALCON 4i (4k x 4k)"

        if key == "Aperture[OBJ].Name":
            objectiveAperture = data["CustomData"]["a:KeyValueOfstringanyType"][i]["a:Value"]["#text"]
            if objectiveAperture == "None":
                objectiveAperture = '?'

    for i, value in enumerate(keyMicroscopeList):
        keyMicroscopeData = \
        data["microscopeData"]["acquisition"]["camera"]["CameraSpecificInput"]["a:KeyValueOfstringanyType"][i]["a:Key"]
        if keyMicroscopeData == "ElectronCountingEnabled":
            counting = \
            data["microscopeData"]["acquisition"]["camera"]["CameraSpecificInput"]["a:KeyValueOfstringanyType"][i][
                "a:Value"]["#text"]

        if keyMicroscopeData == "SuperResolutionFactor":
            superResolution = \
            data["microscopeData"]["acquisition"]["camera"]["CameraSpecificInput"]["a:KeyValueOfstringanyType"][i][
                "a:Value"]["#text"]

    if counting == "true":
        if superResolution == "1":
            detectorMode = "SUPER-RESOLUTION"
        elif superResolution == "2":
            detectorMode = "COUNTING"

    # Retrieve the values
    # xmlDoseRate = data["CustomData"]["a:KeyValueOfstringanyType"][keyvalue]["a:Value"]["#text"]
    xmlDoseRate = "?"  # the data file has only electron_dose on camera and not the dose used on the specimen
    avgExposureTime = data["microscopeData"]["acquisition"]["camera"]["ExposureTime"]
    slitWid = data["microscopeData"]["optics"]["EnergyFilter"]["EnergySelectionSlitWidth"]
    slitInserted = data["microscopeData"]["optics"]["EnergyFilter"]["EnergySelectionSlitInserted"]
    if slitInserted == "true":
        slitWidth = slitWid
    else:
        slitWidth = "?"
    electronSource = data["microscopeData"]["gun"]["Sourcetype"]
    tiltAngleMin = round(float(data["microscopeData"]["stage"]["Position"]["A"]) * (180 / math.pi), 5)
    tiltAngleMax = round(float(data["microscopeData"]["stage"]["Position"]["B"]) * (180 / math.pi), 5)

    FoilHoleDataDict = dict(sessionName=sessionName, xmlDoseRate=xmlDoseRate, detectorName=detectorName,
                            avgExposureTime=avgExposureTime, detectorMode=detectorMode, slitWidth=slitWidth,
                            electronSource=electronSource, tiltAngleMin=tiltAngleMin, tiltAngleMax=tiltAngleMax, objectiveAperture=objectiveAperture)

    return FoilHoleDataDict

