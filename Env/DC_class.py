import comtypes.client
import comtypes.gen
from comtypes import COMError
from comtypes.automation import VARIANT
import array
from multiprocessing import Process

# tell comtypes to load type libs
cofeTlb = ('{0D1006C7-6086-4838-89FC-FBDCC0E98780}', 1, 0)  # COFE type lib
cofeTypes = comtypes.client.GetModule(cofeTlb)
coTlb = ('{4A5E2E81-C093-11D4-9F1B-0010A4D198C2}', 1, 1)  # CAPE-OPEN v1.1 type lib
coTypes = comtypes.client.GetModule(coTlb)


class SimulatorDC:
    def __init__(self, doc_path):
        """
        doc_path: path to flowsheet.fsd COCO file
        :param doc_path:
        """
        self.doc = comtypes.client.CreateObject('COCO_COFE.Document', interface=cofeTypes.ICOFEDocument)
        self.doc.Import(doc_path)

    def set_inlet_flowrates(self, flowrates):
        try:
            self.doc.GetStream('1').QueryInterface(coTypes.ICapeThermoMaterial).SetOverallProp("flow", "mole", array.array('d', flowrates))
        except COMError:
            print("Error:", self.doc.GetStream('1').QueryInterface(coTypes.ECapeRoot).name)

    def get_inlet_flowrates(self):
        return self.doc.GetStream('1').QueryInterface(coTypes.ICapeThermoMaterial).GetOverallProp("flow", "mole")

    def get_outputs(self):
        tops_flow = self.doc.GetStream('2').QueryInterface(coTypes.ICapeThermoMaterial).GetOverallProp("flow", "mole")
        bottoms_flow = self.doc.GetStream('3').QueryInterface(coTypes.ICapeThermoMaterial).GetOverallProp("flow", "mole")

        TAC = self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).\
            Item("Total Annual Cost").QueryInterface(coTypes.ICapeParameter).value
        condenser_duty = self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).\
            Item("Reboiler duty").QueryInterface(coTypes.ICapeParameter)
        reboiler_duty = self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).\
            Item("Reboiler duty").QueryInterface(coTypes.ICapeParameter)
        return tops_flow, bottoms_flow, TAC, condenser_duty, reboiler_duty

    def get_unit_inputs(self):
        n_stages = self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Number of stages").QueryInterface(coTypes.ICapeParameter).value
        reflux_ratio = self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Reflux ratio").QueryInterface(coTypes.ICapeParameter).value
        reboil_ratio = self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Reboil ratio").QueryInterface(coTypes.ICapeParameter).value
        return n_stages, reflux_ratio, reboil_ratio

    def set_unit_inputs(self, n_stages, reflux_ratio, reboil_ratio):
        self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Number of stages").QueryInterface(coTypes.ICapeParameter).value = float(n_stages)
        self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Reflux ratio").QueryInterface(coTypes.ICapeParameter).value = float(reflux_ratio)
        self.doc.GetUnit('Column_1').QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Reboil ratio").QueryInterface(coTypes.ICapeParameter).value = float(reboil_ratio)


    def timed_solve(self, time=30):
        self.doc.Solve()
        """Limits solve time, returns 1 if solve didn't work"""
        """
        p = Process(target=self.doc.Solve)
        p.start()
        # Wait for 10 seconds or until process finishes
        p.join(time)
        # If thread is still active
        if p.is_alive():
            print("Still running after 30 seconds so must kill")
            # Terminate
            p.terminate()
            p.join()
            return 1
        else:
            return 0
        """
