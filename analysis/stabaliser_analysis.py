'''
A script to run a standard analysis
on samples with added stablisers
(amines). Assumes the Boxerino output
files have been converted into root
histo's using analysis/rootify. 

Author : Ed Leming
Date   : 26/01/2017
'''
import argparse
import ROOT
import datetime
import re
import sys
import utils.utils as utils
import numpy as np
from collections import defaultdict

colors = [ROOT.kBlack, ROOT.kRed-4, ROOT.kOrange+7, ROOT.kGreen+2, ROOT.kCyan+2, ROOT.kBlue, ROOT.kMagenta+1, ROOT.kGray]
markers = [4,5,2,7]

class DataStructure(object):
    """Rogue class to so we can make array of objects with all info"""
    def __init__(self, hist_name, histo):
        """Init structure"""
        self._histo = histo
        self._hist_name = hist_name
        self._relative_time = None
        self.unpack_hist_name()
        self.estimate_end_point()

    def unpack_hist_name(self):
        """Read some interesting parameters from hist name string"""
        variables = self._hist_name.split("_")
        blank = False
        pure_lab = False
        if len(variables) == 5:
            blank = False
        elif len(variables) == 4:
            blank  = True
        elif len(variables) == 2:
            pure_lab = True
        else:
            print "Looks like the file name doesn't follow convention:"
            print self._hist_name
            print "It should look like: date_Te%_PPO_ratio_A/B"
            print "If you've added an extra descriptor please remove and re-try"
            sys.exit(1)
        ##################
        # Unpack variables from string
        # Date
        try:
            date = datetime.datetime.strptime(variables[0], "%d%m%y")
        except:
            try:
                date = datetime.datetime.strptime(variable[0], "%d%m%Y")
            except:
                print "Looks like there isn't a date at the start of the histo name..."
                raise
        self._date = date
        
        # Molar ratio (concentration)
        if blank:
            concentration = "0.0"            
        elif pure_lab:
            concentration = ""
        else:
            concentration_field = variables[-2]
            concentration = ".".join(re.findall(r'\d+', concentration_field))
        self._conc = concentration

        # Sample name
        if pure_lab:
            self._sample = "Pure_LAB"
        else:
            self._sample = variables[-1]
        self._identifier = "{0}{1}".format(self._conc, self._sample)

    def estimate_end_point(self):
        """Use the median of the highest 50 events to estimate
        the endpoint
        """
        current_bin = self._histo.FindLastBinAbove(0)
        sum = 0
        x,y = [],[]
        while(sum<75):
            content = self._histo.GetBinContent(current_bin)
            current_bin = current_bin - 1
            if content > 1:
                sum = sum + content
                self._histo.GetBinLowEdge(current_bin), content, sum
                x.append(self._histo.GetBinLowEdge(current_bin))
                y.append(content) 
        self._endpoint_median = ROOT.TMath.Median(len(x), np.array(x), np.array(y))
        self._endpoint_mean = ROOT.TMath.Mean(len(x), np.array(x), np.array(y))
            
    def get_id(self):
        return self._identifier

    def get_concentration(self):
        return self._conc

    def get_sample(self):
        return self._sample

    def get_date(self):
        return self._date

    def get_histo(self):
        return self._histo

    def get_hist_name(self):
        return self._hist_name

    def get_endpoint_median(self):
        return self._endpoint_median

    def get_endpoint_mean(self):
        try:
            return self._endpoint_median
        except:
            _, median = self.estimate_end_point()
            return median

    def get_relative_time(self, units="days"):
        if units == "days":
            return self._relative_time.days
        if units == "hours":
            return self._relative_time.hours

    def set_relative_time(self, time):
        self._relative_time = time

        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser("Reads all spectrum files in a directory and creates histos")
    parser.add_argument("in_file", type=str, help="path to root file generated with summary histos")
    parser.add_argument("out_dir", type=str, help="directory where summary root file will be created")
    parser.add_argument("stabaliser", type=str, help="name of stabaliser used in this test")
    parser.add_argument("te", type=float, help="percentage concentration of Te used in this test")
    parser.add_argument("-p", "--ppo", type=float, help="concentration of PP0 used in g/l [2]",
                        default = 2)
    args = parser.parse_args()

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetTitleStyle(0)

    summary = ROOT.TFile(args.in_file)
    summary.cd()
    
    #################
    # Store measurement objects in an array.
    # Addtionally, define a couple of different
    # dictionaries -  Allows easy searching 
    # as a function of your chosen parameter.
    # 
    data_array = []
    dates, samples = defaultdict(list), defaultdict(list)
    concentrations, ids = defaultdict(list), defaultdict(list)
    for h in summary.GetListOfKeys():
        h = h.ReadObj()
        hist_name = h.GetName()

        data = DataStructure(hist_name, h)
        data_array.append(data)

        dates[data.get_date()].append(data)
        samples[data.get_sample()].append(data)
        concentrations[data.get_concentration()].append(data)
        ids[data.get_id()].append(data)
    # Loop over all data objects to find fist date
    check = datetime.datetime.strptime("31-12-3000", "%d-%m-%Y")
    for data in data_array:
        this_date = data.get_date()
        if this_date < check:
            check = this_date
    # Add a relative time field to the objects
    for data in data_array:
        data.set_relative_time( data.get_date()-check )
    # Sort by date for nice plotting
    data_array.sort(key=lambda x: x.get_date())

    #######################
    # Make output file and put the raw
    # histo's in it.
    #
    out_dir = utils.check_dir(args.out_dir)
    outFile = ROOT.TFile("{0}stabaliser_plots.root".format(out_dir), "recreate")

    for dKey in sorted(dates):
        for sKey in samples:
            # Make title strings and root objects for this loop
            hist = False
            date_str = dKey.strftime("%d/%m/%Y")
            base_name = "{0}_{1}".format(date_str, sKey)
            stack_name = "THStack_{0}".format(base_name)
            stack_title = "{0}% Te, {1}g/l PPO, {2}, {3}, {4}".format(args.te, args.ppo, args.stabaliser, date_str, sKey)
            canvas_name = "TCanvas_{0}".format(base_name)
            stack = ROOT.THStack(stack_name, stack_title)
            legend = ROOT.TLegend(0.65,0.65,0.9,0.9);
            can = ROOT.TCanvas(canvas_name, "c1", 1)

            # Create collections of relavent histograms and measurments
            counter = 1
            endpoints = []
            for data in data_array:
                if(data.get_date() == dKey and data.get_sample() == sKey):
                    hist = data.get_histo()
                    hist.SetLineColor(colors[counter])
                    stack.Add(hist)
                    if data.get_concentration == "":
                        legend_str = "LAB {0}g/l PPO".format(args.ppo)
                    else:
                        legend_str = "{0} {1}:Te".format(data.get_concentration(), args.stabaliser)
                    legend.AddEntry(data.get_histo(), legend_str)
                    counter = counter + 1

            # Possible some measurements were not taken on all dates
            if hist:
                # Formatting
                stack.SetTitle(stack_title)
                stack.Draw("nostack")
                stack.GetXaxis().SetTitle("ADC")
                stack.GetYaxis().SetTitle("Counts / ADC bin")
                stack.SetMinimum(1)
                max_x = round(stack.GetStack().Last().FindLastBinAbove(1)/10.)*10.
                stack.GetXaxis().SetRangeUser(0, max_x)
                can.SetLogy()
                
                # Draw and write
                stack.Write()
                legend.Draw()
                can.Update()
                can.Write()
                can.SaveAs("./results/Spectra_{0}_{1}.png".format(sKey, dKey.strftime("%d%m%y")))
                del can

    ########################
    # Make endpoint vs date plot
    #
    # First make TGraph for each sample concentration
    #
    TGraphs = {}
    graph_legend = ROOT.TLegend(0.80,0.4,0.995,0.9);
    graph_legend.SetFillStyle(0)
    for iKey in sorted(ids):
        graph = ROOT.TGraph()
        # Set marker style by keys
        for i, sKey in enumerate(samples):
            if ids[iKey][0].get_sample() == sKey:
               graph.SetMarkerStyle(markers[i]) 
        # Set line colour by concentration
        for i, cKey in enumerate(concentrations):
            if ids[iKey][0].get_concentration() == cKey:
                graph.SetLineColor(colors[i])
                graph.SetMarkerColor(colors[i])
                graph.SetFillStyle(0)
                graph.SetFillColor(0)
        if ids[iKey][0].get_concentration() == "":
            legend_str = "Pure LAB-PPO".format(ids[iKey][0].get_concentration(), ids[iKey][0].get_sample())
        else:
            legend_str = "{0} molar ratio {1}".format(ids[iKey][0].get_concentration(), ids[iKey][0].get_sample())
        graph_legend.AddEntry(graph, legend_str)
        TGraphs[iKey] = graph

    ###############
    # Fill those graphs
    multiCan = ROOT.TCanvas("TCanvas_Enpoint_vs_date", "multi", 1)
    multiCan.SetRightMargin(0.20);
    for data in data_array:
        this_id =  data.get_id()
        points = TGraphs[this_id].GetN()
        TGraphs[this_id].SetPoint(points, data.get_relative_time(), data.get_endpoint_median())

    ################
    # Put filled graphs into to a multigraph and draw
    multiGraph = ROOT.TMultiGraph()

    for key in sorted(TGraphs):
        multiGraph.Add(TGraphs[key])
    multiGraph.Draw("apl")
    multiGraph.GetXaxis().SetTitle("Time [days]")
    multiGraph.GetYaxis().SetTitle("Estimated Endpoint [ADC units]")
    multiGraph.SetName("TMulti_Endpoints_vs_time")
    graph_legend.Draw()
    multiGraph.Write()
    multiCan.Update()
    multiCan.Write()
    multiCan.SaveAs("./results/Endpoints.png")
