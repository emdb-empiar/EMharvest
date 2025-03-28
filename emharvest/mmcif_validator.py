import os
import subprocess

def mmcif_validation(cif_file, dic_file, output_file):
    """
    Validates an mmCIF file using the Gemmi validate command and saves the output to a file.

    Parameters:
    cif_file (str): Path to the mmCIF file.
    dic_file (str): Path to the dictionary file for validation (default: mmcif_pdbx_v50.dic).
    output_file (str): Path to save the validation output (default: val_TOMO_data.txt).

    Returns:
    bool: True if the file is valid, False otherwise.
    str: Detailed output message from the validation command.
    """
    try:
        # Ensure input files exist
        if not os.path.isfile(cif_file):
            return False, f"Error: Input CIF file '{cif_file}' does not exist."
        if not os.path.isfile(dic_file):
            return False, f"Error: Dictionary file '{dic_file}' does not exist. Download it using the option -d yes"

        # Construct the Gemmi command
        command = [
            "gemmi", "validate", "-v", cif_file, "-d", dic_file
        ]

        # Execute the command and redirect output to a file
        with open(output_file, "w") as outfile:
            result = subprocess.run(command, stdout=outfile, stderr=subprocess.PIPE, text=True, env=os.environ.copy())

        # Check for errors in stderr or non-zero exit status
        if result.returncode != 0:
            print( f"Validation failed with error and output saved to {output_file}")
            return False
        if result.stderr.strip():
            print(f"Validation encountered issues: {result.stderr.strip()}")
            return False

        print(f"Validation succeeded. Results saved to {output_file}")
        return True

    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"
