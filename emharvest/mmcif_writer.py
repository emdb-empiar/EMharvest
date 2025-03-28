from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.PdbxWriter import PdbxWriter


def write_mmcif_file(data_list, sessionName):
    """
    pdbx writer is used to write data stored in self.__dataList
    :return written: a boolean; True when pdf writer is finished
    """
    from emharvest.emharvest_main import parse_arguments
    args = parse_arguments()
    written = False
    depfilepath = args.output_dir + '/' + sessionName
    if depfilepath:
        mmcif_filename = depfilepath + '_dep.cif'
        with open(mmcif_filename, "w") as cfile:
            pdbx_writer = PdbxWriter(cfile)
            pdbx_writer.write(data_list)
        written = True
    return written


def add_container(data_list, container_id):
    """
    Adds a container with the specified container_id to the data_list.
    """
    container = DataContainer(container_id)
    data_list.append(container)
    return container


def add_category(container, category_id, items):
    """
    Adds a category with the specified category_id and items to the container.
    """
    category = DataCategory(category_id)
    for item in items:
        category.appendAttribute(item)
    container.append(category)


def insert_data(container, category_id, data_list):
    """
    Inserts data_list into the specified category_id within the container.
    """
    cat_obj = container.getObj(category_id)
    if cat_obj is None:
        return

    if all(isinstance(i, list) for i in data_list):
        list_values = [list(t) for t in zip(*data_list)]
        cat_obj.extend(list_values)
    else:
        cat_obj.append(data_list)


def translate_xml_to_cif(input_data, sessionName):
    """
    Translates input XML data into a CIF file.
    """
    from emharvest.emharvest_main import parse_arguments
    args = parse_arguments()

    if not input_data:
        return False

    input_data_filtered = {key: value for key, value in input_data.items() if key != "?"}
    cif_data_list = []

    # Create a dictionary to store container_id with corresponding categories and values
    container_dict = {}

    # Iterate over the input data and accumulate category names and values
    for key, value in input_data_filtered.items():
        if isinstance(key, str) and key != "?":
            container_id, category = key.split(".")
            if container_id not in container_dict:
                container_dict[container_id] = {}
            if category not in container_dict[container_id]:
                container_dict[container_id][category] = [value]
            else:
                # Handle duplicate categories if needed
                pass

    # Add all accumulated categories and values to the CIF container
    container = add_container(cif_data_list, sessionName)

    for category_name, categories_values in container_dict.items():
        category_list = []
        cif_values_list = []
        for category, cif_values in categories_values.items():
            if category == "date":
                cif_values = [cif_values[0].split(" ")[0]]
            elif category == "accelerating_voltage":
                if not args.category == "serialEM":
                    if cif_values[0] != "?":
                        cif_values = [int(float(cif_values[0]) / 1000)]
            elif category == "nominal_defocus_min":
                if cif_values[0] != "?":
                    cif_values = [int((cif_values[0]) * -1000)]
            elif category == "nominal_defocus_max":
                if cif_values[0] != "?":
                    cif_values = [int((cif_values[0]) * -1000)]
            elif category == "mode":
                if cif_values[0] == "BrightField":
                    cif_values = ["BRIGHT FIELD"]
            elif category == "topology" or category == "material":
                cif_values = [cif_values[0].upper()]
            elif category == "electron_source":
                if cif_values[0] == "FieldEmission":
                    cif_values = ["FIELD EMISSION GUN"]
            # elif category == "illumination_mode":
            #     if cif_values[0] == "PARALLEL":
            #         cif_values = ["FLOOD BEAM"]
            elif category == "microscope_model":
                if cif_values[0] == "EMBL Krios 3":
                    cif_values = ["TFS KRIOS"]

            category_list.append(category)
            cif_values_list.append(cif_values)
        add_category(container, category_name, category_list)
        insert_data(container, category_name, cif_values_list)

    # Write the modified CIF data to a file
    return write_mmcif_file(cif_data_list, sessionName)