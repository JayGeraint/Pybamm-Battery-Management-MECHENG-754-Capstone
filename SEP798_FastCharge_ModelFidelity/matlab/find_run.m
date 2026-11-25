function r = find_run(runs, model, value, Tamb)
% FIND_RUN  Return the run struct for (model, C-rate or UDDS scale, ambient T), or [] if absent.
r = [];
for k = 1:numel(runs)
    s = runs(k);
    if strcmp(strtrim(char(s.model)), model) && abs(double(s.value) - value) < 1e-9 ...
            && abs(double(s.T_amb_C) - Tamb) < 1e-9
        r = s; return;
    end
end
end
