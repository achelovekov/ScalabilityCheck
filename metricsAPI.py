from abc import ABCMeta, abstractmethod
from ttp import ttp 

class TTPAuxilary():
    
    def getParserResult(parserResult, moduleNumber):
        if isinstance(parserResult, list):
            for i in parserResult:
                if isinstance(i, list):
                    for j in i:
                        if isinstance(j, list):
                            for k in j:
                                if isinstance(k, dict):
                                    if k['moduleNumber'] == moduleNumber:
                                        return k
                        if isinstance(j, dict):
                            if j['moduleNumber'] == moduleNumber:
                                return j
    
    def generateTTPTemplates():
        di = {}
        di['hardwareCapacity'] = {}
        di['hardwareCapacity']['Cloudscale'] = """
IPv4/IPv6  hosts and routes summary on module : {{ moduleNumber }}
Percentage utilization of IPv4 native host routes : {{ IPv4NativeHost }}{{ _exact_ }} 
Percentage utilization of IPv6 native host routes : {{ IPv6NativeHost }}{{ _exact_ }}  
Percentage utilization of IPv6 ND/local routes : {{ IPv6ND }}  
Percentage utilization of IPv6 host /128 learnt routes : {{ IPv6Host }}  
Percentage utilization of IPv4 trie routes : {{ IPv4Trie }}{{ _exact_ }} 
Percentage utilization of IPv6 trie routes : {{ IPv6Trie }}{{ _exact_ }}   
Percentage utilization of IPv4 TCAM routes : {{ IPv4TCAM }}{{ _exact_ }}  
Percentage utilization of IPv6 TCAM routes : {{ IPv6TCAM }}{{ _exact_ }}
Percentage utilization of nexthop entries : {{ NH }}{{ _exact_ }}
ECMP groups used: {{ ecmp }}
"""
        di['hardwareCapacity']['Jerico'] = """
IP/IPv6 routes summary on Module: {{ moduleNumber }}
Host Table - Percentage Utilization by IPv4 Host Routes : {{ IPv4Host }}{{ _exact_ }}
LPM - Percentage Utilization by IPv6 Host: {{ IPv6Host }}{{ _exact_ }}
LPM - Percentage Utilization by IPv4 LPM routes: {{ IPv4LPMRoutes }}{{ _exact_ }}
LPM - Percentage Utilization by IPv6(Host+LPM) routes : {{ IPv6LPMRoutes }}{{ _exact_ }}
""" 
        return di

    def parseTTPTemplate(data, templateName, chipset):
            ttpTemplate = TTPAuxilary.TTPTemplates[templateName][chipset]

            parser = ttp(data=data, template=ttpTemplate)
            parser.parse()

            return parser.result()

    TTPTemplates = generateTTPTemplates()

class AbstractAPI(metaclass=ABCMeta):
    impls = []
    versions = []
    chipsets = []


    @abstractmethod
    def svi(self, *args):
        pass

    @abstractmethod
    def mac(self, *args):
        pass

    @abstractmethod
    def vlan(self, *args):
        pass
    
    @abstractmethod
    def vtep(self, *args):
        pass
    
    @abstractmethod
    def mcast(self, *args):
        pass

    @abstractmethod
    def v4_hosts(self, *args):
        pass

    @abstractmethod
    def v6_hosts(self, *args):
        pass

    @abstractmethod
    def v6_nd_local(self, *args):
        pass

    @abstractmethod
    def v4_trie(self, *args):
        pass

    @abstractmethod
    def v6_trie(self, *args):
        pass

    @abstractmethod
    def v4_tcam(self, *args):
        pass

    @abstractmethod
    def v6_tcam(self, *args):
        pass

    @abstractmethod
    def next_hop(self, *args):
        pass

    @abstractmethod
    def ecmp(self, *args):
        pass

    @abstractmethod
    def l3vni(self, *args):
        pass

    @abstractmethod
    def l2vni(self, *args):
        pass

    @abstractmethod
    def bfd_linecard(self, *args):
        pass

    @abstractmethod
    def bfd_global(self, *args):
        pass

    @abstractmethod
    def arp(self, *args):
        pass

    def __init_subclass__(cls, **kwargs):
        AbstractAPI.impls.append(cls)
    
    @staticmethod
    def executeAPICall(*args):
        current_version = args[0]
        current_chipset = args[1]
        metric = args[2]
        for impl in AbstractAPI.impls:
            if current_version in impl.versions and current_chipset in impl.chipsets:
                return getattr(impl(), metric, None)(*args[3:])

class APIvHK123hkJ(AbstractAPI):
    versions = ['9.3(4)', '9.3(7)', '9.3(7a)']
    chipsets = ['Cloudscale']

    def svi(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_intf"]["ROW_intf"], list):
                for svi in data["TABLE_intf"]["ROW_intf"]:
                    if "Vlan" in svi["intf-name"] and "prefix" in svi:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_intf"]["ROW_intf"], dict):
                if "Vlan" in data["TABLE_intf"]["ROW_intf"]["intf-name"] and "prefix" in data["TABLE_intf"]["ROW_intf"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def mac(self, data):
        return data["TABLE-macaddtblcount"]["total_cnt"]

    def vlan(self, data):
        for entry in data["TABLE_resource"]["ROW_resource"]:
            if entry["resource_name"] == "vlan": 
                return entry["total_used"]

    def vtep(self, data):
        count = 0
        for vtep in data["TABLE_nve_peers"]["ROW_nve_peers"]:
            count += 1
        return str(count)

    def mcast(self, data):
        return data["TABLE_vrf"]["ROW_vrf"]["TABLE_route_summary"]["ROW_route_summary"]["total-num-routes"]

    def v4_hosts(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                result = dataEntry["v4_hosts_pctage"]
            else:
                result = 'n/a'
        return result

    def v6_hosts(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                result = dataEntry["v6_hosts_pctage"]
            else:
                result = 'n/a'
        return result

    def v6_nd_local(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                result = dataEntry["v6_nd_local_pctage"]
            else:
                result = 'n/a'
        return result

    def v4_trie(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                result = dataEntry["v4_trie_pctage"]
            else:
                result = 'n/a'
        return result

    def v6_trie(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                result = dataEntry["v6_trie_pctage"]
            else:
                result = 'n/a'
        return result

    def v4_tcam(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                result = dataEntry["v4_tcam_pctage"]
            else:
                result = 'n/a'
        return result

    def v6_tcam(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                result = dataEntry["v6_tcam_pctage"]
            else:
                result = 'n/a'
        return result

    def next_hop(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                result = dataEntry["next_hop_pctage"]
            else:
                result = 'n/a'
        return result

    def ecmp(self, data, moduleNumber):
        result = None
        for dataEntry in data:
            if dataEntry["module_number"] == moduleNumber:
                if "ecmp_entries_used" in dataEntry:
                    result = dataEntry["ecmp_entries_used"]
            else:
                result = 'n/a'
        return result

    def l3vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L3" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L3" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def l2vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L2" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L2" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_linecard(self, data, moduleNumber):
        count = 0
        inftName = f"Ethernet{moduleNumber}/"

        try:
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], list):
                for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    if inftName in neighbor["intf"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], dict):
                if inftName in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_global(self, data):
        count = 0
        try:
            for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                count += 1
            return str(count)
        except TypeError as e:
            raise TypeError(e)

    def arp(self, data):
        try:
            return data["TABLE_vrf"]["ROW_vrf"]["cnt-total"]
        except TypeError as e:
            raise TypeError(e)

class APIvHK123hkZ(AbstractAPI):
    versions = ['9.3(4)', '9.3(7)', '9.3(7a)']
    chipsets = ['Jerico']

    def svi(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_intf"]["ROW_intf"], list):
                for svi in data["TABLE_intf"]["ROW_intf"]:
                    if "Vlan" in svi["intf-name"] and "prefix" in svi:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_intf"]["ROW_intf"], dict):
                if "Vlan" in data["TABLE_intf"]["ROW_intf"]["intf-name"] and "prefix" in data["TABLE_intf"]["ROW_intf"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def mac(self, data):
        return data["TABLE-macaddtblcount"]["total_cnt"]

    def vlan(self, data):
        for entry in data["TABLE_resource"]["ROW_resource"]:
            if entry["resource_name"] == "vlan": 
                return entry["total_used"]

    def vtep(self, data):
        count = 0
        for vtep in data["TABLE_nve_peers"]["ROW_nve_peers"]:
            count += 1
        return str(count)

    def mcast(self, data):
        return data["TABLE_vrf"]["ROW_vrf"]["TABLE_route_summary"]["ROW_route_summary"]["total-num-routes"]

    def v4_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Jerico'), moduleNumber)['IPv4Host']
        except (KeyError, TypeError):
            return 'n/a'
    
    def v6_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Jerico'), moduleNumber)['IPv6Host']
        except (KeyError, TypeError):
            return 'n/a'
    
    def v4_lpm_routes(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Jerico'), moduleNumber)['IPv4LPMRoutes']
        except (KeyError, TypeError):
            return 'n/a'
    
    def v6_lpm_routes(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Jerico'), moduleNumber)['IPv6LPMRoutes']
        except (KeyError, TypeError):
            return 'n/a'

    """ for interface compatability """
    def v6_nd_local(self, data, moduleNumber):
        pass

    def v4_trie(self, data, moduleNumber):
        pass

    def v6_trie(self, data, moduleNumber):
        pass

    def v4_tcam(self, data, moduleNumber):
        pass

    def v6_tcam(self, data, moduleNumber):
        pass

    def next_hop(self, data, moduleNumber):
        pass

    def ecmp(self, data, moduleNumber):
        pass
    """ end """

    def l3vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L3" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L3" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def l2vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L2" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L2" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_linecard(self, data, moduleNumber):
        count = 0
        inftName = f"Ethernet{moduleNumber}/"

        try:
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], list):
                for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    if inftName in neighbor["intf"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], dict):
                if inftName in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_global(self, data):
        count = 0
        try:
            for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                count += 1
            return str(count)
        except TypeError as e:
            raise TypeError(e)

    def arp(self, data):
        try:
            return data["TABLE_vrf"]["ROW_vrf"]["cnt-total"]
        except TypeError as e:
            raise TypeError(e)

class APIvHK123hkL(AbstractAPI):
    versions = ['9.2(3)', '9.2(4)', "9.3(1)"]
    chipsets = ['Jerico', 'Cloudscale']

    def svi(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_intf"]["ROW_intf"], list):
                for svi in data["TABLE_intf"]["ROW_intf"]:
                    if "Vlan" in svi["intf-name"] and "prefix" in svi:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_intf"]["ROW_intf"], dict):
                if "Vlan" in data["TABLE_intf"]["ROW_intf"]["intf-name"] and "prefix" in data["TABLE_intf"]["ROW_intf"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def mac(self, data):
        return data["TABLE-macaddtblcount"]["total_cnt"]

    def vlan(self, data):
        for entry in data["TABLE_resource"]["ROW_resource"]:
            if entry["resource_name"] == "vlan": 
                return entry["total_used"]

    def vtep(self, data):
        count = 0
        for vtep in data["TABLE_nve_peers"]["ROW_nve_peers"]:
            count += 1
        return str(count)

    def mcast(self, data):
        return data["TABLE_vrf"]["ROW_vrf"]["TABLE_route_summary"]["ROW_route_summary"]["total-num-routes"]

    def v4_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4NativeHost']
        except KeyError:
            return 'n/a'

    def v6_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6NativeHost']
        except KeyError:
            return 'n/a'

    def v6_nd_local(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6ND']
        except KeyError: 
            return 'n/a'

    def v4_trie(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4Trie']
        except KeyError:
            return 'n/a'

    def v6_trie(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6Trie']
        except KeyError: 
            return 'n/a'

    def v4_tcam(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4TCAM']
        except KeyError:
            return 'n/a'

    def v6_tcam(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6TCAM']
        except KeyError:
            return 'n/a'

    def next_hop(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['NH']
        except KeyError:
            return 'n/a'

    def ecmp(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['ecmp']
        except KeyError:
            return 'n/a'

    def l3vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L3" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L3" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def l2vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L2" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L2" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_linecard(self, data, moduleNumber):
        count = 0
        inftName = f"Ethernet{moduleNumber}/"

        try:
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], list):
                for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    if inftName in neighbor["intf"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], dict):
                if inftName in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_global(self, data):
        count = 0
        try:
            for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                count += 1
            return str(count)
        except TypeError as e:
            raise TypeError(e)

    def arp(self, data):
        try:
            return data["TABLE_vrf"]["ROW_vrf"]["cnt-total"]
        except TypeError as e:
            raise TypeError(e)

class APIvHK123hkP(AbstractAPI):
    versions = ['7.0(3)I7(2)']
    chipsets = ['Jerico', 'Cloudscale']

    def svi(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_intf"]["ROW_intf"], list):
                for svi in data["TABLE_intf"]["ROW_intf"]:
                    if "Vlan" in svi["intf-name"] and "prefix" in svi:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_intf"]["ROW_intf"], dict):
                if "Vlan" in data["TABLE_intf"]["ROW_intf"]["intf-name"] and "prefix" in data["TABLE_intf"]["ROW_intf"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def mac(self, data):
        return data["TABLE-macaddtblcount"]["total_cnt"]

    def vlan(self, data):
        for entry in data["TABLE_resource"]["ROW_resource"]:
            if entry["resource_name"] == "vlan": 
                return entry["total_used"]

    def vtep(self, data):
        count = 0
        for vtep in data["TABLE_nve_peers"]["ROW_nve_peers"]:
            count += 1
        return str(count)

    def mcast(self, data):
        return data["TABLE_vrf"]["ROW_vrf"]["TABLE_route_summary"]["ROW_route_summary"]["total-num-routes"]

    def v4_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4NativeHost']
        except KeyError:
            return 'n/a'

    def v6_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6NativeHost']
        except KeyError:
            return 'n/a'

    def v6_nd_local(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6ND']
        except KeyError: 
            return 'n/a'

    def v4_trie(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4Trie']
        except KeyError:
            return 'n/a'

    def v6_trie(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6Trie']
        except KeyError: 
            return 'n/a'

    def v4_tcam(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4TCAM']
        except KeyError:
            return 'n/a'

    def v6_tcam(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6TCAM']
        except KeyError:
            return 'n/a'

    def next_hop(self, data, moduleNumber):
        pass

    def ecmp(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['ecmp']
        except KeyError:
            return 'n/a'

    def l3vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L3" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L3" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def l2vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L2" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L2" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_linecard(self, data, moduleNumber):
        count = 0
        inftName = f"Ethernet{moduleNumber}/"

        try:
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], list):
                for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    if inftName in neighbor["intf"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], dict):
                if inftName in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_global(self, data):
        count = 0
        try:
            for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                count += 1
            return str(count)
        except TypeError as e:
            raise TypeError(e)

    def arp(self, data):
        try:
            return data["TABLE_vrf"]["ROW_vrf"]["cnt-total"]
        except TypeError as e:
            raise TypeError(e)

class APIvHK123hjM(AbstractAPI):
    versions = ['7.0(3)I7(5)']
    chipsets = ['Jerico', 'Cloudscale']

    def svi(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_intf"], list):
                for svi in data["TABLE_intf"]:
                    if "Vlan" in svi["ROW_intf"]["intf-name"] and "prefix" in svi["ROW_intf"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_intf"], dict):
                if "Vlan" in data["TABLE_intf"]["ROW_intf"]["intf-name"] and "prefix" in data["TABLE_intf"]["ROW_intf"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def mac(self, data):
        return data["TABLE-macaddtblcount"]["total_cnt"]

    def vlan(self, data):
        for entry in data["TABLE_resource"]["ROW_resource"]:
            if entry["resource_name"] == "vlan": 
                return entry["total_used"]

    def vtep(self, data):
        count = 0
        for vtep in data["TABLE_nve_peers"]["ROW_nve_peers"]:
            count += 1
        return str(count)

    def mcast(self, data):
        return data["TABLE_vrf"]["ROW_vrf"]["TABLE_route_summary"]["ROW_route_summary"]["total-num-routes"]

    def v4_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4NativeHost']
        except KeyError:
            return 'n/a'

    def v6_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6NativeHost']
        except KeyError:
            return 'n/a'

    def v6_nd_local(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6ND']
        except KeyError: 
            return 'n/a'

    def v4_trie(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4Trie']
        except KeyError:
            return 'n/a'

    def v6_trie(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6Trie']
        except KeyError: 
            return 'n/a'

    def v4_tcam(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4TCAM']
        except KeyError:
            return 'n/a'

    def v6_tcam(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6TCAM']
        except KeyError:
            return 'n/a'

    def next_hop(self, data, moduleNumber):
        pass

    def ecmp(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['ecmp']
        except KeyError:
            return 'n/a'
    def l3vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L3" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L3" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def l2vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L2" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L2" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_linecard(self, data, moduleNumber):
        count = 0
        inftName = f"Ethernet{moduleNumber}/"

        try:
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], list):
                for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    if inftName in neighbor["intf"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], dict):
                if inftName in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_global(self, data):
        count = 0
        try:
            for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                count += 1
            return str(count)
        except TypeError as e:
            raise TypeError(e)

    def arp(self, data):
        try:
            return data["TABLE_vrf"]["ROW_vrf"]["cnt-total"]
        except TypeError as e:
            raise TypeError(e)

class APIvHK123hkB(AbstractAPI):
    versions = ['7.0(3)I7(5a)', '7.0(3)I7(6)']
    chipsets = ['Jerico', 'Cloudscale']

    def svi(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_intf"], list):
                for svi in data["TABLE_intf"]:
                    if "Vlan" in svi["ROW_intf"]["intf-name"] and "prefix" in svi["ROW_intf"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_intf"], dict):
                if "Vlan" in data["TABLE_intf"]["ROW_intf"]["intf-name"] and "prefix" in data["TABLE_intf"]["ROW_intf"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)
            
    def mac(self, data):
        return data["TABLE-macaddtblcount"]["total_cnt"]

    def vlan(self, data):
        for entry in data["TABLE_resource"]["ROW_resource"]:
            if entry["resource_name"] == "vlan": 
                return entry["total_used"]

    def vtep(self, data):
        count = 0
        for vtep in data["TABLE_nve_peers"]["ROW_nve_peers"]:
            count += 1
        return str(count)

    def mcast(self, data):
        return data["TABLE_vrf"]["ROW_vrf"]["TABLE_route_summary"]["ROW_route_summary"]["total-num-routes"]

    def v4_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4NativeHost']
        except KeyError:
            return 'n/a'

    def v6_hosts(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6NativeHost']
        except KeyError:
            return 'n/a'

    def v6_nd_local(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6ND']
        except KeyError: 
            return 'n/a'

    def v4_trie(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4Trie']
        except KeyError:
            return 'n/a'

    def v6_trie(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6Trie']
        except KeyError: 
            return 'n/a'

    def v4_tcam(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv4TCAM']
        except KeyError:
            return 'n/a'

    def v6_tcam(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['IPv6TCAM']
        except KeyError:
            return 'n/a'

    def next_hop(self, data, moduleNumber):
        pass

    def ecmp(self, data, moduleNumber):
        try:
            return TTPAuxilary.getParserResult(TTPAuxilary.parseTTPTemplate(data, 'hardwareCapacity', 'Cloudscale'), moduleNumber)['ecmp']
        except KeyError:
            return 'n/a'
            
    def l3vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L3" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L3" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def l2vni(self, data):
        count = 0
        try:
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], list):
                for vni in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    if "L2" in vni["type"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_nve_vni"]["ROW_nve_vni"], dict):
                if "L2" in data["TABLE_nve_vni"]["ROW_nve_vni"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_linecard(self, data, moduleNumber):
        count = 0
        inftName = f"Ethernet{moduleNumber}/"

        try:
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], list):
                for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    if inftName in neighbor["intf"]:
                        count += 1
                return str(count)
            if isinstance(data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"], dict):
                if inftName in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                    count += 1
                return str(count)
        except TypeError as e:
            raise TypeError(e)

    def bfd_global(self, data):
        count = 0
        try:
            for neighbor in data["TABLE_bfdNeighbor"]["ROW_bfdNeighbor"]:
                count += 1
            return str(count)
        except TypeError as e:
            raise TypeError(e)

    def arp(self, data):
        try:
            return data["TABLE_vrf"]["ROW_vrf"]["cnt-total"]
        except TypeError as e:
            raise TypeError(e)