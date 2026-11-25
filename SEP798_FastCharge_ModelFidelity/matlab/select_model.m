function [model, reason] = select_model(Crate, Tamb, matDir)
% SELECT_MODEL  Cheapest model that is still an adequate substitute for DFN for a CC-CV charge.
%   [model, reason] = select_model(Crate, Tamb_degC, matDir)
%   Uses the simulated adequacy map.  To stay on the safe side the query is
%   rounded to the next HIGHER C-rate and the next LOWER ambient temperature on the grid.
if nargin < 3
    matDir = fullfile(fileparts(mfilename('fullpath')), '..', 'results', 'matlab');
end
S = load(fullfile(matDir, 'adequacy_maps.mat'));
G = S.charge;
C = G.Crate(:); T = G.T_amb_C(:);
i = find(C >= Crate - 1e-9, 1, 'first');
j = find(T <= Tamb + 1e-9, 1, 'last');
if isempty(i) || isempty(j)
    model = 'DFN';
    reason = 'outside the simulated range (0.5-3C, 0-40 C): use the full model';
    return
end
if G.class_SPM(i, j) == 0
    model = 'SPM';
    reason = sprintf('SPM adequate (V RMSE %.0f mV)', G.Vrmse_mV_SPM(i, j));
elseif G.class_SPMe(i, j) == 0
    model = 'SPMe';
    reason = sprintf('SPMe adequate (V RMSE %.0f mV, |dT_peak| %.1f K); SPM V RMSE %.0f mV', ...
        G.Vrmse_mV_SPMe(i, j), abs(G.Tpeak_err_K_SPMe(i, j)), G.Vrmse_mV_SPM(i, j));
elseif G.class_SPMe(i, j) == 3
    model = 'DFN';
    reason = sprintf('SPMe breaks down (electrolyte depletion; DFN min c_e = %.0f mol/m^3)', G.ce_min_DFN(i, j));
else
    model = 'DFN';
    reason = 'reduced models outside error thresholds';
end
end
