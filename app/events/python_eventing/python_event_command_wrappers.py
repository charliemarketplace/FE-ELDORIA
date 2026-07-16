
###############################################################################################################################
# This code was generated using `source_generator.py`. DO NOT MAKE ANY EDITS TO THIS FILE - YOUR CHANGES WILL BE OVERWRITTEN. #
###############################################################################################################################
from typing import Any, Callable, List, Tuple
from .. import event_commands, event_validators

def optional_value_filter(required_keywords: List[str]) -> Callable[[Tuple[str, Any]], bool]:
    # pair is a (key, value) pair
    return lambda pair: (pair[0] in required_keywords) or (pair[1] is not None)
def music(Music, FadeIn=None, ):
    command_t = event_commands.Music
    parameters = {"Music": Music, "FadeIn": FadeIn}
    parameters = dict(filter(optional_value_filter(["Music"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def music_fade_back(FadeOut=None, ):
    command_t = event_commands.MusicFadeBack
    parameters = {"FadeOut": FadeOut}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def music_clear(FadeOut=None, ):
    command_t = event_commands.MusicClear
    parameters = {"FadeOut": FadeOut}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def sound(Sound, Volume=None, ):
    command_t = event_commands.Sound
    parameters = {"Sound": Sound, "Volume": Volume}
    parameters = dict(filter(optional_value_filter(["Sound"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def stop_sound(Sound, ):
    command_t = event_commands.StopSound
    parameters = {"Sound": Sound}
    parameters = dict(filter(optional_value_filter(["Sound"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_music(Phase, Music, ):
    command_t = event_commands.ChangeMusic
    parameters = {"Phase": Phase, "Music": Music}
    parameters = dict(filter(optional_value_filter(["Phase", "Music"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_special_music(SpecialMusicType, Music, ):
    command_t = event_commands.ChangeSpecialMusic
    parameters = {"SpecialMusicType": SpecialMusicType, "Music": Music}
    parameters = dict(filter(optional_value_filter(["SpecialMusicType", "Music"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_portrait(Portrait, ScreenPosition, Slide=None, ExpressionList=None, SpeedMult=None, ):
    command_t = event_commands.AddPortrait
    parameters = {"Portrait": Portrait, "ScreenPosition": ScreenPosition, "Slide": Slide, "ExpressionList": ExpressionList, "SpeedMult": SpeedMult}
    parameters = dict(filter(optional_value_filter(["Portrait", "ScreenPosition"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def multi_add_portrait(Portrait1, ScreenPosition1, Portrait2, ScreenPosition2, Portrait3=None, ScreenPosition3=None, Portrait4=None, ScreenPosition4=None, ):
    command_t = event_commands.MultiAddPortrait
    parameters = {"Portrait1": Portrait1, "ScreenPosition1": ScreenPosition1, "Portrait2": Portrait2, "ScreenPosition2": ScreenPosition2, "Portrait3": Portrait3, "ScreenPosition3": ScreenPosition3, "Portrait4": Portrait4, "ScreenPosition4": ScreenPosition4}
    parameters = dict(filter(optional_value_filter(["Portrait1", "ScreenPosition1", "Portrait2", "ScreenPosition2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_portrait(Portrait, SpeedMult=None, Slide=None, ):
    command_t = event_commands.RemovePortrait
    parameters = {"Portrait": Portrait, "SpeedMult": SpeedMult, "Slide": Slide}
    parameters = dict(filter(optional_value_filter(["Portrait"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def multi_remove_portrait(Portrait1, Portrait2, Portrait3=None, Portrait4=None, ):
    command_t = event_commands.MultiRemovePortrait
    parameters = {"Portrait1": Portrait1, "Portrait2": Portrait2, "Portrait3": Portrait3, "Portrait4": Portrait4}
    parameters = dict(filter(optional_value_filter(["Portrait1", "Portrait2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def move_portrait(Portrait, ScreenPosition, SpeedMult=None, ):
    command_t = event_commands.MovePortrait
    parameters = {"Portrait": Portrait, "ScreenPosition": ScreenPosition, "SpeedMult": SpeedMult}
    parameters = dict(filter(optional_value_filter(["Portrait", "ScreenPosition"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def bop_portrait(Portrait, ):
    command_t = event_commands.BopPortrait
    parameters = {"Portrait": Portrait}
    parameters = dict(filter(optional_value_filter(["Portrait"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def mirror_portrait(Portrait, SpeedMult=None, ):
    command_t = event_commands.MirrorPortrait
    parameters = {"Portrait": Portrait, "SpeedMult": SpeedMult}
    parameters = dict(filter(optional_value_filter(["Portrait"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def expression(Portrait, ExpressionList, ):
    command_t = event_commands.Expression
    parameters = {"Portrait": Portrait, "ExpressionList": ExpressionList}
    parameters = dict(filter(optional_value_filter(["Portrait", "ExpressionList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def speak_style(Style, Speaker=None, Position=None, Width=None, Speed=None, FontColor=None, FontType=None, Background=None, NumLines=None, DrawCursor=None, MessageTail=None, Transparency=None, NameTagBg=None, BoopSound=None, ):
    command_t = event_commands.SpeakStyle
    parameters = {"Style": Style, "Speaker": Speaker, "Position": Position, "Width": Width, "Speed": Speed, "FontColor": FontColor, "FontType": FontType, "Background": Background, "NumLines": NumLines, "DrawCursor": DrawCursor, "MessageTail": MessageTail, "Transparency": Transparency, "NameTagBg": NameTagBg, "BoopSound": BoopSound}
    parameters = dict(filter(optional_value_filter(["Style"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def speak(SpeakerOrStyle, Text, TextPosition=None, Width=None, StyleNid=None, TextSpeed=None, FontColor=None, FontType=None, DialogBox=None, NumLines=None, DrawCursor=None, MessageTail=None, Transparency=None, NameTagBg=None, BoopSound=None, ):
    command_t = event_commands.Speak
    parameters = {"SpeakerOrStyle": SpeakerOrStyle, "Text": Text, "TextPosition": TextPosition, "Width": Width, "StyleNid": StyleNid, "TextSpeed": TextSpeed, "FontColor": FontColor, "FontType": FontType, "DialogBox": DialogBox, "NumLines": NumLines, "DrawCursor": DrawCursor, "MessageTail": MessageTail, "Transparency": Transparency, "NameTagBg": NameTagBg, "BoopSound": BoopSound}
    parameters = dict(filter(optional_value_filter(["SpeakerOrStyle", "Text"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def say(SpeakerOrStyle, *Text, TextPosition=None, Width=None, StyleNid=None, TextSpeed=None, FontColor=None, FontType=None, DialogBox=None, NumLines=None, DrawCursor=None, MessageTail=None, Transparency=None, NameTagBg=None, BoopSound=None, ):
    command_t = event_commands.Say
    parameters = {"SpeakerOrStyle": SpeakerOrStyle, "Text": Text, "TextPosition": TextPosition, "Width": Width, "StyleNid": StyleNid, "TextSpeed": TextSpeed, "FontColor": FontColor, "FontType": FontType, "DialogBox": DialogBox, "NumLines": NumLines, "DrawCursor": DrawCursor, "MessageTail": MessageTail, "Transparency": Transparency, "NameTagBg": NameTagBg, "BoopSound": BoopSound}
    parameters = dict(filter(optional_value_filter(["SpeakerOrStyle", "*Text"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def unhold(Nid, ):
    command_t = event_commands.Unhold
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def unpause(Nid=None, ):
    command_t = event_commands.Unpause
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def transition(Direction=None, Speed=None, Color3=None, Panorama=None, ):
    command_t = event_commands.Transition
    parameters = {"Direction": Direction, "Speed": Speed, "Color3": Color3, "Panorama": Panorama}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_background(Panorama=None, ):
    command_t = event_commands.ChangeBackground
    parameters = {"Panorama": Panorama}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def pause_background(PauseAt=None, ):
    command_t = event_commands.PauseBackground
    parameters = {"PauseAt": PauseAt}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def unpause_background():
    command_t = event_commands.UnpauseBackground
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def disp_cursor(ShowCursor, ):
    command_t = event_commands.DispCursor
    parameters = {"ShowCursor": ShowCursor}
    parameters = dict(filter(optional_value_filter(["ShowCursor"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def move_cursor(Position, Speed=None, ):
    command_t = event_commands.MoveCursor
    parameters = {"Position": Position, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def center_cursor(Position, Speed=None, ):
    command_t = event_commands.CenterCursor
    parameters = {"Position": Position, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def flicker_cursor(Position, ):
    command_t = event_commands.FlickerCursor
    parameters = {"Position": Position}
    parameters = dict(filter(optional_value_filter(["Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def screen_shake(Duration, ShakeType=None, ):
    command_t = event_commands.ScreenShake
    parameters = {"Duration": Duration, "ShakeType": ShakeType}
    parameters = dict(filter(optional_value_filter(["Duration"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def screen_shake_end():
    command_t = event_commands.ScreenShakeEnd
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def game_var(Nid, Expression, ):
    command_t = event_commands.GameVar
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def inc_game_var(Nid, Expression=None, ):
    command_t = event_commands.IncGameVar
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def level_var(Nid, Expression, ):
    command_t = event_commands.LevelVar
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def inc_level_var(Nid, Expression=None, ):
    command_t = event_commands.IncLevelVar
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_next_chapter(Chapter, ):
    command_t = event_commands.SetNextChapter
    parameters = {"Chapter": Chapter}
    parameters = dict(filter(optional_value_filter(["Chapter"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def enable_convoy(Activated, ):
    command_t = event_commands.EnableConvoy
    parameters = {"Activated": Activated}
    parameters = dict(filter(optional_value_filter(["Activated"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def enable_repair_shop(Activated, ):
    command_t = event_commands.EnableRepairShop
    parameters = {"Activated": Activated}
    parameters = dict(filter(optional_value_filter(["Activated"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def enable_supports(Activated, ):
    command_t = event_commands.EnableSupports
    parameters = {"Activated": Activated}
    parameters = dict(filter(optional_value_filter(["Activated"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def enable_turnwheel(Activated, ):
    command_t = event_commands.EnableTurnwheel
    parameters = {"Activated": Activated}
    parameters = dict(filter(optional_value_filter(["Activated"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def enable_fog_of_war(Activated, ):
    command_t = event_commands.EnableFogOfWar
    parameters = {"Activated": Activated}
    parameters = dict(filter(optional_value_filter(["Activated"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_fog_of_war(FogOfWarType, Radius, AIRadius=None, OtherRadius=None, ):
    command_t = event_commands.SetFogOfWar
    parameters = {"FogOfWarType": FogOfWarType, "Radius": Radius, "AIRadius": AIRadius, "OtherRadius": OtherRadius}
    parameters = dict(filter(optional_value_filter(["FogOfWarType", "Radius"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def end_turn(Team=None, ):
    command_t = event_commands.EndTurn
    parameters = {"Team": Team}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def win_game():
    command_t = event_commands.WinGame
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def lose_game():
    command_t = event_commands.LoseGame
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def main_menu():
    command_t = event_commands.MainMenu
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def force_chapter_clean_up():
    command_t = event_commands.ForceChapterCleanUp
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def skip_save(TrueOrFalse, ):
    command_t = event_commands.SkipSave
    parameters = {"TrueOrFalse": TrueOrFalse}
    parameters = dict(filter(optional_value_filter(["TrueOrFalse"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def activate_turnwheel(Force=None, ):
    command_t = event_commands.ActivateTurnwheel
    parameters = {"Force": Force}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def battle_save():
    command_t = event_commands.BattleSave
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def delete_save(SaveSlot=None, ):
    command_t = event_commands.DeleteSave
    parameters = {"SaveSlot": SaveSlot}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def clear_turnwheel():
    command_t = event_commands.ClearTurnwheel
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def stop_turnwheel_recording():
    command_t = event_commands.StopTurnwheelRecording
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def start_turnwheel_recording():
    command_t = event_commands.StartTurnwheelRecording
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_tilemap(Tilemap, PositionOffset=None, LoadTilemap=None, ):
    command_t = event_commands.ChangeTilemap
    parameters = {"Tilemap": Tilemap, "PositionOffset": PositionOffset, "LoadTilemap": LoadTilemap}
    parameters = dict(filter(optional_value_filter(["Tilemap"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_bg_tilemap(Tilemap=None, ):
    command_t = event_commands.ChangeBgTilemap
    parameters = {"Tilemap": Tilemap}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_game_board_bounds(MinX, MinY, MaxX, MaxY, ):
    command_t = event_commands.SetGameBoardBounds
    parameters = {"MinX": MinX, "MinY": MinY, "MaxX": MaxX, "MaxY": MaxY}
    parameters = dict(filter(optional_value_filter(["MinX", "MinY", "MaxX", "MaxY"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_game_board_bounds():
    command_t = event_commands.RemoveGameBoardBounds
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def load_unit(UniqueUnit, Team=None, AI=None, ):
    command_t = event_commands.LoadUnit
    parameters = {"UniqueUnit": UniqueUnit, "Team": Team, "AI": AI}
    parameters = dict(filter(optional_value_filter(["UniqueUnit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def make_generic(Nid, Klass, Level, Team, AI=None, Faction=None, AnimationVariant=None, ItemList=None, ):
    command_t = event_commands.MakeGeneric
    parameters = {"Nid": Nid, "Klass": Klass, "Level": Level, "Team": Team, "AI": AI, "Faction": Faction, "AnimationVariant": AnimationVariant, "ItemList": ItemList}
    parameters = dict(filter(optional_value_filter(["Nid", "Klass", "Level", "Team"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def create_unit(Unit, Nid=None, Level=None, Position=None, EntryType=None, Placement=None, ):
    command_t = event_commands.CreateUnit
    parameters = {"Unit": Unit, "Nid": Nid, "Level": Level, "Position": Position, "EntryType": EntryType, "Placement": Placement}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_unit(Unit, Position=None, EntryType=None, Placement=None, AnimationType=None, ):
    command_t = event_commands.AddUnit
    parameters = {"Unit": Unit, "Position": Position, "EntryType": EntryType, "Placement": Placement, "AnimationType": AnimationType}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def move_unit(Unit, Position=None, MovementType=None, Placement=None, Speed=None, ):
    command_t = event_commands.MoveUnit
    parameters = {"Unit": Unit, "Position": Position, "MovementType": MovementType, "Placement": Placement, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_unit(Unit, RemoveType=None, AnimationType=None, ):
    command_t = event_commands.RemoveUnit
    parameters = {"Unit": Unit, "RemoveType": RemoveType, "AnimationType": AnimationType}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def kill_unit(Unit, ):
    command_t = event_commands.KillUnit
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_all_units():
    command_t = event_commands.RemoveAllUnits
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_all_enemies():
    command_t = event_commands.RemoveAllEnemies
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def interact_unit(Unit, Position, CombatScript=None, Ability=None, Rounds=None, ):
    command_t = event_commands.InteractUnit
    parameters = {"Unit": Unit, "Position": Position, "CombatScript": CombatScript, "Ability": Ability, "Rounds": Rounds}
    parameters = dict(filter(optional_value_filter(["Unit", "Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_name(Unit, String, ):
    command_t = event_commands.SetName
    parameters = {"Unit": Unit, "String": String}
    parameters = dict(filter(optional_value_filter(["Unit", "String"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_variant(Unit, String=None, ):
    command_t = event_commands.SetVariant
    parameters = {"Unit": Unit, "String": String}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_current_hp(Unit, HP, ):
    command_t = event_commands.SetCurrentHP
    parameters = {"Unit": Unit, "HP": HP}
    parameters = dict(filter(optional_value_filter(["Unit", "HP"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_current_mana(Unit, Mana, ):
    command_t = event_commands.SetCurrentMana
    parameters = {"Unit": Unit, "Mana": Mana}
    parameters = dict(filter(optional_value_filter(["Unit", "Mana"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_fatigue(Unit, Fatigue, ):
    command_t = event_commands.AddFatigue
    parameters = {"Unit": Unit, "Fatigue": Fatigue}
    parameters = dict(filter(optional_value_filter(["Unit", "Fatigue"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_unit_field(GlobalUnit, Key, Value, ):
    command_t = event_commands.SetUnitField
    parameters = {"GlobalUnit": GlobalUnit, "Key": Key, "Value": Value}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Key", "Value"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_unit_note(Unit, Key, Value, ):
    command_t = event_commands.SetUnitNote
    parameters = {"Unit": Unit, "Key": Key, "Value": Value}
    parameters = dict(filter(optional_value_filter(["Unit", "Key", "Value"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_unit_note(Unit, Key, ):
    command_t = event_commands.RemoveUnitNote
    parameters = {"Unit": Unit, "Key": Key}
    parameters = dict(filter(optional_value_filter(["Unit", "Key"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def resurrect(GlobalUnit, ):
    command_t = event_commands.Resurrect
    parameters = {"GlobalUnit": GlobalUnit}
    parameters = dict(filter(optional_value_filter(["GlobalUnit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def reset(Unit, ):
    command_t = event_commands.Reset
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def has_attacked(Unit, ):
    command_t = event_commands.HasAttacked
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def has_traded(Unit, ):
    command_t = event_commands.HasTraded
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def has_finished(Unit, ):
    command_t = event_commands.HasFinished
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def recruit_generic(Unit, Nid, Name=None, ):
    command_t = event_commands.RecruitGeneric
    parameters = {"Unit": Unit, "Nid": Nid, "Name": Name}
    parameters = dict(filter(optional_value_filter(["Unit", "Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_group(Group, StartingGroup=None, EntryType=None, Placement=None, ):
    command_t = event_commands.AddGroup
    parameters = {"Group": Group, "StartingGroup": StartingGroup, "EntryType": EntryType, "Placement": Placement}
    parameters = dict(filter(optional_value_filter(["Group"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def spawn_group(Group, CardinalDirection, StartingGroup, MovementType=None, Placement=None, ):
    command_t = event_commands.SpawnGroup
    parameters = {"Group": Group, "CardinalDirection": CardinalDirection, "StartingGroup": StartingGroup, "MovementType": MovementType, "Placement": Placement}
    parameters = dict(filter(optional_value_filter(["Group", "CardinalDirection", "StartingGroup"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def move_group(Group, StartingGroup, MovementType=None, Placement=None, ):
    command_t = event_commands.MoveGroup
    parameters = {"Group": Group, "StartingGroup": StartingGroup, "MovementType": MovementType, "Placement": Placement}
    parameters = dict(filter(optional_value_filter(["Group", "StartingGroup"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_group(Group, RemoveType=None, ):
    command_t = event_commands.RemoveGroup
    parameters = {"Group": Group, "RemoveType": RemoveType}
    parameters = dict(filter(optional_value_filter(["Group"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def give_item(GlobalUnitOrConvoy, Item, Party=None, ):
    command_t = event_commands.GiveItem
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "Party": Party}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def equip_item(GlobalUnit, Item, ):
    command_t = event_commands.EquipItem
    parameters = {"GlobalUnit": GlobalUnit, "Item": Item}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Item"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_item(GlobalUnitOrConvoy, Item, Party=None, ):
    command_t = event_commands.RemoveItem
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "Party": Party}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def move_item(Giver, Receiver, Item=None, ):
    command_t = event_commands.MoveItem
    parameters = {"Giver": Giver, "Receiver": Receiver, "Item": Item}
    parameters = dict(filter(optional_value_filter(["Giver", "Receiver"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def move_item_between_convoys(Item, Party1, Party2, ):
    command_t = event_commands.MoveItemBetweenConvoys
    parameters = {"Item": Item, "Party1": Party1, "Party2": Party2}
    parameters = dict(filter(optional_value_filter(["Item", "Party1", "Party2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def open_convoy(GlobalUnit, ):
    command_t = event_commands.OpenConvoy
    parameters = {"GlobalUnit": GlobalUnit}
    parameters = dict(filter(optional_value_filter(["GlobalUnit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_item_uses(GlobalUnitOrConvoy, Item, Uses, ):
    command_t = event_commands.SetItemUses
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "Uses": Uses}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item", "Uses"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_item_data(GlobalUnitOrConvoy, Item, Nid, Expression, ):
    command_t = event_commands.SetItemData
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item", "Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_item_droppable(GlobalUnit, Item, Droppable, ):
    command_t = event_commands.SetItemDroppable
    parameters = {"GlobalUnit": GlobalUnit, "Item": Item, "Droppable": Droppable}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Item", "Droppable"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def break_item(GlobalUnitOrConvoy, Item, ):
    command_t = event_commands.BreakItem
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_item_name(GlobalUnitOrConvoy, Item, String, ):
    command_t = event_commands.ChangeItemName
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "String": String}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item", "String"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_item_desc(GlobalUnitOrConvoy, Item, String, ):
    command_t = event_commands.ChangeItemDesc
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "String": String}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item", "String"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_item_to_multiitem(GlobalUnitOrConvoy, MultiItem, ChildItem, ):
    command_t = event_commands.AddItemToMultiitem
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "MultiItem": MultiItem, "ChildItem": ChildItem}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "MultiItem", "ChildItem"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_item_from_multiitem(GlobalUnitOrConvoy, MultiItem, ChildItem=None, ):
    command_t = event_commands.RemoveItemFromMultiitem
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "MultiItem": MultiItem, "ChildItem": ChildItem}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "MultiItem"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_item_component(GlobalUnitOrConvoy, Item, ItemComponent, Expression=None, ):
    command_t = event_commands.AddItemComponent
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "ItemComponent": ItemComponent, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item", "ItemComponent"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def modify_item_component(GlobalUnitOrConvoy, Item, ItemComponent, Expression, ComponentProperty=None, ):
    command_t = event_commands.ModifyItemComponent
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "ItemComponent": ItemComponent, "Expression": Expression, "ComponentProperty": ComponentProperty}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item", "ItemComponent", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_item_component(GlobalUnitOrConvoy, Item, ItemComponent, ):
    command_t = event_commands.RemoveItemComponent
    parameters = {"GlobalUnitOrConvoy": GlobalUnitOrConvoy, "Item": Item, "ItemComponent": ItemComponent}
    parameters = dict(filter(optional_value_filter(["GlobalUnitOrConvoy", "Item", "ItemComponent"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_skill_component(GlobalUnit, Skill, SkillComponent, Expression=None, ):
    command_t = event_commands.AddSkillComponent
    parameters = {"GlobalUnit": GlobalUnit, "Skill": Skill, "SkillComponent": SkillComponent, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Skill", "SkillComponent"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def modify_skill_component(GlobalUnit, Skill, SkillComponent, Expression, ComponentProperty=None, ):
    command_t = event_commands.ModifySkillComponent
    parameters = {"GlobalUnit": GlobalUnit, "Skill": Skill, "SkillComponent": SkillComponent, "Expression": Expression, "ComponentProperty": ComponentProperty}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Skill", "SkillComponent", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_skill_component(GlobalUnit, Skill, SkillComponent, ):
    command_t = event_commands.RemoveSkillComponent
    parameters = {"GlobalUnit": GlobalUnit, "Skill": Skill, "SkillComponent": SkillComponent}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Skill", "SkillComponent"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def give_money(Money, Party=None, ):
    command_t = event_commands.GiveMoney
    parameters = {"Money": Money, "Party": Party}
    parameters = dict(filter(optional_value_filter(["Money"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def give_bexp(Bexp, Party=None, String=None, ):
    command_t = event_commands.GiveBexp
    parameters = {"Bexp": Bexp, "Party": Party, "String": String}
    parameters = dict(filter(optional_value_filter(["Bexp"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def give_exp(GlobalUnit, Experience, ):
    command_t = event_commands.GiveExp
    parameters = {"GlobalUnit": GlobalUnit, "Experience": Experience}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Experience"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_exp(GlobalUnit, Experience, ):
    command_t = event_commands.SetExp
    parameters = {"GlobalUnit": GlobalUnit, "Experience": Experience}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Experience"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def give_wexp(GlobalUnit, WeaponType, Integer, ):
    command_t = event_commands.GiveWexp
    parameters = {"GlobalUnit": GlobalUnit, "WeaponType": WeaponType, "Integer": Integer}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "WeaponType", "Integer"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_wexp(GlobalUnit, WeaponType, WholeNumber, ):
    command_t = event_commands.SetWexp
    parameters = {"GlobalUnit": GlobalUnit, "WeaponType": WeaponType, "WholeNumber": WholeNumber}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "WeaponType", "WholeNumber"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def give_skill(GlobalUnit, Skill, Initiator=None, ):
    command_t = event_commands.GiveSkill
    parameters = {"GlobalUnit": GlobalUnit, "Skill": Skill, "Initiator": Initiator}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Skill"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_skill(GlobalUnit, Skill, Count=None, ):
    command_t = event_commands.RemoveSkill
    parameters = {"GlobalUnit": GlobalUnit, "Skill": Skill, "Count": Count}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Skill"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_skill_data(GlobalUnit, Skill, Nid, Expression, ):
    command_t = event_commands.SetSkillData
    parameters = {"GlobalUnit": GlobalUnit, "Skill": Skill, "Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Skill", "Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_ai(GlobalUnit, AI, ):
    command_t = event_commands.ChangeAI
    parameters = {"GlobalUnit": GlobalUnit, "AI": AI}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "AI"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_roam_ai(GlobalUnit, AI, ):
    command_t = event_commands.ChangeRoamAI
    parameters = {"GlobalUnit": GlobalUnit, "AI": AI}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "AI"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_ai_group(GlobalUnit, AIGroup, ):
    command_t = event_commands.ChangeAIGroup
    parameters = {"GlobalUnit": GlobalUnit, "AIGroup": AIGroup}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "AIGroup"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_party(GlobalUnit, Party, ):
    command_t = event_commands.ChangeParty
    parameters = {"GlobalUnit": GlobalUnit, "Party": Party}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Party"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_faction(GlobalUnit, Faction, ):
    command_t = event_commands.ChangeFaction
    parameters = {"GlobalUnit": GlobalUnit, "Faction": Faction}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Faction"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_team(GlobalUnit, Team, ):
    command_t = event_commands.ChangeTeam
    parameters = {"GlobalUnit": GlobalUnit, "Team": Team}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Team"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_portrait(GlobalUnit, PortraitNid, ):
    command_t = event_commands.ChangePortrait
    parameters = {"GlobalUnit": GlobalUnit, "PortraitNid": PortraitNid}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "PortraitNid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_unit_desc(GlobalUnit, String, ):
    command_t = event_commands.ChangeUnitDesc
    parameters = {"GlobalUnit": GlobalUnit, "String": String}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "String"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_affinity(GlobalUnit, Affinity, ):
    command_t = event_commands.ChangeAffinity
    parameters = {"GlobalUnit": GlobalUnit, "Affinity": Affinity}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Affinity"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_stats(GlobalUnit, StatList, ):
    command_t = event_commands.ChangeStats
    parameters = {"GlobalUnit": GlobalUnit, "StatList": StatList}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "StatList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_stats(GlobalUnit, StatList, ):
    command_t = event_commands.SetStats
    parameters = {"GlobalUnit": GlobalUnit, "StatList": StatList}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "StatList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_growths(GlobalUnit, StatList, ):
    command_t = event_commands.ChangeGrowths
    parameters = {"GlobalUnit": GlobalUnit, "StatList": StatList}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "StatList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_growths(GlobalUnit, StatList, ):
    command_t = event_commands.SetGrowths
    parameters = {"GlobalUnit": GlobalUnit, "StatList": StatList}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "StatList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_stat_cap_modifiers(GlobalUnit, StatList, ):
    command_t = event_commands.ChangeStatCapModifiers
    parameters = {"GlobalUnit": GlobalUnit, "StatList": StatList}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "StatList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_stat_cap_modifiers(GlobalUnit, StatList, ):
    command_t = event_commands.SetStatCapModifiers
    parameters = {"GlobalUnit": GlobalUnit, "StatList": StatList}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "StatList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_unit_level(GlobalUnit, Level, ):
    command_t = event_commands.SetUnitLevel
    parameters = {"GlobalUnit": GlobalUnit, "Level": Level}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Level"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def autolevel_to(GlobalUnit, Level, GrowthMethod=None, ):
    command_t = event_commands.AutolevelTo
    parameters = {"GlobalUnit": GlobalUnit, "Level": Level, "GrowthMethod": GrowthMethod}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Level"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_mode_autolevels(Level, ):
    command_t = event_commands.SetModeAutolevels
    parameters = {"Level": Level}
    parameters = dict(filter(optional_value_filter(["Level"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_mode_rng(rng, ):
    command_t = event_commands.SetModeRNG
    parameters = {"rng": rng}
    parameters = dict(filter(optional_value_filter(["rng"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def promote(GlobalUnit, KlassList=None, ):
    command_t = event_commands.Promote
    parameters = {"GlobalUnit": GlobalUnit, "KlassList": KlassList}
    parameters = dict(filter(optional_value_filter(["GlobalUnit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_class(GlobalUnit, KlassList=None, ):
    command_t = event_commands.ChangeClass
    parameters = {"GlobalUnit": GlobalUnit, "KlassList": KlassList}
    parameters = dict(filter(optional_value_filter(["GlobalUnit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_tag(GlobalUnit, Tag, ):
    command_t = event_commands.AddTag
    parameters = {"GlobalUnit": GlobalUnit, "Tag": Tag}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Tag"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_tag(GlobalUnit, Tag, ):
    command_t = event_commands.RemoveTag
    parameters = {"GlobalUnit": GlobalUnit, "Tag": Tag}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Tag"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_talk(Unit1, Unit2, ):
    command_t = event_commands.AddTalk
    parameters = {"Unit1": Unit1, "Unit2": Unit2}
    parameters = dict(filter(optional_value_filter(["Unit1", "Unit2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_talk(Unit1, Unit2, ):
    command_t = event_commands.RemoveTalk
    parameters = {"Unit1": Unit1, "Unit2": Unit2}
    parameters = dict(filter(optional_value_filter(["Unit1", "Unit2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_lore(Lore, ):
    command_t = event_commands.AddLore
    parameters = {"Lore": Lore}
    parameters = dict(filter(optional_value_filter(["Lore"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_lore(Lore, ):
    command_t = event_commands.RemoveLore
    parameters = {"Lore": Lore}
    parameters = dict(filter(optional_value_filter(["Lore"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_base_convo(Nid, ):
    command_t = event_commands.AddBaseConvo
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def ignore_base_convo(Nid, Ignore=None, ):
    command_t = event_commands.IgnoreBaseConvo
    parameters = {"Nid": Nid, "Ignore": Ignore}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_base_convo(Nid, ):
    command_t = event_commands.RemoveBaseConvo
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def increment_support_points(Unit1, Unit2, SupportPoints, ):
    command_t = event_commands.IncrementSupportPoints
    parameters = {"Unit1": Unit1, "Unit2": Unit2, "SupportPoints": SupportPoints}
    parameters = dict(filter(optional_value_filter(["Unit1", "Unit2", "SupportPoints"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def unlock_support_rank(Unit1, Unit2, SupportRank, ):
    command_t = event_commands.UnlockSupportRank
    parameters = {"Unit1": Unit1, "Unit2": Unit2, "SupportRank": SupportRank}
    parameters = dict(filter(optional_value_filter(["Unit1", "Unit2", "SupportRank"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def disable_support_rank(Unit1, Unit2, SupportRank, ):
    command_t = event_commands.DisableSupportRank
    parameters = {"Unit1": Unit1, "Unit2": Unit2, "SupportRank": SupportRank}
    parameters = dict(filter(optional_value_filter(["Unit1", "Unit2", "SupportRank"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_market_item(Item, Stock=None, ):
    command_t = event_commands.AddMarketItem
    parameters = {"Item": Item, "Stock": Stock}
    parameters = dict(filter(optional_value_filter(["Item"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_market_item(Item, Stock=None, ):
    command_t = event_commands.RemoveMarketItem
    parameters = {"Item": Item, "Stock": Stock}
    parameters = dict(filter(optional_value_filter(["Item"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def clear_market_items():
    command_t = event_commands.ClearMarketItems
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def dump_vars():
    command_t = event_commands.DumpVars
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_region(Region, Position, Size, RegionType, String=None, TimeLeft=None, ):
    command_t = event_commands.AddRegion
    parameters = {"Region": Region, "Position": Position, "Size": Size, "RegionType": RegionType, "String": String, "TimeLeft": TimeLeft}
    parameters = dict(filter(optional_value_filter(["Region", "Position", "Size", "RegionType"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def region_condition(Region, Expression, ):
    command_t = event_commands.RegionCondition
    parameters = {"Region": Region, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Region", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_region(Region, ):
    command_t = event_commands.RemoveRegion
    parameters = {"Region": Region}
    parameters = dict(filter(optional_value_filter(["Region"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_generics_from_region(Nid, ):
    command_t = event_commands.RemoveGenericsFromRegion
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def show_layer(Layer, LayerTransition=None, ):
    command_t = event_commands.ShowLayer
    parameters = {"Layer": Layer, "LayerTransition": LayerTransition}
    parameters = dict(filter(optional_value_filter(["Layer"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def hide_layer(Layer, LayerTransition=None, ):
    command_t = event_commands.HideLayer
    parameters = {"Layer": Layer, "LayerTransition": LayerTransition}
    parameters = dict(filter(optional_value_filter(["Layer"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_weather(Weather, Position=None, ):
    command_t = event_commands.AddWeather
    parameters = {"Weather": Weather, "Position": Position}
    parameters = dict(filter(optional_value_filter(["Weather"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_weather(Weather, Position=None, ):
    command_t = event_commands.RemoveWeather
    parameters = {"Weather": Weather, "Position": Position}
    parameters = dict(filter(optional_value_filter(["Weather"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_objective_simple(EvaluableString, ):
    command_t = event_commands.ChangeObjectiveSimple
    parameters = {"EvaluableString": EvaluableString}
    parameters = dict(filter(optional_value_filter(["EvaluableString"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_objective_win(EvaluableString, ):
    command_t = event_commands.ChangeObjectiveWin
    parameters = {"EvaluableString": EvaluableString}
    parameters = dict(filter(optional_value_filter(["EvaluableString"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_objective_loss(EvaluableString, ):
    command_t = event_commands.ChangeObjectiveLoss
    parameters = {"EvaluableString": EvaluableString}
    parameters = dict(filter(optional_value_filter(["EvaluableString"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_position(Position, ):
    command_t = event_commands.SetPosition
    parameters = {"Position": Position}
    parameters = dict(filter(optional_value_filter(["Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def map_anim(MapAnim, FloatPosition, Speed=None, ):
    command_t = event_commands.MapAnim
    parameters = {"MapAnim": MapAnim, "FloatPosition": FloatPosition, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["MapAnim", "FloatPosition"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_map_anim(MapAnim, Position, ):
    command_t = event_commands.RemoveMapAnim
    parameters = {"MapAnim": MapAnim, "Position": Position}
    parameters = dict(filter(optional_value_filter(["MapAnim", "Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_unit_map_anim(MapAnim, Unit, Speed=None, ):
    command_t = event_commands.AddUnitMapAnim
    parameters = {"MapAnim": MapAnim, "Unit": Unit, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["MapAnim", "Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_unit_map_anim(MapAnim, Unit, ):
    command_t = event_commands.RemoveUnitMapAnim
    parameters = {"MapAnim": MapAnim, "Unit": Unit}
    parameters = dict(filter(optional_value_filter(["MapAnim", "Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def merge_parties(Party1, Party2, ):
    command_t = event_commands.MergeParties
    parameters = {"Party1": Party1, "Party2": Party2}
    parameters = dict(filter(optional_value_filter(["Party1", "Party2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def arrange_formation():
    command_t = event_commands.ArrangeFormation
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def prep(PickUnitsEnabled=None, Music=None, OtherOptions=None, OtherOptionsEnabled=None, OtherOptionsOnSelect=None, ):
    command_t = event_commands.Prep
    parameters = {"PickUnitsEnabled": PickUnitsEnabled, "Music": Music, "OtherOptions": OtherOptions, "OtherOptionsEnabled": OtherOptionsEnabled, "OtherOptionsOnSelect": OtherOptionsOnSelect}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def base(Background, Music=None, OtherOptions=None, OtherOptionsEnabled=None, OtherOptionsOnSelect=None, ):
    command_t = event_commands.Base
    parameters = {"Background": Background, "Music": Music, "OtherOptions": OtherOptions, "OtherOptionsEnabled": OtherOptionsEnabled, "OtherOptionsOnSelect": OtherOptionsOnSelect}
    parameters = dict(filter(optional_value_filter(["Background"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_custom_options(CustomOptions, CustomOptionsEnabled=None, CustomOptionsDesc=None, CustomOptionsOnSelect=None, ):
    command_t = event_commands.SetCustomOptions
    parameters = {"CustomOptions": CustomOptions, "CustomOptionsEnabled": CustomOptionsEnabled, "CustomOptionsDesc": CustomOptionsDesc, "CustomOptionsOnSelect": CustomOptionsOnSelect}
    parameters = dict(filter(optional_value_filter(["CustomOptions"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def shop(Unit, ItemList, ShopFlavor=None, StockList=None, ShopId=None, ):
    command_t = event_commands.Shop
    parameters = {"Unit": Unit, "ItemList": ItemList, "ShopFlavor": ShopFlavor, "StockList": StockList, "ShopId": ShopId}
    parameters = dict(filter(optional_value_filter(["Unit", "ItemList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def choice(Nid, Title, Choices, RowWidth=None, Orientation=None, Alignment=None, BG=None, EventNid=None, EntryType=None, Dimensions=None, TextAlign=None, ):
    command_t = event_commands.Choice
    parameters = {"Nid": Nid, "Title": Title, "Choices": Choices, "RowWidth": RowWidth, "Orientation": Orientation, "Alignment": Alignment, "BG": BG, "EventNid": EventNid, "EntryType": EntryType, "Dimensions": Dimensions, "TextAlign": TextAlign}
    parameters = dict(filter(optional_value_filter(["Nid", "Title", "Choices"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def unchoice():
    command_t = event_commands.Unchoice
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def textbox(NID, Text, BoxPosition=None, Width=None, NumLines=None, StyleNid=None, TextSpeed=None, FontColor=None, FontType=None, BG=None, ):
    command_t = event_commands.Textbox
    parameters = {"NID": NID, "Text": Text, "BoxPosition": BoxPosition, "Width": Width, "NumLines": NumLines, "StyleNid": StyleNid, "TextSpeed": TextSpeed, "FontColor": FontColor, "FontType": FontType, "BG": BG}
    parameters = dict(filter(optional_value_filter(["NID", "Text"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def table(Nid, TableData, Title=None, Dimensions=None, RowWidth=None, Alignment=None, BG=None, EntryType=None, TextAlign=None, ):
    command_t = event_commands.Table
    parameters = {"Nid": Nid, "TableData": TableData, "Title": Title, "Dimensions": Dimensions, "RowWidth": RowWidth, "Alignment": Alignment, "BG": BG, "EntryType": EntryType, "TextAlign": TextAlign}
    parameters = dict(filter(optional_value_filter(["Nid", "TableData"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_table(Nid, ):
    command_t = event_commands.RemoveTable
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def text_entry(Nid, String, PositiveInteger=None, IllegalCharacterList=None, ):
    command_t = event_commands.TextEntry
    parameters = {"Nid": Nid, "String": String, "PositiveInteger": PositiveInteger, "IllegalCharacterList": IllegalCharacterList}
    parameters = dict(filter(optional_value_filter(["Nid", "String"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def chapter_title(Music=None, String=None, ):
    command_t = event_commands.ChapterTitle
    parameters = {"Music": Music, "String": String}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def draw_overlay_sprite(Nid, SpriteID, Position=None, ZLevel=None, Animation=None, Speed=None, ):
    command_t = event_commands.DrawOverlaySprite
    parameters = {"Nid": Nid, "SpriteID": SpriteID, "Position": Position, "ZLevel": ZLevel, "Animation": Animation, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Nid", "SpriteID"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove_overlay_sprite(Nid, Animation=None, Speed=None, ):
    command_t = event_commands.RemoveOverlaySprite
    parameters = {"Nid": Nid, "Animation": Animation, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def alert(String, Item=None, Skill=None, Icon=None, ):
    command_t = event_commands.Alert
    parameters = {"String": String, "Item": Item, "Skill": Skill, "Icon": Icon}
    parameters = dict(filter(optional_value_filter(["String"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def victory_screen(Sound=None, ):
    command_t = event_commands.VictoryScreen
    parameters = {"Sound": Sound}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def records_screen():
    command_t = event_commands.RecordsScreen
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def open_library():
    command_t = event_commands.OpenLibrary
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def open_guide():
    command_t = event_commands.OpenGuide
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def open_unit_management(Panorama=None, ):
    command_t = event_commands.OpenUnitManagement
    parameters = {"Panorama": Panorama}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def open_trade(Unit1, Unit2, ):
    command_t = event_commands.OpenTrade
    parameters = {"Unit1": Unit1, "Unit2": Unit2}
    parameters = dict(filter(optional_value_filter(["Unit1", "Unit2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def open_bexp_menu(Panorama=None, Music=None, ):
    command_t = event_commands.OpenBexpMenu
    parameters = {"Panorama": Panorama, "Music": Music}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def show_minimap():
    command_t = event_commands.ShowMinimap
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def open_achievements(Background, ):
    command_t = event_commands.OpenAchievements
    parameters = {"Background": Background}
    parameters = dict(filter(optional_value_filter(["Background"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def location_card(String, ):
    command_t = event_commands.LocationCard
    parameters = {"String": String}
    parameters = dict(filter(optional_value_filter(["String"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def credits(Role, Credits, ):
    command_t = event_commands.Credits
    parameters = {"Role": Role, "Credits": Credits}
    parameters = dict(filter(optional_value_filter(["Role", "Credits"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def ending(Portrait, Title, Text, ):
    command_t = event_commands.Ending
    parameters = {"Portrait": Portrait, "Title": Title, "Text": Text}
    parameters = dict(filter(optional_value_filter(["Portrait", "Title", "Text"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def paired_ending(LeftPortrait, RightPortrait, LeftTitle, RightTitle, Text, ):
    command_t = event_commands.PairedEnding
    parameters = {"LeftPortrait": LeftPortrait, "RightPortrait": RightPortrait, "LeftTitle": LeftTitle, "RightTitle": RightTitle, "Text": Text}
    parameters = dict(filter(optional_value_filter(["LeftPortrait", "RightPortrait", "LeftTitle", "RightTitle", "Text"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def pop_dialog():
    command_t = event_commands.PopDialog
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def unlock(Unit, ):
    command_t = event_commands.Unlock
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def trigger_script(Event, Unit1=None, Unit2=None, ):
    command_t = event_commands.TriggerScript
    parameters = {"Event": Event, "Unit1": Unit1, "Unit2": Unit2}
    parameters = dict(filter(optional_value_filter(["Event"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def trigger_script_with_args(Event, ArgList=None, ):
    command_t = event_commands.TriggerScriptWithArgs
    parameters = {"Event": Event, "ArgList": ArgList}
    parameters = dict(filter(optional_value_filter(["Event"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_roaming(FreeRoamEnabled, ):
    command_t = event_commands.ChangeRoaming
    parameters = {"FreeRoamEnabled": FreeRoamEnabled}
    parameters = dict(filter(optional_value_filter(["FreeRoamEnabled"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def change_roaming_unit(Unit, ):
    command_t = event_commands.ChangeRoamingUnit
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def clean_up_roaming():
    command_t = event_commands.CleanUpRoaming
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_to_initiative(Unit, Integer, ):
    command_t = event_commands.AddToInitiative
    parameters = {"Unit": Unit, "Integer": Integer}
    parameters = dict(filter(optional_value_filter(["Unit", "Integer"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def move_in_initiative(Unit, Integer, ):
    command_t = event_commands.MoveInInitiative
    parameters = {"Unit": Unit, "Integer": Integer}
    parameters = dict(filter(optional_value_filter(["Unit", "Integer"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def pair_up(Unit1, Unit2, ):
    command_t = event_commands.PairUp
    parameters = {"Unit1": Unit1, "Unit2": Unit2}
    parameters = dict(filter(optional_value_filter(["Unit1", "Unit2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def separate(Unit, ):
    command_t = event_commands.Separate
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def overworld_cinematic(OverworldNID=None, ):
    command_t = event_commands.OverworldCinematic
    parameters = {"OverworldNID": OverworldNID}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_overworld_position(OverworldEntity, OverworldLocation, ):
    command_t = event_commands.SetOverworldPosition
    parameters = {"OverworldEntity": OverworldEntity, "OverworldLocation": OverworldLocation}
    parameters = dict(filter(optional_value_filter(["OverworldEntity", "OverworldLocation"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def overworld_move_unit(OverworldEntity, OverworldLocation=None, Speed=None, PointList=None, ):
    command_t = event_commands.OverworldMoveUnit
    parameters = {"OverworldEntity": OverworldEntity, "OverworldLocation": OverworldLocation, "Speed": Speed, "PointList": PointList}
    parameters = dict(filter(optional_value_filter(["OverworldEntity"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def reveal_overworld_node(OverworldNodeNid, ):
    command_t = event_commands.RevealOverworldNode
    parameters = {"OverworldNodeNid": OverworldNodeNid}
    parameters = dict(filter(optional_value_filter(["OverworldNodeNid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def reveal_overworld_road(Node1, Node2, ):
    command_t = event_commands.RevealOverworldRoad
    parameters = {"Node1": Node1, "Node2": Node2}
    parameters = dict(filter(optional_value_filter(["Node1", "Node2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def create_overworld_entity(Nid, Unit=None, Team=None, ):
    command_t = event_commands.CreateOverworldEntity
    parameters = {"Nid": Nid, "Unit": Unit, "Team": Team}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def disable_overworld_entity(Nid, ):
    command_t = event_commands.DisableOverworldEntity
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def toggle_narration_mode(Direction, Speed=None, ):
    command_t = event_commands.ToggleNarrationMode
    parameters = {"Direction": Direction, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Direction"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def hide_combat_ui():
    command_t = event_commands.HideCombatUI
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def show_combat_ui():
    command_t = event_commands.ShowCombatUI
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_overworld_menu_option_enabled(OverworldNodeNid, OverworldNodeMenuOption, Setting, ):
    command_t = event_commands.SetOverworldMenuOptionEnabled
    parameters = {"OverworldNodeNid": OverworldNodeNid, "OverworldNodeMenuOption": OverworldNodeMenuOption, "Setting": Setting}
    parameters = dict(filter(optional_value_filter(["OverworldNodeNid", "OverworldNodeMenuOption", "Setting"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_overworld_menu_option_visible(OverworldNodeNID, OverworldNodeMenuOption, Setting, ):
    command_t = event_commands.SetOverworldMenuOptionVisible
    parameters = {"OverworldNodeNID": OverworldNodeNID, "OverworldNodeMenuOption": OverworldNodeMenuOption, "Setting": Setting}
    parameters = dict(filter(optional_value_filter(["OverworldNodeNID", "OverworldNodeMenuOption", "Setting"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def enter_level_from_overworld(LevelNid, ):
    command_t = event_commands.EnterLevelFromOverworld
    parameters = {"LevelNid": LevelNid}
    parameters = dict(filter(optional_value_filter(["LevelNid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def create_achievement(Nid, Name, Description, ):
    command_t = event_commands.CreateAchievement
    parameters = {"Nid": Nid, "Name": Name, "Description": Description}
    parameters = dict(filter(optional_value_filter(["Nid", "Name", "Description"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def update_achievement(Achievement, Name, Description, ):
    command_t = event_commands.UpdateAchievement
    parameters = {"Achievement": Achievement, "Name": Name, "Description": Description}
    parameters = dict(filter(optional_value_filter(["Achievement", "Name", "Description"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def complete_achievement(Achievement, Completed, ):
    command_t = event_commands.CompleteAchievement
    parameters = {"Achievement": Achievement, "Completed": Completed}
    parameters = dict(filter(optional_value_filter(["Achievement", "Completed"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def clear_achievements():
    command_t = event_commands.ClearAchievements
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def create_record(Nid, Expression, ):
    command_t = event_commands.CreateRecord
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def update_record(Nid, Expression, ):
    command_t = event_commands.UpdateRecord
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def replace_record(Nid, Expression, ):
    command_t = event_commands.ReplaceRecord
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def delete_record(Nid, ):
    command_t = event_commands.DeleteRecord
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def unlock_difficulty(DifficultyMode, ):
    command_t = event_commands.UnlockDifficulty
    parameters = {"DifficultyMode": DifficultyMode}
    parameters = dict(filter(optional_value_filter(["DifficultyMode"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def party_transfer(Party1, Party2, FixedUnits=None, Party1Name=None, Party2Name=None, Party1Limit=None, Party2Limit=None, ):
    command_t = event_commands.PartyTransfer
    parameters = {"Party1": Party1, "Party2": Party2, "FixedUnits": FixedUnits, "Party1Name": Party1Name, "Party2Name": Party2Name, "Party1Limit": Party1Limit, "Party2Limit": Party2Limit}
    parameters = dict(filter(optional_value_filter(["Party1", "Party2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def m(Music, FadeIn=None, ):
    command_t = event_commands.Music
    parameters = {"Music": Music, "FadeIn": FadeIn}
    parameters = dict(filter(optional_value_filter(["Music"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def mf(FadeOut=None, ):
    command_t = event_commands.MusicFadeBack
    parameters = {"FadeOut": FadeOut}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def u(Portrait, ScreenPosition, Slide=None, ExpressionList=None, SpeedMult=None, ):
    command_t = event_commands.AddPortrait
    parameters = {"Portrait": Portrait, "ScreenPosition": ScreenPosition, "Slide": Slide, "ExpressionList": ExpressionList, "SpeedMult": SpeedMult}
    parameters = dict(filter(optional_value_filter(["Portrait", "ScreenPosition"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def uu(Portrait1, ScreenPosition1, Portrait2, ScreenPosition2, Portrait3=None, ScreenPosition3=None, Portrait4=None, ScreenPosition4=None, ):
    command_t = event_commands.MultiAddPortrait
    parameters = {"Portrait1": Portrait1, "ScreenPosition1": ScreenPosition1, "Portrait2": Portrait2, "ScreenPosition2": ScreenPosition2, "Portrait3": Portrait3, "ScreenPosition3": ScreenPosition3, "Portrait4": Portrait4, "ScreenPosition4": ScreenPosition4}
    parameters = dict(filter(optional_value_filter(["Portrait1", "ScreenPosition1", "Portrait2", "ScreenPosition2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def r(Portrait, SpeedMult=None, Slide=None, ):
    command_t = event_commands.RemovePortrait
    parameters = {"Portrait": Portrait, "SpeedMult": SpeedMult, "Slide": Slide}
    parameters = dict(filter(optional_value_filter(["Portrait"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def rr(Portrait1, Portrait2, Portrait3=None, Portrait4=None, ):
    command_t = event_commands.MultiRemovePortrait
    parameters = {"Portrait1": Portrait1, "Portrait2": Portrait2, "Portrait3": Portrait3, "Portrait4": Portrait4}
    parameters = dict(filter(optional_value_filter(["Portrait1", "Portrait2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def bop(Portrait, ):
    command_t = event_commands.BopPortrait
    parameters = {"Portrait": Portrait}
    parameters = dict(filter(optional_value_filter(["Portrait"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def mirror(Portrait, SpeedMult=None, ):
    command_t = event_commands.MirrorPortrait
    parameters = {"Portrait": Portrait, "SpeedMult": SpeedMult}
    parameters = dict(filter(optional_value_filter(["Portrait"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def e(Portrait, ExpressionList, ):
    command_t = event_commands.Expression
    parameters = {"Portrait": Portrait, "ExpressionList": ExpressionList}
    parameters = dict(filter(optional_value_filter(["Portrait", "ExpressionList"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def s(SpeakerOrStyle, Text, TextPosition=None, Width=None, StyleNid=None, TextSpeed=None, FontColor=None, FontType=None, DialogBox=None, NumLines=None, DrawCursor=None, MessageTail=None, Transparency=None, NameTagBg=None, BoopSound=None, ):
    command_t = event_commands.Speak
    parameters = {"SpeakerOrStyle": SpeakerOrStyle, "Text": Text, "TextPosition": TextPosition, "Width": Width, "StyleNid": StyleNid, "TextSpeed": TextSpeed, "FontColor": FontColor, "FontType": FontType, "DialogBox": DialogBox, "NumLines": NumLines, "DrawCursor": DrawCursor, "MessageTail": MessageTail, "Transparency": Transparency, "NameTagBg": NameTagBg, "BoopSound": BoopSound}
    parameters = dict(filter(optional_value_filter(["SpeakerOrStyle", "Text"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def t(Direction=None, Speed=None, Color3=None, Panorama=None, ):
    command_t = event_commands.Transition
    parameters = {"Direction": Direction, "Speed": Speed, "Color3": Color3, "Panorama": Panorama}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def b(Panorama=None, ):
    command_t = event_commands.ChangeBackground
    parameters = {"Panorama": Panorama}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_cursor(Position, Speed=None, ):
    command_t = event_commands.MoveCursor
    parameters = {"Position": Position, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def highlight(Position, ):
    command_t = event_commands.FlickerCursor
    parameters = {"Position": Position}
    parameters = dict(filter(optional_value_filter(["Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def gvar(Nid, Expression, ):
    command_t = event_commands.GameVar
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def ginc(Nid, Expression=None, ):
    command_t = event_commands.IncGameVar
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def lvar(Nid, Expression, ):
    command_t = event_commands.LevelVar
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid", "Expression"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def linc(Nid, Expression=None, ):
    command_t = event_commands.IncLevelVar
    parameters = {"Nid": Nid, "Expression": Expression}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add(Unit, Position=None, EntryType=None, Placement=None, AnimationType=None, ):
    command_t = event_commands.AddUnit
    parameters = {"Unit": Unit, "Position": Position, "EntryType": EntryType, "Placement": Placement, "AnimationType": AnimationType}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def move(Unit, Position=None, MovementType=None, Placement=None, Speed=None, ):
    command_t = event_commands.MoveUnit
    parameters = {"Unit": Unit, "Position": Position, "MovementType": MovementType, "Placement": Placement, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def remove(Unit, RemoveType=None, AnimationType=None, ):
    command_t = event_commands.RemoveUnit
    parameters = {"Unit": Unit, "RemoveType": RemoveType, "AnimationType": AnimationType}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def kill(Unit, ):
    command_t = event_commands.KillUnit
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def interact(Unit, Position, CombatScript=None, Ability=None, Rounds=None, ):
    command_t = event_commands.InteractUnit
    parameters = {"Unit": Unit, "Position": Position, "CombatScript": CombatScript, "Ability": Ability, "Rounds": Rounds}
    parameters = dict(filter(optional_value_filter(["Unit", "Position"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def resurrect_unit(GlobalUnit, ):
    command_t = event_commands.Resurrect
    parameters = {"GlobalUnit": GlobalUnit}
    parameters = dict(filter(optional_value_filter(["GlobalUnit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def reset_unit(Unit, ):
    command_t = event_commands.Reset
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def morph_group(Group, StartingGroup, MovementType=None, Placement=None, ):
    command_t = event_commands.MoveGroup
    parameters = {"Group": Group, "StartingGroup": StartingGroup, "MovementType": MovementType, "Placement": Placement}
    parameters = dict(filter(optional_value_filter(["Group", "StartingGroup"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def add_skill(GlobalUnit, Skill, Initiator=None, ):
    command_t = event_commands.GiveSkill
    parameters = {"GlobalUnit": GlobalUnit, "Skill": Skill, "Initiator": Initiator}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "Skill"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_ai(GlobalUnit, AI, ):
    command_t = event_commands.ChangeAI
    parameters = {"GlobalUnit": GlobalUnit, "AI": AI}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "AI"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_roam_ai(GlobalUnit, AI, ):
    command_t = event_commands.ChangeRoamAI
    parameters = {"GlobalUnit": GlobalUnit, "AI": AI}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "AI"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def set_ai_group(GlobalUnit, AIGroup, ):
    command_t = event_commands.ChangeAIGroup
    parameters = {"GlobalUnit": GlobalUnit, "AIGroup": AIGroup}
    parameters = dict(filter(optional_value_filter(["GlobalUnit", "AIGroup"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def unlock_lore(Lore, ):
    command_t = event_commands.AddLore
    parameters = {"Lore": Lore}
    parameters = dict(filter(optional_value_filter(["Lore"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def rmtable(Nid, ):
    command_t = event_commands.RemoveTable
    parameters = {"Nid": Nid}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def draw_overlay(Nid, SpriteID, Position=None, ZLevel=None, Animation=None, Speed=None, ):
    command_t = event_commands.DrawOverlaySprite
    parameters = {"Nid": Nid, "SpriteID": SpriteID, "Position": Position, "ZLevel": ZLevel, "Animation": Animation, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Nid", "SpriteID"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def delete_overlay(Nid, Animation=None, Speed=None, ):
    command_t = event_commands.RemoveOverlaySprite
    parameters = {"Nid": Nid, "Animation": Animation, "Speed": Speed}
    parameters = dict(filter(optional_value_filter(["Nid"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def rescue(Unit1, Unit2, ):
    command_t = event_commands.PairUp
    parameters = {"Unit1": Unit1, "Unit2": Unit2}
    parameters = dict(filter(optional_value_filter(["Unit1", "Unit2"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def drop(Unit, ):
    command_t = event_commands.Separate
    parameters = {"Unit": Unit}
    parameters = dict(filter(optional_value_filter(["Unit"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def omove(OverworldEntity, OverworldLocation=None, Speed=None, PointList=None, ):
    command_t = event_commands.OverworldMoveUnit
    parameters = {"OverworldEntity": OverworldEntity, "OverworldLocation": OverworldLocation, "Speed": Speed, "PointList": PointList}
    parameters = dict(filter(optional_value_filter(["OverworldEntity"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def wait(Time, ):
    command_t = event_commands.Wait
    parameters = {"Time": Time}
    parameters = dict(filter(optional_value_filter(["Time"]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def finish():
    command_t = event_commands.Finish
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')

def end_skip():
    command_t = event_commands.EndSkip
    parameters = {}
    parameters = dict(filter(optional_value_filter([]), parameters.items()))
    for k, v in parameters.items():
        if isinstance(v, str):
            param_name = command_t.get_validator_from_keyword(k)
            param_validator = event_validators.get(param_name)
            if issubclass(param_validator, event_validators.EnumValidator):
                parameters[k] = event_validators.convert(param_name, v)
    return command_t(parameters=parameters).set_flags('from_python')
