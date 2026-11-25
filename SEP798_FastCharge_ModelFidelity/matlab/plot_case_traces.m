function plot_case_traces(matDir, Crate, Tamb)
% PLOT_CASE_TRACES  Voltage, current, temperature, SOC and plating indicator for one CC-CV charge case.
L = load(fullfile(matDir, 'traces_charge.mat'));
runs = L.runs;
models = {'DFN', 'SPMe', 'SPM'};
cols   = {[0.04 0.04 0.04], [0.165 0.471 0.839], [0.922 0.408 0.204]};
styles = {'-', '-', '--'};
figure('Name', sprintf('CC-CV %gC at %g C', Crate, Tamb), 'Color', 'w', 'Position', [100 60 900 820]);
ylabs = {'Voltage [V]', 'Charge current [A]', 'Temperature [^oC]', 'SOC [%]', '\phi_s-\phi_e at sep. [mV]'};
for k = 1:numel(models)
    r = find_run(runs, models{k}, Crate, Tamb);
    if isempty(r) || isempty(r.t), continue; end
    t = r.t / 60;
    sig = {r.V, -r.I, r.T_C, 100*r.SOC, 1e3*r.phi_sep};
    name = models{k};
    if ~strcmp(strtrim(char(r.status)), 'ok'), name = [name ' (breakdown)']; end
    for p = 1:5
        subplot(5, 1, p); hold on; grid on
        plot(t, sig{p}, styles{k}, 'Color', cols{k}, 'LineWidth', 1.6, 'DisplayName', name);
        ylabel(ylabs{p});
    end
end
subplot(5,1,1); legend('Location', 'southeast');
subplot(5,1,5); plot(xlim, [0 0], 'r:'); xlabel('Time [min]');
add_suptitle(sprintf('Yuhui (Joe) Wu - %gC CC-CV charge, ambient %g ^oC', Crate, Tamb));
end
