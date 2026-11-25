"""Regression checks for scientific interpretation and invalid-input handling."""
import io
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from study_contract import capacity_basis, classify, read_trace, validate_config
from run_study import time_to_soc, error_on_grid
from select_model import select


class Contracts(unittest.TestCase):
    def test_soc_basis_and_target(self):
        q = capacity_basis()["electrode_window_capacity_ah"]
        self.assertGreater(q, 5)
        f = pd.DataFrame({"time_s":[0.,1000.], "soc":[.1,.1+4/q], "soc_nominal":[.1,.9]})
        self.assertGreater(time_to_soc(f,.8), time_to_soc(f,.8,"soc_nominal"))
        self.assertTrue(np.isnan(time_to_soc(f,1.)))
        self.assertTrue(np.isnan(time_to_soc(f,0.)))

    def test_missing_nonfinite_and_accuracy_are_distinct(self):
        good = dict(voltage_cc_mv_rmse=10.,temperature_c_max_abs=.5,time_to_80_error_s=-30.)
        self.assertEqual(classify(good),"adequate")
        self.assertEqual(classify(dict(good,voltage_cc_mv_rmse=55.)),"accuracy_failure")
        for key in good:
            bad = dict(good); del bad[key]
            self.assertEqual(classify(bad),"invalid_metrics")
            for value in [None, "", False, float("nan"),float("inf"),-float("inf")]:
                self.assertEqual(classify(dict(good,**{key:value})),"invalid_metrics")

    def test_switch_timestamp_round_trip_and_explicit_cleanup(self):
        text = "time_s,voltage_v\n0,3\n2669.033742,4.2\n2669.0337420000006,4.2\n"
        self.assertEqual(len(read_trace(io.StringIO(text))),3)
        dup = "time_s,voltage_v\n0,3\n1,4\n1,4.2\n"
        with self.assertRaises(ValueError): read_trace(io.StringIO(dup))
        clean = read_trace(io.StringIO(dup),duplicate_policy="keep_last")
        self.assertEqual(clean.attrs["exact_duplicates_removed"],1)
        self.assertEqual(clean.voltage_v.iloc[-1],4.2)

    def test_no_silent_extrapolation(self):
        f=pd.DataFrame({"time_s":[1.,2.],"v":[3.,4.]})
        with self.assertRaises(ValueError): error_on_grid(f,f,"v",2.)
        f.time_s=[0.,2.]
        with self.assertRaises(ValueError): error_on_grid(f,f,"v",3.)

    def test_config_rejects_invalid_inputs(self):
        cfg=json.loads((Path(__file__).parent/"configs/baseline.json").read_text())
        for update in [dict(rates_c=[float("nan")]),dict(repeats=0),dict(initial_soc=.9),
                       dict(temperatures_c=[float("inf")]),dict(parameter_variant="other"),dict(mesh_points=2.5)]:
            with self.assertRaises(ValueError): validate_config(dict(cfg,**update))

    def test_selector_bounds_and_quick_run(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"config.json").write_text(json.dumps(dict(rates_c=[1,2],temperatures_c=[10,25],repeats=1)))
            for rate,temp in [(float("nan"),25),(1,float("inf")),(1.5,25),(1,0)]:
                self.assertEqual(select(p,rate,temp)["status"],"out_of_domain")
            self.assertEqual(select(p,1,25)["status"],"insufficient_benchmark_repeats")


if __name__ == "__main__":
    unittest.main()
