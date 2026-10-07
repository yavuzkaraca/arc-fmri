function run_nordic_bids(subjects, bids_root, use_phase)
% run_nordic_bids  Batch NORDIC over the func/ folder(s) of one or more subjects.
%
%   run_nordic_bids                     % all sub-* under BIDS_ROOT_DIR (../.env)
%   run_nordic_bids('sub-03')           % just sub-03
%   run_nordic_bids({'sub-01','sub-07'})% a specific list
%   run_nordic_bids('all', '/data/bids')% all subjects, explicit BIDS root
%   run_nordic_bids('sub-03', '', true) % also use phase images if available
%
%   For every magnitude *_bold.nii.gz found under <sub>/**/func/ this writes a
%   BIDS-valid denoised copy INTO THE SAME func/ folder (Option A). Existing
%   rec-nordic* files are never used as inputs and phase images are never
%   denoised on their own; re-running is safe (existing outputs are not
%   recomputed).
%
%   use_phase (default false):
%     false -> magnitude-only NORDIC, output rec-nordic.
%     true  -> the matching part-phase image is passed to NORDIC when it
%              exists, output rec-nordicphase; runs without a phase image
%              fall back to magnitude-only (rec-nordic).
%   The two labels coexist, so running once with each setting gives both
%   versions side by side for comparison.
%
%   Requires NIFTI_NORDIC.m and NORDIC_denoising.m on the MATLAB path.

if nargin < 1 || isempty(subjects), subjects = 'all'; end
if nargin < 3 || isempty(use_phase), use_phase = false; end

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
fprintf('Subjects  : %s\n', strjoin(subjects, ', '));
fprintf('Use phase : %d\n\n', use_phase);

% ---- Collect BOLD files, then hand off to NORDIC_denoising --------------
for i = 1:numel(subjects)
    sub = subjects{i};
    files = dir(fullfile(bids_root, sub, '**', 'func', '*_bold.nii.gz'));

    paths = {};
    for k = 1:numel(files)
        nm = files(k).name;
        if contains(nm, 'rec-nordic') || contains(nm, 'part-phase')
            % Already denoised, or a phase image (phase is paired with its
            % magnitude run inside NORDIC_denoising when use_phase is set).
            continue;
        end
        paths{end+1} = fullfile(files(k).folder, nm); %#ok<AGROW>
    end

    if isempty(paths)
        fprintf('[%s] no BOLD runs to process.\n', sub);
        continue;
    end

    fprintf('[%s] %d run(s) to denoise.\n', sub, numel(paths));
    % out_dir = '' -> write beside each source file (raw func/ folder).
    NORDIC_denoising(paths, '', 'nordic', false, use_phase);
end

fprintf('\nDone. rec-nordic* files written into each func/ folder.\n');
end
