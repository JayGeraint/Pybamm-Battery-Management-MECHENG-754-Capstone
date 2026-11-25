function add_suptitle(txt)
% ADD_SUPTITLE  sgtitle if available (MATLAB R2018b+), otherwise a figure annotation (Octave).
if exist('sgtitle', 'file') || exist('sgtitle', 'builtin')
    sgtitle(txt);
else
    annotation('textbox', [0 0.95 1 0.05], 'String', txt, 'EdgeColor', 'none', ...
               'HorizontalAlignment', 'center', 'FontWeight', 'bold');
end
end
