import os
import sys

# Add the parent directory of 'lib' to sys.path
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(lib_path)

# Set the current working directory to the directory of the script
os.chdir(os.path.dirname(os.path.abspath(__file__)))
