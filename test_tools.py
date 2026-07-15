from tools import calculator
from console_output import print_json

print_json("CALCULATOR TEST", {"result": calculator.invoke({"expression": "25 * 12"})})
