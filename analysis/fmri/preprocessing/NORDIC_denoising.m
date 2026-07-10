function nii_fpaths_out = NORDIC_denoising(nii_fpaths_in, out_dir, rec_label, overwrite)
% NORDIC_denoising  Run NORDIC on BOLD NIfTIs and write BIDS-valid output.
%
%   Outputs are named with a BIDS "reconstruction" entity (default rec-nordic)
%   inserted at the correct position, e.g.
%       sub-01_task-rest_run-1_bold.nii.gz
%   ->  sub-01_task-rest_run-1_rec-nordic_bold.nii.gz
%   By default the denoised file is written NEXT TO its source file (i.e. into
%   the same raw BIDS func/ folder), which is what "Option A" needs so that
%   fMRIPrep can pick it up from the raw tree via a --bids-filter-file.
%
%   nii_fpaths_out = NORDIC_denoising(nii_fpaths_in, out_dir, rec_label, overwrite)
%
%   nii_fpaths_in : char or cellstr of magnitude BOLD .nii/.nii.gz paths.
%                   If empty, every sub-*/**/func/*_bold.nii.gz under
%                   BIDS_ROOT_DIR (from ../.env) is processed.
%   out_dir       : (optional) target directory for ALL outputs. If omitted or
%                   empty, each output is written beside its source file.
%   rec_label     : (optional) reconstruction label. Default 'nordic'.
%   overwrite     : (optional) logical. If false (default) existing outputs are
%                   skipped, so the script is safe to re-run.
%
%   Returns the full paths of the written (or pre-existing) NORDIC files.

if nargin < 2, out_dir   = ''; end
if nargin < 3 || isempty(rec_label), rec_label = 'nordic'; end
if nargin < 4 || isempty(overwrite), overwrite = false; end

% ---- Resolve inputs -----------------------------------------------------
process_all = isempty(nii_fpaths_in);

if process_all
    loadenv('../.env');
    data_dir = getenv("BIDS_ROOT_DIR");
    if isempty(data_dir)
        error('BIDS_ROOT_DIR is not set in ../.env');
    end
    nii_files = dir(fullfile(data_dir, 'sub-*', '**', 'func', '*_bold.nii.gz'));
    nii_fpaths_in = {};
    for nf_num = 1:numel(nii_files)
        nii_fpaths_in{end+1} = fullfile(nii_files(nf_num).folder, ...
            nii_files(nf_num).name); %#ok<AGROW>
    end
end

if ischar(nii_fpaths_in)
    nii_fpaths_in = {nii_fpaths_in};
end

% Never re-process an already-NORDIC'd file, and (magnitude-only) skip phase.
keep = true(size(nii_fpaths_in));
for k = 1:numel(nii_fpaths_in)
    [~, nm, ~] = fileparts(nii_fpaths_in{k});
    if contains(nm, ['rec-' rec_label]) || contains(nm, 'part-phase')
        keep(k) = false;
    end
end
nii_fpaths_in = nii_fpaths_in(keep);

if ~isempty(out_dir) && ~exist(out_dir, 'dir')
    error('output directory does not exist:\n%s', out_dir);
end

% ---- Fixed NORDIC arguments --------------------------------------------
nordic_args.magnitude_only       = 1;
nordic_args.write_gzipped_niftis = 1;

nii_fpaths_out = cell(size(nii_fpaths_in));

for nf_num = 1:numel(nii_fpaths_in)

    fun_mag   = nii_fpaths_in{nf_num};
    fun_phase = [];

    [src_dir, name, ext] = fileparts(fun_mag);   % ext='.gz', name ends '.nii'
    if endsWith(name, '.nii')
        name = name(1:end-4);
    end

    % BIDS-valid output stem with rec-<label> inserted in canonical order.
    out_stem = bids_insert_rec(name, rec_label);

    % Where to write: beside the source (default) or the shared out_dir.
    if isempty(out_dir)
        target_dir = src_dir;
    else
        target_dir = out_dir;
    end

    out_path = fullfile(target_dir, [out_stem '.nii.gz']);
    nii_fpaths_out{nf_num} = out_path;

    if exist(out_path, 'file') && ~overwrite
        fprintf('[skip] exists: %s\n', out_path);
        continue;
    end

    fprintf('[NORDIC] %s\n     ->  %s\n', fun_mag, out_path);
    nordic_args.DIROUT = [target_dir filesep];
    NIFTI_NORDIC(fun_mag, fun_phase, out_stem, nordic_args);

end

end


% =========================================================================
function out_stem = bids_insert_rec(in_stem, rec_label)
% Insert rec-<label> into a BIDS filename stem at the correct entity position.
% in_stem e.g. 'sub-01_ses-1_task-rest_run-1_bold' (no extension).

tokens = strsplit(in_stem, '_');
suffix = tokens{end};                 % e.g. 'bold' / 'sbref'
ent_tokens = tokens(1:end-1);

% Canonical BIDS entity order (subset relevant to func).
order = {'sub','ses','sample','task','acq','ce','trc','stain','rec', ...
         'dir','run','mod','echo','flip','inv','mt','part','recording','chunk'};

keys = {}; vals = {};
for i = 1:numel(ent_tokens)
    dash = strfind(ent_tokens{i}, '-');
    if isempty(dash)
        % Not a key-value entity (unusual) -- carry through unchanged.
        keys{end+1} = ent_tokens{i}; vals{end+1} = ''; %#ok<AGROW>
    else
        keys{end+1} = ent_tokens{i}(1:dash(1)-1);      %#ok<AGROW>
        vals{end+1} = ent_tokens{i}(dash(1)+1:end);    %#ok<AGROW>
    end
end

% Add or overwrite the reconstruction entity.
idx = find(strcmp(keys, 'rec'), 1);
if isempty(idx)
    keys{end+1} = 'rec'; vals{end+1} = rec_label;
else
    vals{idx} = rec_label;
end

% Reassemble: known entities in canonical order, then any leftovers.
parts = {};
used  = false(size(keys));
for i = 1:numel(order)
    j = find(strcmp(keys, order{i}), 1);
    if ~isempty(j)
        parts{end+1} = entity_str(keys{j}, vals{j}); %#ok<AGROW>
        used(j) = true;
    end
end
for j = 1:numel(keys)
    if ~used(j)
        parts{end+1} = entity_str(keys{j}, vals{j}); %#ok<AGROW>
    end
end

out_stem = sprintf('%s_%s', strjoin(parts, '_'), suffix);
end


function s = entity_str(k, v)
if isempty(v)
    s = k;
else
    s = sprintf('%s-%s', k, v);
end
end
