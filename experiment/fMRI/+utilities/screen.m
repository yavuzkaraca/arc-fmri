classdef screen
methods(Static)

function [w, rect] = setup_window(config)
    Screen('Preference', 'SkipSyncTests', config.skip_sync_tests);
    Screen('Preference', 'Verbosity', 1);
    AssertOpenGL;

    PsychImaging('PrepareConfiguration');
    screenId = max(Screen('Screens'));

    if config.use_windowed_mode
        [w, rect] = PsychImaging('OpenWindow', screenId, config.bg_color, config.window_rect);
    else
        % Compute size of virtual window if eye-tracker occludes bottom quarter.
        square_win_sz = .85 * config.native_resolution(2);
        % Size of margin on left and right
        margin_sz = (config.native_resolution(1) - square_win_sz) / 2;
        dstRect = [margin_sz, ...
                   config.native_resolution(2) - square_win_sz, ...
                   config.native_resolution(1) - margin_sz, ...
                   config.native_resolution(2)];
        srcRect = [0, 0, config.resolution(1), config.resolution(2)];

        PsychImaging('AddTask', 'General', 'UsePanelFitter', config.resolution, 'Custom', srcRect, dstRect);
        [w, rect] = PsychImaging('OpenWindow', screenId, config.bg_color);
    end

    Screen('ColorRange', w, 1);
    Screen('TextFont', w, 'Arial');
    fprintf('PTB window opened on screen %d.\n', screenId);
end


function [key, time] = wait_key(validKeys, escapeKey)
    KbReleaseWait;
    while true
        [isDown, keyTime, keyCode] = KbCheck;
        if ~isDown, continue; end
        if keyCode(escapeKey), error('Experiment aborted with ESC.'); end
        if any(keyCode(validKeys))
            key = find(keyCode, 1, 'first');
            time = keyTime;
            KbReleaseWait;
            return
        end
    end
end


function message_screen(w, ~, text)
    utilities.screen.clear_screen(w);
    Screen('TextStyle', w, 0);
    Screen('TextSize', w, 34);
    DrawFormattedText(w, char(string(text)), 'center', 'center', [1 1 1]);
    Screen('Flip', w);
end


function clear_screen(w)
    Screen('FillRect', w, [0.15 0.15 0.15]); % for light grayish background
end


function fixation_screen(w, rect, seconds)
    utilities.screen.clear_screen(w);
    crossColor = [1 1 1];
    crossSize = 20;
    lineWidth = 4;

    xCenter = rect(3) / 2;
    yCenter = rect(4) / 2;
    Screen('DrawLine', w, crossColor, xCenter - crossSize, yCenter, xCenter + crossSize, yCenter, lineWidth);
    Screen('DrawLine', w, crossColor, xCenter, yCenter - crossSize, xCenter, yCenter + crossSize, lineWidth);
    WaitSecs('UntilTime', Screen('Flip', w) + seconds);
end


function ctx = make_ctx(w, rect, textureCache, button_mapping, keys)
    % Bundle all session-stable rendering state into context so trial functions stay clean.
    ctx.w            = w;
    ctx.rect         = rect;
    ctx.textureCache = textureCache;
    ctx.button_mapping = button_mapping;
    ctx.sameKey      = keys.sameResponse;
    ctx.differentKey = keys.differentResponse;
    ctx.escapeKey    = keys.escape;
end


function [resp, rt, tOn, allResponses, allRts] = trial_screen(ctx, block, trialIndex, trialData, duration)
    utilities.screen.draw_trial(ctx, block, trialIndex, trialData, "");
    tOn = Screen('Flip', ctx.w);
    [resp, rt, allResponses, allRts] = utilities.screen.collect_responses( ...
        ctx, block, trialIndex, trialData, tOn, duration);
end


function [firstResponse, firstRt, allResponses, allRts] = collect_responses( ...
    ctx, block, trialIndex, trialData, tOn, duration)

    firstResponse        = "timeout";
    firstRt              = NaN;
    allResponses         = strings(0, 1);
    allRts               = [];
    deadline             = tOn + duration;
    previousResponseDown = false;
 
    while GetSecs() < deadline
        [isDown, keyTime, keyCode] = KbCheck;
 
        if ~isDown
            previousResponseDown = false;
            WaitSecs(0.001);
            continue
        end

        if keyCode(ctx.escapeKey), error('Experiment aborted with ESC.'); end

        isNewPress           = (keyCode(ctx.sameKey) || keyCode(ctx.differentKey)) && ~previousResponseDown;
        previousResponseDown =  keyCode(ctx.sameKey) || keyCode(ctx.differentKey);

        if ~isNewPress, continue; end

        responseOptions     = ["same", "different"];
        response            = responseOptions(1 + keyCode(ctx.differentKey));
        rt                  = keyTime - tOn;
        allResponses(end+1) = response; %#ok<AGROW>
        allRts(end+1)       = rt;       %#ok<AGROW>
 
        if firstResponse == "timeout"
            firstResponse = response;
            firstRt       = rt;
            utilities.screen.draw_trial(ctx, block, trialIndex, trialData, response);
            Screen('Flip', ctx.w);
        end
    end
end


function draw_trial(ctx, block, trialIndex, trialData, selectedResponse)
    utilities.screen.clear_screen(ctx.w);
    Screen('FrameRect', ctx.w, utilities.screen.context_frame_rgb(block.frame_color), ctx.rect, 30);
    utilities.screen.draw_header(ctx, block.context, trialIndex, selectedResponse);
    utilities.screen.draw_two_stacked_imgs(ctx, trialData.imgs);
end


function draw_header(ctx, context, trialIndex, selectedResponse)
    [hint, leftText, rightText] = utilities.screen.context_trial_text( ...
        context, trialIndex, ctx.button_mapping);

    Screen('TextStyle', ctx.w, 1);
    Screen('TextSize', ctx.w, 38);
    DrawFormattedText(ctx.w, char(hint), 'center', ctx.rect(4) * 0.12, [1 1 1]);

    Screen('TextStyle', ctx.w, 0);
    Screen('TextSize', ctx.w, 30);
    utilities.screen.draw_response_tip(ctx, selectedResponse, leftText, rightText);
end


function draw_response_tip(ctx, selectedResponse, leftText, rightText)
    y          = ctx.rect(4) * 0.18;
    leftColor  = [1 1 1];
    rightColor = [1 1 1];
    same_is_left = strcmp(string(ctx.button_mapping.same), 'left');

    if selectedResponse == "same"
        if same_is_left, leftColor  = [1 1 0]; else, rightColor = [1 1 0]; end
    elseif selectedResponse == "different"
        if same_is_left, rightColor = [1 1 0]; else, leftColor  = [1 1 0]; end
    end

    centerX = ctx.rect(3) / 2;
    gap     = ctx.rect(3) * 0.08;
    DrawFormattedText(ctx.w, char(leftText),  'right',      y, leftColor,  [], [], [], [], [], ...
        [0 0 centerX - gap ctx.rect(4)]);
    DrawFormattedText(ctx.w, char(rightText), centerX + gap, y, rightColor);
end


function [hint, leftText, rightText] = context_trial_text(context, trialIndex, button_mapping)
    switch context
        case 'inference',   hint = "Previous";
        case 'application', hint = "First";
    end

    if trialIndex == 1
        leftText  = "←   Ready";
        rightText = "Ready   →";

    elseif strcmp(string(button_mapping.same), 'left')
        leftText  = "←   Same";
        rightText = "Different   →";
    else
        leftText  = "←   Different";
        rightText = "Same   →";
    end
end


function draw_two_stacked_imgs(ctx, imgsField)
    topTexture    = ctx.textureCache(char(imgsField{1}));
    bottomTexture = ctx.textureCache(char(imgsField{2}));

    gap         = ctx.rect(4) * 0.06;
    imageWidth  = ctx.rect(3) * 0.80;
    imageHeight = ctx.rect(4) * 0.30;
    topLimit    = ctx.rect(4) * 0.22;
    bottomLimit = ctx.rect(4) * 0.94;

    scale       = min(1, (bottomLimit - topLimit) / (2 * imageHeight + gap));
    imageWidth  = imageWidth  * scale;
    imageHeight = imageHeight * scale;

    centerX = ctx.rect(3) / 2;
    centerY = (topLimit + bottomLimit) / 2;

    Screen('DrawTexture', ctx.w, topTexture,    [], ...
        CenterRectOnPointd([0 0 imageWidth imageHeight], centerX, centerY - imageHeight/2 - gap/2));
    Screen('DrawTexture', ctx.w, bottomTexture, [], ...
        CenterRectOnPointd([0 0 imageWidth imageHeight], centerX, centerY + imageHeight/2 + gap/2));
end


function rgb = context_frame_rgb(frame_color)
    luminosity = 0.4;
    switch string(frame_color)
        case "yellow", baseRgb = [1 1 0];
        case "cyan",   baseRgb = [0 1 1];
        otherwise,     rgb = [0 0 0]; return
    end
    hsv = rgb2hsv(baseRgb);
    hsv(3) = luminosity;
    rgb = hsv2rgb(hsv);
end


end
end