function run_experiment(sessionPath)
% Run by calling: run_experiment("session.json")

config = utilities.session.default_config();
% Change configurations in utilities.session

try
    session = jsondecode(fileread(sessionPath));
    keys = utilities.session.setup_keys(config, session.button_mapping);
    [window, windowRect] = utilities.screen.setup_window(config);
    textureCache = utilities.session.preload_textures(session, sessionPath, window);
    ctx = utilities.screen.make_ctx(window, windowRect, textureCache, session.button_mapping, keys);

    experimentLog = utilities.log.init_log(session, config);
    [experimentStartTime, scannerSync, eyelink] = prepare_experiment();
    experimentLog.experiment_start_abs = experimentStartTime;

    for blockIndex = 1:numel(session.blocks)
        block = session.blocks(blockIndex);

        utilities.log.print_block_prepare(blockIndex, numel(session.blocks), block);

        blockTrials = run_block(block);

        experimentLog.trials = [experimentLog.trials; blockTrials];
        blockSummary = utilities.log.summarize_trials(blockTrials);
        utilities.log.print_block_summary(blockIndex, blockSummary);
    end

    utilities.screen.fixation_screen(window, windowRect, config.rest_time);

    if config.use_scanner_trigger
        experimentLog.scanner_sync = scannerSync;
    end

    utilities.log.save_log(experimentLog, sessionPath, session);

    if config.eyelink_flag
        fprintf('[EyeLink] Stopping recording...\n');
        utilities.eyelink.stop_recording();
        utilities.eyelink.close(eyelink.edfFile, fileparts(sessionPath));
    end

    % One session-wide feedback screen for the participant at the end.
    sessionSummary = utilities.log.summarize_trials(experimentLog.trials);
    utilities.screen.message_screen( ...
        window, windowRect, utilities.log.format_session_feedback(sessionSummary));
    utilities.screen.wait_key(keys.response, keys.escape);

    Screen('CloseAll');
    fprintf('\nExperiment finished successfully.\n');

catch errorInfo
    utilities.eyelink.emergency_shutdown();
    try Screen('CloseAll'); end %#ok<TRYNC>
    rethrow(errorInfo);
end

% ========================================================================
% Experiment-flow functions
% ========================================================================

function blockTrials = run_block(block)

    blockTrials = repmat(utilities.log.trial_template(), 0, 1);

    utilities.screen.fixation_screen(window, windowRect, config.rest_time);

    for trialIndex = 1:numel(block.trials)
        trial = run_trial(block, trialIndex, block.trials(trialIndex));

        blockTrials(end+1, 1) = trial; %#ok<AGROW>
        utilities.log.print_trial(trial);
    end
end


function trial = run_trial(block, trialIndex, trialData)

    trialId = utilities.log.make_trial_id(block.block_index, trialIndex -1); % matlab index starts at 1. I like 0 better.
    utilities.eyelink.eyelink_trial_id(config, trialId);

    [response, reactionTime, stimulusOnsetTime, allResponses, allReactionTimes] = ...
    utilities.screen.trial_screen(ctx, block, trialIndex, trialData, config.response_time_window);

    trial = utilities.log.make_trial(block, trialIndex, trialData,response, reactionTime, stimulusOnsetTime, ...
        experimentStartTime, allResponses, allReactionTimes);
end


function [experimentStartTime, scannerSync, eyelink] = prepare_experiment()

    fprintf('==============================\n');
    fprintf('Experiment setup\n');
    fprintf('Participant: %s\n', string(session.participant));
    fprintf('==============================\n');

    utilities.screen.message_screen( ...
        window, windowRect, ...
        sprintf(['Experiment setup\n\n' ...
                 'Press any response button when ready.']));

    if config.eyelink_flag
        fprintf('[EyeLink] Opening calibration screen...\n');

        eyelink = utilities.eyelink.setup( ...
            window, windowRect, session.participant);

        utilities.eyelink.calibrate(eyelink);

        fprintf('[EyeLink] Starting recording...\n');
        utilities.eyelink.start_recording();

        utilities.screen.message_screen( ...
            window, windowRect, ...
            sprintf(['Eye tracker calibration is complete.\n\n' ...
                     'Press any response button when ready for the scan.']));
    else
        fprintf('[EyeLink] Disabled.\n');

        utilities.screen.message_screen( ...
            window, windowRect, ...
            sprintf(['Eye tracker calibration is disabled.\n\n' ...
                     'Press any response button when ready for the scan.']));

        eyelink = [];
    end

    fprintf('[Participant] Waiting for readiness button press...\n');
    utilities.screen.wait_key(keys.response, keys.escape);
    fprintf('[Participant] Ready.\n');

    if config.use_scanner_trigger
        scannerSync = struct();
        scannerSync.TR = config.TR;
        scannerSync.n_dummies = config.n_dummies;
        scannerSync.trigger_key_name = string(config.trigger_key_name);
        scannerSync.trigger_times = [];

        utilities.screen.message_screen(window, windowRect, 'Waiting for scanner...');

        fprintf('[Scanner] Waiting for %d dummy triggers...\n', ...
            config.n_dummies);

        for triggerIndex = 1:(config.n_dummies)
            [~, triggerTime] = utilities.screen.wait_key(keys.scannerTrigger, keys.escape);

            scannerSync.trigger_times(end+1, 1) = triggerTime; %#ok<AGROW>

            fprintf('[Scanner] Received dummy trigger %d/%d\n', triggerIndex, config.n_dummies);
        end

        experimentStartTime = triggerTime;
        scannerSync.trigger_times = scannerSync.trigger_times - experimentStartTime;

    else
        scannerSync = [];
        experimentStartTime = GetSecs();

        fprintf('[Scanner] Disabled.\n');
    end

    fprintf('[Experiment] Start time: %.4f\n\n', experimentStartTime);

    if config.eyelink_flag
        utilities.eyelink.msg('EXPERIMENT_START');
    end
end

end

