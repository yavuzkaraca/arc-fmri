
classdef session
methods(Static)

function config = default_config()
    config = struct();

    % ---- general config ----
    config.skip_sync_tests = 0; % 0 in production
    config.rest_time = 5; % 5 in production
    config.response_time_window = 10; % 10 in production

    % ---- screen config ----
    config.use_windowed_mode = false;  % false in production
    config.window_rect = [50 50 1350 1350]; % [X_start Y_start X_end Y_end]
    config.resolution = [1300 1300];
    config.bg_color = [25 25 25]; % for grayish background
    
    % Native resolution of display device
    config.native_resolution = [1920, 1080];     % in 3T lab
    % config.native_resolution = [1600, 1200];    % at desktop
    % config.native_resolution = [3440, 1440];    % at brunsstr


    % ---- response keys ----
    config.keys.same      = '4$'; % left button. 
    config.keys.different = '3#'; % right button. 
    % 3T lab keyboard for RIGHT hand has '4$' on index finger (left-most button) and '3#' on middle finger (second-from-left button).
    % For standard keyboard swap them.

    % ---- EyeLink config ----
    config.eyelink_flag = 1;  % 1 in production

    % ---- scanner config ----
    config.use_scanner_trigger = true;
    config.trigger_key_name = 'w';
    config.TR = 2.0;
    config.dummy_seconds = 10;
    config.n_dummies = ceil(config.dummy_seconds / config.TR);
end


function keys = setup_keys(config)
    KbName('UnifyKeyNames');
 
    keys.sameResponse      = KbName(config.keys.same);
    keys.differentResponse = KbName(config.keys.different);
    keys.escape            = KbName('ESCAPE');
    keys.scannerTrigger    = KbName(config.trigger_key_name);
    keys.response          = [keys.sameResponse keys.differentResponse];
end

function texCache = preload_textures(session, sessionPath, w)

    fprintf('Preloading images...\n');

    baseDir = fileparts(sessionPath);
    if isempty(baseDir), baseDir = pwd; end

    allImgs = {};
    for b = 1:numel(session.blocks)
        for t = 1:numel(session.blocks(b).trials)
            allImgs = [allImgs; session.blocks(b).trials(t).imgs(:)]; %#ok<AGROW>
        end
    end

    allImgs = unique(allImgs, 'stable');
    texCache = containers.Map();

    for i = 1:numel(allImgs)
        rel = allImgs{i};
        im = imread(fullfile(baseDir, rel));
        texCache(rel) = Screen('MakeTexture', w, im);
    end

    fprintf('Image preloading finished.\n');
end

end
end