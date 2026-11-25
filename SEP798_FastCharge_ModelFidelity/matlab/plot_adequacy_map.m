function plot_adequacy_map(matDir, proto)
% PLOT_ADEQUACY_MAP  Colour map of where SPM / SPMe are adequate substitutes for DFN.
%   proto = 'charge' (CC-CV charge) or 'discharge' (CC discharge)
%   Class: 0 adequate, 1 marginal, 2 inadequate, 3 model breakdown (electrolyte depletion)
S = load(fullfile(matDir, 'adequacy_maps.mat'));
if ~isfield(S, proto)
    warning('No %s map found', proto); return;
end
G = S.(proto);
C = G.Crate(:); T = G.T_amb_C(:);
cmap = [0.047 0.639 0.047;   % adequate   (green)
        0.980 0.698 0.098;   % marginal   (amber)
        0.816 0.231 0.231;   % inadequate (red)
        0.435 0.431 0.412];  % breakdown  (grey)
labels = {'Adequate', 'Marginal', 'Inadequate', 'Breakdown'};
models = {'SPM', 'SPMe'};
figure('Name', ['Adequacy map - ' proto], 'Color', 'w', 'Position', [80 80 1250 520]);
for k = 1:2
    subplot(1, 2, k);
    Z = G.(['class_' models{k}]);
    V = G.(['Vrmse_mV_' models{k}]);
    img = ind2rgb(round(Z) + 1, cmap);
    image(1:numel(T), 1:numel(C), img); axis xy; hold on
    for i = 1:numel(C)
        for j = 1:numel(T)
            if Z(i,j) == 3
                txt = 'fail';
            else
                txt = sprintf('%.0f', V(i,j));
            end
            if Z(i,j) >= 2, col = 'w'; else, col = 'k'; end
            text(j, i, txt, 'HorizontalAlignment', 'center', 'FontSize', 7, 'Color', col);
        end
    end
    set(gca, 'XTick', 1:numel(T), 'XTickLabel', compose_labels(T), ...
             'YTick', 1:numel(C), 'YTickLabel', compose_labels(C));
    xlabel('Ambient temperature [^oC]'); ylabel([upper(proto(1)) proto(2:end) ' C-rate']);
    title(sprintf('%s vs DFN (%s)', models{k}, proto));
end
% legend patches
hold on
h = zeros(1, 4);
for q = 1:4
    h(q) = patch(NaN, NaN, cmap(q,:));
end
legend(h, labels, 'Location', 'southoutside', 'Orientation', 'horizontal');
add_suptitle('Number in cell = voltage RMSE vs DFN [mV]');
end

function c = compose_labels(x)
c = arrayfun(@(v) sprintf('%g', v), x, 'UniformOutput', false);
end
