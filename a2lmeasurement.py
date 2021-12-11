import csv
import re
import uuid
import pprint

from os import path
from pya2l import DB, model
from pya2l.api import inspect
from sys import argv

db = DB()
print("Opening A2l as database")

session = (
    db.open_existing(argv[1]) if path.exists(f"{argv[1]}db") else db.import_a2l(argv[1])
)

print("A2l Opened as database")

header = (
    "Name",
    "Unit",
    "Equation",
    "Format",
    "Address",
    "Length",
    "Signed",
    "ProgMin",
    "ProgMax",
    "WarnMin",
    "WarnMax",
    "Smoothing",
    "Enabled",
    "Tabs",
    "Assign To",
)


data_sizes = {
    "UWORD": 2,
    "UBYTE": 1,
    "SBYTE": 1,
    "SWORD": 2,
    "ULONG": 4,
    "SLONG": 4,
    "FLOAT32_IEEE": 4,
}


categories = []



# Helpers



# A2L to "normal" conversion methods


def fix_degree(bad_string):
    return re.sub(
        "\uFFFD", "\u00B0", bad_string
    )  # Replace Unicode "unknown" with degree sign


def coefficients_to_equation(coefficients):
    a, b, c, d, e, f = (
        str(coefficients["a"]),
        str(coefficients["b"]),
        str(coefficients["c"]),
        str(coefficients["d"]),
        str(coefficients["e"]),
        str(coefficients["f"]),
    )
    if a == "0.0" and d == "0.0":  # Polynomial is of order 1, ie linear
        return f"(({f} * x) - {c} ) / ({b} - ({e} * x))"
    else:
        return "Cannot handle polynomial ratfunc because we do not know how to invert!"


# Begin


output_csv = []

output_csv.append(",".join(header))

with open(argv[2], encoding="utf-8-sig") as csvfile:
    csvreader = csv.DictReader(csvfile)
    for row in csvreader:
        output_row = []

        paramname = row["Param Name"]
        custom_name = row["Custom Name"]

        measurement = (
            session.query(model.Measurement)
            .order_by(model.Measurement.name)
            .filter(model.Measurement.name == paramname)
            .first()
        )
        if measurement is None:
            print("******** Could not find ! ", paramname)
            continue

        m_data = inspect.Measurement(session, paramname)
        math = coefficients_to_equation(m_data.compuMethod.coeffs)


        if len(custom_name) > 0:
            output_row.append(custom_name)
        else: 
            output_row.append(m_data.name)
        output_row.append(m_data.compuMethod.unit)
        output_row.append(math)
        output_row.append(str(m_data.format) + "f")
        output_row.append(str(hex(m_data.ecuAddress)))
        output_row.append(str(data_sizes[m_data.datatype]))
        if m_data.datatype[0] == 'S':
            output_row.append("TRUE")
        else:
            output_row.append("FALSE")
        output_row.append(str(m_data.lowerLimit))
        output_row.append(str(m_data.upperLimit))
        output_row.append(str(m_data.lowerLimit))
        output_row.append(str(m_data.upperLimit))
        output_row.append("0")
        output_row.append("TRUE")
        output_row.append("")
        output_row.append("")

        output_csv.append(",".join(output_row))

with open(argv[1] + "_params.csv", 'w') as output_file:
    for row in output_csv:
        output_file.write(row + "\n")
