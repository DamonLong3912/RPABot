from .base_action import BaseAction
from .ui_actions import (
    ClickRegionAction,
    WaitAndClickRegionAction,
    ScrollAction,
    SwipeAction
)
from .ocr_actions import (
    GetTextFromRegionAction,
    VerifyTextInRegionAction,
    WaitAndClickOCRTextAction,
    HandlePopupsUntilTargetAction,
    WaitForInputReadyAction,
    InputTextAction,
    GetElementPositionAction
)
from .data_actions import (
    AppendToListAction,
    ExportDataAction,
    SetVariableAction,
    GetVariableAction
)
from .flow_actions import (
    LoopAction,
    SleepAction,
    ForEachAction,
    CheckRepeatedValueAction
)
from .app_actions import (
    CheckAndInstallAppAction,
    VerifyAppInstalledAction,
    StartAppAction,
    WaitForAppInstalledAction
)

# 动作类型映射表
ACTION_MAP = {
    'click_region': ClickRegionAction,
    'wait_and_click_region': WaitAndClickRegionAction,
    'scroll': ScrollAction,
    'swipe': SwipeAction,
    'get_text_from_region': GetTextFromRegionAction,
    'verify_text_in_region': VerifyTextInRegionAction,
    'wait_and_click_ocr_text': WaitAndClickOCRTextAction,
    'handle_popups_until_target': HandlePopupsUntilTargetAction,
    'wait_for_input_ready': WaitForInputReadyAction,
    'input_text': InputTextAction,
    'append_to_list': AppendToListAction,
    'export_data': ExportDataAction,
    'set_variable': SetVariableAction,
    'get_variable': GetVariableAction,
    'loop': LoopAction,
    'sleep': SleepAction,
    'get_element_position': GetElementPositionAction,
    'check_and_install_app': CheckAndInstallAppAction,
    'verify_app_installed': VerifyAppInstalledAction,
    'start_app': StartAppAction,
    'wait_for_app_installed': WaitForAppInstalledAction,
    'for_each': ForEachAction,
    'check_repeated_value': CheckRepeatedValueAction
}

def get_action_class(action_type: str) -> type:
    """获取动作类"""
    if action_type not in ACTION_MAP:
        raise ValueError(f"未知的动作类型: {action_type}")
    return ACTION_MAP[action_type] 