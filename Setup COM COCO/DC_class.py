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
        self.doc = comtypes.client.CreateObject('COCO_COFE.Document', interface=cofeTypes.ICOFEDocument)

        self.doc.Import(doc_path)
        self.inlet_stream = self.doc.GetStream('1')
        self.Unit = self.doc.GetUnit('Column_1')

        """INLET FLOWRATES"""
        self.inlet_stream_material = self.inlet_stream.QueryInterface(coTypes.ICapeThermoMaterial)

        """OUTPUTS"""
        self.TAC = self.Unit.QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).\
            Item("Total Annual Cost").QueryInterface(coTypes.ICapeParameter)
        self.condenser_duty = self.Unit.QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).\
            Item("Reboiler duty").QueryInterface(coTypes.ICapeParameter)
        self.reboiler_duty = self.Unit.QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(
            coTypes.ICapeCollection). \
            Item("Condenser duty").QueryInterface(coTypes.ICapeParameter)
        self.tops = self.doc.GetStream('2').QueryInterface(coTypes.ICapeThermoMaterial)
        self.bottoms = self.doc.GetStream('3').QueryInterface(coTypes.ICapeThermoMaterial)

        """UNIT INPUTS"""
        self.n_stages = self.Unit.QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Number of stages").QueryInterface(coTypes.ICapeParameter)
        self.reflux_ratio = self.Unit.QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Reflux ratio").QueryInterface(coTypes.ICapeParameter)
        self.reboil_ratio = self.Unit.QueryInterface(coTypes.ICapeUtilities).Parameters.QueryInterface(coTypes.ICapeCollection).Item(
            "Reboil ratio").QueryInterface(coTypes.ICapeParameter)

    def set_inlet_flowrates(self, flowrates):
        try:
            self.inlet_stream_material.SetOverallProp("flow", "mole", array.array('d', flowrates))
        except COMError:
            print("Error:", self.inlet_stream.QueryInterface(coTypes.ECapeRoot).name)

    def get_outputs(self):
        tops_flow = self.tops.GetOverallProp("flow", "mole")
        bottoms_flow = self.bottoms.GetOverallProp("flow", "mole")
        return self.TAC.value, tops_flow, bottoms_flow, self.condenser_duty.value, self.reboiler_duty.value

    def get_unit_inputs(self):
        return self.n_stages.value, self.reflux_ratio.value, self.reboil_ratio.value

    def set_unit_inputs(self, n_stages, reflux_ratio, reboil_ratio):
        self.n_stages.value = float(n_stages)
        self.reflux_ratio.value = float(reflux_ratio)
        self.reboil_ratio.value = float(reboil_ratio)

    def solve(self, with_print=False):
        try:
            self.doc.Solve()
            if with_print is True:
                print("Solved without exception")
        except:  # #TODO add some specifics here
            if with_print is True:
                print("Weird solve error thing")

    def timed_solve(self, time=30):
        """Limits solve time, returns 1 if solve didn't work"""
        if __name__ == '__main__':
            p = Process(target=self.solve)
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
