import os
import xmltodict
import fnmatch

def findpattern(pattern, path):
    """
         Searches for files matching a given pattern in a specified directory.

         Args:
             pattern (str): The file pattern to search for (e.g., "*.xml").
             path (str): The directory path to search in.

         Returns:
             list: A list of file paths that match the specified pattern.
    """
    print("Searching for pattern:", pattern, "in", path)
    result = []
    path = os.path.abspath(path)
    for root, _, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.relpath(os.path.join(root, name), start=path))
    return result

def searchSupervisorAtlas(path):
    """
        Searches for Supervisor Atlas XML files and returns metadata.

        Args:
            path (str): The directory path to search for Supervisor Atlas XML files.

        Returns:
            dict: A dictionary containing metadata about the found Atlas XML files.
    """
    print("Searching Supervisor Atlas directory for XMLs, MRC, and JPG")

    xmlAtlasList = findpattern("Atlas*.xml", path)
    xmlAtlas = xmlAtlasList[0] if xmlAtlasList else None

    xmlAtlasTileList = findpattern("Tile*.xml", path)
    xmlAtlasTile = xmlAtlasTileList[0] if xmlAtlasTileList else None

    if xmlAtlas:
        with open(os.path.join(path, xmlAtlas), "r") as xml:
            xmlAtlasDict = xmltodict.parse(xml.read())
    else:
        xmlAtlasDict = None

    if xmlAtlasTile:
        with open(os.path.join(path, xmlAtlasTile), "r") as xml:
            xmlAtlasTileDict = xmltodict.parse(xml.read())
    else:
        xmlAtlasTileDict = None

    print(f"Found Atlas: {xmlAtlas}")
    print(f"Found Atlas tile: {xmlAtlasTile}\n")

    return {
        "xmlAtlasList": xmlAtlasList,
        "xmlAtlas": xmlAtlas,
        "xmlAtlasTileList": xmlAtlasTileList,
        "xmlAtlasTile": xmlAtlasTile,
        "xmlAtlasDict": xmlAtlasDict,
        "xmlAtlasTileDict": xmlAtlasTileDict,
    }

def searchSupervisorData(path):
    """
        Searches for Supervisor Data files and extracts relevant information.

        Args:
            path (str): The directory path to search for Supervisor Data files.

        Returns:
            dict: A dictionary containing extracted data from the found Supervisor Data files.
    """
    print('Searching Supervisor Data directory for xmls, mrc, and jpg')
    print()

    def find_and_get_first(pattern, path, exclude=None):
        file_list = findpattern(pattern, path)
        if exclude:
            file_list = [x for x in file_list if exclude not in x]
        # Avoid duplicating 'path'
        file_list = [x if x.startswith(path) else os.path.join(path, x) for x in file_list]
        return file_list[0] if file_list else 'None'

    print('Finding GridSquare xml')
    xmlSquare = find_and_get_first('GridSquare*.xml', path)
    print('Done' if xmlSquare != 'None' else 'None found')

    print('Finding FoilHole xml')
    xmlHole = find_and_get_first('FoilHole*.xml', path, exclude="Data")
    print('Done' if xmlHole != 'None' else 'None found')

    print('Finding AcquisitionData xml')
    xmlData = find_and_get_first('FoilHole*Data*.xml', path)
    print('Done' if xmlData != 'None' else 'None found')

    print('Finding AcquisitionData mrc')
    mrc = find_and_get_first('FoilHole*Data*.mrc', path)
    print('Done' if mrc != 'None' else 'None found')

    print('Finding AcquisitionData jpg')
    jpg = find_and_get_first('FoilHole*Data*.jp*g', path)
    print('Done' if jpg != 'None' else 'None found')

    print('Found representative xml file for pulling metadata about EPU session')
    print(f'Square: {xmlSquare}')
    print(f'Hole: {xmlHole}')
    print(f'Acquisition: {xmlData}')
    print()

    def parse_xml_to_dict(file_path):
        try:
            with open(file_path, "r") as xml:
                return xmltodict.parse(xml.read())
        except:
            print(f'Error parsing {file_path}')
            return {}

    result = {
        "xmlSquare": xmlSquare,
        "xmlHole": xmlHole,
        "xmlData": xmlData,
        "mrc": mrc,
        "jpg": jpg,
        "xmlSquareDict": parse_xml_to_dict(xmlSquare) if xmlSquare != 'None' else {},
        "xmlHoleDict": parse_xml_to_dict(xmlHole) if xmlHole != 'None' else {},
        "xmlDataDict": parse_xml_to_dict(xmlData) if xmlData != 'None' else {}
    }

    return result