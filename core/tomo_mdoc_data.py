import re
import math
import datetime

def unique_values(existing_list, new_values):
    """Add unique values to the list, handling NaN separately."""
    for value in new_values:
        if isinstance(value, float) and math.isnan(value):
            if not any(isinstance(v, float) and math.isnan(v) for v in existing_list):
                existing_list.append(value)
        elif value not in existing_list:
            existing_list.append(value)
    return existing_list

def TomoMdocData(mdocpath):
    """Reading the mdoc file information and storing in a dictionary."""
    from core.emharvest_main import parse_arguments
    args = parse_arguments()

    mdoc_data = {}
    data_dict = {}

    with open(mdocpath, "r") as file:
        first_line = file.readline().strip()

        if args.mode == "SPA" or args.mode == "TOMO":
            if args.category == "serialEM":
                match = re.match(
                    r"T\s*=\s*(\w+):\s*(.+?)\s+(\d+)\s+(\d{2}-[A-Za-z]{3}-\d{2})\s+([\d:]+)",
                    first_line.strip()
                )
                if match:
                    date_str = match.group(4).strip()
                    if date_str:
                        try:
                            datetime.datetime.strptime(date_str, "%Y-%m-%d")
                            formatted_date = date_str
                        except ValueError:
                            try:
                                formatted_date = datetime.datetime.strptime(date_str, "%d-%b-%y").strftime("%Y-%m-%d")
                            except ValueError:
                                formatted_date = None
                                print(f"Invalid date format: {date_str}")
                    else:
                        formatted_date = None
                    data_dict = {
                        "software_name": match.group(1),
                        "model": match.group(2).strip(),
                        "microscope_serial_number": match.group(3).strip(),
                        "date": formatted_date,
                        "time": match.group(5).strip(),
                    }
                else:
                    print("Line format does not match the expected pattern.")


        for line in file:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                line = line[1:-1].strip()
            if not line:
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Handle multiple values in one line
                if " " in value:
                    values = value.split()
                    try:
                        values = [float(v) for v in values]
                    except ValueError:
                        pass
                else:
                    try:
                        values = [float(value)]
                    except ValueError:
                        values = [value]

                # Update the mdoc_data dictionary
                if key in mdoc_data:
                    mdoc_data[key] = unique_values(mdoc_data[key], values)
                else:
                    mdoc_data[key] = values

    for key, value in mdoc_data.items():
        if isinstance(value, list):
            if len(value) == 1:
                mdoc_data[key] = value[0]
            else:
                unique_val = list(set(value))
                if len(unique_val) == 1:
                    mdoc_data[key] = unique_val[0]

    if args.mode == "SPA" or args.mode == "TOMO" and args.category == "serialEM":
        mdoc_data_dict = {**data_dict, **mdoc_data}
    else:
        mdoc_data_dict = mdoc_data

    return mdoc_data_dict

