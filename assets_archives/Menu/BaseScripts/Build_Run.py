# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 21:14:08 2021

@author: Steven
"""
import sys
from Helperfunctions import *



    
if __name__ == "__main__":
    
    #Parameters
    sourceFile = sys.argv[1]
    newFileName = sys.argv[2]
    n = int(sys.argv[3])
    startPoint = sys.argv[4]
    step= int(sys.argv[5])
    nbObject = int(sys.argv[6])
    
    helper = Helper()
    helper.PointerHeader = sys.argv[7]
    

    #Create the script
    helper.createScript(newFileName+"_script.txt", n, startPoint, step, nbObject)
    
    #Run the script
    helper.runscript(sourceFile, newFileName)
    
    #Clean the dump file
    helper.cleanDump(newFileName+"_dump.txt")
