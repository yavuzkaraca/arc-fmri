function mat2json_trials(logfilesDir)
% Converts each log_p*.mat file under <logfilesDir>/sub-*/ into a
% sibling .json file containing the same content (log.participant,
% log.session, log.trials, log.scanner_sync, ...).
%
% MATLAB's `string` type is not readable by scipy.io.loadmat or mat73,
% since it is serialized as an opaque MCOS object rather than plain text.
% jsonencode natively supports `string`, so this script is the bridge
% that lets the Python side (parse_mat_events.py) work with plain JSON.
%
% Safe to re-run: a .mat file is only re-converted if its .json sibling
% is missing or older than the .mat file, so adding new subjects does
% not require reprocessing existing ones.
%
% Usage (from shell):
%   matlab -batch "mat2json_trials('/path/to/experimental_logfiles')"

if nargin < 1
    % Read environment variables from .env folder in parent directory
    mfile_dir = fileparts(mfilename('fullpath'));
    env_pth = fullfile(mfile_dir, '..', '.env');
    loadenv(env_pth);
    SOURCE_DATA_DIR = getenv('SOURCE_DATA_DIR');
    logfilesDir = fullfile(SOURCE_DATA_DIR, 'experimental_logfiles');
end

matFiles = dir(fullfile(logfilesDir, 'sub-*', 'log_p*.mat'));

fprintf('Found %d log_p*.mat file(s) under %s\n', numel(matFiles), logfilesDir);

for i = 1:numel(matFiles)
    matPath = fullfile(matFiles(i).folder, matFiles(i).name);
    [~, baseName, ~] = fileparts(matFiles(i).name);
    jsonPath = fullfile(matFiles(i).folder, [baseName '.json']);

    if isfile(jsonPath)
        jsonInfo = dir(jsonPath);
        if jsonInfo.datenum >= matFiles(i).datenum
            fprintf('Skipping (up to date): %s\n', matPath);
            continue
        end
    end

    fprintf('Converting: %s\n', matPath);
    data = load(matPath, 'log');
    jsonText = jsonencode(data.log, 'PrettyPrint', true);

    fid = fopen(jsonPath, 'w');
    if fid == -1
        error('Could not open %s for writing.', jsonPath);
    end
    fwrite(fid, jsonText, 'char');
    fclose(fid);

    fprintf('Wrote: %s\n', jsonPath);
end

