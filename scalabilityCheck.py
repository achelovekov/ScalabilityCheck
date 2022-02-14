from devtools import debug
import csv 
from modelConstructor import *
import argparse
from tqdm import tqdm
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
    
    print(f"commandsDefinitionConstructor:")
    for i in tqdm(range(1)): commandsDefinition = commandsDefinitionConstructor("CommandsDefinition.json")  
    print(f"parseRawCollection:")  
    for i in tqdm(range(1)): model, deviceList = parseRawCollection(f"{args.path}/CLI")
    print(f"ReferenceDefinitions initialization:")  
    for i in tqdm(range(1)): referenceDefinitions = ReferenceDefinitions.initialize()

    print(f"constructHostOperDB:")
    for i in tqdm(range(1)): model.constructHostOperDB(f"{args.path}/CLI")

    print(f"Prepare hardware capacity info for 9.3.(4,7,7a):")
    for i in tqdm(range(1)): model.prepareHardwareCapacityInfoForAll(f"{args.path}/CLI", ["9.3(4)", "9.3(7)", "9.3(7a)"], ['Cloudscale'])
    
    print(f"Model populate:")
    model.populate(f"{args.path}/CLI", commandsDefinition, referenceDefinitions)

    print(f"writeRawResult:")
    for i in tqdm(range(1)): model.writeRawResult()
    
    cSVHeaders = CSVHeaders().generateCSVHeaders(commandsDefinition, model, referenceDefinitions, ['Cloudscale', 'Jerico'])
    cSVHeaders.generateCSVs(model)
    
    model.writeRawResult() 
