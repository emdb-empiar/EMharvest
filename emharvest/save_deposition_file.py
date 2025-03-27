import pandas as pd
import numpy as np
import json
import urllib
import hashlib

from emharvest.mmcif_writer import translate_xml_to_cif
from emharvest.mmcif_validator import *

def SubFramePath(CompleteDataDict, n):
    """
       Extracts the information from SubFramPath value in mdoc file.

       Args:
           CompleteDataDict (dict): A dictionary containing the complete data.
           n (int): The index of the SubFramePath value to extract.

       Returns:
           str: The angle value extracted from the SubFramePath.
    """
    SubFramePath = CompleteDataDict['SubFramePath'][n]
    file_name = SubFramePath.split('\\')[-1]
    parts = file_name.split('.')[0]
    angle = parts.split('_')[-1]
    return angle

def checksum(path, out):
    """
        https://www.quickprogrammingtips.com/python/how-to-calculate-sha256-hash-of-a-file-in-python.html
       Calculates the SHA-256 checksum of a file and writes it to a output file.

       Args:
           path (str): The path to the file to calculate the checksum for.
           out (str): The path to the output file where the checksum will be written.

       Returns:
           None
    """
    filename = path
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()

    # Open file for writing
    checkfile = open(out, "w")
    # Write checksum string
    n = checkfile.write(checksum)
    # Close file
    checkfile.close()

    print('Created checksum')
    print()

def save_deposition_file(CompleteDataDict):
    """
        Saves the deposition file based on the provided complete data dictionary.

        Args:
            CompleteDataDict (dict): A dictionary containing the complete data.

        Returns:
            None
    """
    from emharvest.emharvest_main import parse_arguments

    args = parse_arguments()
    # Save doppio deposition csv file
    dictHorizontal1 = {
        'Microscope': CompleteDataDict['model'],
        'microscope_serial_number': CompleteDataDict['microscope_serial_number'],
        'software_version': CompleteDataDict['software_version'],
        'date': CompleteDataDict['date'],
        'eV': CompleteDataDict['eV'],
        'mag': CompleteDataDict['xmlMag'],
        'apix': CompleteDataDict['xmlAPix'],
        'nominal_defocus_min_microns': CompleteDataDict['nominal_defocus_min_microns'],
        'grid_topology': CompleteDataDict['grid_topology'],
        'grid_material': CompleteDataDict['grid_material'],
        'nominal_defocus_max_microns': CompleteDataDict['nominal_defocus_max_microns'],
        'spot_size': CompleteDataDict['spot_size'],
        'C2_micron': CompleteDataDict['C2_micron'],
        'Objective_micron': CompleteDataDict['Objective_micron'],
        'Beam_diameter_micron': CompleteDataDict['Beam_diameter_micron'],
        'collection': CompleteDataDict['collection'],
        'number_of_images': CompleteDataDict['number_of_images'],
        'software_name': CompleteDataDict["software_name"],
        'software_category': "IMAGE ACQUISITION",
        'microscope_mode': CompleteDataDict['microscope_mode'],
        'detector_name': CompleteDataDict['detectorName'],
        'dose_rate': CompleteDataDict['xmlDoseRate'],
        'avg_exposure_time': CompleteDataDict['avgExposureTime'],
        'detector_mode': CompleteDataDict['detectorMode'],
        'illumination_mode': CompleteDataDict['illumination'].upper(),
        'slit_width': CompleteDataDict['slitWidth'],
        'electron_source': CompleteDataDict['electronSource'],
        'tilt_angle_min': CompleteDataDict['tiltAngleMin'],
        'tilt_angle_max': CompleteDataDict['tiltAngleMax'],
        'objectiveAperture': CompleteDataDict['objectiveAperture']
    }
    if args.mode == "TOMO" and args.category != "serialEM":
        dictHorizontal1.update({'pixel_spacing_x': CompleteDataDict['PixelSpacing'],
                                'pixel_spacing_y': CompleteDataDict['PixelSpacing'],
                                'pixel_spacing_z': CompleteDataDict['PixelSpacing'],
                                'angle_increment': float(SubFramePath(CompleteDataDict, 2)) - float(
                                    SubFramePath(CompleteDataDict, 1)),
                                'rotation_axis': CompleteDataDict['RotationAngle'],
                                'max_angle': SubFramePath(CompleteDataDict, -1),
                                'min_angle': SubFramePath(CompleteDataDict, -2),
                                'angle2_increment': '?',
                                'max_angle2': '?',
                                'min_angle2': '?'
                                })

    df1 = pd.DataFrame([dictHorizontal1])

    # Sample data for the second row
    dictHorizontal2 = {
        'Microscope': 'em_imaging.microscope_model',
        'microscope_serial_number': 'em_imaging.microscope_serial_number',
        'software_name': 'em_software.name',
        'software_version': 'em_software.version',
        'software_category': 'em_software.category',
        'date': 'em_imaging.date',
        'eV': 'em_imaging.accelerating_voltage',
        'mag': 'em_imaging.nominal_magnification',
        'apix': '?',
        'nominal_defocus_min_microns': 'em_imaging.nominal_defocus_min',
        'nominal_defocus_max_microns': 'em_imaging.nominal_defocus_max',
        'spot_size': '?',
        'C2_micron': 'em_imaging.c2_aperture_diameter',
        'Objective_micron': '?',
        'Beam_diameter_micron': '?',
        'collection': '?',
        'number_of_images': '?',
        "microscope_mode": 'em_imaging.mode',
        "grid_material": 'em_support_film.material',
        "grid_topology": 'em_support_film.topology',
        "detector_name": "em_image_recording.film_or_detector_model",
        "dose_rate": "em_image_recording.avg_electron_dose_per_image",
        "avg_exposure_time": "em_image_recording.average_exposure_time",
        "detector_mode": "em_image_recording.detector_mode",
        "illumination_mode": "em_imaging.illumination_mode",
        "slit_width": "em_imaging_optics.energyfilter_slit_width",
        "electron_source": "em_imaging.electron_source",
        "tilt_angle_min": "em_imaging.tilt_angle_min",
        "tilt_angle_max": "em_imaging.tilt_angle_max",
        "objectiveAperture": "em_imaging.objective_aperture"
    }
    if args.mode == "TOMO" and args.category != "serialEM":
        dictHorizontal2.update({"pixel_spacing_x": "em_map.pixel_spacing_x",
                                "pixel_spacing_y": "em_map.pixel_spacing_y",
                                "pixel_spacing_z": "em_map.pixel_spacing_z",
                                "angle_increment": "em_tomography.axis1_angle_increment",
                                "rotation_axis": "em_tomography.dual_tilt_axis_rotation",
                                "max_angle": "em_tomography.axis1_max_angle",
                                "min_angle": "em_tomography.axis1_min_angle",
                                "angle2_increment": "em_tomography.axis2_angle_increment",
                                "max_angle2": "em_tomography.axis2_max_angle",
                                "min_angle2": "em_tomography.axis2_min_angle"})

    df2 = pd.DataFrame([dictHorizontal2])

    # Append the second row to the DataFrame
    df = pd.concat([df1, df2], ignore_index=True, sort=False)
    # df = df1.merge(df2, left_index=0, right_index=0)

    ## Deposition file
    depfilepath = args.output_dir + '/' + CompleteDataDict['main_sessionName'] + '_dep.json'
    checksumpath = args.output_dir + '/' + CompleteDataDict['main_sessionName'] + '_dep.checksum'

    # Human readable deposition file
    # df.to_csv (args.output_dir+'/'+sessionName+'.dep', index = False, header=True)
    # Manual headings
    headings = ['Value', 'JSON', 'mmCIF']
    # Duplicate the last row
    mmcif_name = df.iloc[-1]
    # Append to DF
    df = pd.concat([df, pd.DataFrame([mmcif_name])], ignore_index=True)

    # df = df.append(mmcif_name, ignore_index=True)

    tfs_xml_path_list = [
        '[MicroscopeImage][microscopeData][instruments][InstrumentModel]',
        '?',
        '[MicroscopeImage][microscopeData][emharvest][ApplicationSoftware]',
        '[MicroscopeImage][microscopeData][acquisitionDateTime]',
        '[MicroscopeImage][microscopeData][gun][AccelerationVoltage]',
        '[MicroscopeImage][microscopeData][optics][TemMagnification][NominalMagnification]',
        '[MicroscopeImage][SpatialScale][pixelSize][x][numericValue]',
        '[MicroscopeImage][microscopeData][optics][TemMagnification][NominalMagnification]',
        '[Samples][_items][SampleXml][0][GridType]',
        '[Samples][_items][SampleXml][0][GridType]',
        '[MicroscopeImage][microscopeData][optics][Defocus]',
        '[MicroscopeImage][microscopeData][optics][SpotIndex]',
        '[MicroscopyImage][CustomData][a:KeyValueOfstringanyType][a:Key] is Aperture[C2].Name then extract [<a:Value>]',
        '[MicroscopyImage][CustomData][a:KeyValueOfstringanyType][a:Key] is Aperture[OBJ].Name then extract [<a:Value>]',
        '[MicroscopeImage][microscopeData][optics][BeamDiameter]',
        '?',
        '?',
        '[MicroscopeImage][microscopeData][emharvest][ApplicationSoftwareVersion]',
        'PREDEFINED VALUE',
        '[MicroscopeImage][microscopeData][optics][ColumnOperatingTemSubMode]',
        '[MicroscopyImage][CustomData][a:KeyValueOfstringanyType][a:Key] isDetectorCommercialName then extract [<a:Value>]',
        '?',
        '[MicroscopeImage][microscopeData][acquisition][camera][ExposureTime]',
        '[MicroscopeImage][microscopeData][acquisition][camera][CameraSpecificInput][a:KeyValueOfstringanyType][a:Key] is ElectronCountingEnabled and [<a:Vallue>] is true then COUNTING',
        '[MicroscopeImage][microscopeData][optics][IlluminationMode]',
        '[MicroscopeImage][microscopeData][optics][EnergyFilter][EnergySelectionSlitWidth]',
        '[MicroscopeImage][microscopeData][gun][Sourcetype]',
        '[MicroscopeImage][microscopeData][stage][Position][A]',
        '[MicroscopeImage][microscopeData][stage][Position][B]',
        '?'
    ]
    if args.mode == "TOMO" and args.category != "serialEM":
        tfs_xml_path_list.extend(['[PixelSpacing]',
                                  '[PixelSpacing]',
                                  '[PixelSpacing]',
                                  '[SubFramPath]',
                                  '[RotationAngle]',
                                  '[SubFramePath]',
                                  '[SubFramePath]',
                                  '[CryoTomo is usually single axis tilt]',
                                  '[CryoTomo is usually single axis tilt]',
                                  '[CryoTomo is usually single axis tilt]'])

    emdb_xml_path_list = [
        '[emd][structure_determination_list][structure_determination][microscopy_list]',
        '?',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][software_list][software][version]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][date]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][acceleration_voltage]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][nominal_magnification]',
        '?',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][nominal_defocus_min]',
        '[emd][structure_determination_list][structure_determination][specimen_preparation_list][single_particle_preparation][grid][support_film][film_topolgy]',
        '[emd][structure_determination_list][structure_determination][specimen_preparation_list][single_particle_preparation][grid][support_film][film_material]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][nominal_defocus_max]',
        '?',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][c2_aperture_diameter]',
        '?',
        '?',
        '?',
        '?',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][software_list][software][name]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][imaging_mode]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][image_recording_list][image_recording][film_or_detector_model]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][image_recording_list][image_recording][average_electron_dose_per_image]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][image_recording_list][image_recording][average_exposure_time]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][image_recording_list][image_recording][detector_mode]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][microscopy][illumination_mode]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][specialist_optics][energyfilter][slith_width]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][electron_source]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][tilt_angle_min]',
        '[emd][structure_determination_list][structure_determination][microscopy_list][single_particle_microscopy][tilt_angle_max]',
        '?'
    ]
    if args.mode == "TOMO" and args.category != "serialEM":
        emdb_xml_path_list.extend(['[emd][map][pixel_spacing][x]',
                                   '[emd][map][pixel_spacing][y]',
                                   '[emd][map][pixel_spacing][z]',
                                   '[emd][structure_determination_list][structure_determination][microscopy_list][tomgraphy_microscopy][tilt_series][axis1][angle_increment]',
                                   '[emd][structure_determination_list][structure_determination][microscopy_list][tomgraphy_microscopy][tilt_series][axis_rotation]',
                                   '[emd][structure_determination_list][structure_determination][microscopy_list][tomgraphy_microscopy][tilt_series][axis1][max_angle]',
                                   '[emd][structure_determination_list][structure_determination][microscopy_list][tomgraphy_microscopy][tilt_series][axis1][min_angle]',
                                   '[emd][structure_determination_list][structure_determination][microscopy_list][tomgraphy_microscopy][tilt_series][axis2][angle_increment]',
                                   '[emd][structure_determination_list][structure_determination][microscopy_list][tomgraphy_microscopy][tilt_series][axis2][max_angle]',
                                   '[emd][structure_determination_list][structure_determination][microscopy_list][tomgraphy_microscopy][tilt_series][axis2][min_angle]'
                                   ])

    # Transpose
    df_transpose = df.T
    # Set headings
    df_transpose.columns = headings
    # Add XML paths
    if len(tfs_xml_path_list) != len(df_transpose):
        raise ValueError("Length of tfs_xml_path_list must match the number of rows in the DataFrame")
    df_transpose['TFS XML Path'] = tfs_xml_path_list
    if len(emdb_xml_path_list) != len(df_transpose):
        raise ValueError("Length of emdb_xml_path_list must match the number of rows in the DataFrame")
    df_transpose['EMDB XML Path'] = emdb_xml_path_list
    # Set the name of the index
    df_transpose.index.name = 'Items'
    # add square brackets around keys
    df_transpose['JSON'] = df_transpose['JSON'].apply(lambda x: '[' + x.replace('.', '][') + ']')
    # Save to CSV
    df_transpose.to_csv(args.output_dir + '/' + CompleteDataDict['main_sessionName'] + '_dep.csv', index=True, header=True)
    df1_selected = df1.apply(lambda x: x.map(lambda item: item.item() if isinstance(item, (np.generic, np.ndarray)) else item) if x.name in df1.columns else x, axis=0)

    # df1_selected = df1.applymap(lambda x: x.item() if isinstance(x, (np.generic, np.ndarray)) else x)

    # Create nested dictionary from the DataFrame
    nested_dict = {}
    for col, new_col in dictHorizontal2.items():
        if '?' not in new_col and col in df1_selected.columns:
            top_key, sub_key = new_col.split('.')
            if top_key not in nested_dict:
                nested_dict[top_key] = {}
            nested_dict[top_key][sub_key] = df1.at[0, col]

    # Convert nested dictionary to JSON
    json_output = json.dumps(nested_dict, indent=4, default=str)

    # write to json file
    with open(depfilepath, 'w') as f:
        f.write(json_output)

    # This can be run before doing full analysis of the session directories
    print("Created deposition file")

    # Deposition Checksum
    checksum(depfilepath, checksumpath)

    # Input data as cif dictionary
    cif_dict = {}

    for key in dictHorizontal2:
        cif_dict[dictHorizontal2[key]] = dictHorizontal1[key]

    # transalating and writting to cif file
    print("CIF_DICTIONARY", cif_dict, "\n")
    translate_xml_to_cif(cif_dict, CompleteDataDict['main_sessionName'])

    cif_filepath = args.output_dir + '/' + CompleteDataDict['main_sessionName'] + '_dep.cif'
    dic_path = os.path.join(os.getcwd(), "mmcif_dictionary/mmcif_pdbx_v50.dic")

    if args.download_dict == "yes":
        urllib.request.urlretrieve("https://mmcif.wwpdb.org/dictionaries/ascii/mmcif_pdbx_v50.dic", dic_path)
    validation_output = args.output_dir + '/' + 'val_' + CompleteDataDict['main_sessionName'] + '.txt'
    mmcif_validation(cif_filepath, dic_path, validation_output)

