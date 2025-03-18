from core.foilHole_data import FoilHoleData
from core.xml_data_harvest import AnyXMLDataFile
from core.save_deposition_file import save_deposition_file
from core.tomo_mdoc_data import TomoMdocData

def perform_serialEM_harvest(mdoc_file, output_dir):
    """
        Performs a serialEM harvest, extracting relevant data from the mdoc file.

        Args:
            mdoc_file (str): The path to the mdoc file to harvest data from.
            output_dir (str): The directory where the harvested data will be saved.

        Returns:
            None
    """
    print(f"Processing serialEM data from file: {mdoc_file}")
    print(f"Output will be saved to: {output_dir}")

    serialEMDataDict = TomoMdocData(mdoc_file)

    main_sessionName = "SerialEM_microscopy_data"

    EpuDataDict = dict(main_sessionName=main_sessionName, grid_topology="?", grid_material="?",
                       nominal_defocus_min_microns="?", nominal_defocus_max_microns="?",
                       collection="?", number_of_images="?", spot_size="?", C2_micron="?", Objective_micron="?",
                       Beam_diameter_micron="?", software_version="?", xmlAPix="?", microscope_mode="?", detectorName="?",
                       xmlDoseRate="?", detectorMode="?", illumination="?", electronSource="?",
                       objectiveAperture="?")

    serialEMDataDict['tiltAngleMax'] = "?"
    serialEMDataDict['tiltAngleMin'] = "?"
    serialEMDataDict["eV"] = serialEMDataDict.pop("Voltage")
    serialEMDataDict['xmlMag'] = serialEMDataDict['Magnification']
    serialEMDataDict['avgExposureTime'] = serialEMDataDict.pop('ExposureTime')
    serialEMDataDict["slitWidth"] = serialEMDataDict["FilterSlitAndLoss"][0]
    serialEMDataDict["Loss"] = serialEMDataDict["FilterSlitAndLoss"][1]

    SerialEMSPATOMODataDict = {**EpuDataDict, **serialEMDataDict}

    save_deposition_file(SerialEMSPATOMODataDict)

def perform_tomogram_harvest(tomogram_file, mdoc_file, output_dir):
    """
        Performs an EBIC tomogram data harvest, extracting relevant data from the tomogram file and mdoc file.

        Args:
            tomogram_file (str): The path to the tomogram file to harvest data from.
            mdoc_file (str): The path to the mdoc file to harvest data from.
            output_dir (str): The directory where the harvested data will be saved.

        Returns:
            None
    """
    print(f"Processing tomogram data from file: {tomogram_file} and {mdoc_file}")
    print(f"Output will be saved to: {output_dir}")

    FoilDataDict = FoilHoleData(tomogram_file)
    FoilDataDict['tiltAngleMax'] = "?"
    FoilDataDict['tiltAngleMin'] = "?"
    main_sessionName = FoilDataDict["sessionName"]

    EpuDataDict = dict(main_sessionName=main_sessionName, grid_topology="?", grid_material="?",
                       nominal_defocus_min_microns="?", nominal_defocus_max_microns="?",
                       collection="?", number_of_images="?", spot_size="?", C2_micron="?", Objective_micron="?",
                       Beam_diameter_micron="?")

    TomoOverViewDataDict = {**FoilDataDict, **EpuDataDict}

    OverViewDataDict = AnyXMLDataFile(tomogram_file)
    TomoDataDict = {**TomoOverViewDataDict, **OverViewDataDict}

    TomoMdocDataDict = TomoMdocData(mdoc_file)

    TomoDataDict['xmlMag'] = int(TomoMdocDataDict['Magnification'])
    CompleteTomoDataDict = {**TomoDataDict, **TomoMdocDataDict}

    save_deposition_file(CompleteTomoDataDict)

def perform_spa_harvest_nonepu(input_spa_file, output_dir):
    """
        Performs a EBIC SPA harvest without dm files, extracting relevant data from the input SPA file.

        Args:
            input_spa_file (str): The path to the SPA file to harvest data from.
            output_dir (str): The directory where the harvested data will be saved.

        Returns:
            None
    """
    print(f"Processing tomogram data from file: {input_spa_file}")
    print(f"Output will be saved to: {output_dir}")

    SPADataDict = FoilHoleData(input_spa_file)
    main_sessionName = SPADataDict["sessionName"]

    EpuDataDict = dict(main_sessionName=main_sessionName, grid_topology="?", grid_material="?",
                       nominal_defocus_min_microns="?", nominal_defocus_max_microns="?",
                       collection="?", number_of_images="?", spot_size="?", C2_micron="?", Objective_micron="?",
                       Beam_diameter_micron="?")

    NonEpuDataDict = AnyXMLDataFile(input_spa_file)

    SPATotalDataDict = {**SPADataDict, **EpuDataDict}

    CompleteSPADataDict = {**SPATotalDataDict, **NonEpuDataDict}

    save_deposition_file(CompleteSPADataDict)
