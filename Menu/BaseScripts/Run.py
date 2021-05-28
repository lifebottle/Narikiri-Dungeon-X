import sys
from HelperFunctions import *



if __name__ == "__main__":
    
    
    fileName = sys.argv[1]
    #Run the script
    runscript(fileName)
    
    #Clean the dump file
    clean(fileName+"_dump.txt")
