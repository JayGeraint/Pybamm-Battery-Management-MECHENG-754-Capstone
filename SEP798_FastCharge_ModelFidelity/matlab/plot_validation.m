function plot_validation(matDir)
% PLOT_VALIDATION  Measured LG M50T voltage vs DFN / SPMe / SPM (current-driven, no fitting).
S = load(fullfile(matDir, 'validation.mat'));
sets = {'C10', 'pulse'};
models = {'DFN', 'SPMe', 'SPM'};
cols   = {[0.04 0.04 0.04], [0.165 0.471 0.839], [0.922 0.408 0.204]};
figure('Name', 'Validation vs LG M50T', 'Color', 'w', 'Position', [100 100 1100 700]);
for i = 1:numel(sets)
    if ~isfield(S, sets{i}), continue; end
    d = S.(sets{i});
    subplot(2, 2, 2*i-1); hold on; grid on
    plot(d.data_Q_Ah, d.data_V, 'Color', [0.6 0.6 0.58], 'LineWidth', 3, 'DisplayName', 'Measured');
    for k = 1:numel(models)
        if isfield(d, models{k})
            m = d.(models{k});
            plot(m.Q_dis, m.V, 'Color', cols{k}, 'LineWidth', 1.3, 'DisplayName', models{k});
        end
    end
    xlabel('Discharged capacity [Ah]'); ylabel('Voltage [V]'); title(char(d.name));
    legend('Location', 'southwest');
    subplot(2, 2, 2*i); hold on; grid on
    plot(d.data_t/60, d.data_T_C, 'Color', [0.6 0.6 0.58], 'LineWidth', 3, 'DisplayName', 'Measured');
    for k = 1:numel(models)
        if isfield(d, models{k})
            m = d.(models{k});
            plot(m.t/60, m.T_C, 'Color', cols{k}, 'LineWidth', 1.3, 'DisplayName', models{k});
        end
    end
    xlabel('Time [min]'); ylabel('Temperature [^oC]'); title('Temperature');
end
add_suptitle('Validation against measured LG M50T data (Chen2020 parameters, no fitting)');
end
