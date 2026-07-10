function run_nordic_bids(subjects, bids_root)
% run_nordic_bids  Batch NORDIC over the func/ folder(s) of one or more subjects.
%
%   run_nordic_bids                     % all sub-* under BIDS_ROOT_DIR (../.env)
%   run_nordic_bids('sub-03')           % just sub-03
%   run_nordic_bids({'sub-01','sub-07'})% a specific list
%   run_nordic_bids('all', '/data/bids')% all subjects, explicit BIDS root
%
%   For every *_bold.nii.gz found under <sub>/**/func/ this writes a
%   BIDS-valid rec-nordic copy INTO THE SAME func/ folder (Option A). Files
%   that already have a rec-nordic version, or phase images, are skipped, and
%   re-running is safe (existing outputs are not recomputed).
%
%   Requires NIFTI_NORDIC.m and NORDIC_denoising.m on the MATLAB path.

if nargin < 1 || isempty(subjects), subjects = 'all'; end

% ---- Resolve BIDS root --------------------------------------------------
if nargin < 2 || isempty(bids_root)
    loadenv('../.env');
    bids_root = getenv("BIDS_ROOT_DIR");
end
if isempty(bids_root) || ~exist(bids_root, 'dir')
    error('BIDS root not found. Set BIDS_ROOT_DIR in ../.env or pass it in.');
end

% ---- Resolve subject list ----------------------------------------------
if ischar(subjects) && strcmpi(subjects, 'all')
    d = dir(fullfile(bids_root, 'sub-*'));
    subjects = {d([d.isdir]).name};
elseif ischar(subjects)
    subjects = {subjects};
end
% Tolerate ids given with or without the 'sub-' prefix.
for i = 1:numel(subjects)
    if ~startsWith(subjects{i}, 'sub-')
        subjects{i} = ['sub-' subjects{i}];
    end
end

if isempty(subjects)
    warning('No subjects found under %s', bids_root);
    return;
end

fprintf('BIDS root : %s\n', bids_root);
fprintf('Subjects  : %s\n\n', strjoin(subjects, ', '));

% ---- Collect BOLD files, then hand off to NORDIC_denoising --------------
for i = 1:numel(subjects)
    sub = subjects{i};
    files = dir(fullfile(bids_root, sub, '**', 'func', '*_bold.nii.gz'));

    paths = {};
    for k = 1:numel(files)
        nm = files(k).name;
        if contains(nm, 'rec-nordic') || contains(nm, 'part-phase')
            continue;   % already denoised, or phase image
        end
        paths{end+1} = fullfile(files(k).folder, nm); %#ok<AGROW>
    end

    if isempty(paths)
        fprintf('[%s] no BOLD runs to process.\n', sub);
        continue;
    end

    fprintf('[%s] %d run(s) to denoise.\n', sub, numel(paths));
    % out_dir = '' -> write beside each source file (raw func/ folder).
    NORDIC_denoising(paths, '', 'nordic');
end

fprintf('\nDone. rec-nordic files written into each func/ folder.\n');
end
