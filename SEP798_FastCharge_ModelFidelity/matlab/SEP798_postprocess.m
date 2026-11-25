%% SEP798 Final Project - Plan A: model fidelity vs. cost in fast-charge simulation
%  MATLAB post-processing of the PyBaMM results.
%
%  The simulations themselves are run in Python/PyBaMM (folder ../src).
%  This script only reads the exported .mat files in ../results/matlab and
%  re-creates the key figures in MATLAB, plus a small "which model should I
%  use?" helper (select_model.m) that a BMS designer could call.
%
%  How to use:  open this folder in MATLAB and press Run.
%  (To regenerate the .mat files: in ../src run  python export_matlab.py)
%
%  Author: Yuhui (Joe) Wu - SEP798, Fall 2026
clear; clc; close all;

here   = fileparts(mfilename('fullpath'));
matDir = fullfile(here, '..', 'results', 'matlab');
addpath(here);

%% 1) Adequacy maps: where can SPM / SPMe replace DFN?
plot_adequacy_map(matDir, 'charge');
plot_adequacy_map(matDir, 'discharge');

%% 2) Time traces for a few charge cases (DFN vs SPMe vs SPM)
plot_case_traces(matDir, 1.0, 25);
plot_case_traces(matDir, 2.0, 10);
plot_case_traces(matDir, 3.0, 0);

%% 3) Validation against measured LG M50T data
if exist(fullfile(matDir, 'validation.mat'), 'file')
    plot_validation(matDir);
end

%% 4) Model selector examples
cases = [0.5 25; 1.0 0; 1.5 0; 2.0 25; 3.0 25; 3.0 40];
fprintf('\n%-8s %-8s %-6s  %s\n', 'C-rate', 'T [C]', 'Model', 'Reason');
for k = 1:size(cases, 1)
    [m, why] = select_model(cases(k,1), cases(k,2), matDir);
    fprintf('%-8.2f %-8.1f %-6s  %s\n', cases(k,1), cases(k,2), m, why);
end
