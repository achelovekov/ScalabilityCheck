import os
import re
import sys
import csv
from tqdm import tqdm

from typing import Dict, List, Tuple, Callable, Optional, Type, Union

from pydantic import BaseModel
from pydantic.errors import TupleError
from devtools import debug
import json
from metricsAPI import *
import traceback

class Linecard(BaseModel):
    moduleNumber: int
    moduleType: str


class Fabricmodule(BaseModel):
    moduleNumber: int
    moduleType: str


class Value(BaseModel):
    originalValue: str
    referenceValue: str
    loadValue: str
    loadLevel: str


class MetricValuesByModuleItem(BaseModel):
    chassis: str
    moduleNumber: Optional[str]
    moduleType: Optional[str]
    value: Value

class MetricsValue(BaseModel):
    metric: str
    metricValuesByModule: List[MetricValuesByModuleItem] = []

    def populateMetricsValue(self, originalValue, referenceValue, chassis, moduleNumber, moduleType):
        if originalValue == 'n/a':
            loadValue = 'n/a'
            loadLevel = 'n/a'
        else:
            loadValue = round(float(float(originalValue)/float(referenceValue)), 2)
            loadLevel = GroupInventoryItem.loadLevel(loadValue)

        value = Value(
            originalValue=originalValue, 
            referenceValue=referenceValue, 
            loadValue=loadValue, 
            loadLevel=loadLevel
            )
        metricValuesByModuleItem = MetricValuesByModuleItem(
            chassis=chassis, 
            moduleNumber=moduleNumber, 
            moduleType=moduleType, 
            value=value)
        self.metricValuesByModule.append(metricValuesByModuleItem)

def readJSONFile(filename) -> Dict:
    try:
        with open(filename, encoding = 'utf-8') as f:
            try:   
                result = json.load(f)
                return result
            except json.decoder.JSONDecodeError as e:
                raise e
    except OSError as e:
        raise e

def readFile(filename):
    try:
        with open(filename, encoding = 'utf-8') as f:
            return f.read()
    except OSError as e:
        raise e

class GroupInventoryItem(BaseModel):
    hostname: str
    featureset: str = ''
    chassis: str = ''
    chipset: str = ''
    version: str = ''
    linecards: List[Linecard] = []
    fabricmodules: List[Fabricmodule] = []
    metricsValues: List[MetricsValue] = []

    @staticmethod
    def loadLevel(loadValue):
        if loadValue < 0.74:
            return "Ok"
        elif loadValue < 0.90:
            return "Warn"
        else: 
            return "Critical"

    def populateMetricValuePerChassis(self, metricsValue, command, data, referenceDefinitions):
        referenceMetrics = []

        for linecard in self.linecards:
            try:
                metricValue = referenceDefinitions.getMetricValue(self.featureset, self.version, command.metric, self.chassis, linecard.moduleType)
                if metricValue:
                    referenceMetrics.append(int(metricValue))

            except ValueError as e:
                print(f"{traceback.format_exc()} {e} with host {self.hostname} for metric {command.metric} {self.chassis} {linecard.moduleType}. May be wrong or non-exist reference for {self.version}")

        try:
            originalValue = AbstractAPI.executeAPICall(self.version, self.chipset, command.metric, data)
            if len(referenceMetrics) > 0: 
                referenceValue=min(referenceMetrics)  
                metricsValue.populateMetricsValue(originalValue, referenceValue, self.chassis, "unnumbered", "chassis")

        except (TypeError, ValueError) as e:
            print(f"{traceback.format_exc()} {e} with host {self.hostname} for metric {command.metric} {self.chassis} {linecard.moduleType}. May be old software version {self.version} or not implemented API")

    def populateMetricValuePerModule(self, metricsValue, command, data, referenceDefinitions, hardware):
        try:
            originalValue = AbstractAPI.executeAPICall(self.version, self.chipset, command.metric, data, str(hardware.moduleNumber))
            try:
                referenceValue = referenceDefinitions.getMetricValue(self.featureset, self.version, command.metric, self.chassis, hardware.moduleType)
                metricsValue.populateMetricsValue(originalValue, referenceValue, self.chassis, hardware.moduleNumber, hardware.moduleType)
            except ValueError as e:
                print(f"{traceback.format_exc()} {e} with host {self.hostname} for metric {command.metric} {self.chassis} {hardware.moduleType}. May be wrong or non-exist reference for {self.version}")

        except (TypeError, ValueError) as e:
            print(f"{traceback.format_exc()} {e} with host {self.hostname} for metric {command.metric} {self.chassis} {hardware.moduleType}. May be old software version {self.version}")

    def populateMetricValue(self, command, data, referenceDefinitions):
        metricsValue = MetricsValue(metric=command.metric)
        self.metricsValues.append(metricsValue)
        if command.type == "per-module":
            if len(self.linecards) > 0:
                for linecard in self.linecards: self.populateMetricValuePerModule(metricsValue, command, data, referenceDefinitions, linecard)
            if len(self.fabricmodules) > 0:
                for faricmodule in self.fabricmodules: self.populateMetricValuePerModule(metricsValue, command, data, referenceDefinitions, faricmodule)

        if command.type == "per-linecard":
            if len(self.linecards) > 0:
                for linecard in self.linecards: self.populateMetricValuePerModule(metricsValue, command, data, referenceDefinitions, linecard)

        if command.type == "per-chassis":
            self.populateMetricValuePerChassis(metricsValue, command, data, referenceDefinitions)

    def addMetricsData(self, rawInventoryFolder, command, referenceDefinitions):
        if self.featureset in command.features:
            commandFile = f"{rawInventoryFolder}/{self.hostname}/{self.hostname}-{command.command}"
            if command.mode == "json":
                try:
                    data = readJSONFile(commandFile)
                    self.populateMetricValue(command, data, referenceDefinitions)
                except OSError as e:
                    pass
                    #print(f"{e} with {self.hostname} for metric {command.metric}")
                except json.decoder.JSONDecodeError as e:
                    pass
                    #print(f"{e} may be not a valid data in file {command.command} for host {self.hostname} chassis {self.chassis} version {self.version}")
            if command.mode == "text":
                    try:
                        data = readFile(commandFile)
                        self.populateMetricValue(command, data, referenceDefinitions)
                    except OSError as e:
                        print(f"{e} with {self.hostname} for metric {command.metric}")

    def get_chassis_info(self, data):
        for item in data["TABLE_inv"]["ROW_inv"]:
            if "Chassis" in item["name"]:
                self.chassis = item["productid"]

    def get_linecards_info(self, data):
        linecards = []
        for item in data["TABLE_inv"]["ROW_inv"]:
            if "Ethernet" in item["desc"] and "Module" in item["desc"]:
                moduleNumber = str(re.search(r'\d+',item["name"]).group())
                moduleType = item["productid"]
                linecard = Linecard(moduleNumber=moduleNumber, moduleType=moduleType)
                linecards.append(linecard)
        self.linecards = linecards

    def get_fabricmodules_info(self, data):
        fabricmodules = []
        for item in data["TABLE_inv"]["ROW_inv"]:
            if "Fabric" in item["desc"] and "Module" in item["desc"]:
                moduleNumber = str(re.search(r'\d+',item["name"]).group())
                moduleType = item["productid"]
                fabricmodule = Fabricmodule(moduleNumber=moduleNumber, moduleType=moduleType)
                fabricmodules.append(fabricmodule)
        self.fabricmodules = fabricmodules

    def get_chipset_info(self, data):
        for item in data["TABLE_inv"]["ROW_inv"]:
            if "N9K-X9636C-R" in item["productid"]:
                self.chipset = "Jerico"
                return
            else: 
                self.chipset = "Cloudscale"

    def getMetricMaxLoadValue(self, metricValuesByModule):

        """
        0.0 0.3 0.0 0.1
        n/a 0.0 0.0 0.2
        0.2 n/a n/a 0.2
        n/a n/a n/a n/a 
        0.2 0.1 0.3 n/a
        """

        if len(metricValuesByModule) == 0:
            return 'n/a'

        if len(metricValuesByModule) == 0:
            return 'n/a'
        else:
            def counter(metricValuesByModule):
                result = 0
                for metricValueByModule in metricValuesByModule:
                    if metricValueByModule.value.loadValue == 'n/a':
                        result += 1
                return result 

            if counter(metricValuesByModule) == len(metricValuesByModule):
                return 'n/a'

        loadValue = '0.0'

        for metricValueByModule in metricValuesByModule:
            try:
                if float(metricValueByModule.value.loadValue) > float(loadValue):
                    loadValue = metricValueByModule.value.loadValue
            except ValueError as e:
                pass 
        return loadValue

    def getMetricLoadValue(self, metric):
        for metricItem in self.metricsValues:
            if metricItem.metric == metric:
                loadValue = self.getMetricMaxLoadValue(metricItem.metricValuesByModule)
                return str(loadValue).replace('.', ',')
        return 'n/a'

    def findProperList(self, data):
        try:
            data = json.loads(data)
            
            li = []
            for dataEntry in data:
                if "TABLE_module" in dataEntry:
                    if "ROW_module" in dataEntry["TABLE_module"]:
                        if "v4_trie_used" in dataEntry["TABLE_module"]["ROW_module"]:
                            li.append(dataEntry["TABLE_module"]["ROW_module"])
            if len(li) > 0:
                return li
            else:
                raise ValueError('bad command format for hardware capacity. May be old software version') 
        except json.decoder.JSONDecodeError as e:
            raise e

    def writeDataToFile(self, data, rawInventoryFolder):
        with open(f"{rawInventoryFolder}/{self.hostname}/{self.hostname}-show_hardware_capacity_forwarding_processed|_json.txt", 'w') as f:
            f.write(json.dumps(data))

    def prepareHardwareCapacityInfo(self, rawInventoryFolder):
        try:
            with open(f"{rawInventoryFolder}/{self.hostname}/{self.hostname}-show_hardware_capacity_forwarding_|_json.txt", encoding = 'utf-8') as f:
                data = f.read()
            data = re.sub('{"TABLE_', ',{"TABLE_', data)
            data = list(data)
            data[0] = "["
            data.remove(',')
            data.append("]")
            data.pop(-2)
            data = ''.join(data)

            try:
                li = self.findProperList(data)
                self.writeDataToFile(li, rawInventoryFolder)
            except json.decoder.JSONDecodeError as e:
                print(f"Can't load hardware capacity json data for {self.hostname}")
            except ValueError as e:
                print(f"{e} for device {self.hostname}, software version {self.version}, chassis {self.chassis}")

        except OSError as e:
            print(e)
        
class SegmentInventoryItem(BaseModel):
    groupName: str
    groupInventory: List[GroupInventoryItem]

    def __iter__(self):
        return iter(self.groupInventory)
    
    def append(self, groupInventoryItem:GroupInventoryItem):
        self.groupInventory.append(groupInventoryItem)


class RoomInventoryItem(BaseModel):
    segmentName: str
    segmentInventory: List[SegmentInventoryItem]
    
    def __iter__(self):
        return iter(self.segmentInventory)
    
    def append(self, segmentInventoryItem:SegmentInventoryItem):
        self.segmentInventory.append(segmentInventoryItem)

class ModelItem(BaseModel):
    room: str
    roomInventory: List[RoomInventoryItem]

    def __iter__(self):
        return iter(self.roomInventory)
    
    def append(self, roomInventoryItem:RoomInventoryItem):
        self.roomInventory.append(roomInventoryItem)


class Model(BaseModel):
    __root__: List[ModelItem] = []
    
    def append(self, modelItem:ModelItem):
        self.__root__.append(modelItem)
    
    def __iter__(self):
        return iter(self.__root__)

    def getHostList(self):
        result = []
        for room in self:
            for segment in room.roomInventory:
                for group in segment.segmentInventory:
                    for host in group.groupInventory: 
                        result.append(host)
        return result

    def getVersionList(self):
        result = set()
        for room in self:
            for segment in room.roomInventory:
                for group in segment.segmentInventory:
                    for host in group.groupInventory: 
                        result.add(host.version)
        return list(result)

    def getGroupInventoryItemByName(self, hostname) -> Union[GroupInventoryItem, None]:
        for host in self.getHostList():
            if host.hostname == hostname:
                return host
        return None

    def populate(self, rawInventoryFolder, commandsDefinition, referenceDefinitions):
        for host in tqdm(self.getHostList()):
            try:
                for command in commandsDefinition.getCommandListFromVersionAndChipset(host.version, host.chipset):
                    groupInventoryItem = self.getGroupInventoryItemByName(host.hostname)
                    groupInventoryItem.addMetricsData(rawInventoryFolder, command, referenceDefinitions) 

            except TypeError:
                    print(f"{host.version} is not found in commandsDefinition")


    def constructHostOperDB(self, rawInventoryFolder):
        for host in self.getHostList():
            filename = f"{rawInventoryFolder}/{host.hostname}/{host.hostname}-show_inventory_|_json.txt"
            groupInventoryItem = self.getGroupInventoryItemByName(host.hostname)
            try:
                with open(filename, encoding = 'utf-8') as f:
                    data = json.loads(f.read())

                    groupInventoryItem.get_chassis_info(data),
                    groupInventoryItem.get_linecards_info(data),
                    groupInventoryItem.get_fabricmodules_info(data)
                    groupInventoryItem.get_chipset_info(data)
                    groupInventoryItem.featureset = 'BGP-EVPN'   
            except OSError as e:
                print(e)

    def prepareHardwareCapacityInfoForAll(self, rawInventoryFolder, versions, chipsets):
        for host in self.getHostList():
            if host.version in versions and host.chipset in chipsets:
                host.prepareHardwareCapacityInfo(rawInventoryFolder)

    def writeRawResult(self):
        with open('RawReport.json', "w") as file:
            file.write(self.json())

def checkRoomExist(model, room) -> Tuple[bool, ModelItem]:
    for item in model:
        if item.room == room:
            return (True, item)
    return (False, None)

def createRoom(model, room) -> ModelItem:
    r = checkRoomExist(model, room)

    if not r[0]:
        modelItem = ModelItem(room=room, roomInventory=[])
        model.append(modelItem)
        return modelItem
    else:
        return r[1]
    
def checkSegmentExist(room, segmentName) -> Tuple[bool, RoomInventoryItem]:
    for item in room:
        if item.segmentName == segmentName:
            return (True, item)
    return (False, None)

def createSegment(room, segmentName) -> RoomInventoryItem:
    r = checkSegmentExist(room, segmentName)

    if not r[0]:
        roomInventoryItem = RoomInventoryItem(segmentName=segmentName, segmentInventory=[])
        room.append(roomInventoryItem)
        return roomInventoryItem
    else:
        return r[1]

def checkGroupExist(segment, groupName) -> Tuple[bool, SegmentInventoryItem]:
    for item in segment:
        if item.groupName == groupName:
            return (True, item)
    return (False, None)

def createGroup(segment, groupName) -> SegmentInventoryItem:

    r = checkGroupExist(segment, groupName)

    if not r[0]:
        segmentInventoryItem = SegmentInventoryItem(groupName=groupName, groupInventory=[])
        segment.append(segmentInventoryItem)
        return segmentInventoryItem
    else:
        return r[1]

def checkHostExist(group, hostname) -> Tuple[bool, GroupInventoryItem]:
    for item in group:
        if item.hostname == hostname:
            return (True, item)
    return (False, None)

def createHost(group, hostname, version) -> GroupInventoryItem:

    r = checkHostExist(group, hostname)

    if not r[0]:
        groupInventoryItem = GroupInventoryItem(hostname=hostname, version=version)
        group.append(groupInventoryItem)
        return groupInventoryItem
    else:
        return r[1]

def getVersion(rawInventoryFolder, deviceName) -> str:
    data = readJSONFile(f"{rawInventoryFolder}/{deviceName}/{deviceName}-show_version_|_json.txt")
    try:
        return data["kickstart_ver_str"]
    except KeyError:
        print("no key 'kickstart_ver_str' in data")

def parseRawCollection(rawInventoryFolder) -> Tuple[Model, List]:
    regex = (".*(?P<deviceType>(AC|AG|CR|RS|SS|BL|BG|F2FM|ML|C2|SC))-(?P<room>[A-Z0-9]+).*(?P<segment>(INT|EXT|DMZ|GWN))")
    list_subfolders_with_paths = [f.name for f in os.scandir(rawInventoryFolder) if f.is_dir()]

    model = Model()

    for deviceName in list_subfolders_with_paths:

        try:
            modelItem = createRoom(model, re.search(regex, deviceName).group('room'))
            roomInventoryItem = createSegment(modelItem, re.search(regex, deviceName).group('segment'))
            segmentInventoryItem = createGroup(roomInventoryItem, re.search(regex, deviceName).group('deviceType'))
            createHost(segmentInventoryItem, deviceName, getVersion(rawInventoryFolder, deviceName))
        except AttributeError as e:
            print(f"{e} with {deviceName}")

    return model, list_subfolders_with_paths

class CommandDefinition(BaseModel):
    type: str
    metric: str 
    features: List[str]
    command: str
    mode: str
    regex: Optional[str]
    takeMax: Optional[bool]

class CommandList(BaseModel):
    __root__: List[CommandDefinition]

    def append(self, commandDefinition:CommandDefinition):
        self.__root__.append(commandDefinition)

    def __iter__(self):
        return iter(self.__root__)

class CommandSetPerVersions(BaseModel):
    versions: List[str]
    chipsets: List[str]
    commands: CommandList

class CommandsDefinition(BaseModel):
    __root__: List[CommandSetPerVersions]

    def append(self, commandSetPerVersions:CommandSetPerVersions):
        self.__root__.append(commandSetPerVersions)

    def __iter__(self):
        return iter(self.__root__)
    
    def getCommandListFromVersionAndChipset(self, version, chipset) -> Union[CommandList, None]:
        for commandsDefinitionItem in self:
            if version in commandsDefinitionItem.versions and chipset in commandsDefinitionItem.chipsets:
                return commandsDefinitionItem.commands
        return None
    
    def getCommandListFromVersion(self, version) -> Union[CommandList, None]:
        for commandsDefinitionItem in self:
            if version in commandsDefinitionItem.versions:
                return commandsDefinitionItem.commands
        return None

def commandsDefinitionConstructor(filename) -> CommandsDefinition:
    try:
        with open(filename, encoding = 'utf-8') as f:
            data = f.read()
            return CommandsDefinition.parse_raw(data)  

    except Exception as e:
        print(f"{e}")
        sys.exit()

class ReferenceValue(BaseModel):
    platform: str
    linecard: str
    value: str

class ReferenceValues(BaseModel):
    __root__: List[ReferenceValue]

    def append(self, referenceMetricValue:ReferenceValue):
        self.__root__.append(referenceMetricValue)
    
    def __iter__(self):
        return iter(self.__root__)

class ReferenceMetric(BaseModel):
    metric: str
    hardware: ReferenceValues

class ReferenceMetrics(BaseModel):
    __root__: List[ReferenceMetric]

    def append(self, referenceMetric:ReferenceMetric):
        self.__root__.append(referenceMetric)

    def __iter__(self):
        return iter(self.__root__)

class ReferenceFeature(BaseModel):
    featureset: str
    metrics: ReferenceMetrics

class ReferenceFeatureSet(BaseModel):
    __root__: List[ReferenceFeature]

    def append(self, referenceFeature:ReferenceFeature):
        self.__root__.append(referenceFeature)
    
    def __iter__(self):
        return iter(self.__root__)

class ReferenceDefinition(BaseModel):
    versions: List[str]
    definition: ReferenceFeatureSet

    def __iter__(self):
        return iter(self.definition)

class ReferenceDefinitions(BaseModel):
    __root__: List[ReferenceDefinition] = []

    def append(self, referenceDefinition:ReferenceDefinition):
        self.__root__.append(referenceDefinition)
    
    def __iter__(self):
        return iter(self.__root__)

    def getMetricValue(self, featureset, version, metric, platform, linecard):

        result = None

        for referenceDefinition in self:
            if version in referenceDefinition.versions:
                for referenceFeature in referenceDefinition:
                    if referenceFeature.featureset == featureset:
                        for metricEntry in referenceFeature.metrics:
                            if metricEntry.metric == metric:
                                for referenceValue in metricEntry.hardware:
                                    if referenceValue.platform == platform and referenceValue.linecard == linecard:
                                        return referenceValue.value

        if result is None:
            raise ValueError(f"Can't get reference value for {metric}, {platform}, {linecard}")
        
        return result
    
    def getVersionsFromReference(self):
        res = []
        for referenceDefinition in self:
            res += referenceDefinition.versions
        return res

    @classmethod
    def initialize(cls):
        referenceFiles = [f for f in os.listdir('.') if os.path.isfile(f) and 'Reference' in f]

        referenceDefinitions = ReferenceDefinitions()

        for referenceFile in referenceFiles:
            try:
                with open(referenceFile, encoding = 'utf-8') as f:
                    data = json.loads(f.read())
                referenceDefinitions.append(ReferenceDefinition.parse_obj(data))

            except Exception as e:
                print(f"{e}")
                sys.exit()
        
        return referenceDefinitions

class CSVHeader(BaseModel):
    version: str
    chipset: str
    fieldnames: List[str]

    def generateModelCSV(self, model: Model):
        result = []
        fieldnames = self.fieldnames
        for host in model.getHostList():
            if self.version == host.version and self.chipset == host.chipset: 
                di = {}
                di["hostname"] = host.hostname
                di["featureset"] = host.featureset
                di["version"] = host.version
                
                for metric in fieldnames[3:]:
                    di[metric] =  host.getMetricLoadValue(metric)
                result.append(di)
        return result

class CSVHeaders(BaseModel):
    __root__: List[CSVHeader] = []

    def append(self, cSVHeader:CSVHeader):
        self.__root__.append(cSVHeader)
    
    def __iter__(self):
        return iter(self.__root__)
    
    def generateCSVHeaders(self, commandsDefinition: CommandsDefinition, model: Model, referenceDefinitions: ReferenceDefinitions, chipsets: List[str]):
        intersection = set(referenceDefinitions.getVersionsFromReference()) & set(model.getVersionList())
        
        for version in intersection:
            for chipset in chipsets:
                fieldnames = ['hostname', 'featureset', 'version']
                for command in commandsDefinition.getCommandListFromVersionAndChipset(version, chipset):
                    fieldnames += [ command.metric ]
            
                cSVHeader = CSVHeader(version=version, fieldnames=fieldnames, chipset=chipset)
                self.append(cSVHeader)
        return self
    
    def generateCSVs(self, model):
        for cSVHeader in self:
            result = cSVHeader.generateModelCSV(model)
            if len(result) > 0:
                filename = f"CSVReport-{cSVHeader.version}-{cSVHeader.chipset}.csv"
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=cSVHeader.fieldnames, delimiter='\t')
                    writer.writeheader()
                    for item in result: 
                        writer.writerow(item) 





             



         