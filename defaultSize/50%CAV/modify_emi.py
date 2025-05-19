import xml.etree.ElementTree as ET
import argparse

def add_lane_change_mode(input_file: str, output_file: str):
    """
    Reads a SUMO .emi.xml file, adds laneChangeMode="0" to every <vehicle> element,
    and writes the modified XML to a new file.
    """
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Iterate over all <vehicle> elements and set the laneChangeMode attribute
    for vehicle in root.findall('vehicle'):
        vehicle.set('laneChangeMode', '0')

    # Write back to file with XML declaration
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add laneChangeMode=\"0\" to every <vehicle> in a SUMO .emi.xml file."
    )
    parser.add_argument("input", help="Path to the input .emi.xml file")
    parser.add_argument("output", help="Path for the modified output .emi.xml file")
    args = parser.parse_args()

    add_lane_change_mode(args.input, args.output)
    print(f"Processed '{args.input}' → '{args.output}'. All <vehicle> tags now include laneChangeMode=\"0\".")
