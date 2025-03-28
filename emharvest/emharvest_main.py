#!/usr/bin/env python3

import os
import fnmatch
import math
import argparse
import datetime

import dateutil.parser
import glob
from pathlib import Path
import pandas as pd
import numpy as np
import re

import json
from rich.pretty import pprint
from typing import Any, Dict
import xmltodict

from emharvest.harvestor import perform_tomogram_harvest, perform_spa_harvest_nonepu, perform_serialEM_harvest
from emharvest.atlas_files import findpattern, searchSupervisorAtlas, searchSupervisorData
from emharvest.foilHole_data import FoilHoleData
from emharvest.save_deposition_file import save_deposition_file

def parse_arguments():
    prog = "EM HARVEST"
    usage = """
                Harvesting microscopy data for automatic depostion.
                Example:
                For single particle data usage is:
                python emh.py -m SPA -c epu -e _repo_data/Supervisor_20230919_140141_84_bi23047-106_grid1/EpuSession.dm -a _repo_data/atlas/Supervisor_20230919_115905_Atlas_bi23047-106/ScreeningSession.dm  -o harvested/Supervisor_20230919_140141_84_bi23047-106_grid1
                or for non-standard epu files the command is like:
                python emh.py -m SPA -c epu_no_dm -i _repo_data/cm33879-3/raw5/metadata/Images-Disc1/GridSquare_30454884/GridSquare_20230531_130838.xml  -o harvested/cm33879-3
                or for tomogram data usage is:
                python emh.py -m TOMO -c epu -t _repo_data/tomo_data/SearchMaps/Overview.xml -d _repo_data/tomo_data/Position_1_33.mdoc -o harvested/ebic_tomo
                """
    parser = argparse.ArgumentParser(description="Harvesting microscopy data for automatic deposition.")
    parser.add_argument("-m", "--mode", required=True, choices=["SPA", "TOMO"], help="Microscopy mode")
    parser.add_argument("-c", "--category", required=True, choices=["epu", "epu_no_dm", "serialEM"], help="Data category")
    parser.add_argument("-e", "--epu", help="EPU XML file")
    parser.add_argument("-a", "--atlas", help="Atlas XML file")
    parser.add_argument("-i", "--input_file", help="Input XML file for non-EPU data")
    parser.add_argument("-t", "--tomogram_file", help="Tomogram file for TOMO mode")
    parser.add_argument("-d", "--mdoc_file", help="MDOC metadata file")
    parser.add_argument("-l", "--download_dict", help="Download the latest mmCIF dictionary")
    parser.add_argument("-o", "--output_dir", help="Output directory for generated files")
    parser.add_argument("-p", "--print", action="store_true", help="Print parsed XML")
    return parser.parse_args()

def main():
    global args
    args = parse_arguments()
    if args.mode == "SPA" and args.category == "epu":
        if not args.epu or not args.atlas:
            args.error("SPA mode requires both --epu and --atlas files.")

        main.epu_xml = args.epu
        main.epu_directory = os.path.dirname(args.epu)

        if args.print:
            print_epu_xml(main.epu_xml)
            exit(1)

        main.atlas_xml = args.atlas
        main.atlas_directory = os.path.dirname(args.atlas)

        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

        perform_minimal_harvest_epu(main.epu_xml, args.output_dir)

    if args.mode == "SPA" and args.category == "epu_no_dm":
        main.input_xml = args.input_file
        main.input_directory = os.path.dirname(args.input_file)

        if args.print:
            print_epu_xml(main.input_xml)
            exit(1)

        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

        perform_spa_harvest_nonepu(main.input_xml, args.output_dir)

    elif args.mode == "TOMO" and args.category != "serialEM":
        tomogram_file = args.tomogram_file
        mdoc_file = args.mdoc_file
        if not tomogram_file or not mdoc_file:
            args.error("TOMO mode requires both --tomogram_file and a --mdoc file.")

        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

        perform_tomogram_harvest(tomogram_file, mdoc_file,args.output_dir)

    elif args.mode == "SPA" or args.mode == "TOMO":
        if args.category == "serialEM":
            mdoc_file = args.mdoc_file
            if not mdoc_file:
                args.error("SPA and TOMO mode both requires a --mdoc file for SerialEM.")

            if not os.path.exists(args.output_dir):
                os.makedirs(args.output_dir)
            perform_serialEM_harvest(mdoc_file, args.output_dir)

def get_output_folder_name(path):
    parts = path.lstrip(os.sep).split(os.sep)  # Split path into parts
    return parts[1] if len(parts) > 1 else None

def findpattern(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    # result = glob.glob('**/'+str(pattern), recursive=True)
    return result


def roundup(n, decimals=0):
    # https://realpython.com/python-rounding/
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

def print_epu_xml(xml_path: Path) -> Dict[str, Any]:
    # Use this function for troubleshooting/viewing the raw xml to find data structure
    with open(xml_path, "r") as xml:
        for_parsing = xml.read()
        data = xmltodict.parse(for_parsing)
    data = data["EpuSessionXml"]

    data = json.loads(json.dumps(data))
    pprint(data)


def getXmlMag(xml_path: Path) -> Dict[str, Any]:
    try:
        with open(xml_path, "r") as xml:
            for_parsing = xml.read()
            data = xmltodict.parse(for_parsing)
        data = data["MicroscopeImage"]
    except:
        xmlMag = 0
        xmlAPix = 0
    else:
        xmlMag = data["microscopeData"]["optics"]["TemMagnification"]["NominalMagnification"]
        xmlMetrePix = data["SpatialScale"]["pixelSize"]["x"]["numericValue"]

        xmlAPix = float(xmlMetrePix) * 1e10
        xmlAPix = roundup(xmlAPix, 1)

    return xmlMag, str(xmlAPix)


# def xml_presets(xml_path: Path) -> Dict[str, Any]:
def xml_presets(xml_path: Path, atlas_data: Dict[str, Any], tile_data: Dict[str, Any]) -> Dict[str, Any]:
    with open(xml_path, "r") as xml:
        for_parsing = xml.read()
        data = xmltodict.parse(for_parsing)
    data = data["EpuSessionXml"]

    ## Presets
    # Loop through the presets in the Microscope Settings list
    presets = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
        "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"]
    length = len(presets)
    camera = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
        "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][0]["value"]["b:Acquisition"]["c:camera"][
        "c:CameraSpecificInput"]["KeyValuePairs"]["KeyValuePairOfstringanyType"]
    lengthCam = len(camera)

    # Create list for gathering preset conditions for reporting
    # DEV DEV DEV might be more flexible to have these going into dataframe
    namePresetList = []
    probePresetList = []
    magPresetList = []
    apixPresetList = []
    spotPresetList = []
    c2PresetList = []
    beamDPresetList = []
    defocusPresetList = []
    timePresetList = []
    binPresetList = []

    # Loop to gather all microscope presets used for session
    for x in range(0, length):
        name = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
            "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["key"]

        # Get magnifications from image xml, they are not stored in the epu session file
        if name == 'Atlas':
            if atlas_data["xmlAtlas"]:
                mag = getXmlMag(atlas_data["xmlAtlas"])[0]
                apix = getXmlMag(atlas_data["xmlAtlas"])[1]
        elif name == 'GridSquare':
            if tile_data["xmlSquare"]:
                mag = getXmlMag(tile_data["xmlSquare"])[0]
                apix = getXmlMag(tile_data["xmlSquare"])[1]
        elif name == 'Hole':
            if tile_data["xmlHole"]:
                mag = getXmlMag(tile_data["xmlHole"])[0]
                apix = getXmlMag(tile_data["xmlHole"])[1]
        elif name == 'Acquisition':
            if tile_data["xmlData"]:
                mag = getXmlMag(tile_data["xmlData"])[0]
                apix = getXmlMag(tile_data["xmlData"])[1]
        else:
            mag = 0
            apix = 0

        probeMode = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
            "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Optics"]["c:ProbeMode"]
        spot = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
            "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Optics"]["c:SpotIndex"]
        c2 = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
            "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Optics"]["c:Apertures"][
            "c:C2Aperture"]["c:Diameter"]
        beamD = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
            "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Optics"]["c:BeamDiameter"]
        # Deal with two condensor lens systems that don't know beam diameter
        if isinstance(beamD, dict):
            beamD = 0
        else:
            beamD = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
                "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Optics"][
                "c:BeamDiameter"]
        beamDmicron = float(beamD) * 1e6
        DF = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
            "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Optics"]["c:Defocus"]
        DFmicron = float(DF) * 1e6
        time = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
            "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Acquisition"]["c:camera"][
            "c:ExposureTime"]
        epuBin = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"][
            "KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Acquisition"]["c:camera"][
            "c:Binning"]["d:x"]

        # Here we face data in lists and not always in the same list position so need to loop to find position
        # for y in range(0, lengthCam):
        # listKeyValue = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"]["KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Acquisition"]["c:camera"]["c:CameraSpecificInput"]["KeyValuePairs"]["KeyValuePairOfstringanyType"][y]["key"]["#text"]
        # if listKeyValue == 'SuperResolutionFactor':
        # superRes = listKeyValue
        # superResOn = data["Samples"]["_items"]["SampleXml"][0]["MicroscopeSettings"]["KeyValuePairs"]["KeyValuePairOfExperimentSettingsIdMicroscopeSettingsCG2rZ1D8"][x]["value"]["b:Acquisition"]["c:camera"]["c:CameraSpecificInput"]["KeyValuePairs"]["KeyValuePairOfstringanyType"][y]["value"]["#text"]

        # Rounding
        spot = round(float(spot))
        c2 = round(float(c2))
        beamDmicron = roundup(float(beamDmicron), 1)
        DFmicron = roundup(float(DFmicron), 1)
        time = roundup(float(time), 2)
        mag = round(float(mag))
        apix = roundup(float(apix), 3)

        # Report presets or continue silentily
        print(name)
        print('Nominal magnification: ' + str(mag) + ' X')
        print('Pixel size: ' + str(apix) + ' apix')
        print('Probe mode: ' + str(probeMode))
        print('Spot: ' + str(spot))
        print('C2 apeture: ' + str(c2) + ' microns')
        print('Beam diameter: ' + str(beamDmicron) + ' microns')
        print('Defocus: ' + str(DFmicron) + ' microns')
        print('Exposure time: ' + str(time) + ' seconds')
        print('')

        # Append presets to the preset lists for reporting
        namePresetList.append(name)
        magPresetList.append(mag)
        apixPresetList.append(apix)
        probePresetList.append(probeMode)
        spotPresetList.append(spot)
        c2PresetList.append(c2)
        beamDPresetList.append(beamDmicron)
        defocusPresetList.append(DFmicron)
        timePresetList.append(time)
        binPresetList.append(epuBin)

        # Gather main params for reporting
        if name == 'Acquisition':
            xml_presets.time = time
            xml_presets.beamD = beamDmicron
            xml_presets.probe = probeMode
            xml_presets.C2 = c2
            xml_presets.spot = spot
            xml_presets.epuBin = epuBin
            xml_presets.mag = mag
            xml_presets.apix = apix
            # xml_presets.superRes = superRes
            # xml_presets.superResOn = superResOn
        if name == 'AutoFocus':
            xml_presets.beamDAutoFocus = beamDmicron

        # Gather all presets for mass reporting
        xml_presets.namePresetList = namePresetList
        xml_presets.magPresetList = magPresetList
        xml_presets.apixPresetList = apixPresetList
        xml_presets.probePresetList = probePresetList
        xml_presets.spotPresetList = spotPresetList
        xml_presets.c2PresetList = c2PresetList
        xml_presets.beamDPresetList = beamDPresetList
        xml_presets.defocusPresetList = defocusPresetList
        xml_presets.timePresetList = timePresetList
        xml_presets.binPresetList = binPresetList

    # report complete
    print('Finished gathering all microscope presets')


def xml_presets_data(micpath: Path) -> Dict[str, Any]:
    # This will fetch the first micrograph xml data
    with open(micpath, "r") as xml:
        for_parsing = xml.read()
        data = xmltodict.parse(for_parsing)
    data = data["MicroscopeImage"]

    ## SuperResolutionBinning Factor
    # The SuperResolutionFactor is not always in the same list position in a:KeyValueOfstringanyType
    keyValueList = data["microscopeData"]["acquisition"]["camera"]["CameraSpecificInput"]["a:KeyValueOfstringanyType"]

    # Loop through the list to find the SuperResolutionFactor list position
    i = 0
    for value in keyValueList:
        key = data["microscopeData"]["acquisition"]["camera"]["CameraSpecificInput"]["a:KeyValueOfstringanyType"][i][
            "a:Key"]
        if key == "SuperResolutionFactor":
            j = i
        i = i + 1

    try:
        superResBin = \
        data["microscopeData"]["acquisition"]["camera"]["CameraSpecificInput"]["a:KeyValueOfstringanyType"][j][
            "a:Value"]["#text"]
    except:
        superResBin = 'Unknown'

    ## Energy filter
    # Known error in nt29493-49 - glacios
    try:
        filterSlit = data["microscopeData"]["optics"]["EnergyFilter"]["EnergySelectionSlitInserted"]
    except:
        filterSlit = 'None'
    else:
        filterSlit = data["microscopeData"]["optics"]["EnergyFilter"]["EnergySelectionSlitInserted"]
    try:
        filterSlitWidth = data["microscopeData"]["optics"]["EnergyFilter"]["EnergySelectionSlitWidth"]
    except:
        filterSlitWidth = 'None'
    else:
        filterSlitWidth = data["microscopeData"]["optics"]["EnergyFilter"]["EnergySelectionSlitWidth"]

    # Aperture(s)
    # Loop through the list to find the Objective aperture list position
    i = 0
    for value in keyValueList:
        key = data["CustomData"]["a:KeyValueOfstringanyType"][i]["a:Key"]
        if key == "Aperture[OBJ].Name":
            keyvalue = i
            objectiveAperture = data["CustomData"]["a:KeyValueOfstringanyType"][i]["a:Value"]["#text"]
            if objectiveAperture == "None":
                objectiveAperture = '?'
        i = i + 1

    # Stage tilt
    stageAlphaRad = getStageTilt(micpath)[0]
    stageBetaRad = getStageTilt(micpath)[1]
    stageAlpha = roundup(math.degrees(float(stageAlphaRad)), 2)
    stageBeta = roundup(math.degrees(float(stageBetaRad)), 2)

    # Report
    xml_presets_data.superResBin = superResBin
    xml_presets_data.filterSlitWidth = filterSlitWidth
    xml_presets_data.filterSlit = filterSlit
    xml_presets_data.stageAlpha = roundup(float(stageAlpha), 1)
    xml_presets_data.stageBeta = roundup(float(stageBeta), 1)
    xml_presets_data.objective = objectiveAperture


def getStageTilt(micpath: Path) -> Dict[str, Any]:
    # This will fetch the first micrograph xml data
    with open(micpath, "r") as xml:
        for_parsing = xml.read()
        data = xmltodict.parse(for_parsing)
    data = data["MicroscopeImage"]

    # Find the stage Alpha (DEV DEV think the units might be 1/100th)
    stageAlpha = data["microscopeData"]["stage"]["Position"]["A"]
    stageBeta = data["microscopeData"]["stage"]["Position"]["B"]

    return [stageAlpha, stageBeta]


def xml_session(xml_path: Path) -> pd.DataFrame:
    data_dict = {}
    with open(xml_path, "r") as xml:
        first_line = xml.readline().strip()  # Read only the first line to extract version
        xml.seek(0) # Reset file pointer to read full content
        for_parsing = xml.read()
        data = xmltodict.parse(for_parsing)
    data = data["EpuSessionXml"]

    # Location of EPU session directory on which this script was ran
    data_dict['realPath'] = os.path.realpath(xml_path)

    # EPU version (old way of harvesting EPU Version, did not work well when harvested from Epusession.dm files)
    # epuId = data["Version"]["@z:Id"]
    # epuBuild = data["Version"]["a:_Build"]
    # epuMajor = data["Version"]["a:_Major"]
    # epuMinor = data["Version"]["a:_Minor"]
    # epuRevision = data["Version"]["a:_Revision"]
    # data_dict['epuVersion'] = str(epuMajor) + '.' + str(epuMinor) + '.' + str(epuRevision) + '-' + str(
    #     epuId) + '.' + str(epuBuild)

    #Extract EPU version from the first line's z:Assembly
    assembly_match = re.search(r'z:Assembly="([^"]+)"', first_line)
    z_assembly = assembly_match.group(1) if assembly_match else "Unknown"

    version_match = re.search(r'Version=([\d.]+)', z_assembly)
    epu_version = version_match.group(1) if version_match else "?"

    data_dict['epuVersion'] = epu_version

    # Output format
    data_dict['doseFractionOutputFormat'] = data["DoseFractionsOutputFormat"]["#text"]

    # Autoloader slot (starts at 0)
    autoSlot = data["AutoloaderSlot"]
    data_dict['autoSlot'] = float(autoSlot) + 1

    # SampleXml is a list denoted inside [], pull 0 out
    # Then the text of AtlasId is in a key pair in the dictionary denoted by {}, so call that key pair
    # Use the print_epu_xml def to see full [] and {} formatted data structure
    data_dict['atlasDir'] = data["Samples"]["_items"]["SampleXml"][0]["AtlasId"]["#text"]

    # Session name and creation time
    sessionName = xml_sessionName(xml_path)
    sessionDate = data["Samples"]["_items"]["SampleXml"][0]["StartDateTime"]
    sessionDateFormat = formatEPUDate(sessionDate)
    data_dict['sessionName'] = sessionName
    data_dict['sessionDate'] = sessionDateFormat

    # Grid type - lacey or holeycarbon or holeygold
    try:
        data_dict['gridType'] = data["Samples"]["_items"]["SampleXml"][0]["GridType"]
    except:
        data_dict['gridType'] = 'Unknown'

    # The I0 filter settings may hint at what grid type is being used
    try:
        data_dict['I0set'] = data["Samples"]["_items"]["SampleXml"][0]["FilterHolesSettings"]["IsCalibrated"]
    except:
        data_dict['I0set'] = 'Unknown'

    try:
        data_dict['I0MaxInt'] = round(
            float(data["Samples"]["_items"]["SampleXml"][0]["FilterHolesSettings"]["MaximumIntensity"]))
    except:
        data_dict['I0MaxInt'] = 'Unknown'

    try:
        data_dict['I0MinInt'] = round(
            float(data["Samples"]["_items"]["SampleXml"][0]["FilterHolesSettings"]["MinimumIntensity"]))
    except:
        data_dict['I0MinInt'] = 'Unknown'

    # Clustering method
    data_dict['clustering'] = data["ClusteringMode"]
    data_dict['clusteringRadius'] = float(data["ClusteringRadius"]) * 1e6 if data[
                                                                                 "ClusteringMode"] == 'ClusteringWithImageBeamShift' else np.nan

    data_dict['focusWith'] = \
    data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["AutoFocusArea"]["FocusWith"]["#text"]
    data_dict['focusRecurrence'] = \
    data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["AutoFocusArea"]["Recurrence"]["#text"]

    data_dict['delayImageShift'] = data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"][
        "DelayAfterImageShift"]
    data_dict['delayStageShift'] = data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"][
        "DelayAfterStageShift"]

    # AFIS or accurate
    if data["ClusteringMode"] == 'ClusteringWithImageBeamShift':
        data_dict['afisMode'] = 'AFIS'
        data_dict['afisRadius'] = data_dict['clusteringRadius']
    else:
        data_dict['afisMode'] = 'Accrt'
        data_dict['afisRadius'] = np.nan

    # Send xml dict over to function to get defocus range
    defocusRange = getDefocusRange(data)

    # In some cases the defocus list is a single value, test to deal with
    # Also find max and min defocus values
    if isinstance(defocusRange, str):
        # data_dict['defocusList'] = "xml read error"
        data_dict['defocusMax'] = "xml read error"
        data_dict['defocusMin'] = "xml read error"
    elif isinstance(defocusRange, list):
        defocusRangeMicron = [float(element) * 1 for element in defocusRange]
        defocusRangeRound = [round(num, 2) for num in defocusRangeMicron]
        # data_dict['defocusList'] = defocusRangeRound
        data_dict['defocusMax'] = min(defocusRangeRound)
        data_dict['defocusMin'] = max(defocusRangeRound)

    df = pd.DataFrame(data_dict, index=[0])

    # Print to terminal
    print('EPU version:', data_dict['epuVersion'])
    print('Dose fraction output:', data_dict['doseFractionOutputFormat'])
    print('EPU Session:', data_dict['sessionName'])
    print('EPU Session date:', data_dict['sessionDate'])
    print('EPU Session path:', data_dict['realPath'])
    print()
    print('Clustering mode:', data_dict['clustering'])
    print('Clustering radius:', data_dict['clusteringRadius'])
    print('Focus mode:', data_dict['focusWith'])
    print('Focus recurrance:', data_dict['focusRecurrence'])
    print()
    print('Autoloader slot:', data_dict['autoSlot'])
    print('Atlas directory:', data_dict['atlasDir'])
    print()
    # print('Defocus list:', data_dict['defocus'])
    print('Defocus max:', data_dict['defocusMax'])
    print('Defocus min:', data_dict['defocusMin'])
    print()
    print('Image shift delay:', data_dict['delayImageShift'])
    print('Stage shift delay:', data_dict['delayStageShift'])
    print('Grid type:', data_dict['gridType'])
    print('I0 set:', data_dict['I0set'])
    print('I0 max:', data_dict['I0MaxInt'])
    print('I0 min:', data_dict['I0MinInt'])
    print()
    print('\033[1m' + 'Finished gathering metadata from main EPU session file' + '\033[0m')
    print()

    return df


def xml_sessionName(xml_path):
    # It is necessary to have a function for getting xml session name elsewhere in script
    with open(xml_path, "r") as xml:
        for_parsing = xml.read()
        data = xmltodict.parse(for_parsing)
    data = data["EpuSessionXml"]

    sessionName = data["Name"]["#text"]

    return sessionName


def formatEPUDate(d):
    # Returns formatted in datetime, needs to be string for printing

    # https://stackoverflow.com/questions/17594298/date-time-formats-in-python
    # https://www.w3schools.com/python/python_datetime.asp
    # https://www.tutorialexample.com/python-detect-datetime-string-format-and-convert-to-different-string-format-python-datetime-tutorial/amp/
    # Read in EPU formatted date and time - remember input is a string
    epuDate = dateutil.parser.parse(d)
    epuDate = epuDate.strftime("%Y-%m-%d %H:%M:%S")
    return datetime.datetime.strptime(epuDate, "%Y-%m-%d %H:%M:%S")


def getDefocusRange(data):
    # Need to deal with cases where it's multi shot or single shot
    templates = \
    data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["DataAcquisitionAreas"]["a:m_serializationArray"][
        "b:KeyValuePairOfintDataAcquisitionAreaXmlBpEWF4JT"]

    if isinstance(templates, list):
        shotType = 'Multishot'
        # DEV DEV This defocus code might need a revisit if you get lots of errors
        d = data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["DataAcquisitionAreas"][
            "a:m_serializationArray"]["b:KeyValuePairOfintDataAcquisitionAreaXmlBpEWF4JT"][0]["b:value"][
            "ImageAcquisitionSettingXml"]["Defocus"]
        if d.get("a:double"):
            try:
                df = data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["DataAcquisitionAreas"][
                    "a:m_serializationArray"]["b:KeyValuePairOfintDataAcquisitionAreaXmlBpEWF4JT"][0]["b:value"][
                    "ImageAcquisitionSettingXml"]["Defocus"]["a:double"]
                # Sometimes the values contain unicode en-dash and not ASCII hyphen
                # df.replace('\U00002013', '-')
            except:
                print('Warning, could not find defocus range in xml file')
                df = ['xml read error']
        else:
            try:
                df = data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["DataAcquisitionAreas"][
                    "a:m_serializationArray"]["b:KeyValuePairOfintDataAcquisitionAreaXmlBpEWF4JT"]["b:value"][
                    "ImageAcquisitionSettingXml"]["Defocus"]["a:_items"]["a:double"]
                # Sometimes the values contain unicode en-dash and not ASCII hyphen
            # df.replace('\U00002013', '-')
            except:
                print('Warning, could not find defocus range in xml file')
                df = ['xml read error']
    else:
        shotType = 'Single'
        # There is sometimes a data structure change I think in single shot acqusition, cause currently unknown, check for it
        d = data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["DataAcquisitionAreas"][
            "a:m_serializationArray"]["b:KeyValuePairOfintDataAcquisitionAreaXmlBpEWF4JT"]["b:value"][
            "ImageAcquisitionSettingXml"]["Defocus"]
        if d.get("a:double"):
            try:
                df = data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["DataAcquisitionAreas"][
                    "a:m_serializationArray"]["b:KeyValuePairOfintDataAcquisitionAreaXmlBpEWF4JT"]["b:value"][
                    "ImageAcquisitionSettingXml"]["Defocus"]["a:double"]
                # Sometimes the values contain unicode en-dash and not ASCII hyphen
                # df.replace('\U00002013', '-')
            except:
                print('Warning, could not find defocus range in xml file')
                df = ['xml read error']
        else:
            try:
                df = data["Samples"]["_items"]["SampleXml"][0]["TargetAreaTemplate"]["DataAcquisitionAreas"][
                    "a:m_serializationArray"]["b:KeyValuePairOfintDataAcquisitionAreaXmlBpEWF4JT"]["b:value"][
                    "ImageAcquisitionSettingXml"]["Defocus"]["a:_items"]["a:double"]
                # Sometimes the values contain unicode en-dash and not ASCII hyphen
                # df.replace('\U00002013', '-')
            except:
                print('Warning, could not find defocus range in xml file')
                df = ['xml read error']

    getDefocusRange.shotType = shotType

    # Remember df in this case means defocus, not dataframe!!
    # Sometimes there is a single value in the defocus list and then this gets stored as a single string
    if isinstance(df, str):
        # Convert to list is str and thus single value
        df = df.split(sep=None, maxsplit=-1)

    # Check for error, which is stored as single item list
    read = df[0]
    if df[0] == "xml read error":
        return df
    # Otherwise convert metres into microns
    else:
        dfMicron = [float(item) * 1e6 for item in df]
        return dfMicron


def find_mics(path, search):
    # Need to have an independent function to find the mics, then move into search_mics to sort them out
    # So find mics can be used independently

    print('Looking for micrograph data in EPU directory using extension: ' + search)

    # Old method of finding xml files
    searchedFiles = glob.glob(path + "/**/GridSquare*/Data/*" + search + '*')
    # searchedFiles = glob.iglob(main.epu+"/Images-Disc1/GridSquare*/Data/*"+search)
    if searchedFiles:
        print('Found micrograph data: ' + str(len(searchedFiles)))
    else:
        print('No micrographs found with search term: ' + search)
        searchedFiles = 'exit'

    return searchedFiles


def deposition_file(xml):
    tile_data = searchSupervisorData(os.path.dirname(args.epu))
    # Get EPU session name from main EPU xml file, this is a function
    main_sessionName = xml_sessionName(xml)
    # This is the data xml metadata file already in a dictionary
    data = tile_data["xmlDataDict"]["MicroscopeImage"]
    # aqu_data = tile_data["xmlDataDict"]["MicroscopeImage"]
    software_version = df_lookup(main.masterdf, 'epuVersion')
    date = df_lookup(main.masterdf, 'sessionDate').strftime("%Y-%m-%d %H:%M:%S")
    nominal_defocus_min_microns = df_lookup(main.masterdf, 'defocusMin')
    nominal_defocus_max_microns = df_lookup(main.masterdf, 'defocusMax')
    collection = df_lookup(main.masterdf, 'afisMode')
    number_of_images = main.mic_count
    spot_size = xml_presets.spot
    C2_micron = xml_presets.C2
    Objective_micron = str(xml_presets_data.objective)
    Beam_diameter_micron = xml_presets.beamD

    # Get mag
    xmlMag = data["microscopeData"]["optics"]["TemMagnification"]["NominalMagnification"]
    xmlMetrePix = data["SpatialScale"]["pixelSize"]["x"]["numericValue"]
    xmlAPix = float(xmlMetrePix) * 1e10
    xmlAPix = roundup(xmlAPix, 1)

    # Get scope and kV
    model = data["microscopeData"]["instrument"]["InstrumentModel"]
    model_serial = data["microscopeData"]["instrument"]["InstrumentModel"]
    model_serial_split = re.split(r'(\d+)', model_serial, maxsplit=1)
    model = model_serial_split[0]
    if model == "TITAN":
        model = "TFS KRIOS"
    elif model == "ARCTICA":
        model = "TFS TALOS"
    microscope_serial_number = model_serial_split[1]
    eV = data["microscopeData"]["gun"]["AccelerationVoltage"]

    microscope_mode = data["microscopeData"]["optics"]["ColumnOperatingTemSubMode"]
    # illumination = data["microscopeData"]["optics"]["IlluminationMode"]

    grid_type = df_lookup(main.masterdf, 'gridType')
    grid_parts = re.findall(r'[A-Z][a-z]*', grid_type)

    # Now, parts will be ['Holey', 'Carbon']
    grid_topology = grid_parts[0]
    grid_material = grid_parts[1]

    EpuDataDict = dict(main_sessionName=main_sessionName, xmlMag=xmlMag, xmlMetrePix=xmlMetrePix, xmlAPix=xmlAPix,
                       model=model, microscope_serial_number=microscope_serial_number, eV=eV, microscope_mode=microscope_mode, grid_topology=grid_topology,
                       grid_material=grid_material,
                       software_name="EPU", software_version=software_version, date=date,
                       nominal_defocus_min_microns=nominal_defocus_min_microns,
                       nominal_defocus_max_microns=nominal_defocus_max_microns,
                       collection=collection, number_of_images=number_of_images, spot_size=spot_size,
                       C2_micron=C2_micron, Objective_micron=Objective_micron,
                       Beam_diameter_micron=Beam_diameter_micron, illumination="?",
                       PixelSpacing="?", SubFramePath="?")

    FoilHoleDataDict = FoilHoleData(tile_data["xmlData"])
    CompleteDataDict = {**EpuDataDict, **FoilHoleDataDict}
    save_deposition_file(CompleteDataDict)


def df_lookup(df, column):
    """
    Perform a lookup in a DataFrame based on a given column and value.

    Parameters:
        df (pd.DataFrame): The DataFrame to search.
        column (str): The name of the column to search.
        value: The value to look for in the specified column.

    Returns:
        pd.DataFrame: Subset of the original DataFrame containing rows where the specified column matches the given value.
    """
    return df[column][0]

def perform_minimal_harvest_epu(xml_path, output_dir):
    # Before running full eminsight analysis, look for all image files, via xml, mrc or jpg
    # This will declare global searchSupervisorData variables with the file lists, for xml, mrc and jpg
    # searchSupervisorAtlas(main.atlas_directory)
    # searchSupervisorData(main.epu_directory)
    # Get presets for EPU session xml
    print('')
    print('\033[1m' + 'Finding all presets from EPU session:' + '\033[0m')
    print('')
    atlas_folder = os.path.dirname(args.atlas)
    atlas_root = os.path.dirname(atlas_folder)
    atlas_data = searchSupervisorAtlas(atlas_folder)

    tile_folder = os.path.dirname(args.epu)
    tile_data = searchSupervisorData(tile_folder)

    xml_presets(xml_path, atlas_data, tile_data)

    # Get presets specific to acqusition magnifcation which are only contained in an acqusition image xml
    tile_file = os.path.join(tile_folder, tile_data["xmlData"])

    xml_presets_data(tile_data["xmlData"])

    # Get main set up parameters from EPU session xml
    print('')
    print('\033[1m' + 'Finding main EPU session parameters:' + '\033[0m')
    print('')

    main.masterdf = xml_session(xml_path)

    grid_folder = os.path.dirname(args.epu)
    searchedFiles = find_mics(grid_folder, 'xml')
    if searchedFiles == 'exit':
        print("exiting due to not finding any image xml data")
        exit()
    main.mic_count = len(searchedFiles)
    # Create a deposition file
    deposition_file(xml_path)


if __name__ == "__main__":
    main()
