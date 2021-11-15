from devtools import debug
import csv 
from modelConstructor import *
import argparse
'''
toDo: 
add list/dist check in api
add arg folder
add regex as argument
add BGP-EVPN as conditional
'''
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('path', type=str, help='A required folder with raw inventory export from np')
    args = parser.parse_args()
    
    commandsDefinition = commandsDefinitionConstructor("CommandsDefinition.json")    
    model, deviceList = parseRawCollection(f"{args.path}/CLI")
    referenceDefinitions = ReferenceDefinitions.initialize()

    model.constructHostOperDB(f"{args.path}/CLI")
    
    model.prepareHardwareCapacityInfoForAll(f"{args.path}/CLI", ["9.3(4)", "9.3(7)", "9.3(7a)"], ['Cloudscale'])
    model.populate(f"{args.path}/CLI", commandsDefinition, referenceDefinitions)
    model.writeRawResult()
    cSVHeaders = CSVHeaders().generateCSVHeaders(commandsDefinition, model, referenceDefinitions, ['Cloudscale', 'Jerico'])
    cSVHeaders.generateCSVs(model)
    
    model.writeRawResult() 
