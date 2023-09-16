import json
import time

import numpy as np

from bot.base.task import TaskStatus, EndTaskReason
from module.umamusume.asset.point import *
from module.umamusume.context import TurnInfo
from module.umamusume.script.cultivate_task.const import SKILL_LEARN_PRIORITY_LIST
from module.umamusume.script.cultivate_task.event import get_event_choice
from module.umamusume.script.cultivate_task.parse import *

log = logger.get_logger(__name__)


def script_cultivate_main_menu(ctx: UmamusumeContext):
    img = ctx.current_screen
    current_date = parse_date(img, ctx)
    if current_date == -1:
        log.warning("解析日期失败")
        return
    # 如果进入新的一回合，记录旧的回合信息并创建新的
    if ctx.cultivate_detail.turn_info is None or current_date != ctx.cultivate_detail.turn_info.date:
        if ctx.cultivate_detail.turn_info is not None:
            ctx.cultivate_detail.turn_info_history.append(ctx.cultivate_detail.turn_info)
        ctx.cultivate_detail.turn_info = TurnInfo()
        ctx.cultivate_detail.turn_info.date = current_date
        log.debug("进入新回合，日期：" + str(current_date))
        ctx.cultivate_detail.reset_skill_learn()

    # 解析主界面
    if not ctx.cultivate_detail.turn_info.parse_main_menu_finish:
        parse_cultivate_main_menu(ctx, img)

    has_extra_race = len([i for i in ctx.cultivate_detail.extra_race_list if str(i)[:2]
                            == str(ctx.cultivate_detail.turn_info.date)]) != 0

    # 意外情况处理
    if not ctx.cultivate_detail.turn_info.turn_learn_skill_done and ctx.cultivate_detail.learn_skill_done:
        ctx.cultivate_detail.reset_skill_learn()

    if (ctx.cultivate_detail.turn_info.uma_attribute.skill_point > ctx.cultivate_detail.learn_skill_threshold
            and not ctx.cultivate_detail.turn_info.turn_learn_skill_done):
        ctx.ctrl.click_by_point(CULTIVATE_SKILL_LEARN)
        ctx.cultivate_detail.turn_info.parse_main_menu_finish = False
        return
    else:
        ctx.cultivate_detail.reset_skill_learn()

    if not ctx.cultivate_detail.turn_info.parse_train_info_finish:
        if has_extra_race or ctx.cultivate_detail.turn_info.remain_stamina < 40:
            ctx.cultivate_detail.turn_info.parse_train_info_finish = True
            return
        else:
            ctx.ctrl.click_by_point(TO_TRAINING_SELECT)
            return

    turn_operation = ctx.cultivate_detail.turn_info.turn_operation
    if turn_operation is not None:
        if turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_TRAINING:
            ctx.ctrl.click_by_point(TO_TRAINING_SELECT)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_REST:
            ctx.ctrl.click_by_point(CULTIVATE_REST)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_MEDIC:
            if 36 < ctx.cultivate_detail.turn_info.date <= 40 or 60 < ctx.cultivate_detail.turn_info.date <= 64:
                ctx.ctrl.click_by_point(CULTIVATE_MEDIC_SUMMER)
            else:
                ctx.ctrl.click_by_point(CULTIVATE_MEDIC)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_TRIP:
            ctx.ctrl.click_by_point(CULTIVATE_TRIP)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_RACE:
            if 36 < ctx.cultivate_detail.turn_info.date <= 40 or 60 < ctx.cultivate_detail.turn_info.date <= 64:
                ctx.ctrl.click_by_point(CULTIVATE_RACE_SUMMER)
            else:
                ctx.ctrl.click_by_point(CULTIVATE_RACE)


def script_cultivate_training_select(ctx: UmamusumeContext):
    if ctx.cultivate_detail.turn_info is None:
        log.warning("回合信息未初始化")
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return

    if ctx.cultivate_detail.turn_info.turn_operation is not None:
        if (ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type ==
                TurnOperationType.TURN_OPERATION_TYPE_TRAINING):
            ctx.ctrl.click_by_point(
                TRAINING_POINT_LIST[ctx.cultivate_detail.turn_info.turn_operation.training_type.value - 1])
            time.sleep(0.5)
            ctx.ctrl.click_by_point(
                TRAINING_POINT_LIST[ctx.cultivate_detail.turn_info.turn_operation.training_type.value - 1])
            time.sleep(3)
            return
        else:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
            return

    if not ctx.cultivate_detail.turn_info.parse_train_info_finish:
        img = ctx.current_screen
        train_type = parse_train_type(ctx, img)
        if train_type == TrainingType.TRAINING_TYPE_UNKNOWN:
            return
        parse_training_result(ctx, img, train_type)
        parse_training_support_card(ctx, img, train_type)
        viewed = train_type.value
        for i in range(5):
            if i != (viewed - 1):
                retry = 0
                max_retry = 3
                ctx.ctrl.click_by_point(TRAINING_POINT_LIST[i])
                img = ctx.ctrl.get_screen()
                while parse_train_type(ctx, img) != TrainingType(i + 1) and retry < max_retry:
                    if retry > 2:
                        ctx.ctrl.click_by_point(TRAINING_POINT_LIST[i])
                    time.sleep(0.2)
                    img = ctx.ctrl.get_screen()
                    retry += 1
                if retry == max_retry:
                    return
                parse_training_result(ctx, img, TrainingType(i + 1))
                parse_training_support_card(ctx, img, TrainingType(i + 1))
        ctx.cultivate_detail.turn_info.parse_train_info_finish = True
    if not ctx.cultivate_detail.turn_info.parse_main_menu_finish:
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return


def script_main_menu(ctx: UmamusumeContext):
    if ctx.cultivate_detail.cultivate_finish:
        ctx.task.end_task(TaskStatus.TASK_STATUS_SUCCESS, EndTaskReason.COMPLETE)
        return
    ctx.ctrl.click_by_point(TO_CULTIVATE_SCENARIO_CHOOSE)


def script_scenario_select(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_umamusume_select(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_extend_umamusume_select(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_support_card_select(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen(to_gray=True)
    if image_match(img, REF_CULTIVATE_SUPPORT_CARD_EMPTY).find_match:
        ctx.ctrl.click_by_point(TO_FOLLOW_SUPPORT_CARD_SELECT)
        return
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_follow_support_card_select(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen()
    while True:
        selected = find_support_card(ctx, img)
        if selected:
            break
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if compare_color_equal(img[1096, 693], [125, 120, 142]):
            while True:
                img = cv2.cvtColor(ctx.ctrl.get_screen(), cv2.COLOR_BGR2RGB)
                if compare_color_equal(img[127, 697], [211, 209, 219]):
                    ctx.ctrl.swipe(x1=350, y1=400, x2=350, y2=1000, duration=200, name="")
                else:
                    break
            ctx.ctrl.click_by_point(FOLLOW_SUPPORT_CARD_SELECT_REFRESH)
            return
        ctx.ctrl.swipe(x1=350, y1=1000, x2=350, y2=400, duration=1000, name="")
        time.sleep(1)
        img = ctx.ctrl.get_screen()


def script_cultivate_final_check(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_FINAL_CHECK_START)


def script_cultivate_event(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen()
    event_name, selector_list = parse_cultivate_event(ctx, img)
    log.debug("当前事件：%s", event_name)
    if len(selector_list) != 0:
        choice_index = get_event_choice(event_name)
        ctx.ctrl.click(selector_list[choice_index - 1][0], selector_list[choice_index - 1][1],
                       "事件选项-" + str(choice_index))
    else:
        log.debug("未出现选项")


def script_cultivate_goal_race(ctx: UmamusumeContext):
    img = ctx.current_screen
    current_date = parse_date(img, ctx)
    if current_date == -1:
        log.warning("解析日期失败")
        return
    # 如果进入新的一回合，记录旧的回合信息并创建新的
    if ctx.cultivate_detail.turn_info is None or current_date != ctx.cultivate_detail.turn_info.date:
        if ctx.cultivate_detail.turn_info is not None:
            ctx.cultivate_detail.turn_info_history.append(ctx.cultivate_detail.turn_info)
        ctx.cultivate_detail.turn_info = TurnInfo()
        ctx.cultivate_detail.turn_info.date = current_date
    ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_1)


def script_cultivate_race_list(ctx: UmamusumeContext):
    time.sleep(2)
    if ctx.cultivate_detail.turn_info is None:
        log.warning("回合信息未初始化")
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return
    img = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2GRAY)
    if image_match(img, REF_RACE_LIST_GOAL_RACE).find_match:
        ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_2)
    elif image_match(img, REF_RACE_LIST_URA_RACE).find_match:
        ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_2)
    else:
        if ctx.cultivate_detail.turn_info.turn_operation is None:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
            return
        if ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_RACE:
            while True:
                ctx.ctrl.swipe(x1=20, y1=850, x2=20, y2=1000, duration=200, name="")
                img = cv2.cvtColor(ctx.ctrl.get_screen(), cv2.COLOR_BGR2RGB)
                if not compare_color_equal(img[705, 701], [211, 209, 219]):
                    time.sleep(1.5)
                    break
            img = ctx.ctrl.get_screen()
            while True:
                selected = find_race(ctx, img, ctx.cultivate_detail.turn_info.turn_operation.race_id)
                if selected:
                    time.sleep(1)
                    ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_2)
                    time.sleep(1)
                    return
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                if not compare_color_equal(img[1006, 701], [211, 209, 219]):
                    log.warning("未找到目标赛事")
                    # 没有合适的赛事就使用备用的操作
                    if ctx.cultivate_detail.turn_info.turn_operation.race_id == 0:
                        ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type = ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type_replace
                    ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
                    break
                ctx.ctrl.swipe(x1=20, y1=1000, x2=20, y2=850, duration=1000, name="")
                time.sleep(1)
                img = ctx.ctrl.get_screen()
        else:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)

# 575 745
def script_cultivate_before_race(ctx: UmamusumeContext):
    img = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2RGB)
    p_check_skip = img[1175, 330]

    date = ctx.cultivate_detail.turn_info.date
    if date != -1:
        tactic_check_point_list = [img[668, 480], img[668, 542], img[668, 600], img[668, 670]]
        if date <= 72:
            p_check_tactic = tactic_check_point_list[ctx.cultivate_detail.tactic_list[int((date-1)/24)] - 1]
        else:
            p_check_tactic = tactic_check_point_list[ctx.cultivate_detail.tactic_list[2] - 1]
        if compare_color_equal(p_check_tactic, [170, 170, 170]):
            ctx.ctrl.click_by_point(BEFORE_RACE_CHANGE_TACTIC)
            return

    if p_check_skip[0] < 200 and p_check_skip[1] < 200 and p_check_skip[2] < 200:
        ctx.ctrl.click_by_point(BEFORE_RACE_START)
    else:
        ctx.ctrl.click_by_point(BEFORE_RACE_SKIP)


def script_cultivate_in_race_uma_list(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(IN_RACE_UMA_LIST_CONFIRM)


def script_in_race(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(IN_RACE_SKIP)


def script_cultivate_race_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(RACE_RESULT_CONFIRM)


def script_cultivate_race_reward(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(RACE_REWARD_CONFIRM)


def script_cultivate_goal_achieved(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(GOAL_ACHIEVE_CONFIRM)


def script_cultivate_goal_failed(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(GOAL_FAIL_CONFIRM)

def script_cultivate_next_goal(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(NEXT_GOAL_CONFIRM)


def script_cultivate_extend(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_EXTEND_CONFIRM)


def script_cultivate_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_RESULT_CONFIRM)


def script_cultivate_catch_doll(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_CATCH_DOLL_START)


def script_cultivate_catch_doll_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_CATCH_DOLL_RESULT_CONFIRM)


def script_cultivate_finish(ctx: UmamusumeContext):
    if not ctx.cultivate_detail.learn_skill_done or not ctx.cultivate_detail.cultivate_finish:
        ctx.cultivate_detail.cultivate_finish = True
        ctx.ctrl.click_by_point(CULTIVATE_FINISH_LEARN_SKILL)
    else:
        ctx.ctrl.click_by_point(CULTIVATE_FINISH_CONFIRM)


def script_cultivate_learn_skill(ctx: UmamusumeContext):
    if ctx.cultivate_detail.learn_skill_done:
        if ctx.cultivate_detail.learn_skill_selected:
            ctx.ctrl.click_by_point(CULTIVATE_LEARN_SKILL_CONFIRM)
        else:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
        return
    learn_skill_list: list
    if ctx.cultivate_detail.cultivate_finish or not ctx.cultivate_detail.learn_skill_only_user_provided:
        if len(ctx.cultivate_detail.learn_skill_list) == 0:
            learn_skill_list = SKILL_LEARN_PRIORITY_LIST
        else:
            learn_skill_list = [ctx.cultivate_detail.learn_skill_list] + SKILL_LEARN_PRIORITY_LIST
    else:
        if len(ctx.cultivate_detail.learn_skill_list) == 0:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
            ctx.cultivate_detail.learn_skill_done = True
            ctx.cultivate_detail.turn_info.turn_learn_skill_done = True
            return
        else:
            learn_skill_list = [ctx.cultivate_detail.learn_skill_list]
    for i in range(len(learn_skill_list)):
        log.debug("目标技能列表：%s, 优先级：%s", str(learn_skill_list[i]), str(i))
        while True:
            img = ctx.ctrl.get_screen()
            find_skill(ctx, img, learn_skill_list[i], learn_any_skill=False)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if not compare_color_equal(img[1006, 701], [211, 209, 219]):
                break
            ctx.ctrl.swipe(x1=23, y1=1000, x2=23, y2=660, duration=1000, name="")
            time.sleep(1)
        while True:
            ctx.ctrl.swipe(x1=23, y1=620, x2=23, y2=1000, duration=100, name="")
            img = cv2.cvtColor(ctx.ctrl.get_screen(), cv2.COLOR_BGR2RGB)
            if not compare_color_equal(img[488, 701], [211, 209, 219]):
                time.sleep(1.5)
                break
    time.sleep(1)
    if ctx.cultivate_detail.cultivate_finish or not ctx.cultivate_detail.learn_skill_only_user_provided:
        while True:
            img = ctx.ctrl.get_screen()
            find_skill(ctx, img, [], learn_any_skill=True)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if not compare_color_equal(img[1006, 701], [211, 209, 219]):
                break
            ctx.ctrl.swipe(x1=23, y1=1000, x2=23, y2=640, duration=1000, name="")
            time.sleep(1)
    ctx.cultivate_detail.learn_skill_done = True
    ctx.cultivate_detail.turn_info.turn_learn_skill_done = True


def script_not_found_ui(ctx: UmamusumeContext):
    ctx.ctrl.click(719, 1, "")


def script_receive_cup(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_RECEIVE_CUP_CLOSE)


def script_cultivate_level_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_LEVEL_RESULT_CONFIRM)


def script_factor_receive(ctx: UmamusumeContext):
    if ctx.cultivate_detail.parse_factor_done:
        ctx.ctrl.click_by_point(CULTIVATE_FACTOR_RECEIVE_CONFIRM)
    else:
        parse_factor(ctx)


def script_historical_rating_update(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(HISTORICAL_RATING_UPDATE_CONFIRM)


def script_scenario_rating_update(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(SCENARIO_RATING_UPDATE_CONFIRM)

