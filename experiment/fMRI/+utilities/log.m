classdef log
methods(Static)

function log = init_log(session,config)
    log = struct();

    log.participant = string(session.participant);
    log.started_at = string(datetime("now", "Format", "yyyyMMdd'T'HHmmss"));

    log.session = struct();
    log.session.seed = session.seed;

    log.session.starting_context = session.starting_context;
    log.session.number_of_decision_trials_per_block = session.number_of_decision_trials_per_block;
    log.session.number_of_trials_per_block = session.number_of_trials_per_block;
    log.session.number_of_blocks = session.number_of_blocks;
    log.session.number_of_trials_total = session.number_of_trials_total;
    log.session.button_mapping = session.button_mapping;
    log.session.keys = config.keys;

    log.trials = repmat(utilities.log.trial_template(), 0, 1);
end


function trialTemplate = trial_template()
    trialTemplate = struct( ...
        'uid', "", ...
        'block_index', [], ...
        'block_family', "", ...
        'context', "", ...
        'frame_color', "", ...
        'trial_role', "", ...
        'trial_index', [], ...
        'rule', "", ...
        'imgs', strings(0, 1), ...
        'correct', "", ...
        'resp', "", ...
        'is_correct', [], ...
        'rt', [], ...
        'all_responses', strings(0, 1), ...
        'all_rts', [], ...
        'stim_onset_rel', [], ...
        'stimulus_info', [] ...
    );
end


function trial = make_trial( ...
    block, trialIndex, ...
    trialData, response, reactionTime, stimulusOnsetTime, experimentStartTime, ...
    allResponses, allReactionTimes)

    trial = utilities.log.trial_template();

    isInitialTrial = (trialIndex == 1);
    display_index = trialIndex - 1; % matlab index starts at 1. I like 0 better.

    trial.block_index = block.block_index;
    trial.block_family = string(block.family);
    trial.uid = utilities.log.make_trial_id(block.block_index, display_index);

    trial.context = string(block.context);
    trial.frame_color = string(block.frame_color);
    trial.trial_role = utilities.log.trial_role_name(isInitialTrial);
    trial.trial_index = display_index;

    trial.rule = utilities.log.get_field_str(trialData, 'rule');
    trial.imgs = utilities.log.get_field_strarr(trialData, 'imgs');
    trial.correct = utilities.log.get_field_str(trialData, 'correct');

    trial.resp          = utilities.log.normalize_response(isInitialTrial, string(response));
    trial.all_responses = utilities.log.normalize_responses(isInitialTrial, allResponses);
    trial.all_rts = allReactionTimes;
    trial.rt = reactionTime;
    trial.is_correct = utilities.log.score(trial.resp, trial.correct);

    trial.stim_onset_rel = stimulusOnsetTime - experimentStartTime;
    trial.stimulus_info = trialData;
end

function name = trial_role_name(isInitialTrial)
    if isInitialTrial
        name = "initial";
    else
        name = "decision";
    end
end


function is_correct = score(resp, correct)
    is_correct = [];
    if correct == "same" || correct == "different"
        is_correct = (resp == correct);
    end
end


function out = get_field_str(s, field)
    out = "";
    if isstruct(s) && isfield(s, field) && ~isempty(s.(field))
        out = string(s.(field));
    end
end


function out = get_field_strarr(s, field)
    out = strings(0, 1);
    if isstruct(s) && isfield(s, field) && ~isempty(s.(field))
        out = string(s.(field));
    end
end


function summary = summarize_trials(trials)
    hasAnswer = arrayfun(@(trial) ~isempty(trial.is_correct), trials);
    decisionTrials = trials(hasAnswer);
    summary.decisionCount = numel(decisionTrials);

    if summary.decisionCount == 0
        summary.correctCount = 0;
        summary.accuracyPercent = NaN;
        summary.meanRt = NaN;
        return
    end

    correctness = [decisionTrials.is_correct];
    reactionTimes = [decisionTrials.rt];

    summary.correctCount = sum(correctness);
    summary.accuracyPercent = 100 * summary.correctCount / summary.decisionCount;
    summary.meanRt = mean(reactionTimes, 'omitnan');
end


function text = format_session_feedback(summary)
    text = sprintf( ...
        ['Session finished!\n\n\n\n' ...
         'Accuracy: %.1f%%\n\n' ...
         'Mean RT:  %.3f s\n\n\n\n' ...
         'Thank you!\n\n\n' ...
         'Press any button to close this screen.'], ...
        summary.accuracyPercent, summary.meanRt);
end
 
 
function save_log(log, sessionPath, session)
    baseDir = fileparts(sessionPath);

    if baseDir == ""
        baseDir = pwd;
    end

    outName = sprintf('log_%s_%s.mat', ...
        string(session.participant), ...
        string(datetime("now", "Format", "yyyyMMdd'T'HHmmss")));

    outPath = fullfile(baseDir, outName);
    save(outPath, 'log');
    fprintf('Saved log: %s\n', outPath);
end

function trialId = make_trial_id(blockId, trialIndex)
    trialId = sprintf('%d_%d', blockId, trialIndex);
end

function resp = normalize_response(isInitialTrial, resp)
    if isInitialTrial && resp ~= "timeout"
        resp = "ready";
    end
end

function responses = normalize_responses(isInitialTrial, responses)
    for i = 1:numel(responses)
        responses(i) = utilities.log.normalize_response(isInitialTrial, responses(i));
    end
end


function print_block_prepare(b, nBlocks, block)
    fprintf('=======================================\n');
    fprintf('Block %d / %d | family: %s | context: %s\n', ...
        b, nBlocks, string(block.family), string(block.context));
    fprintf('=======================================\n');
end


function print_trial(trial)
    if isempty(trial.is_correct)
        correctStr = 'NA';
        marker = '   ';
    elseif trial.is_correct
        correctStr = 'true';
        marker = '   ';
    else
        correctStr = 'FALSE';
        marker = ' ! ';
    end

    fprintf( ...
        '%s [Block %d | Trial %02d] rule=%s resp=%s rt=%.3f correct=%s\n', ...
        marker, ...
        trial.block_index, ...
        trial.trial_index, ...
        char(string(trial.rule)), ...
        char(string(trial.resp)), ...
        trial.rt, ...
        correctStr);
end


function print_block_summary(blockIndex, summary)
    fprintf('\n[Block %d summary]\n', blockIndex);
    fprintf('Trials:   %d decision trials\n', summary.decisionCount);
    fprintf('Correct:  %d\n', summary.correctCount);
    fprintf('Accuracy: %.1f%%\n', summary.accuracyPercent);
    fprintf('Mean RT:  %.3f s\n\n', summary.meanRt);
end

end
end